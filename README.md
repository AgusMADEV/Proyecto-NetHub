# 🌐 NetHub - Sistema Unificado de Comunicaciones en Red

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

**NetHub v2.0** es un sistema completo de comunicaciones en red desarrollado para el módulo de **Programación de Servicios y Procesos** del ciclo DAM-2. Implementa múltiples protocolos, servicios web, inteligencia artificial y herramientas de monitoreo profesionales.

---

## 📋 Características

### 🔧 Módulos Core
- ✉️ **Correo Electrónico**: Cliente SMTP con TLS para envío y cliente IMAP SSL para lectura
- 🔌 **Sockets TCP**: Servidor y cliente con soporte para múltiples conexiones concurrentes
- 🌐 **WebSockets**: Comunicación bidireccional en tiempo real
- 🧠 **Inteligencia Artificial**: Integración con Ollama local y API remota
- 🎓 **TAME**: Asistente de enseñanza personalizado con IA

### 🚀 Funcionalidades Avanzadas (v2.0)
- 🔐 **API REST con Flask**: API completa con autenticación JWT
- 🔒 **Autenticación JWT**: Sistema seguro de tokens para autenticación
- 📊 **Dashboard Web**: Panel de control en tiempo real para monitoreo
- 🗄️ **Base de Datos SQLite**: Persistencia con SQLite3 nativo (sin ORM)
- 📈 **Métricas Vanilla**: Sistema completo de monitoreo sin dependencias externas
- 🔐 **Sockets TLS/SSL**: Comunicaciones TCP cifradas con certificados
- 📊 **Métricas Nativas**: Sistema de monitoreo vanilla sin dependencias externas

---

## 🛠️ Instalación

### Requisitos Previos
- **Python 3.10 o superior**
- pip (gestor de paquetes de Python)

### Instalación de Dependencias

```bash
# Clonar el repositorio
git clone <url-repositorio>
cd Proyecto-NetHub

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración del Entorno

1. Copiar el archivo de ejemplo de variables de entorno:
```bash
copy .env.example .env
```

2. Editar `.env` con tus credenciales:
```env
# SMTP (Envío de correo)
SMTP_SERVER=smtp.tu-servidor.com
SMTP_PORT=587
SMTP_USER=tu-usuario@ejemplo.com
SMTP_PASSWORD=tu-contraseña

# IMAP (Lectura de correo)
IMAP_SERVER=imap.tu-servidor.com
IMAP_PORT=993

# IA Remota
IA_REMOTA_URL=https://tu-api.ngrok-free.app/api.php
IA_REMOTA_KEY=tu-clave-api

# JWT (Opcional, se genera automáticamente si no existe)
JWT_SECRET_KEY=tu-clave-secreta-muy-segura
```

---

## 🚀 Uso

### Menú Principal

Ejecutar NetHub con el menú interactivo:

```bash
python nethub.py
```

### Módulos Individuales

También puedes ejecutar cada módulo directamente:

```bash
# Enviar correo
python 001-smtp_envio_correo.py

# Leer correo
python 002-imap_leer_correo.py

# Servidor TCP
python 003a-socket_servidor.py

# Cliente TCP
python 003b-socket_cliente.py

# Servidor WebSocket
python 004a-websocket_servidor.py

# Cliente WebSocket
python 004b-websocket_cliente.py

# IA remota
python 005-ia_remota_jocarsa.py

# TAME IA personalizada
python 006-tame_ia_personalizada.py

# Ollama (3 métodos)
python 007-ia_ollama_python.py

# API REST
python 008-api_rest_flask.py

# Servidor TLS
python 009a-socket_tls_servidor.py

# Cliente TLS
python 009b-socket_tls_cliente.py
```

---

## 📊 API REST y Dashboard

### Iniciar API REST

```bash
python 008-api_rest_flask.py
```

### Acceder a la Documentación

- **Swagger UI**: http://127.0.0.1:8000/api/docs
- **ReDoc**: http://127.0.0.1:8000/api/redoc
- **Dashboard**: http://127.0.0.1:8000/dashboard.html
- **Métricas (JSON)**: http://127.0.0.1:8000/metrics

### Autenticación

Credenciales por defecto:
- **Usuario**: `admin`
- **Contraseña**: `admin123`

### Endpoints Principales

```http
POST   /api/auth/login          # Autenticación
GET    /api/auth/verify         # Verificar token
POST   /api/email/send          # Enviar correo
GET    /api/email/inbox         # Leer bandeja
POST   /api/ia/ollama           # Consultar Ollama
POST   /api/ia/remota           # Consultar IA remota
GET    /api/logs                # Obtener logs
GET    /api/stats               # Estadísticas del sistema
DELETE /api/logs/clear          # Limpiar logs
```

---

## 🔐 Sockets con TLS/SSL

### Generar Certificados

Los certificados se generan automáticamente al iniciar el servidor TLS por primera vez. Se almacenan en la carpeta `certs/`.

Para producción, usa certificados de una CA confiable.

### Conectar con Cliente TLS

```bash
# Terminal 1 - Servidor
python 009a-socket_tls_servidor.py

