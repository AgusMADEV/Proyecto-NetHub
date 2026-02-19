#!/usr/bin/env python3
"""
====================================================
  MÓDULO 5 - CONEXIÓN A SERVIDOR DE IA REMOTO
====================================================
Conecta a la API REST del servidor de IA jocarsa
(expuesto a través de ngrok) usando requests.
Las credenciales se leen desde el archivo .env

Requiere: pip install requests python-dotenv
====================================================
"""

import os
import json
import requests
from dotenv import load_dotenv

# Integración con base de datos
try:
    from database_models import SessionLocal, crear_log
    DB_DISPONIBLE = True
except ImportError:
    DB_DISPONIBLE = False

# Deshabilitar avisos de SSL no verificado
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# URL y API Key del servidor remoto de IA jocarsa
IA_REMOTA_URL = os.getenv(
    "IA_REMOTA_URL",
    "https://tu-ngrok-url.ngrok-free.app/api.php"
)
IA_REMOTA_KEY = os.getenv("IA_REMOTA_KEY", "TEST_API_KEY_JOCARSA_123")


def preguntar_ia_remota(pregunta: str) -> str:
    """
    Envía una pregunta a la API REST de jocarsa y retorna la respuesta.

    Parámetros:
        pregunta -- texto de la consulta

    Retorna la respuesta como cadena de texto.
    """
    # Registrar consulta en BD
    if DB_DISPONIBLE:
        db = SessionLocal()
        try:
            crear_log(db, "INFO", "IA_Remota", f"Consulta: {pregunta[:50]}...")
        finally:
            db.close()
    
    try:
        respuesta = requests.post(
            IA_REMOTA_URL,
            headers={"X-API-Key": IA_REMOTA_KEY},
            data={"question": pregunta},
            timeout=120,
            verify=False,   # Certificado auto-firmado de ngrok
        )
    except requests.exceptions.ConnectionError:
        error_msg = "❌ Error: No se pudo conectar al servidor de IA remoto."
        if DB_DISPONIBLE:
            db = SessionLocal()
            try:
                crear_log(db, "ERROR", "IA_Remota", "Error de conexión")
            finally:
                db.close()
        return error_msg
    except requests.exceptions.Timeout:
        error_msg = "❌ Error: El servidor tardó demasiado en responder (timeout)."
        if DB_DISPONIBLE:
            db = SessionLocal()
            try:
                crear_log(db, "ERROR", "IA_Remota", "Timeout")
            finally:
                db.close()
        return error_msg
    except requests.exceptions.RequestException as e:
        if DB_DISPONIBLE:
            db = SessionLocal()
            try:
                crear_log(db, "ERROR", "IA_Remota", str(e))
            finally:
                db.close()
        return f"❌ Error en la solicitud: {e}"

    if respuesta.status_code != 200:
        return f"❌ El servidor respondió con HTTP {respuesta.status_code}: {respuesta.text}"

    try:
        payload = respuesta.json()
    except json.JSONDecodeError:
        return f"❌ Respuesta no es JSON válido:\n{respuesta.text}"

    respuesta_texto = payload.get("answer")
    if respuesta_texto is None:
        return f"❌ La respuesta no contiene el campo 'answer'.\nPayload: {payload}"

    return respuesta_texto


def main():
    print("=" * 60)
    print("  CLIENTE IA REMOTA JOCARSA — API REST")
    print("=" * 60)
    print(f"  Servidor : {IA_REMOTA_URL}")
    print("  Escribe 'salir' para terminar.\n")

    while True:
        try:
            pregunta = input("Tú > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[IA REMOTA] 👋 Cerrando.")
            break

        if not pregunta:
            continue
        if pregunta.lower() in ("salir", "exit", "quit"):
            print("[IA REMOTA] 👋 ¡Hasta pronto!")
            break

        print("[IA REMOTA] ⏳ Consultando...")
        respuesta = preguntar_ia_remota(pregunta)
        print(f"\n[IA REMOTA] 🤖 {respuesta}\n")


if __name__ == "__main__":
    main()
