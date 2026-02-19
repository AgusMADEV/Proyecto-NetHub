#!/usr/bin/env python3
"""
====================================================
  MÓDULO 9A - SERVIDOR TCP CON CIFRADO TLS/SSL
====================================================
Servidor TCP seguro con cifrado TLS para comunicaciones
protegidas. Incluye autenticación de clientes y logging
a base de datos.
====================================================
"""

import socket
import ssl
import threading
import json
import datetime
import os
from pathlib import Path

# Importar modelos de BD
from database_models import SessionLocal, crear_log, crear_conexion, cerrar_conexion
from metrics_prometheus import (
    ACTIVE_CONNECTIONS, registrar_mensaje_recibido, 
    registrar_mensaje_enviado, ERRORS_COUNT
)

# ══════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════

HOST = "0.0.0.0"
PORT = 9502
ENCODE = "utf-8"

# Rutas de certificados TLS
CERT_DIR = Path(__file__).parent / "certs"
CERT_FILE = CERT_DIR / "server.crt"
KEY_FILE = CERT_DIR / "server.key"

# ══════════════════════════════════════════════════
#  GENERACIÓN DE CERTIFICADOS AUTOFIRMADOS
# ══════════════════════════════════════════════════

def generar_certificados_ssl():
    """
    Genera certificados SSL autofirmados si no existen.
    En producción, usar certificados de una CA confiable.
    """
    if CERT_FILE.exists() and KEY_FILE.exists():
        print("[TLS] ✅ Certificados SSL encontrados")
        return True
    
    print("[TLS] 📝 Generando certificados SSL autofirmados...")
    
    # Crear directorio si no existe
    CERT_DIR.mkdir(exist_ok=True)
    
    # Intentar con pyOpenSSL
    try:
        from OpenSSL import crypto
        
        # Generar clave privada
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)
        
        # Generar certificado
        cert = crypto.X509()
        cert.get_subject().C = "ES"
        cert.get_subject().ST = "Madrid"
        cert.get_subject().L = "Madrid"
        cert.get_subject().O = "NetHub"
        cert.get_subject().OU = "DAM-2"
        cert.get_subject().CN = "localhost"
        
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1 año
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha256')
        
        # Guardar certificado
        with open(CERT_FILE, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        
        # Guardar clave privada
        with open(KEY_FILE, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
        
        print(f"[TLS] ✅ Certificados generados con pyOpenSSL")
        return True
        
    except ImportError:
        print("[TLS] ⚠️  pyOpenSSL no instalado. Intentando con OpenSSL CLI...")
        
        # Método alternativo usando subprocess y openssl CLI
        import subprocess
        
        comando = [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", str(KEY_FILE),
            "-out", str(CERT_FILE),
            "-days", "365", "-nodes",
            "-subj", "/C=ES/ST=Madrid/L=Madrid/O=NetHub/OU=DAM-2/CN=localhost"
        ]
        
        try:
            subprocess.run(comando, check=True, capture_output=True)
            print(f"[TLS] ✅ Certificados generados con OpenSSL CLI")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[TLS] ❌ No se pudieron generar certificados automáticamente")
            print("       ")
            print("       Opciones:")
            print("       1. Instala pyOpenSSL: pip install pyOpenSSL")
            print("       2. Instala OpenSSL: https://slproweb.com/products/Win32OpenSSL.html")
            print("       3. Genera manualmente los certificados")
            return False
    
    return True


# ══════════════════════════════════════════════════
#  PROCESAMIENTO DE COMANDOS
# ══════════════════════════════════════════════════

def procesar_comando_seguro(comando: str, cliente_info: dict) -> dict:
    """
    Procesa comandos del cliente de forma segura.
    Incluye comandos adicionales para demostrar TLS.
    """
    cmd = comando.strip().lower()
    
    comandos = {
        "hora": lambda: {
            "estado": "ok",
            "comando": "hora",
            "respuesta": datetime.datetime.now().strftime("%H:%M:%S"),
            "cifrado": True
        },
        "fecha": lambda: {
            "estado": "ok",
            "comando": "fecha",
            "respuesta": datetime.datetime.now().strftime("%d/%m/%Y"),
            "cifrado": True
        },
        "ping": lambda: {
            "estado": "ok",
            "comando": "ping",
            "respuesta": "pong",
            "cifrado": True
        },
        "info": lambda: {
            "estado": "ok",
            "comando": "info",
            "servidor": "NetHub TLS Server v2.0",
            "protocolo": f"TLS {cliente_info.get('version', 'unknown')}",
            "cipher": cliente_info.get('cipher', 'unknown'),
            "certificado": "Autofirmado",
            "cifrado": True
        },
        "stats": lambda: {
            "estado": "ok",
            "comando": "stats",
            "conexion_segura": True,
            "ip_cliente": cliente_info.get('ip', 'unknown'),
            "puerto_cliente": cliente_info.get('puerto', 0),
            "cifrado": True
        },
        "help": lambda: {
            "estado": "ok",
            "comando": "help",
            "comandos_disponibles": [
                "hora - Obtener hora actual",
                "fecha - Obtener fecha actual",
                "ping - Test de conectividad",
                "info - Información del servidor",
                "stats - Estadísticas de conexión",
                "help - Esta ayuda",
                "ia <pregunta> - Consultar IA",
                "exit - Cerrar conexión"
            ],
            "cifrado": True
        }
    }
    
    # Comando genérico
    if cmd in comandos:
        return comandos[cmd]()
    
    # Comando de IA
    if cmd.startswith("ia "):
        pregunta = comando[3:].strip()
        try:
            import ollama
            response = ollama.chat(
                model="llama2",
                messages=[{"role": "user", "content": pregunta}]
            )
            return {
                "estado": "ok",
                "comando": "ia",
                "pregunta": pregunta,
                "respuesta": response["message"]["content"],
                "cifrado": True
            }
        except ImportError:
            return {
                "estado": "error",
                "comando": "ia",
                "mensaje": "Ollama SDK no instalado. Instala con: pip install ollama",
                "cifrado": True
            }
        except Exception as e:
            return {
                "estado": "error",
                "comando": "ia",
                "mensaje": f"Error en IA: {str(e)}",
                "cifrado": True
            }
    
    # Comando desconocido
    return {
        "estado": "error",
        "comando": cmd,
        "mensaje": "Comando no reconocido. Usa 'help' para ver comandos disponibles.",
        "cifrado": True
    }


# ══════════════════════════════════════════════════
#  MANEJADOR DE CLIENTE
# ══════════════════════════════════════════════════

def manejar_cliente_tls(conn_ssl, addr, db):
    """
    Maneja la conexión de un cliente TLS.
    """
    cliente_ip, cliente_puerto = addr
    conexion_id = None
    
    try:
        # Obtener información del cifrado
        cipher = conn_ssl.cipher()
        version = conn_ssl.version()
        
        cliente_info = {
            'ip': cliente_ip,
            'puerto': cliente_puerto,
            'cipher': cipher[0] if cipher else 'unknown',
            'version': version if version else 'unknown'
        }
        
        print(f"\n[TLS] 🔒 Cliente conectado: {cliente_ip}:{cliente_puerto}")
        print(f"      Cipher: {cliente_info['cipher']}")
        print(f"      Version: {cliente_info['version']}")
        
        # Registrar conexión en BD
        conexion_id = crear_conexion(
            db,
            tipo="TCP_TLS",
            ip_cliente=cliente_ip,
            puerto_cliente=cliente_puerto,
            ip_servidor=HOST,
            puerto_servidor=PORT,
            estado="ACTIVA"
        ).id
        
        crear_log(
            db,
            "INFO",
            "TCP_TLS",
            f"Conexión segura establecida desde {cliente_ip}:{cliente_puerto}",
            ip_origen=cliente_ip
        )
        
        # Mensaje de bienvenida
        bienvenida = {
            "tipo": "bienvenida",
            "mensaje": "Bienvenido al servidor NetHub TLS",
            "version": "2.0",
            "conexion_segura": True,
            "cipher": cliente_info['cipher'],
            "instrucciones": "Escribe 'help' para ver comandos disponibles"
        }
        
        conn_ssl.sendall((json.dumps(bienvenida) + "\n").encode(ENCODE))
        registrar_mensaje_enviado("tcp_tls")
        
        bytes_recibidos = 0
        bytes_enviados = len(json.dumps(bienvenida))
        
        # Loop de comunicación
        while True:
            data = conn_ssl.recv(4096)
            
            if not data:
                print(f"[TLS] 🔌 Cliente {cliente_ip} desconectado")
                break
            
            bytes_recibidos += len(data)
            mensaje = data.decode(ENCODE).strip()
            
            print(f"[TLS] 📨 {cliente_ip}: {mensaje}")
            registrar_mensaje_recibido("tcp_tls")
            
            # Procesar comando
            if mensaje.lower() == "exit":
                respuesta = {
                    "estado": "ok",
                    "mensaje": "Cerrando conexión. ¡Hasta pronto!",
                    "cifrado": True
                }
                conn_ssl.sendall((json.dumps(respuesta) + "\n").encode(ENCODE))
                break
            
            respuesta = procesar_comando_seguro(mensaje, cliente_info)
            respuesta_json = json.dumps(respuesta) + "\n"
            
            conn_ssl.sendall(respuesta_json.encode(ENCODE))
            bytes_enviados += len(respuesta_json)
            registrar_mensaje_enviado("tcp_tls")
            
            print(f"[TLS] 📤 Respuesta enviada (cifrada)")
        
        # Cerrar conexión en BD
        if conexion_id:
            cerrar_conexion(db, conexion_id, bytes_enviados, bytes_recibidos)
        
        crear_log(
            db,
            "INFO",
            "TCP_TLS",
            f"Conexión cerrada: {cliente_ip}:{cliente_puerto} "
            f"({bytes_recibidos} bytes ↓, {bytes_enviados} bytes ↑)",
            ip_origen=cliente_ip
        )
        
    except ssl.SSLError as e:
        print(f"[TLS] ❌ Error SSL con {cliente_ip}: {e}")
        crear_log(db, "ERROR", "TCP_TLS", f"Error SSL: {str(e)}", ip_origen=cliente_ip)
        ERRORS_COUNT.labels(service="tcp_tls", error_type="ssl_error").inc()
        
    except Exception as e:
        print(f"[TLS] ❌ Error con {cliente_ip}: {e}")
        crear_log(db, "ERROR", "TCP_TLS", f"Error: {str(e)}", ip_origen=cliente_ip)
        ERRORS_COUNT.labels(service="tcp_tls", error_type=type(e).__name__).inc()
        
    finally:
        conn_ssl.close()
        ACTIVE_CONNECTIONS.labels(connection_type="tcp_tls").dec()


# ══════════════════════════════════════════════════
#  SERVIDOR PRINCIPAL
# ══════════════════════════════════════════════════

def iniciar_servidor_tls():
    """Inicia el servidor TCP con TLS."""
    
    # Generar certificados si no existen
    if not generar_certificados_ssl():
        print("[TLS] ❌ No se pudo iniciar el servidor sin certificados")
        return
    
    # Crear contexto SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    # Configuraciones de seguridad
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    
    # Crear socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)
    
    print("╔══════════════════════════════════════════════════╗")
    print("║       Servidor TCP con Cifrado TLS/SSL          ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"\n🔒 Servidor escuchando en {HOST}:{PORT}")
    print(f"🔐 Cifrado: TLS 1.2+")
    print(f"📜 Certificado: {CERT_FILE.name}")
    print(f"🔑 Clave: {KEY_FILE.name}")
    print("\n⚡ Presiona Ctrl+C para detener el servidor")
    print("─" * 52)
    
    # Inicializar contador de conexiones
    ACTIVE_CONNECTIONS.labels(connection_type="tcp_tls").set(0)
    
    # Crear log inicial
    db = SessionLocal()
    crear_log(db, "INFO", "TCP_TLS", f"Servidor TLS iniciado en {HOST}:{PORT}")
    db.close()
    
    try:
        while True:
            # Aceptar conexión
            conn, addr = sock.accept()
            
            # Envolver en TLS
            conn_ssl = context.wrap_socket(conn, server_side=True)
            
            # Incrementar contador
            ACTIVE_CONNECTIONS.labels(connection_type="tcp_tls").inc()
            
            # Manejar en un hilo separado
            db = SessionLocal()
            hilo = threading.Thread(
                target=manejar_cliente_tls,
                args=(conn_ssl, addr, db),
                daemon=True
            )
            hilo.start()
            
    except KeyboardInterrupt:
        print("\n\n[TLS] 🛑 Deteniendo servidor...")
        db = SessionLocal()
        crear_log(db, "INFO", "TCP_TLS", "Servidor TLS detenido")
        db.close()
        
    finally:
        sock.close()
        print("[TLS] ✅ Servidor cerrado correctamente")


def main():
    """Punto de entrada principal."""
    iniciar_servidor_tls()


if __name__ == "__main__":
    main()
