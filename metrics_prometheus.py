#!/usr/bin/env python3
"""
====================================================
  MÓDULO - MÉTRICAS VANILLA (SIN DEPENDENCIAS)
====================================================
Sistema de métricas nativo para monitoreo.
Recopila estadísticas de uso, rendimiento y errores
sin dependencias externas.
====================================================
"""

from functools import wraps
from threading import Lock
import time
import json
from typing import Callable, Dict, List, Any
from collections import defaultdict

# ══════════════════════════════════════════════════
#  CLASES DE MÉTRICAS VANILLA
# ══════════════════════════════════════════════════

class Counter:
    """Contador simple thread-safe."""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values = defaultdict(int)
        self._lock = Lock()
    
    def labels(self, **kwargs):
        """Retorna un contador con labels específicos."""
        return LabeledCounter(self, **kwargs)
    
    def inc(self, amount=1, **label_values):
        """Incrementar el contador."""
        with self._lock:
            key = tuple(sorted(label_values.items()))
            self._values[key] += amount
    
    def get_value(self, **label_values):
        """Obtener valor actual."""
        key = tuple(sorted(label_values.items()))
        return self._values.get(key, 0)
    
    def get_all(self):
        """Obtener todos los valores."""
        return dict(self._values)


class LabeledCounter:
    """Contador con labels pre-establecidos."""
    
    def __init__(self, counter: Counter, **labels):
        self.counter = counter
        self.labels = labels
    
    def inc(self, amount=1):
        """Incrementar."""
        self.counter.inc(amount, **self.labels)


class Gauge:
    """Gauge simple thread-safe."""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values = defaultdict(float)
        self._lock = Lock()
    
    def labels(self, **kwargs):
        """Retorna un gauge con labels específicos."""
        return LabeledGauge(self, **kwargs)
    
    def set(self, value, **label_values):
        """Establecer valor."""
        with self._lock:
            key = tuple(sorted(label_values.items()))
            self._values[key] = float(value)
    
    def inc(self, amount=1, **label_values):
        """Incrementar."""
        with self._lock:
            key = tuple(sorted(label_values.items()))
            self._values[key] = self._values.get(key, 0) + amount
    
    def dec(self, amount=1, **label_values):
        """Decrementar."""
        with self._lock:
            key = tuple(sorted(label_values.items()))
            self._values[key] = self._values.get(key, 0) - amount
    
    def get_value(self, **label_values):
        """Obtener valor actual."""
        key = tuple(sorted(label_values.items()))
        return self._values.get(key, 0)
    
    def get_all(self):
        """Obtener todos los valores."""
        return dict(self._values)


class LabeledGauge:
    """Gauge con labels pre-establecidos."""
    
    def __init__(self, gauge: Gauge, **labels):
        self.gauge = gauge
        self.labels = labels
    
    def set(self, value):
        """Establecer valor."""
        self.gauge.set(value, **self.labels)
    
    def inc(self, amount=1):
        """Incrementar."""
        self.gauge.inc(amount, **self.labels)
    
    def dec(self, amount=1):
        """Decrementar."""
        self.gauge.dec(amount, **self.labels)


class Histogram:
    """Histograma simple para medir duraciones."""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._observations = defaultdict(list)
        self._lock = Lock()
    
    def labels(self, **kwargs):
        """Retorna un histograma con labels específicos."""
        return LabeledHistogram(self, **kwargs)
    
    def observe(self, value, **label_values):
        """Registrar una observación."""
        with self._lock:
            key = tuple(sorted(label_values.items()))
            self._observations[key].append(float(value))
    
    def get_stats(self, **label_values):
        """Obtener estadísticas (count, sum, avg, min, max)."""
        key = tuple(sorted(label_values.items()))
        observations = self._observations.get(key, [])
        
        if not observations:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}
        
        return {
            "count": len(observations),
            "sum": sum(observations),
            "avg": sum(observations) / len(observations),
            "min": min(observations),
            "max": max(observations)
        }
    
    def get_all(self):
        """Obtener todas las estadísticas."""
        result = {}
        for key, observations in self._observations.items():
            labels_dict = dict(key) if key else {}
            stats = self.get_stats(**labels_dict)
            result[str(labels_dict)] = stats
        return result


class LabeledHistogram:
    """Histograma con labels pre-establecidos."""
    
    def __init__(self, histogram: Histogram, **labels):
        self.histogram = histogram
        self.labels = labels
    
    def observe(self, value):
        """Registrar observación."""
        self.histogram.observe(value, **self.labels)


# ══════════════════════════════════════════════════
#  DEFINICIÓN DE MÉTRICAS
# ══════════════════════════════════════════════════

# Contador de peticiones HTTP por endpoint
REQUEST_COUNT = Counter(
    'nethub_http_requests_total',
    'Total de peticiones HTTP recibidas',
    ['method', 'endpoint', 'status']
)

# Histograma de latencia de peticiones
REQUEST_LATENCY = Histogram(
    'nethub_request_duration_seconds',
    'Duración de peticiones HTTP en segundos',
    ['endpoint']
)

