#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║                      NetHub  v2.0                           ║
║        Sistema unificado de comunicaciones en red           ║
║                                                             ║
║  Programación de Servicios y Procesos — DAM-2               ║
╚══════════════════════════════════════════════════════════════╝

Punto de entrada único que agrupa todos los módulos del proyecto:
  · Correo SMTP / IMAP
  · Sockets TCP  (cliente / servidor)
  · WebSockets   (cliente / servidor)
  · IA remota jocarsa
  · TAME — IA personalizada
  · Ollama API  (3 métodos)
  · API REST con FastAPI (autenticación JWT)
  · Dashboard web de monitoreo en tiempo real
  · Servidor TCP con cifrado TLS/SSL
  · Base de datos SQLite3 nativa
  · Métricas nativas (vanilla) para monitoreo

Uso:
    python nethub.py
"""

import sys
import os
import subprocess

# ── Ruta base del proyecto ────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════
#  BANNER
# ══════════════════════════════════════════════════════════════

BANNER = r"""
  ███╗   ██╗███████╗████████╗    ██╗  ██╗██╗   ██╗██████╗
  ████╗  ██║██╔════╝╚══██╔══╝    ██║  ██║██║   ██║██╔══██╗
  ██╔██╗ ██║█████╗     ██║       ███████║██║   ██║██████╔╝
  ██║╚██╗██║██╔══╝     ██║       ██╔══██║██║   ██║██╔══██╗
  ██║ ╚████║███████╗   ██║       ██║  ██║╚██████╔╝██████╔╝
  ╚═╝  ╚═══╝╚══════╝   ╚═╝       ╚═╝  ╚═╝ ╚═════╝ ╚═════╝
      Sistema unificado de comunicaciones en red v2.0
       Programación de Servicios y Procesos · DAM-2
               🔒 API REST · 📊 Dashboard · 🔐 TLS
