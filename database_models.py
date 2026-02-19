#!/usr/bin/env python3
"""
====================================================
  MÓDULO - BASE DE DATOS SQLite (Nativo)
====================================================
Define las funciones de base de datos para logs, mensajes,
conexiones y usuarios. Utiliza SQLite3 nativo (sin ORM).
====================================================
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Generator, Any
from contextlib import contextmanager
import threading

# ══════════════════════════════════════════════════
#  CONFIGURACIÓN DE BASE DE DATOS
# ══════════════════════════════════════════════════

DATABASE_FILE = "nethub.db"

# Thread-local storage para conexiones
_thread_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Obtener conexión SQLite (una por thread)."""
    if not hasattr(_thread_local, 'conn') or _thread_local.conn is None:
        _thread_local.conn = sqlite3.connect(
            DATABASE_FILE,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        _thread_local.conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
    return _thread_local.conn


# ══════════════════════════════════════════════════
#  CLASES MODELO (Simplificadas)
# ══════════════════════════════════════════════════

class Log:
    """Representación de un log."""
    def __init__(self, row: sqlite3.Row):
        self.id = row['id']
        self.timestamp = datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None
        self.nivel = row['nivel']
        self.servicio = row['servicio']
        self.mensaje = row['mensaje']
        self.ip_origen = row['ip_origen']
        self.usuario = row['usuario']


class Message:
    """Representación de un mensaje."""
    def __init__(self, row: sqlite3.Row):
        self.id = row['id']
        self.timestamp = datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None
        self.tipo = row['tipo']
        self.remitente = row['remitente']
        self.destinatario = row['destinatario']
        self.asunto = row['asunto']
        self.contenido = row['contenido']
        self.estado = row['estado']
        self.tamano_bytes = row['tamano_bytes']


class Connection:
    """Representación de una conexión."""
    def __init__(self, row: sqlite3.Row):
        self.id = row['id']
        self.timestamp_inicio = datetime.fromisoformat(row['timestamp_inicio']) if row['timestamp_inicio'] else None
        self.timestamp_fin = datetime.fromisoformat(row['timestamp_fin']) if row['timestamp_fin'] else None
        self.tipo = row['tipo']
        self.ip_cliente = row['ip_cliente']
        self.puerto_cliente = row['puerto_cliente']
        self.ip_servidor = row['ip_servidor']
        self.puerto_servidor = row['puerto_servidor']
        self.estado = row['estado']
        self.bytes_enviados = row['bytes_enviados']
        self.bytes_recibidos = row['bytes_recibidos']


class DatabaseSession:
    """Sesión de base de datos (simulación de SQLAlchemy Session)."""
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def execute(self, query: str, params: tuple = ()):
        """Ejecutar consulta SQL."""
        return self.cursor.execute(query, params)
    
    def commit(self):
        """Confirmar transacción."""
        self.conn.commit()
    
    def rollback(self):
        """Revertir transacción."""
        self.conn.rollback()
    
    def close(self):
        """Cerrar cursor (conexión se mantiene en thread local)."""
        if self.cursor:
            self.cursor.close()


# ══════════════════════════════════════════════════
#  FUNCIONES DE UTILIDAD
# ══════════════════════════════════════════════════

def crear_tablas():
    """Crear todas las tablas en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            nivel TEXT NOT NULL,
            servicio TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            ip_origen TEXT,
            usuario TEXT
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_nivel ON logs(nivel)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_servicio ON logs(servicio)")
    
    # Tabla de mensajes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            tipo TEXT NOT NULL,
            remitente TEXT NOT NULL,
            destinatario TEXT NOT NULL,
            asunto TEXT,
            contenido TEXT,
            estado TEXT NOT NULL,
            tamano_bytes INTEGER
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_tipo ON messages(tipo)")
    
    # Tabla de conexiones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_inicio TEXT NOT NULL DEFAULT (datetime('now')),
            timestamp_fin TEXT,
            tipo TEXT NOT NULL,
            ip_cliente TEXT NOT NULL,
            puerto_cliente INTEGER NOT NULL,
            ip_servidor TEXT NOT NULL,
            puerto_servidor INTEGER NOT NULL,
            estado TEXT NOT NULL,
            bytes_enviados INTEGER DEFAULT 0,
            bytes_recibidos INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_timestamp ON connections(timestamp_inicio)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_tipo ON connections(tipo)")
    
    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            activo INTEGER DEFAULT 1,
            es_admin INTEGER DEFAULT 0,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now')),
            ultimo_acceso TEXT
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)")
    
    # Tabla de métricas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metricas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            nombre_metrica TEXT NOT NULL,
            valor TEXT NOT NULL,
            etiquetas TEXT
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metricas_timestamp ON metricas(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metricas_nombre ON metricas(nombre_metrica)")
    
    conn.commit()
    print("[DB] ✅ Tablas creadas/verificadas correctamente")


def get_db() -> Generator[DatabaseSession, None, None]:
    """
    Dependency para FastAPI que proporciona una sesión de BD.
    Se cierra automáticamente al finalizar.
    """
    conn = get_connection()
    db = DatabaseSession(conn)
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def SessionLocal() -> DatabaseSession:
    """
    Crear una nueva sesión de base de datos (compatibilidad con código antiguo).
    IMPORTANTE: Debe cerrarse manualmente con db.close()
    """
    conn = get_connection()
    return DatabaseSession(conn)


def crear_log(
    db: DatabaseSession, 
    nivel: str, 
    servicio: str, 
    mensaje: str,
    ip_origen: str = None,
    usuario: str = None
) -> dict:
    """Crear un registro de log en la base de datos."""
    db.execute(
        """INSERT INTO logs (nivel, servicio, mensaje, ip_origen, usuario) 
           VALUES (?, ?, ?, ?, ?)""",
        (nivel, servicio, mensaje, ip_origen, usuario)
    )
    db.commit()
    return {"id": db.cursor.lastrowid, "nivel": nivel, "servicio": servicio}


def crear_mensaje(
    db: DatabaseSession,
    tipo: str,
    remitente: str,
    destinatario: str,
    asunto: str = None,
    contenido: str = None,
    estado: str = "ENVIADO"
) -> dict:
    """Crear un registro de mensaje."""
    tamano_bytes = len(contenido) if contenido else 0
    
    db.execute(
        """INSERT INTO messages (tipo, remitente, destinatario, asunto, contenido, estado, tamano_bytes) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (tipo, remitente, destinatario, asunto, contenido, estado, tamano_bytes)
    )
    db.commit()
    return {"id": db.cursor.lastrowid, "tipo": tipo}


