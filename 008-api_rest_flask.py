#!/usr/bin/env python3
"""
====================================================
  MÓDULO 8 - API REST UNIFICADA (Flask)
====================================================
API RESTful que expone todos los servicios de NetHub
mediante endpoints HTTP. Incluye autenticación JWT
y métricas.
====================================================
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps
import jwt
import datetime
import os
from dotenv import load_dotenv

# Importar el modelo de base de datos
from database_models import (
    SessionLocal, DatabaseSession, crear_log, crear_mensaje
)

# Importar sistema de métricas
from metrics_prometheus import (
    REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_CONNECTIONS,
    ERRORS_COUNT, track_request, obtener_metricas_dict
)

load_dotenv()

# ══════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "nethub-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)  # Permitir CORS para el dashboard

# ══════════════════════════════════════════════════
#  UTILIDADES
# ══════════════════════════════════════════════════

def crear_token(username: str) -> str:
    """Genera un token JWT para el usuario."""
    expiracion = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "exp": expiracion,
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token_jwt(token: str) -> str:
    """Verifica el token JWT y retorna el username."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise ValueError("Token inválido")
        return username
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expirado")
    except jwt.JWTError:
        raise ValueError("No se pudo validar el token")

def requiere_autenticacion(f):
    """Decorador para endpoints que requieren autenticación."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "Token no proporcionado"}), 401
        
        try:
            # Formato: "Bearer <token>"
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({"error": "Formato de token inválido"}), 401
            
            token = parts[1]
            username = verificar_token_jwt(token)
            request.username = username  # Guardarlo en el request
            
        except ValueError as e:
            return jsonify({"error": str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def get_db_session():
    """Obtener sesión de base de datos."""
    return SessionLocal()

# ══════════════════════════════════════════════════
#  ENDPOINTS - RAÍZ Y DASHBOARD
# ══════════════════════════════════════════════════

@app.route('/')
def index():
    """Página principal."""
    return jsonify({
        "nombre": "NetHub API",
        "version": "2.0.0",
        "endpoints": {
            "auth": "/api/auth/login",
            "dashboard": "/dashboard",
            "metrics": "/metrics",
            "docs": "API REST unificada para NetHub"
        }
    })

@app.route('/dashboard')
@app.route('/dashboard.html')
def dashboard():
    """Servir el dashboard HTML."""
    ruta_dashboard = os.path.join(os.path.dirname(__file__), 'dashboard.html')
    return send_file(ruta_dashboard)

# ══════════════════════════════════════════════════
#  ENDPOINTS - AUTENTICACIÓN
# ══════════════════════════════════════════════════

@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Autenticar usuario y obtener token JWT.
    
    Body: {"username": "admin", "password": "admin123"}
    """
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Faltan credenciales"}), 400
    
    username = data['username']
    password = data['password']
    
    # Validación básica
    if len(username) < 3 or len(password) < 6:
        return jsonify({"error": "Credenciales inválidas"}), 400
    
    db = get_db_session()
    try:
        from database_models import obtener_usuario_por_username, verificar_password, actualizar_ultimo_acceso
        
        # Obtener usuario de la base de datos
        usuario = obtener_usuario_por_username(db, username)
        
        if not usuario:
            crear_log(db, "WARNING", "API", f"Usuario no existe: {username}")
            return jsonify({"error": "Credenciales incorrectas"}), 401
        
        # Verificar si el usuario está activo
        if not usuario['activo']:
            crear_log(db, "WARNING", "API", f"Usuario inactivo: {username}")
            return jsonify({"error": "Usuario inactivo"}), 403
        
        # Verificar contraseña
        if not verificar_password(password, usuario['password_hash']):
            crear_log(db, "WARNING", "API", f"Contraseña incorrecta: {username}")
            return jsonify({"error": "Credenciales incorrectas"}), 401
        
        # Actualizar último acceso
        actualizar_ultimo_acceso(db, username)
        
        # Crear token
        token = crear_token(username)
        crear_log(db, "INFO", "API", f"Login exitoso: {username}")
        
        REQUEST_COUNT.inc(endpoint="login", method="POST")
        
        return jsonify({
            "access_token": token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        })
        
    finally:
        db.close()