# Contador de errores por servicio
ERRORS_COUNT = Counter(
    'nethub_errors_total',
    'Total de errores por servicio',
    ['service', 'error_type']
)

# Gauge de conexiones activas
ACTIVE_CONNECTIONS = Gauge(
    'nethub_active_connections',
    'Número de conexiones activas',
    ['connection_type']
)

# Contador de mensajes enviados
MESSAGES_SENT = Counter(
    'nethub_messages_sent_total',
    'Total de mensajes enviados',
    ['message_type']
)

# Contador de mensajes recibidos
MESSAGES_RECEIVED = Counter(
    'nethub_messages_received_total',
    'Total de mensajes recibidos',
    ['message_type']
)

# Gauge de bytes transferidos
BYTES_TRANSFERRED = Gauge(
    'nethub_bytes_transferred',
    'Bytes transferidos',
    ['direction']  # sent/received
)

# Contador de autenticaciones
AUTH_ATTEMPTS = Counter(
    'nethub_auth_attempts_total',
    'Intentos de autenticación',
    ['status']  # success/failure
)

# Histograma de tiempo de respuesta de IA
IA_RESPONSE_TIME = Histogram(
    'nethub_ia_response_seconds',
    'Tiempo de respuesta de consultas a IA',
    ['model']
)

# Gauge de uso de recursos
SYSTEM_CPU_USAGE = Gauge(
    'nethub_system_cpu_percent',
    'Uso de CPU del sistema',
    []
)

SYSTEM_MEMORY_USAGE = Gauge(
    'nethub_system_memory_bytes',
    'Uso de memoria del sistema en bytes',
    []
)

# Contador de operaciones de base de datos
DATABASE_OPERATIONS = Counter(
    'nethub_database_operations_total',
    'Operaciones de base de datos',
    ['operation', 'table']
)

# Registro global de todas las métricas
METRICS_REGISTRY = {
    'REQUEST_COUNT': REQUEST_COUNT,
    'REQUEST_LATENCY': REQUEST_LATENCY,
    'ERRORS_COUNT': ERRORS_COUNT,
    'ACTIVE_CONNECTIONS': ACTIVE_CONNECTIONS,
    'MESSAGES_SENT': MESSAGES_SENT,
    'MESSAGES_RECEIVED': MESSAGES_RECEIVED,
    'BYTES_TRANSFERRED': BYTES_TRANSFERRED,
    'AUTH_ATTEMPTS': AUTH_ATTEMPTS,
    'IA_RESPONSE_TIME': IA_RESPONSE_TIME,
    'SYSTEM_CPU_USAGE': SYSTEM_CPU_USAGE,
    'SYSTEM_MEMORY_USAGE': SYSTEM_MEMORY_USAGE,
    'DATABASE_OPERATIONS': DATABASE_OPERATIONS,
}

# ══════════════════════════════════════════════════
#  DECORADORES PARA TRACKING AUTOMÁTICO
# ══════════════════════════════════════════════════

def track_request(endpoint: str):
    """
    Decorador para trackear métricas de una petición.
    
    Uso:
        @track_request("login")
        async def login(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Registrar petición exitosa
                duration = time.time() - start_time
                REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
                REQUEST_COUNT.labels(
                    method="POST",  # Asumiendo POST, ajustar según necesidad
                    endpoint=endpoint,
                    status="200"
                ).inc()
                
                return result
                
            except Exception as e:
                # Registrar error
                duration = time.time() - start_time
                REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
                REQUEST_COUNT.labels(
                    method="POST",
                    endpoint=endpoint,
                    status="500"
                ).inc()
                
                ERRORS_COUNT.labels(
                    service=endpoint,
                    error_type=type(e).__name__
                ).inc()
                
                raise
        
        return wrapper
    return decorator


def track_ia_query(model: str):
    """Decorador para trackear consultas a IA."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                IA_RESPONSE_TIME.labels(model=model).observe(duration)
                return result
            except Exception as e:
                ERRORS_COUNT.labels(
                    service="ia",
                    error_type=type(e).__name__
                ).inc()
                raise
        
        return wrapper
    return decorator


# ══════════════════════════════════════════════════
#  FUNCIONES DE UTILIDAD
# ══════════════════════════════════════════════════

def registrar_mensaje_enviado(tipo: str):
    """Registrar un mensaje enviado."""
    MESSAGES_SENT.inc(message_type=tipo)


def registrar_mensaje_recibido(tipo: str):
    """Registrar un mensaje recibido."""
    MESSAGES_RECEIVED.inc(message_type=tipo)


def registrar_bytes(direccion: str, cantidad: int):
    """Registrar bytes transferidos."""
    BYTES_TRANSFERRED.set(cantidad, direction=direccion)


def registrar_autenticacion(exitosa: bool):
    """Registrar intento de autenticación."""
    status = "success" if exitosa else "failure"
    AUTH_ATTEMPTS.inc(status=status)


def actualizar_conexiones_activas(tipo: str, cantidad: int):
    """Actualizar número de conexiones activas."""
    ACTIVE_CONNECTIONS.set(cantidad, connection_type=tipo)


