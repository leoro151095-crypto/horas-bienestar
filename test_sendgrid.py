#!/usr/bin/env python
"""
Script para verificar que SendGrid está correctamente configurado.
Uso: python test_sendgrid.py <correo_destino>
"""
import sys
import os
from pathlib import Path

# Agregar ruta al proyecto
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from config import Config
from notifications import send_email

def test_sendgrid():
    if len(sys.argv) < 2:
        print("Uso: python test_sendgrid.py <correo_destino>")
        print("Ejemplo: python test_sendgrid.py usuario@example.com")
        sys.exit(1)
    
    correo_destino = sys.argv[1]
    
    print("=" * 60)
    print("TEST DE CONFIGURACIÓN SENDGRID")
    print("=" * 60)
    
    # Verificar configuración
    print("\n📋 Verificando configuración:")
    print(f"  MAIL_FROM: {'✓ Configurado' if Config.MAIL_FROM else '✗ NO configurado'}")
    print(f"             ({Config.MAIL_FROM if Config.MAIL_FROM else 'N/A'})")
    print(f"  SENDGRID_API_KEY: {'✓ Configurado' if Config.SENDGRID_API_KEY else '✗ NO configurado'}")
    if Config.SENDGRID_API_KEY:
        key_preview = f"{Config.SENDGRID_API_KEY[:7]}...{Config.SENDGRID_API_KEY[-10:]}"
        print(f"                  ({key_preview})")
    print(f"  SMTP_HOST: {'✓ Configurado' if Config.SMTP_HOST else '✗ NO configurado'}")
    print(f"             ({Config.SMTP_HOST if Config.SMTP_HOST else 'N/A'})")
    
    if not Config.MAIL_FROM:
        print("\n❌ Error: MAIL_FROM no está configurado")
        sys.exit(1)
    
    if not Config.SENDGRID_API_KEY and not Config.SMTP_HOST:
        print("\n❌ Error: Ni SendGrid API Key ni SMTP están configurados")
        sys.exit(1)
    
    # Intentar enviar email
    print(f"\n📧 Intentando enviar email a: {correo_destino}")
    print("-" * 60)
    
    test_body = """
Hola,

Este es un email de prueba para verificar que SendGrid está correctamente configurado en tu aplicación.

Si recibiste este email, significa que la configuración es correcta.

Código de prueba: TEST-EMAIL-12345

Saludos,
Sistema de Horas de Bienestar (Prueba)
"""
    
    success, message = send_email(
        Config,
        correo_destino,
        "PRUEBA: Configuración de SendGrid - Horas Bienestar",
        test_body
    )
    
    print(f"\nResultado: {'✓ ÉXITO' if success else '✗ FALLO'}")
    print(f"Mensaje: {message}")
    
    if success:
        print("\n" + "=" * 60)
        print("✓ SendGrid está correctamente configurado")
        print("=" * 60)
        print("\nProximos pasos:")
        print("1. Verifica que recibiste el email en tu bandeja de entrada")
        print("2. Si no lo ves, revisa la carpeta de spam")
        print("3. La configuración de recuperación de contraseña ya funcionará")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ Error al enviar email")
        print("=" * 60)
        print("\nDebugging:")
        print(f"1. Verifica que SENDGRID_API_KEY es válida")
        print(f"2. Verifica que MAIL_FROM es un correo válido")
        print(f"3. Revisa los logs en app.log para más detalles")
        sys.exit(1)

if __name__ == '__main__':
    test_sendgrid()
