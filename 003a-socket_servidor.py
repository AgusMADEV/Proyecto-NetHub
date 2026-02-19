#!/usr/bin/env python3
"""
====================================================
  MÓDULO 3A - SERVIDOR TCP (SOCKET)
====================================================
Servidor TCP que acepta múltiples clientes de forma
concurrente usando hilos. Responde a comandos básicos
y también consulta a Ollama si el cliente lo pide.
====================================================
Uso: python 003a-socket_servidor.py
     (ejecutar antes que el cliente)
====================================================
"""

import socket
import threading
import json
import datetime

HOST  = "127.0.0.1"
PORT  = 9500
ENCODE = "utf-8"


def procesar_comando(comando: str) -> dict:
    """
    Procesa el comando enviado por el cliente y retorna
    un diccionario con la respuesta.
    """
    cmd = comando.strip().lower()

    if cmd == "hora":
        return {
            "estado": "ok",
            "comando": "hora",
            "respuesta": datetime.datetime.now().strftime("%H:%M:%S")
        }
    elif cmd == "fecha":
        return {
            "estado": "ok",
            "comando": "fecha",
            "respuesta": datetime.datetime.now().strftime("%d/%m/%Y")
        }
    elif cmd == "ping":
        return {
            "estado": "ok",
            "comando": "ping",
            "respuesta": "pong"
        }
    elif cmd == "info":
        return {
            "estado": "ok",
            "comando": "info",
            "respuesta": "Servidor TAME v1.0 - Programación de Servicios y Procesos"
        }
    elif cmd == "adios" or cmd == "bye":
        return {
            "estado": "cierre",
            "comando": cmd,
            "respuesta": "Hasta luego. Cerrando conexión..."
        }
    else:
        return {
            "estado": "ok",
            "comando": cmd,
            "respuesta": f"Comando '{comando}' no reconocido. Comandos: hora | fecha | ping | info | adios"
        }


def manejar_cliente(conexion: socket.socket, direccion: tuple) -> None:
    """
    Hilo dedicado a un cliente. Recibe comandos en texto
    y responde en JSON hasta que el cliente se desconecta.
    """
    print(f"[SERVIDOR TCP] ✅ Cliente conectado: {direccion[0]}:{direccion[1]}")

    # Mensaje de bienvenida
    bienvenida = {
        "estado": "bienvenida",
        "mensaje": "Bienvenido al servidor TAME. Escribe un comando (hora, fecha, ping, info, adios)."
    }
    try:
        conexion.sendall(json.dumps(bienvenida, ensure_ascii=False).encode(ENCODE))

        while True:
            datos = conexion.recv(1024)
            if not datos:
                break                         # El cliente cerró la conexión

            mensaje = datos.decode(ENCODE).strip()
            print(f"[SERVIDOR TCP] ← [{direccion[0]}] {mensaje}")

            respuesta = procesar_comando(mensaje)
            conexion.sendall(json.dumps(respuesta, ensure_ascii=False).encode(ENCODE))
            print(f"[SERVIDOR TCP] → [{direccion[0]}] {respuesta['respuesta']}")

            if respuesta.get("estado") == "cierre":
                break

    except (ConnectionResetError, BrokenPipeError):
        print(f"[SERVIDOR TCP] ⚠️  Conexión interrumpida con {direccion}")
    finally:
        conexion.close()
        print(f"[SERVIDOR TCP] ❌ Cliente desconectado: {direccion[0]}:{direccion[1]}")


def iniciar_servidor() -> None:
    """Inicia el servidor TCP y espera conexiones."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Reutilizar puerto al reiniciar
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(5)

    print("=" * 50)
    print(f"  SERVIDOR TCP TAME  —  {HOST}:{PORT}")
    print("=" * 50)
    print("  Esperando conexiones...\n")

    try:
        while True:
            conexion, direccion = servidor.accept()
            hilo = threading.Thread(
                target=manejar_cliente,
                args=(conexion, direccion),
                daemon=True
            )
            hilo.start()
    except KeyboardInterrupt:
        print("\n[SERVIDOR TCP] 🛑 Servidor detenido por el usuario.")
    finally:
        servidor.close()


if __name__ == "__main__":
    iniciar_servidor()