def registrar_operacion_bd(operacion: str, tabla: str):
    """Registrar operación de base de datos."""
    DATABASE_OPERATIONS.inc(operation=operacion, table=tabla)


# ══════════════════════════════════════════════════
#  MONITOREO DE SISTEMA
# ══════════════════════════════════════════════════

def actualizar_metricas_sistema():
    """Actualizar métricas de uso del sistema."""
    try:
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        SYSTEM_CPU_USAGE.set(cpu_percent)
        
        # Memoria
        memoria = psutil.virtual_memory()
        SYSTEM_MEMORY_USAGE.set(memoria.used)
        
    except ImportError:
        # psutil no instalado, métricas del sistema no disponibles
        pass


# ══════════════════════════════════════════════════
#  EXPORTACIÓN DE MÉTRICAS
# ══════════════════════════════════════════════════

def obtener_metricas() -> str:
    """
    Obtener las métricas en formato JSON.
    
    Returns:
        str: Métricas en formato JSON
    """
    actualizar_metricas_sistema()
    
    metricas = {}
    
    for nombre, metrica in METRICS_REGISTRY.items():
        if isinstance(metrica, (Counter, Gauge)):
            metricas[metrica.name] = {
                "description": metrica.description,
                "type": "counter" if isinstance(metrica, Counter) else "gauge",
                "values": {}
            }
            
            # Convertir valores
            for key, value in metrica.get_all().items():
                labels_dict = dict(key) if key else {}
                label_str = json.dumps(labels_dict, sort_keys=True) if labels_dict else "no_labels"
                metricas[metrica.name]["values"][label_str] = value
                
        elif isinstance(metrica, Histogram):
            metricas[metrica.name] = {
                "description": metrica.description,
                "type": "histogram",
                "values": metrica.get_all()
            }
    
    return json.dumps(metricas, indent=2, ensure_ascii=False)


def obtener_metricas_dict() -> dict:
    """
    Obtener las métricas como diccionario Python.
    
    Returns:
        dict: Métricas en formato diccionario
    """
    actualizar_metricas_sistema()
    
    metricas = {}
    
    for nombre, metrica in METRICS_REGISTRY.items():
        if isinstance(metrica, (Counter, Gauge)):
            valores = {}
            for key, value in metrica.get_all().items():
                labels_dict = dict(key) if key else {}
                label_str = json.dumps(labels_dict, sort_keys=True) if labels_dict else "no_labels"
                valores[label_str] = value
            
            metricas[metrica.name] = {
                "description": metrica.description,
                "type": "counter" if isinstance(metrica, Counter) else "gauge",
                "values": valores
            }
                
        elif isinstance(metrica, Histogram):
            metricas[metrica.name] = {
                "description": metrica.description,
                "type": "histogram",
                "values": metrica.get_all()
            }
    
    return metricas


# ══════════════════════════════════════════════════
#  CLASE PARA CONTEXTO
# ══════════════════════════════════════════════════

class MetricaContexto:
    """
    Context manager para medir duración de operaciones.
    
    Uso:
        with MetricaContexto(REQUEST_LATENCY, endpoint="login"):
            # código a medir
            hacer_operacion()
    """
    
    def __init__(self, metrica: Histogram, **labels):
        self.metrica = metrica
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.metrica.observe(duration, **self.labels)


# ══════════════════════════════════════════════════
#  CONFIGURACIÓN INICIAL
# ══════════════════════════════════════════════════

def inicializar_metricas():
    """Inicializar valores por defecto de las métricas."""
    # Inicializar conexiones en 0
    for tipo in ['tcp', 'websocket', 'http', 'tcp_tls']:
        ACTIVE_CONNECTIONS.set(0, connection_type=tipo)
    
    # Inicializar bytes transferidos en 0
    for direccion in ['sent', 'received']:
        BYTES_TRANSFERRED.set(0, direction=direccion)
    
    print("[Métricas] ✅ Sistema de métricas vanilla inicializado")


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════╗")
    print("║       NetHub - Sistema de Métricas Vanilla      ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    inicializar_metricas()
    
    # Ejemplo de uso
    print("📊 Métricas disponibles:")
    print("   • nethub_http_requests_total")
    print("   • nethub_request_duration_seconds")
    print("   • nethub_errors_total")
    print("   • nethub_active_connections")
    print("   • nethub_messages_sent_total")
    print("   • nethub_messages_received_total")
    print("   • nethub_bytes_transferred")
    print("   • nethub_auth_attempts_total")
    print("   • nethub_ia_response_seconds")
    print("   • nethub_system_cpu_percent")
    print("   • nethub_system_memory_bytes")
    print("   • nethub_database_operations_total")
    print()
    print("✅ Accede a /metrics en tu API para ver las métricas en formato JSON")
    print()
    
    # Prueba
    print("🧪 Prueba del sistema:")
    REQUEST_COUNT.inc(method="GET", endpoint="test", status="200")
    ACTIVE_CONNECTIONS.set(5, connection_type="tcp")
    
    print("\nMétricas generadas:")
    print(obtener_metricas())