@app.route('/api/auth/verify', methods=['GET'])
@requiere_autenticacion
def verificar_autenticacion():
    """Verificar si el token es válido."""
    REQUEST_COUNT.inc(endpoint="verify_token", method="GET")
    return jsonify({
        "status": "ok",
        "username": request.username,
        "authenticated": True
    })

# ══════════════════════════════════════════════════
#  ENDPOINTS - CORREO ELECTRÓNICO
# ══════════════════════════════════════════════════

@app.route('/api/email/send', methods=['POST'])
@requiere_autenticacion
def enviar_email():
    """Enviar correo electrónico vía SMTP."""
    data = request.get_json()
    
    if not data or 'destinatario' not in data or 'asunto' not in data or 'cuerpo_html' not in data:
        return jsonify({"error": "Faltan campos requeridos"}), 400
    
    db = get_db_session()
    try:
        # Importar módulo SMTP dinámicamente
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "smtp_module", 
            os.path.join(os.path.dirname(__file__), "001-smtp_envio_correo.py")
        )
        smtp_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(smtp_mod)
        
        # Enviar correo
        exito = smtp_mod.enviar_correo(
            data['destinatario'], 
            data['asunto'], 
            data['cuerpo_html']
        )
        
        if exito:
            crear_log(db, "INFO", "SMTP", f"Correo enviado a {data['destinatario']}")
            crear_mensaje(db, "SMTP", request.username, data['destinatario'], data['asunto'])
            REQUEST_COUNT.inc(endpoint="send_email", method="POST")
            
            return jsonify({
                "status": "ok",
                "mensaje": "Correo enviado correctamente",
                "destinatario": data['destinatario']
            })
        else:
            return jsonify({"error": "Error al enviar correo"}), 500
            
    except Exception as e:
        crear_log(db, "ERROR", "SMTP", f"Error: {str(e)}")
        ERRORS_COUNT.inc(service="smtp", error_type=type(e).__name__)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/email/inbox', methods=['GET'])
@requiere_autenticacion
def obtener_bandeja():
    """Obtener últimos correos de la bandeja de entrada (IMAP)."""
    limite = request.args.get('limite', 10, type=int)
    
    db = get_db_session()
    try:
        crear_log(db, "INFO", "IMAP", f"Consulta de bandeja por {request.username}")
        REQUEST_COUNT.inc(endpoint="get_inbox", method="GET")
        
        return jsonify({
            "status": "ok",
            "mensajes": [],
            "total": 0,
            "info": "Implementar integración con módulo IMAP"
        })
    except Exception as e:
        crear_log(db, "ERROR", "IMAP", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

# ══════════════════════════════════════════════════
#  ENDPOINTS - INTELIGENCIA ARTIFICIAL
# ══════════════════════════════════════════════════

@app.route('/api/ia/ollama', methods=['POST'])
@requiere_autenticacion
def consultar_ollama():
    """Consultar modelo de IA local (Ollama)."""
    data = request.get_json()
    
    if not data or 'prompt' not in data:
        return jsonify({"error": "Falta el campo 'prompt'"}), 400
    
    prompt = data['prompt']
    modelo = data.get('modelo', 'llama2')
    temperatura = data.get('temperatura', 0.7)
    
    db = get_db_session()
    try:
        try:
            import ollama
        except ImportError:
            return jsonify({
                "error": "Ollama SDK no instalado. Instala con: pip install ollama"
            }), 503
        
        crear_log(db, "INFO", "Ollama", f"Consulta por {request.username}: {prompt[:50]}...")
        
        response = ollama.chat(
            model=modelo,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": temperatura}
        )
        
        respuesta = response["message"]["content"]
        
        REQUEST_COUNT.inc(endpoint="ia_ollama", method="POST")
        
        return jsonify({
            "status": "ok",
            "modelo": modelo,
            "prompt": prompt,
            "respuesta": respuesta,
            "temperatura": temperatura
        })
        
    except Exception as e:
        crear_log(db, "ERROR", "Ollama", str(e))
        ERRORS_COUNT.inc(service="ollama", error_type=type(e).__name__)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/ia/remota', methods=['POST'])
@requiere_autenticacion
def consultar_ia_remota():
    """Consultar IA remota (jocarsa.com)."""
    data = request.get_json()
    
    if not data or 'prompt' not in data:
        return jsonify({"error": "Falta el campo 'prompt'"}), 400
    
    db = get_db_session()
    try:
        import requests as req
        
        crear_log(db, "INFO", "IA_Remota", f"Consulta por {request.username}")
        
        # Aquí iría la integración con el servicio remoto
        response = req.post(
            "https://jocarsa.com/ia/api",
            json={"prompt": data['prompt']}
        )
        
        REQUEST_COUNT.inc(endpoint="ia_remota", method="POST")
        
        return jsonify({
            "status": "ok",
            "respuesta": response.json()
        })
        
    except Exception as e:
        crear_log(db, "ERROR", "IA_Remota", str(e))
        ERRORS_COUNT.inc(service="ia_remota", error_type=type(e).__name__)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

# ══════════════════════════════════════════════════
#  ENDPOINTS - MONITOREO Y LOGS
# ══════════════════════════════════════════════════

@app.route('/api/logs', methods=['GET'])
@requiere_autenticacion
def obtener_logs():
    """Obtener logs del sistema."""
    limite = request.args.get('limite', 50, type=int)
    servicio = request.args.get('servicio', None)
    
    db = get_db_session()
    try:
        from database_models import obtener_ultimos_logs
        
        logs = obtener_ultimos_logs(db, limite=limite, servicio=servicio)
        
        REQUEST_COUNT.inc(endpoint="get_logs", method="GET")
        
        return jsonify([
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "nivel": log.nivel,
                "servicio": log.servicio,
                "mensaje": log.mensaje
            }
            for log in logs
        ])
        
    finally:
        db.close()

