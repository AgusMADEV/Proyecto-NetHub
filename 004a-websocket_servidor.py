#!/usr/bin/env python3
"""
====================================================
  MÓDULO 4A - SERVIDOR WEBSOCKET
====================================================
Servidor WebSocket asíncrono basado en la librería
'websockets'. Acepta múltiples clientes, hace broadcast
de mensajes y responde a comandos especiales.

Requiere: pip install websockets
====================================================
Uso: python 004a-websocket_servidor.py
     (ejecutar antes que el cliente)
====================================================
"""

import asyncio
import json
import datetime
import websockets
from websockets.server import WebSocketServerProtocol

# Integración con base de datos
try:
    from database_models import SessionLocal, crear_log, crear_conexion, cerrar_conexion
    DB_DISPONIBLE = True
except ImportError:
    DB_DISPONIBLE = False

HOST  = "localhost"
PORT  = 9501

# Conjunto de clientes conectados
clientes: set[WebSocketServerProtocol] = set()


async def broadcast(mensaje: dict, origen: WebSocketServerProtocol | None = None) -> None:
    """
    Envía un mensaje JSON a todos los clientes conectados,
    excepto al origen (si se indica).
    """
    if not clientes:
        return
    texto = json.dumps(mensaje, ensure_ascii=False)
    destinatarios = clientes - {origen} if origen else clientes
    await asyncio.gather(
        *[cliente.send(texto) for cliente in destinatarios],
        return_exceptions=True,
    )


async def procesar_mensaje(ws: WebSocketServerProtocol, datos: str) -> dict:
    """
    Procesa el mensaje recibido de un cliente WebSocket.
    Soporta comandos especiales con prefijo '/'.
    """
    datos = datos.strip()

    if datos.startswith("/hora"):
        return {"tipo": "sistema", "respuesta": datetime.datetime.now().strftime("%H:%M:%S")}
    elif datos.startswith("/fecha"):
        return {"tipo": "sistema", "respuesta": datetime.datetime.now().strftime("%d/%m/%Y")}
    elif datos.startswith("/usuarios"):
        return {"tipo": "sistema", "respuesta": f"Usuarios conectados: {len(clientes)}"}
    elif datos.startswith("/ayuda"):
        return {
            "tipo": "sistema",
            "respuesta": "Comandos: /hora | /fecha | /usuarios | /ayuda | o escribe cualquier mensaje (se reenvía a todos)"
        }
    else:
        # Reenviar a todos los demás (chat)
        await broadcast({"tipo": "chat", "mensaje": datos}, origen=ws)
        return {"tipo": "eco", "respuesta": f"Mensaje enviado a todos: {datos}"}


async def gestionar_conexion(ws: WebSocketServerProtocol) -> None:
    """Callback que se ejecuta por cada cliente que se conecta."""
    cliente_id = f"{ws.remote_address[0]}:{ws.remote_address[1]}"
    clientes.add(ws)
    print(f"[WS SERVIDOR] ✅ Conectado: {cliente_id} | Total: {len(clientes)}")
    
    # Registrar conexión en BD
    conexion_id = None
    if DB_DISPONIBLE:
        db = SessionLocal()
        try:
            crear_log(db, "INFO", "WebSocket", f"Cliente conectado: {cliente_id}")
            result = crear_conexion(db, "WEBSOCKET", ws.remote_address[0], ws.remote_address[1], HOST, PORT)
            conexion_id = result['id'] if result else None
        finally:
            db.close()

    # Avisar a todos de la nueva conexión
    await broadcast({"tipo": "sistema", "respuesta": f"'{cliente_id}' se ha unido."}, origen=ws)

    # Bienvenida al nuevo cliente
    await ws.send(json.dumps({
        "tipo": "bienvenida",
        "respuesta": f"Bienvenido al servidor WebSocket TAME. Eres el cliente {cliente_id}. Escribe /ayuda para ver comandos."
    }, ensure_ascii=False))

    try:
        async for mensaje in ws:
            print(f"[WS SERVIDOR] ← [{cliente_id}] {mensaje}")
            respuesta = await procesar_mensaje(ws, mensaje)
            await ws.send(json.dumps(respuesta, ensure_ascii=False))
            print(f"[WS SERVIDOR] → [{cliente_id}] {respuesta['respuesta']}")

    except websockets.exceptions.ConnectionClosedOK:
        pass
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"[WS SERVIDOR] ⚠️  Conexión cerrada con error: {e}")
    finally:
        clientes.discard(ws)
        await broadcast({"tipo": "sistema", "respuesta": f"'{cliente_id}' se ha desconectado."})
        print(f"[WS SERVIDOR] ❌ Desconectado: {cliente_id} | Total: {len(clientes)}")
        
        # Cerrar conexión en BD
        if DB_DISPONIBLE and conexion_id:
            db = SessionLocal()
            try:
                cerrar_conexion(db, conexion_id)
                crear_log(db, "INFO", "WebSocket", f"Cliente desconectado: {cliente_id}")
            finally:
                db.close()


async def main() -> None:
    print("=" * 50)
    print(f"  SERVIDOR WEBSOCKET TAME  —  ws://{HOST}:{PORT}")
    print("=" * 50)
    print("  Esperando conexiones...\n")

    async with websockets.serve(gestionar_conexion, HOST, PORT):
        await asyncio.Future()   # Ejecutar indefinidamente


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[WS SERVIDOR] 🛑 Servidor detenido.")
