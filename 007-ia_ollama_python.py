#!/usr/bin/env python3
"""
====================================================
  MÓDULO 7 - CONEXIÓN A IA CON PYTHON (Ollama API)
====================================================
Demuestra tres formas distintas de conectarse a un
servidor de IA con Python:

  A) Llamada directa a la API REST de Ollama (/api/generate)
     con requests y sin streaming (respuesta única).

  B) Llamada a Ollama con streaming línea a línea,
     acumulando el texto completo.

  C) Uso del paquete oficial 'ollama' de Python.

Requiere: pip install requests ollama
          ollama corriendo en localhost:11434
====================================================
"""

import json
import sys
import requests

# Integración con base de datos
try:
    from database_models import SessionLocal, crear_log
    DB_DISPONIBLE = True
except ImportError:
    DB_DISPONIBLE = False

OLLAMA_BASE   = "http://localhost:11434"
MODELO        = "qwen2.5:7b-instruct-q4_0"


# ─────────────────────────────────────────────────
# FORMA A: /api/generate  sin streaming
# ─────────────────────────────────────────────────

def generar_sin_streaming(prompt: str) -> str:
    """
    Llama al endpoint /api/generate de Ollama con stream:false.
    Espera a recibir toda la respuesta de una vez.
    """
    # Registrar consulta
    if DB_DISPONIBLE:
        db = SessionLocal()
        try:
            crear_log(db, "INFO", "Ollama", f"Consulta (sin stream): {prompt[:50]}...")
        finally:
            db.close()
    
    url = f"{OLLAMA_BASE}/api/generate"
    payload = {
        "model":  MODELO,
        "prompt": prompt,
        "stream": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=180)
        r.raise_for_status()
        datos = r.json()
        return datos.get("response", "(Sin respuesta)")
    except requests.exceptions.ConnectionError:
        error_msg = "❌ Ollama no está en ejecución (localhost:11434)."
        if DB_DISPONIBLE:
            db = SessionLocal()
            try:
                crear_log(db, "ERROR", "Ollama", "Servicio no disponible")
            finally:
                db.close()
        return error_msg
    except requests.exceptions.RequestException as e:
        if DB_DISPONIBLE:
            db = SessionLocal()
            try:
                crear_log(db, "ERROR", "Ollama", str(e))
            finally:
                db.close()
        return f"❌ Error: {e}"


# ─────────────────────────────────────────────────
# FORMA B: /api/generate  CON streaming  manual
# ─────────────────────────────────────────────────

def generar_con_streaming(prompt: str) -> str:
    """
    Llama al endpoint /api/generate de Ollama con stream:true.
    Imprime cada fragmento en tiempo real y retorna el texto completo.
    """
    url = f"{OLLAMA_BASE}/api/generate"
    payload = {
        "model":  MODELO,
        "prompt": prompt,
        "stream": True,
    }
    texto_completo = ""
    try:
        with requests.post(url, json=payload, timeout=180, stream=True) as r:
            r.raise_for_status()
            for linea in r.iter_lines():
                if not linea:
                    continue
                chunk = json.loads(linea.decode("utf-8"))
                fragmento = chunk.get("response", "")
                if fragmento:
                    print(fragmento, end="", flush=True)
                    texto_completo += fragmento
                if chunk.get("done", False):
                    break
        print()
        return texto_completo
    except requests.exceptions.ConnectionError:
        return "\n❌ Ollama no está en ejecución (localhost:11434)."
    except requests.exceptions.RequestException as e:
        return f"\n❌ Error: {e}"


# ─────────────────────────────────────────────────
# FORMA C: paquete oficial 'ollama'
# ─────────────────────────────────────────────────

def generar_con_libreria_ollama(prompt: str) -> str:
    """
    Usa el paquete oficial 'ollama' para Python.
    Más limpio y moderno que llamar a la API manualmente.
    """
    try:
        import ollama as ollama_pkg
    except ImportError:
        return "❌ El paquete 'ollama' no está instalado. Ejecuta: pip install ollama"

    try:
        respuesta = ollama_pkg.generate(model=MODELO, prompt=prompt)
        return respuesta["response"]
    except Exception as e:
        return f"❌ Error con la librería ollama: {e}"


# ─────────────────────────────────────────────────
# PROGRAMA PRINCIPAL — Menú de demostración
# ─────────────────────────────────────────────────

def mostrar_menu() -> None:
    print("\n  Elige el método de conexión:")
    print("  [A] /api/generate  sin streaming (respuesta única al final)")
    print("  [B] /api/generate  CON streaming  (texto en tiempo real)")
    print("  [C] Paquete oficial 'ollama'")
    print("  [S] Salir")


def main():
    print("=" * 60)
    print("  CONEXIÓN A IA CON PYTHON — Ollama API")
    print(f"  Servidor: {OLLAMA_BASE}")
    print(f"  Modelo  : {MODELO}")
    print("=" * 60)

    while True:
        mostrar_menu()
        try:
            opcion = input("\nOpción > ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Saliendo.")
            break

        if opcion == "S":
            print("👋 ¡Hasta pronto!")
            break

        if opcion not in ("A", "B", "C"):
            print("⚠️  Opción no válida.")
            continue

        try:
            prompt = input("Prompt > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not prompt:
            continue

        print("\n" + "─" * 60)

        if opcion == "A":
            print("[A] Respuesta sin streaming:\n")
            respuesta = generar_sin_streaming(prompt)
            print(respuesta)

        elif opcion == "B":
            print("[B] Respuesta con streaming:\n")
            generar_con_streaming(prompt)

        elif opcion == "C":
            print("[C] Respuesta con librería 'ollama':\n")
            respuesta = generar_con_libreria_ollama(prompt)
            print(respuesta)

        print("─" * 60)


if __name__ == "__main__":
    main()