@app.route('/api/stats', methods=['GET'])
@requiere_autenticacion
def obtener_estadisticas():
    """Obtener estadísticas del sistema."""
    db = get_db_session()
    try:
        from database_models import obtener_estadisticas as get_stats, obtener_logs_por_nivel, obtener_logs_por_servicio
        
        # Estadísticas generales
        stats = get_stats(db)
        
        # Logs agrupados
        logs_por_nivel = obtener_logs_por_nivel(db)
        logs_por_servicio = obtener_logs_por_servicio(db)
        
        REQUEST_COUNT.inc(endpoint="get_stats", method="GET")
        
        return jsonify({
            "total_logs": stats['total_logs'],
            "total_mensajes": stats['total_mensajes'],
            "total_conexiones": stats['total_conexiones'],
            "logs_por_nivel": logs_por_nivel,
            "logs_por_servicio": logs_por_servicio,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
    finally:
        db.close()

@app.route('/api/logs/clear', methods=['DELETE'])
@requiere_autenticacion
def limpiar_logs():
    """Limpiar todos los logs (solo admin)."""
    if request.username != "admin":
        return jsonify({"error": "Acceso denegado"}), 403
    
    db = get_db_session()
    try:
        db.execute("DELETE FROM logs")
        db.commit()
        
        crear_log(db, "INFO", "API", f"Logs limpiados por {request.username}")
        
        REQUEST_COUNT.inc(endpoint="clear_logs", method="DELETE")
        
        return jsonify({
            "status": "ok",
            "mensaje": "Logs limpiados correctamente"
        })
        
    finally:
        db.close()

# ══════════════════════════════════════════════════
#  ENDPOINTS - MÉTRICAS
# ══════════════════════════════════════════════════

@app.route('/metrics')
def metrics():
    """Obtener métricas del sistema en formato JSON."""
    metricas = obtener_metricas_dict()
    return jsonify(metricas)

# ══════════════════════════════════════════════════
#  EJECUTAR SERVIDOR
# ══════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════╗")
    print("║          NetHub - API REST (Flask)               ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("🌐 Servidor: http://localhost:8000")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("📈 Métricas: http://localhost:8000/metrics")
    print()
    print("🔑 Usuario de prueba: admin / admin123")
    print()
    
    # Inicializar base de datos
    from database_models import inicializar_base_datos
    inicializar_base_datos()
    
    # Iniciar servidor Flask
    app.run(host="0.0.0.0", port=8000, debug=True)
