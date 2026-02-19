#!/usr/bin/env python3
"""
====================================================
  MÓDULO 3B - CLIENTE TCP (SOCKET)
====================================================
Cliente TCP que se conecta al servidor TAME y envía
comandos interactivos recibiendo respuestas JSON.
====================================================
Uso: python 003b-socket_cliente.py
     (el servidor debe estar en ejecución)
====================================================
"""

import socket
import json

HOST   = "127.0.0.1"
PORT   = 9500
ENCODE = "utf-8"


def recibir_respuesta(sock: socket.socket) -> dict | None:
    """
    Recibe un mensaje JSON del servidor.
    Retorna el diccionario parseado o None si falla.
    """
    try:
        datos = sock.recv(4096)
        if not datos:
            return None
        return json.loads(datos.decode(ENCODE))
    except (json.JSONDecodeError, OSError) as error:
        print(f"[CLIENTE TCP] ⚠️  Error al recibir: {error}")
        return None


def iniciar_cliente() -> None:
    """Conecta al servidor y gestiona el bucle interactivo."""
    print("=" * 50)
    print(f"  CLIENTE TCP TAME  —  {HOST}:{PORT}")
    print("=" * 50)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
            cliente.connect((HOST, PORT))
            print(f"[CLIENTE TCP] ✅ Conectado a {HOST}:{PORT}\n")

            # Recibir bienvenida del servidor
            respuesta = recibir_respuesta(cliente)
            if respuesta:
                print(f"[SERVIDOR] {respuesta.get('mensaje', '')}\n")

            while True:
                try:
                    comando = input("Comando > ").strip()
                except EOFError:
                    break

                if not comando:
                    continue

                # Enviar comando al servidor
                cliente.sendall(comando.encode(ENCODE))

                # Recibir respuesta
                respuesta = recibir_respuesta(cliente)
                if respuesta is None:
                    print("[CLIENTE TCP] 🔌 Conexión cerrada por el servidor.")
                    break

                estado   = respuesta.get("estado", "")
                mensaje  = respuesta.get("respuesta", "")
                print(f"[SERVIDOR] [{estado.upper()}] {mensaje}")

                if estado == "cierre":
                    break

    except ConnectionRefusedError:
        print(f"[CLIENTE TCP] ❌ No se pudo conectar a {HOST}:{PORT}")
        print("              Asegúrate de que el servidor esté en ejecución.")
    except KeyboardInterrupt:
        print("\n[CLIENTE TCP] 🛑 Cliente detenido.")


if __name__ == "__main__":
    iniciar_cliente()