def crear_conexion(
    db: DatabaseSession,
    tipo: str,
    ip_cliente: str,
    puerto_cliente: int,
    ip_servidor: str,
    puerto_servidor: int,
    estado: str = "ACTIVA"
) -> dict:
    """Registrar una nueva conexión."""
    db.execute(
        """INSERT INTO connections (tipo, ip_cliente, puerto_cliente, ip_servidor, puerto_servidor, estado) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (tipo, ip_cliente, puerto_cliente, ip_servidor, puerto_servidor, estado)
    )
    db.commit()
    return {"id": db.cursor.lastrowid, "tipo": tipo, "estado": estado}


def cerrar_conexion(
    db: DatabaseSession,
    conexion_id: int,
    bytes_enviados: int = 0,
    bytes_recibidos: int = 0
):
    """Marcar una conexión como cerrada."""
    db.execute(
        """UPDATE connections 
           SET timestamp_fin = datetime('now'), estado = 'CERRADA', 
               bytes_enviados = ?, bytes_recibidos = ?
           WHERE id = ?""",
        (bytes_enviados, bytes_recibidos, conexion_id)
    )
    db.commit()


def obtener_ultimos_logs(db: DatabaseSession, limite: int = 50, servicio: str = None) -> list[Log]:
    """Obtener los últimos logs del sistema."""
    if servicio:
        rows = db.execute(
            "SELECT * FROM logs WHERE servicio = ? ORDER BY timestamp DESC LIMIT ?",
            (servicio, limite)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?",
            (limite,)
        ).fetchall()
    return [Log(row) for row in rows]


def obtener_logs_por_nivel(db: DatabaseSession) -> dict:
    """Obtener conteo de logs agrupados por nivel."""
    rows = db.execute(
        "SELECT nivel, COUNT(*) as count FROM logs GROUP BY nivel"
    ).fetchall()
    return {row['nivel']: row['count'] for row in rows}


def obtener_logs_por_servicio(db: DatabaseSession) -> dict:
    """Obtener conteo de logs agrupados por servicio."""
    rows = db.execute(
        "SELECT servicio, COUNT(*) as count FROM logs GROUP BY servicio"
    ).fetchall()
    return {row['servicio']: row['count'] for row in rows}


def obtener_estadisticas(db: DatabaseSession) -> dict:
    """Obtener estadísticas generales del sistema."""
    stats = {}
    
    stats['total_logs'] = db.execute("SELECT COUNT(*) as count FROM logs").fetchone()['count']
    stats['total_mensajes'] = db.execute("SELECT COUNT(*) as count FROM messages").fetchone()['count']
    stats['total_conexiones'] = db.execute("SELECT COUNT(*) as count FROM connections").fetchone()['count']
    stats['conexiones_activas'] = db.execute(
        "SELECT COUNT(*) as count FROM connections WHERE estado = 'ACTIVA'"
    ).fetchone()['count']
    stats['errores_recientes'] = db.execute(
        "SELECT COUNT(*) as count FROM logs WHERE nivel = 'ERROR'"
    ).fetchone()['count']
    
    return stats


def limpiar_logs_antiguos(db: DatabaseSession, dias: int = 30) -> int:
    """Eliminar logs más antiguos que X días."""
    fecha_limite = (datetime.utcnow() - timedelta(days=dias)).isoformat()
    
    result = db.execute(
        "DELETE FROM logs WHERE timestamp < ?",
        (fecha_limite,)
    )
    db.commit()
    
    return result.rowcount


# ══════════════════════════════════════════════════
#  FUNCIONES DE USUARIOS Y AUTENTICACIÓN
# ══════════════════════════════════════════════════

def obtener_usuario_por_username(db: DatabaseSession, username: str) -> dict | None:
    """Obtener usuario por nombre de usuario."""
    row = db.execute(
        "SELECT * FROM usuarios WHERE username = ?",
        (username,)
    ).fetchone()
    
    if row:
        return {
            'id': row['id'],
            'username': row['username'],
            'email': row['email'],
            'password_hash': row['password_hash'],
            'activo': bool(row['activo']),
            'es_admin': bool(row['es_admin']),
            'fecha_creacion': row['fecha_creacion'],
            'ultimo_acceso': row['ultimo_acceso']
        }
    return None


def verificar_password(password: str, password_hash: str) -> bool:
    """Verificar contraseña contra hash almacenado."""
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except ImportError:
        # Fallback a hash simple
        import hashlib
        hash_simple = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return hash_simple == password_hash


def actualizar_ultimo_acceso(db: DatabaseSession, username: str):
    """Actualizar timestamp del último acceso del usuario."""
    db.execute(
        "UPDATE usuarios SET ultimo_acceso = datetime('now') WHERE username = ?",
        (username,)
    )
    db.commit()


# ══════════════════════════════════════════════════
#  INICIALIZACIÓN
# ══════════════════════════════════════════════════

def inicializar_base_datos():
    """Inicializar la base de datos con datos por defecto."""
    crear_tablas()
    
    conn = get_connection()
    db = DatabaseSession(conn)
    
    try:
        # Verificar si ya hay usuarios
        count = db.execute("SELECT COUNT(*) as count FROM usuarios").fetchone()['count']
        
        if count == 0:
            # Crear usuario admin por defecto
            try:
                import bcrypt
                password_hash = bcrypt.hashpw(
                    "admin123".encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
            except ImportError:
                # Si bcrypt no está instalado, usar hash simple (NO USAR EN PRODUCCIÓN)
                import hashlib
                password_hash = hashlib.sha256("admin123".encode('utf-8')).hexdigest()
                print("[DB] ⚠️  bcrypt no instalado - usando hash básico (instala bcrypt para producción)")
            
            db.execute(
                """INSERT INTO usuarios (username, email, password_hash, activo, es_admin) 
                   VALUES (?, ?, ?, 1, 1)""",
                ("admin", "admin@nethub.local", password_hash)
            )
            
            # Log inicial
            crear_log(
                db, 
                "INFO", 
                "Sistema", 
                "Base de datos inicializada correctamente"
            )
            
            db.commit()
            print("[DB] ✅ Usuario admin creado (usuario: admin, password: admin123)")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════╗")
    print("║     NetHub - Inicialización de Base de Datos    ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    inicializar_base_datos()
    
    # Mostrar estadísticas
    conn = get_connection()
    db = DatabaseSession(conn)
    try:
        stats = obtener_estadisticas(db)
        print("\n📊 Estadísticas:")
        for clave, valor in stats.items():
            print(f"   • {clave}: {valor}")
    finally:
        db.close()
    
    print("\n✅ Base de datos lista para usar")