# Terminal 2 - Cliente
python 009b-socket_tls_cliente.py
```

---

## 🗄️ Base de Datos

### Inicializar Base de Datos

```bash
python database_models.py
```

Esto creará:
- Base de datos SQLite: `nethub.db`
- Tablas: logs, messages, connections, usuarios, metricas
- Usuario admin por defecto

### Estructura de Tablas

#### Logs
- Registro de eventos del sistema
- Niveles: INFO, WARNING, ERROR, DEBUG
- Servicios: SMTP, IMAP, Socket, API, etc.

#### Messages
- Mensajes enviados/recibidos
- Tipos: EMAIL, SOCKET, WEBSOCKET, API

#### Connections
- Conexiones de red activas/cerradas
- Tipos: TCP, WEBSOCKET, HTTP, TCP_TLS

#### Usuarios
- Usuarios del sistema con autenticación
- Hash de contraseñas con bcrypt

---

## 📈 Métricas Vanilla y Monitoreo

### Características

- ✅ Sistema nativo sin dependencias externas
- ✅ Formato JSON fácil de consumir
- ✅ Thread-safe con locks
- ✅ Bajo overhead de rendimiento
- ✅ Compatible con cualquier sistema de monitoreo

### Métricas Disponibles

- `nethub_http_requests_total`: Total de peticiones HTTP
- `nethub_request_duration_seconds`: Duración de peticiones
- `nethub_errors_total`: Total de errores
- `nethub_active_connections`: Conexiones activas
- `nethub_messages_sent_total`: Mensajes enviados
- `nethub_messages_received_total`: Mensajes recibidos
- `nethub_auth_attempts_total`: Intentos de autenticación
- `nethub_system_cpu_percent`: Uso de CPU
- `nethub_system_memory_bytes`: Uso de memoria

### Acceso a las Métricas

Las métricas están disponibles en formato JSON en el endpoint `/metrics`:

```bash
curl http://127.0.0.1:8000/metrics
```

**Formato de respuesta:**
```json
{
  "nethub_http_requests_total": {
    "description": "Total de peticiones HTTP recibidas",
    "type": "counter",
    "values": {
      "{\"method\":\"POST\",\"endpoint\":\"login\",\"status\":\"200\"}": 15
    }
  },
  "nethub_active_connections": {
    "description": "Número de conexiones activas",
    "type": "gauge",
    "values": {
      "{\"connection_type\":\"tcp\"}": 3
    }
  }
}
```

### Integración con Sistemas de Monitoreo

Las métricas en formato JSON pueden integrarse fácilmente con:
- Grafana (vía JSON API datasource)
- ElasticSearch / Kibana
- Custom dashboards
- Scripts de Python/Node.js
- Cualquier sistema que consuma JSON

---

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=. --cov-report=html

# Tests específicos
pytest tests/test_api.py
```

---

## 📁 Estructura del Proyecto

```
Proyecto-NetHub/
│
├── 001-smtp_envio_correo.py          # Envío de correo SMTP
├── 002-imap_leer_correo.py           # Lectura de correo IMAP
├── 003a-socket_servidor.py           # Servidor TCP
├── 003b-socket_cliente.py            # Cliente TCP
├── 004a-websocket_servidor.py        # Servidor WebSocket
├── 004b-websocket_cliente.py         # Cliente WebSocket
├── 005-ia_remota_jocarsa.py          # IA remota
├── 006-tame_ia_personalizada.py      # TAME IA
├── 007-ia_ollama_python.py           # Ollama API
├── 008-api_rest_flask.py           # API REST Flask
├── 009a-socket_tls_servidor.py       # Servidor TLS
├── 009b-socket_tls_cliente.py        # Cliente TLS
│
├── database_models.py                 # Modelos de base de datos
├── metrics_prometheus.py              # Sistema de métricas
├── dashboard.html                     # Dashboard web
│
├── nethub.py                          # Punto de entrada principal
├── requirements.txt                   # Dependencias
├── .env.example                       # Ejemplo de variables de entorno
└── README.md                          # Este archivo
```

**Nota:** Los siguientes archivos/carpetas se generan automáticamente y están excluidos de git:
- `nethub.db` - Base de datos SQLite (se crea con `database_models.py`)
- `certs/` - Certificados TLS/SSL (se generan al iniciar servidor TLS)
- `__pycache__/` - Archivos compilados de Python
- `.env` - Variables de entorno (usar `.env.example` como plantilla)

---

## 🔧 Tecnologías Utilizadas

### Backend
- **Python 3.10+**: Lenguaje principal
- **Flask**: Framework web ligero
- **SQLite3**: Base de datos nativa (incluida en Python)
- **Uvicorn**: Servidor ASGI
- **WebSockets**: Comunicación en tiempo real

### Seguridad
- **PyJWT**: Tokens de autenticación
- **bcrypt**: Hash de contraseñas
- **pyOpenSSL**: Certificados SSL/TLS
- **cryptography**: Operaciones criptográficas

### Monitoreo
- **Métricas Vanilla**: Sistema nativo sin dependencias
- **psutil**: Información del sistema (CPU, RAM)

### IA
- **Ollama Python SDK**: IA local
- **requests**: Llamadas HTTP

---

## 🎓 Créditos

Proyecto desarrollado para el módulo **Programación de Servicios y Procesos** del ciclo formativo **Desarrollo de Aplicaciones Multiplataforma (DAM-2)**.

---

## 📝 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📞 Soporte

Si encuentras algún problema o tienes preguntas, por favor abre un issue en el repositorio.

---

## 🗺️ Roadmap

### ✅ Completado (v2.0)
- [x] API REST con Flask
- [x] Dashboard web
- [x] Base de datos SQLite
- [x] Autenticación JWT
- [x] Métricas Vanilla (nativas)
- [x] Sockets con TLS

### 🚧 En Desarrollo (v2.1)
- [ ] Tests unitarios completos
- [ ] Integración con Docker
- [ ] CI/CD con GitHub Actions
- [ ] Documentación extendida

### 🎯 Futuro (v3.0)
- [ ] Soporte para PostgreSQL/MySQL
- [ ] Clustering y balanceo de carga
- [ ] gRPC para comunicación entre servicios
- [ ] Frontend React/Vue

---

**¡Gracias por usar NetHub!** 🚀