"""

SEPARADOR = "─" * 62


# ══════════════════════════════════════════════════════════════
#  IMPORTACIÓN DINÁMICA DE MÓDULOS
#  Se hace dentro de cada función para no requerir todas las
#  dependencias instaladas si solo se usa un módulo concreto.
# ══════════════════════════════════════════════════════════════

def _importar(nombre_fichero: str):
    """Importa dinámicamente un módulo del proyecto por nombre de fichero."""
    import importlib.util
    ruta = os.path.join(BASE, nombre_fichero)
    spec = importlib.util.spec_from_file_location(nombre_fichero, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _abrir_nueva_terminal(script: str, titulo: str) -> None:
    """
    Abre el script en una nueva ventana de terminal (Windows).
    Usado para los servidores que bloquean el proceso.
    """
    ruta_script = os.path.join(BASE, script)
    print(f"\n[NetHub] Abriendo '{titulo}' en una nueva ventana...")
    subprocess.Popen(
        ["cmd", "/c", "start", titulo, "python", ruta_script],
        shell=True,
    )


# ══════════════════════════════════════════════════════════════
#  ACCIONES DEL MENÚ
# ══════════════════════════════════════════════════════════════

def accion_smtp():
    print(f"\n{SEPARADOR}")
    print("  MÓDULO 1 — Envío de correo SMTP")
    print(SEPARADOR)
    mod = _importar("001-smtp_envio_correo.py")
    mod.main()


def accion_imap():
    print(f"\n{SEPARADOR}")
    print("  MÓDULO 2 — Lectura de correo IMAP")
    print(SEPARADOR)
    mod = _importar("002-imap_leer_correo.py")
    mod.main()


def accion_socket_servidor():
    _abrir_nueva_terminal("003a-socket_servidor.py", "NetHub | Servidor TCP")
    print("  Servidor TCP lanzado en una ventana aparte (puerto 9500).")
    print("  Ciérrala con Ctrl+C cuando termines.")


def accion_socket_cliente():
    print(f"\n{SEPARADOR}")
    print("  MÓDULO 3B — Cliente TCP Socket")
    print(SEPARADOR)
    mod = _importar("003b-socket_cliente.py")
    mod.iniciar_cliente()


def accion_ws_servidor():
    _abrir_nueva_terminal("004a-websocket_servidor.py", "NetHub | Servidor WebSocket")
    print("  Servidor WebSocket lanzado en una ventana aparte (puerto 9501).")
    print("  Ciérrala con Ctrl+C cuando termines.")


def accion_ws_cliente():
    print(f"\n{SEPARADOR}")
    print("  MÓDULO 4B — Cliente WebSocket")
    print(SEPARADOR)
    mod = _importar("004b-websocket_cliente.py")
    import asyncio
    asyncio.run(mod.main())


def accion_ia_remota():
    print(f"\n{SEPARADOR}")
    print("  MÓDULO 5 — IA Remota jocarsa")
    print(SEPARADOR)
    mod = _importar("005-ia_remota_jocarsa.py")
    mod.main()


def accion_tame():
    print(f"\n{SEPARADOR}")
    print("  MÓDULO 6 — TAME (IA personalizada)")
    print(SEPARADOR)
    mod = _importar("006-tame_ia_personalizada.py")
    mod.main()


def accion_ollama():
    print(f"\n{SEPARADOR}")
    print("  MÓDULO 7 — Conexión a Ollama (3 métodos)")
    print(SEPARADOR)
    mod = _importar("007-ia_ollama_python.py")
    mod.main()


def accion_api_rest():
    _abrir_nueva_terminal("008-api_rest_flask.py", "NetHub | API REST")
    print("  API REST FastAPI lanzada en una ventana aparte (puerto 8000).")
    print("  Accede a http://127.0.0.1:8000/api/docs para la documentación.")
    print("  Dashboard: http://127.0.0.1:8000/dashboard.html")


def accion_servidor_tls():
    _abrir_nueva_terminal("009a-socket_tls_servidor.py", "NetHub | Servidor TLS")
    print("  Servidor TCP con TLS lanzado en una ventana aparte (puerto 9502).")
    print("  Ciérrala con Ctrl+C cuando termines.")


def accion_cliente_tls():
    print(f"\n{SEPARADOR}")
    print("  MÓDULO 9B — Cliente TCP con TLS/SSL")
    print(SEPARADOR)
    mod = _importar("009b-socket_tls_cliente.py")
    mod.iniciar_cliente_tls()


def accion_inicializar_bd():
    print(f"\n{SEPARADOR}")
    print("  INICIALIZACIÓN DE BASE DE DATOS")
    print(SEPARADOR)
    mod = _importar("database_models.py")
    mod.inicializar_base_datos()


def accion_abrir_dashboard():
    print(f"\n{SEPARADOR}")
    print("  ABRIENDO DASHBOARD WEB")
    print(SEPARADOR)
    print("\n  Primero debes iniciar la API REST (opción 8)")
    print("  Luego accede a: http://127.0.0.1:8000/dashboard.html")
    print("\n  ¿Deseas iniciar la API REST ahora? (s/n)")
    
    respuesta = input("  > ").strip().lower()
    if respuesta == 's':
        accion_api_rest()
        print("\n  Espera unos segundos y accede a:")
        print("  http://127.0.0.1:8000/dashboard.html")
        
        import webbrowser
        import time
        time.sleep(2)
        webbrowser.open("http://127.0.0.1:8000/dashboard.html")


# ══════════════════════════════════════════════════════════════
#  MENÚ PRINCIPAL
# ══════════════════════════════════════════════════════════════

OPCIONES = [
    # (tecla, etiqueta_menú, función)
    ("1",  "Enviar correo         [SMTP + TLS]",            accion_smtp),
    ("2",  "Leer correo           [IMAP SSL]",              accion_imap),
    ("─",  None, None),
    ("3s", "Lanzar servidor TCP   [nueva ventana]",         accion_socket_servidor),
    ("3c", "Conectar cliente TCP  [interactivo]",           accion_socket_cliente),
    ("─",  None, None),
    ("4s", "Lanzar servidor WS    [nueva ventana]",         accion_ws_servidor),
    ("4c", "Conectar cliente WS   [interactivo]",           accion_ws_cliente),
    ("─",  None, None),
    ("5",  "IA remota jocarsa     [API REST ngrok]",        accion_ia_remota),
    ("6",  "TAME — IA docente     [Ollama local]",          accion_tame),
    ("7",  "Ollama API  3 métodos [demostración]",          accion_ollama),
    ("─",  None, None),
    ("8",  "API REST + Dashboard  [FastAPI puerto 8000]",   accion_api_rest),
    ("9s", "Servidor TCP con TLS  [cifrado SSL]",           accion_servidor_tls),
    ("9c", "Cliente TCP con TLS   [conexión segura]",       accion_cliente_tls),
    ("─",  None, None),
    ("db", "Inicializar BD        [SQLite]",                accion_inicializar_bd),
    ("web","Abrir Dashboard       [navegador]",             accion_abrir_dashboard),
]


def mostrar_menu() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print(BANNER)
    print(SEPARADOR)
    for clave, etiqueta, _ in OPCIONES:
        if clave == "─":
            print()
        else:
            print(f"  [{clave:>2}]  {etiqueta}")
    print()
    print(f"  [ 0]  Salir")
    print(SEPARADOR)


def ejecutar_opcion(clave: str) -> bool:
    """Ejecuta la acción correspondiente. Retorna False si hay que salir."""
    if clave == "0":
        return False

    for c, _, fn in OPCIONES:
        if c == clave and fn is not None:
            try:
                fn()
            except KeyboardInterrupt:
                print("\n[NetHub] ⬅  Volviendo al menú...")
            except ImportError as e:
                print(f"\n[NetHub] ⚠️  Dependencia no instalada: {e}")
                print("           Ejecuta: pip install python-dotenv requests websockets ollama")
            except Exception as e:  # noqa: BLE001
                print(f"\n[NetHub] ❌ Error inesperado: {e}")
            input("\n  Pulsa ENTER para volver al menú...")
            return True

    print(f"\n[NetHub] ⚠️  Opción '{clave}' no reconocida.")
    input("  Pulsa ENTER para continuar...")
    return True


def main() -> None:
    while True:
        mostrar_menu()
        try:
            opcion = input("  Elige una opción > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            opcion = "0"

        if not ejecutar_opcion(opcion):
            print("\n  👋 ¡Hasta pronto! — NetHub\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
