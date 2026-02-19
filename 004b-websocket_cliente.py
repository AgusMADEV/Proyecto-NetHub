#!/usr/bin/env python3
"""
====================================================
  MÓDULO 4B - CLIENTE WEBSOCKET
====================================================
Cliente WebSocket asíncrono que se conecta al servidor
TAME y permite enviar mensajes/comandos en tiempo real.
Usa dos tareas asyncio: una para recibir y otra para
leer la entrada del usuario.

Requiere: pip install websockets
====================================================
Uso: python 004b-websocket_cliente.py
     (el servidor debe estar en ejecución)
====================================================
"""

import asyncio
import json
import sys
import websockets

URI = "ws://localhost:9501"


async def recibir_mensajes(ws) -> None:
    """Tarea que escucha mensajes entrantes del servidor."""
    try:
        async for mensaje_raw in ws:
            try:
                datos = json.loads(mensaje_raw)
                tipo      = datos.get("tipo", "?")
                respuesta = datos.get("respuesta", datos.get("mensaje", ""))
                etiqueta  = {
                    "bienvenida": "🟢 SISTEMA",
                    "sistema":    "⚙️  SISTEMA",
                    "chat":       "💬 CHAT",
                    "eco":        "📤 ECO",
                }.get(tipo, f"[{tipo.upper()}]")
                print(f"\n{etiqueta}: {respuesta}")
                print("Mensaje > ", end="", flush=True)
            except json.JSONDecodeError:
                print(f"\n[RAW] {mensaje_raw}")
    except websockets.exceptions.ConnectionClosed:
        print("\n[CLIENTE WS] 🔌 Servidor cerró la conexión.")


async def enviar_mensajes(ws) -> None:
    """Tarea que lee input del usuario y lo envía al servidor."""
    loop = asyncio.get_event_loop()
    while True:
        try:
            # Leer entrada sin bloquear el event loop
            mensaje = await loop.run_in_executor(None, lambda: input("Mensaje > "))
            mensaje = mensaje.strip()
            if not mensaje:
                continue
            if mensaje.lower() in ("salir", "exit", "quit"):
                print("[CLIENTE WS] 👋 Desconectando...")
                await ws.close()
                break
            await ws.send(mensaje)
        except EOFError:
            break


async def main() -> None:
    print("=" * 50)
    print(f"  CLIENTE WEBSOCKET TAME  —  {URI}")
    print("=" * 50)
    print("  Conectando...\n")

    try:
        async with websockets.connect(URI) as ws:
            print(f"[CLIENTE WS] ✅ Conectado a {URI}")
            print("  Escribe tu mensaje o un comando (/ayuda, /hora, /fecha, /usuarios)")
            print("  Escribe 'salir' para desconectar.\n")

            # Ejecutar las dos tareas de forma concurrente
            tarea_recibir = asyncio.create_task(recibir_mensajes(ws))
            tarea_enviar  = asyncio.create_task(enviar_mensajes(ws))

            # Terminar cuando cualquiera de las dos finalice
            done, pending = await asyncio.wait(
                [tarea_recibir, tarea_enviar],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for tarea in pending:
                tarea.cancel()

    except ConnectionRefusedError:
        print(f"[CLIENTE WS] ❌ No se pudo conectar a {URI}")
        print("              Asegúrate de que el servidor WebSocket esté en ejecución.")
    except KeyboardInterrupt:
        print("\n[CLIENTE WS] 🛑 Detenido por el usuario.")


if __name__ == "__main__":
    asyncio.run(main())
