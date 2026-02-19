#!/usr/bin/env python3
"""
====================================================
  MÓDULO 6 - IA PERSONALIZADA TAME (Ollama local)
====================================================
TAME (Tutor Autónomo de Módulos de Estudio) es una
IA personalizada que actúa como asistente docente
para la asignatura de Programación de Servicios y
Procesos de DAM-2.

Usa el modelo local de Ollama con un system prompt
personalizado que define la identidad de TAME.

Requiere: pip install requests
          ollama corriendo en localhost:11434
====================================================
"""

import json
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO     = "qwen2.5:7b-instruct-q4_0"   # Modelo por defecto del aula

# Historial de la conversación (memoria de contexto)
HISTORIAL: list[dict] = []

# Personalidad de TAME
SYSTEM_PROMPT = """Eres TAME, el Tutor Autónomo de Módulos de Estudio.
Eres un asistente docente especializado en la asignatura de
'Programación de Servicios y Procesos' del ciclo DAM-2 (Desarrollo de
Aplicaciones Multiplataforma).

Tu especialidad cubre los siguientes bloques temáticos:
1. Programación multiproceso (subprocess, multiprocessing, psutil)
2. Programación multihilo (threading, concurrent.futures)
3. Comunicaciones en red (sockets TCP/UDP, SMTP, IMAP)
4. Generación de servicios en red (WebSockets, APIs REST, HTTP)
5. Programación segura (gestión de errores, cifrado básico, .env)

Responde siempre en español, de forma clara y pedagógica. Si el alumno
tiene dudas de código, muestra ejemplos concretos en Python. Cuando
expliques conceptos técnicos, usa analogías sencillas. Eres amable,
paciente y motivador. Si alguien te pregunta quién eres, di que eres
TAME y explica brevemente tu función."""


def chat_tame(pregunta: str) -> str:
    """
    Envía una pregunta a TAME (Ollama) manteniendo el historial
    de conversación, y retorna la respuesta como texto.
    """
    # Añadir la pregunta del usuario al historial
    HISTORIAL.append({"role": "user", "content": pregunta})

    payload = {
        "model":    MODELO,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + HISTORIAL,
        "stream":   True,
    }

    try:
        respuesta_http = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120,
            stream=True,
        )
        respuesta_http.raise_for_status()
    except requests.exceptions.ConnectionError:
        HISTORIAL.pop()   # Deshacer el mensaje no respondido
        return "❌ No se pudo conectar a Ollama. ¿Está en ejecución en localhost:11434?"
    except requests.exceptions.RequestException as e:
        HISTORIAL.pop()
        return f"❌ Error en la solicitud a Ollama: {e}"

    # Acumular la respuesta en streaming
    texto_respuesta = ""
    print("[TAME] ", end="", flush=True)

    for linea in respuesta_http.iter_lines():
        if not linea:
            continue
        try:
            chunk = json.loads(linea.decode("utf-8"))
        except json.JSONDecodeError:
            continue

        delta = chunk.get("message", {}).get("content", "")
        if delta:
            print(delta, end="", flush=True)
            texto_respuesta += delta

        if chunk.get("done", False):
            break

    print()  # Nueva línea al terminar el streaming

    # Añadir respuesta del asistente al historial
    HISTORIAL.append({"role": "assistant", "content": texto_respuesta})

    return texto_respuesta


def main():
    print("=" * 60)
    print("  TAME — Tutor Autónomo de Módulos de Estudio")
    print("  Asignatura: Programación de Servicios y Procesos")
    print("  Modelo: " + MODELO)
    print("=" * 60)
    print("  Escribe tu pregunta o 'salir' para terminar.")
    print("  Escribe 'limpiar' para borrar el historial de conversación.\n")

    while True:
        try:
            pregunta = input("Alumno > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[TAME] 👋 ¡Hasta la próxima! Sigue practicando.")
            break

        if not pregunta:
            continue
        if pregunta.lower() in ("salir", "exit", "quit"):
            print("[TAME] 👋 ¡Hasta la próxima! Recuerda repasar los apuntes. 😊")
            break
        if pregunta.lower() in ("limpiar", "reset", "nueva"):
            HISTORIAL.clear()
            print("[TAME] ✅ Historial borrado. Nueva conversación.\n")
            continue

        chat_tame(pregunta)
        print()


if __name__ == "__main__":
    main()
