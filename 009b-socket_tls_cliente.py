#!/usr/bin/env python3
"""
====================================================
  MÓDULO 9B - CLIENTE TCP CON CIFRADO TLS/SSL
====================================================
Cliente TCP seguro que se conecta al servidor TLS.
Verifica certificados y establece comunicación cifrada.
====================================================
"""

import socket
import ssl
import json
from pathlib import Path

# ══════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════

HOST = "127.0.0.1"
PORT = 9502
ENCODE = "utf-8"

# Ruta del certificado del servidor (para verificación)
CERT_DIR = Path(__file__).parent / "certs"
CERT_FILE = CERT_DIR / "server.crt"

# ══════════════════════════════════════════════════
#  CLIENTE TLS
# ══════════════════════════════════════════════════

def iniciar_cliente_tls():
    """Inicia el cliente TCP con TLS."""
    
    print("╔══════════════════════════════════════════════════╗")
    print("║       Cliente TCP con Cifrado TLS/SSL           ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    # Crear contexto SSL para el cliente
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    
    # En producción, verificar certificados de CA confiables
    # Para certificados autofirmados, desactivamos la verificación
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    # Si queremos verificar el certificado autofirmado:
    # context.load_verify_locations(CERT_FILE)
    # context.verify_mode = ssl.CERT_REQUIRED
    
    # Configurar versión mínima de TLS
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    try:
        # Crear socket normal
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Envolver en TLS
        conn = context.wrap_socket(sock, server_hostname=HOST)
        
        # Conectar al servidor
        print(f"🔌 Conectando a {HOST}:{PORT}...")
        conn.connect((HOST, PORT))
        
        # Obtener información del cifrado
        cipher = conn.cipher()
        version = conn.version()
        
        print(f"✅ Conexión segura establecida")
        print(f"🔐 Cipher: {cipher[0] if cipher else 'unknown'}")
        print(f"🔐 TLS Version: {version}")
        print()
        
        # Recibir mensaje de bienvenida
        bienvenida = conn.recv(4096).decode(ENCODE)
        if bienvenida:
            try:
                data = json.loads(bienvenida)
                print("📨 Mensaje del servidor:")
                print(f"   {data.get('mensaje', '')}")
                if data.get('conexion_segura'):
                    print(f"   🔒 Conexión cifrada con: {data.get('cipher', 'unknown')}")
                print()
            except json.JSONDecodeError:
                print(f"📨 {bienvenida}")
        
        print("╔══════════════════════════════════════════════════╗")
        print("║  Escribe un comando y presiona ENTER            ║")
        print("║  Escribe 'help' para ver comandos disponibles   ║")
        print("║  Escribe 'exit' para salir                      ║")
        print("╚══════════════════════════════════════════════════╝")
        print()
        
        # Loop de comunicación
        while True:
            try:
                # Leer comando del usuario
                comando = input("TLS> ").strip()
                
                if not comando:
                    continue
                
                # Enviar comando al servidor (cifrado)
                conn.sendall((comando + "\n").encode(ENCODE))
                
                # Recibir respuesta (cifrada)
                respuesta_raw = conn.recv(4096).decode(ENCODE)
                
                if not respuesta_raw:
                    print("\n❌ Servidor desconectado")
                    break
                
                # Parsear respuesta JSON
                try:
                    respuesta = json.loads(respuesta_raw)
                    
                    print("\n" + "─" * 52)
                    
                    if respuesta.get('estado') == 'ok':
                        print("✅ Respuesta del servidor:")
                        
                        # Mostrar respuesta según el comando
                        if 'respuesta' in respuesta:
                            print(f"   {respuesta['respuesta']}")
                        
                        # Comando info
                        if respuesta.get('comando') == 'info':
                            print(f"   Servidor: {respuesta.get('servidor', 'unknown')}")
                            print(f"   Protocolo: {respuesta.get('protocolo', 'unknown')}")
                            print(f"   Cipher: {respuesta.get('cipher', 'unknown')}")
                        
                        # Comando stats
                        if respuesta.get('comando') == 'stats':
                            print(f"   Conexión segura: {respuesta.get('conexion_segura', False)}")
                            print(f"   Tu IP: {respuesta.get('ip_cliente', 'unknown')}")
                            print(f"   Tu Puerto: {respuesta.get('puerto_cliente', 'unknown')}")
                        
                        # Comando help
                        if respuesta.get('comando') == 'help':
                            print("   Comandos disponibles:")
                            for cmd in respuesta.get('comandos_disponibles', []):
                                print(f"   • {cmd}")
                        
                        # Mostrar si está cifrado
                        if respuesta.get('cifrado'):
                            print(f"   🔒 Cifrado: TLS {version}")
                        
                    else:
                        print("❌ Error del servidor:")
                        print(f"   {respuesta.get('mensaje', 'Error desconocido')}")
                    
                    print("─" * 52 + "\n")
                    
                    # Si el servidor nos dice que va a cerrar
                    if comando.lower() == 'exit':
                        print("👋 Cerrando conexión...")
                        break
                    
                except json.JSONDecodeError:
                    print(f"📨 {respuesta_raw}")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupción detectada")
                print("   Cerrando conexión...")
                break
            
            except Exception as e:
                print(f"\n❌ Error: {e}")
                break
        
    except ConnectionRefusedError:
        print("❌ No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor TLS esté ejecutándose")
        print(f"   python 009a-socket_tls_servidor.py")
        
    except ssl.SSLError as e:
        print(f"❌ Error SSL: {e}")
        print("   Verifica que el servidor tenga certificados válidos")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        
    finally:
        try:
            conn.close()
            print("\n✅ Conexión cerrada")
        except:
            pass


def main():
    """Punto de entrada principal."""
    iniciar_cliente_tls()
    
    print("\n👋 ¡Hasta pronto!")


if __name__ == "__main__":
    main()
