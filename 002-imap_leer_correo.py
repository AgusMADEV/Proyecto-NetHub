#!/usr/bin/env python3
"""
====================================================
  MÓDULO 2 - LECTURA DE CORREO POR IMAP
====================================================
Conecta a un servidor IMAP, lee los últimos correos
de la bandeja de entrada y los muestra formateados.
====================================================
"""

import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

# Integración con base de datos
try:
    from database_models import SessionLocal, crear_log
    DB_DISPONIBLE = True
except ImportError:
    DB_DISPONIBLE = False

# Cargar variables de entorno
load_dotenv()

IMAP_SERVER   = os.getenv("IMAP_SERVER",   "imap.example.com")
IMAP_PORT     = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER     = os.getenv("SMTP_USER",     "usuario@example.com")
IMAP_PASSWORD = os.getenv("SMTP_PASSWORD", "contraseña")
MAX_CORREOS   = 10


def decodificar_cabecera(valor: str) -> str:
    """Decodifica cabeceras MIME (asunto, remitente, etc.)."""
    partes = decode_header(valor)
    resultado = []
    for parte, charset in partes:
        if isinstance(parte, bytes):
            try:
                resultado.append(parte.decode(charset or "utf-8", errors="replace"))
            except LookupError:
                resultado.append(parte.decode("utf-8", errors="replace"))
        else:
            resultado.append(parte)
    return "".join(resultado)


def obtener_cuerpo(mensaje: email.message.Message) -> str:
    """Extrae el texto plano o HTML del cuerpo del correo."""
    cuerpo = ""
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            tipo = parte.get_content_type()
            disposicion = str(parte.get("Content-Disposition", ""))
            if tipo == "text/plain" and "attachment" not in disposicion:
                payload = parte.get_payload(decode=True)
                charset = parte.get_content_charset() or "utf-8"
                cuerpo = payload.decode(charset, errors="replace")
                break
            elif tipo == "text/html" and "attachment" not in disposicion and not cuerpo:
                payload = parte.get_payload(decode=True)
                charset = parte.get_content_charset() or "utf-8"
                cuerpo = "[HTML] " + payload.decode(charset, errors="replace")[:200]
    else:
        payload = mensaje.get_payload(decode=True)
        charset = mensaje.get_content_charset() or "utf-8"
        cuerpo = payload.decode(charset, errors="replace") if payload else ""
    return cuerpo.strip()


def leer_correos() -> list[dict]:
    """
    Se conecta al servidor IMAP y lee los últimos MAX_CORREOS correos.
    Retorna una lista de diccionarios con los datos de cada correo.
    """
    correos_leidos = []

    try:
        # Conexión segura SSL
        conexion = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        conexion.login(IMAP_USER, IMAP_PASSWORD)
        print(f"[IMAP] ✅ Conectado como {IMAP_USER}")
        
        # Registrar conexión exitosa
        if DB_DISPONIBLE:
            db = SessionLocal()
            try:
                crear_log(db, "INFO", "IMAP", f"Conexión exitosa a {IMAP_SERVER}")
            finally:
                db.close()

        # Seleccionar la bandeja de entrada
        conexion.select("INBOX")

        # Buscar todos los mensajes
        estado, ids_bytes = conexion.search(None, "ALL")
        if estado != "OK" or not ids_bytes[0]:
            print("[IMAP] 📭 No hay mensajes en la bandeja.")
            conexion.logout()
            return []

        ids = ids_bytes[0].split()
        # Los más recientes primero (limitamos a MAX_CORREOS)
        ids_recientes = ids[-MAX_CORREOS:][::-1]

        for num_id in ids_recientes:
            estado, datos = conexion.fetch(num_id, "(RFC822)")
            if estado != "OK":
                continue

            msg_raw = datos[0][1]
            mensaje = email.message_from_bytes(msg_raw)

            asunto  = decodificar_cabecera(mensaje.get("Subject", "(Sin asunto)"))
            remite  = decodificar_cabecera(mensaje.get("From", ""))
            fecha   = mensaje.get("Date", "")
            cuerpo  = obtener_cuerpo(mensaje)

            correo_info = {
                "id":      num_id.decode(),
                "asunto":  asunto,
                "de":      remite,
                "fecha":   fecha,
                "cuerpo":  cuerpo[:300],  # Primeros 300 caracteres
            }
            correos_leidos.append(correo_info)

        conexion.logout()
        print(f"[IMAP] 📬 Se han leído {len(correos_leidos)} correos.")
        
        # Registrar lectura exitosa
        if DB_DISPONIBLE:
            db = SessionLocal()
            try:
                crear_log(db, "INFO", "IMAP", f"{len(correos_leidos)} correos leídos de bandeja de entrada")
            finally:
                db.close()

    except imaplib.IMAP4.error as error:
        print(f"[IMAP] ❌ Error de conexión: {error}")
        
        # Registrar error
        if DB_DISPONIBLE:
            db = SessionLocal()
            try:
                crear_log(db, "ERROR", "IMAP", f"Error de conexión: {str(error)}")
            finally:
                db.close()

    return correos_leidos


def mostrar_correos(correos: list[dict]) -> None:
    """Imprime los correos en formato legible por consola."""
    separador = "─" * 60
    for i, correo in enumerate(correos, start=1):
        print(f"\n{separador}")
        print(f"  Nº {i:02d}  |  ID: {correo['id']}")
        print(f"  Asunto : {correo['asunto']}")
        print(f"  De     : {correo['de']}")
        print(f"  Fecha  : {correo['fecha']}")
        print(f"  Cuerpo : {correo['cuerpo'][:120]}...")
    print(f"\n{separador}")


def main():
    print("=" * 60)
    print("  LECTOR DE CORREO IMAP - TAME")
    print("=" * 60)
    correos = leer_correos()
    if correos:
        mostrar_correos(correos)
    else:
        print("[IMAP] No se pudo leer ningún correo.")


if __name__ == "__main__":
    main()
