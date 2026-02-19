#!/usr/bin/env python3
"""
====================================================
  MÓDULO 1 - ENVÍO DE CORREO POR SMTP
====================================================
Envía un correo electrónico HTML con Python usando
smtplib y las credenciales del archivo .env
====================================================
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

SMTP_SERVER   = os.getenv("SMTP_SERVER",   "smtp.example.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER",     "usuario@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "contraseña")


def enviar_correo(destinatario: str, asunto: str, cuerpo_html: str) -> bool:
    """
    Envía un correo HTML al destinatario indicado.

    Parámetros:
        destinatario  -- dirección de correo del receptor
        asunto        -- asunto del mensaje
        cuerpo_html   -- contenido HTML del cuerpo

    Retorna True si se envió con éxito, False en caso de error.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = SMTP_USER
    msg["To"]      = destinatario

    # Parte HTML del mensaje
    parte_html = MIMEText(cuerpo_html, "html", "utf-8")
    msg.attach(parte_html)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.sendmail(SMTP_USER, destinatario, msg.as_string())
        print(f"[SMTP] ✅ Correo enviado correctamente a {destinatario}")
        return True
    except smtplib.SMTPException as error:
        print(f"[SMTP] ❌ Error al enviar el correo: {error}")
        return False


def main():
    destinatario = input("Introduce el correo destinatario: ").strip()
    asunto       = "Saludo desde TAME - Python SMTP"

    cuerpo = """
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; background:#f4f4f4; padding:30px;">
      <div style="max-width:600px; margin:auto; background:#fff; border-radius:8px;
                  padding:30px; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color:#2c3e50;">TAME - Sistema de Comunicaciones</h1>
        <p>Hola,</p>
        <p>Este mensaje ha sido enviado automáticamente desde una aplicación Python
           como parte de la actividad de <strong>Programación de Servicios y Procesos</strong>.</p>
        <hr>
        <p>Módulos implementados:</p>
        <ul>
          <li>✅ Envío SMTP</li>
          <li>✅ Lectura IMAP</li>
          <li>✅ Sockets TCP (cliente/servidor)</li>
          <li>✅ WebSockets (cliente/servidor)</li>
          <li>✅ Conexión a IA remota</li>
          <li>✅ IA personalizada TAME (Ollama)</li>
        </ul>
        <p style="color:#999; font-size:12px;">Enviado el 19/02/2026</p>
      </div>
    </body>
    </html>
    """

    enviar_correo(destinatario, asunto, cuerpo)


if __name__ == "__main__":
    main()
