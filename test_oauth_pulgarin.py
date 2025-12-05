#!/usr/bin/env python3
"""
Test Script for OAuth 2.0 IMAP Authentication with Office 365
=============================================================

This script tests the OAuth 2.0 Device Code Flow for authenticating
with Office 365 IMAP. It's designed to diagnose authentication issues
and verify that the OAuth flow works correctly for the Pulgarin client.

Usage:
    python test_oauth_pulgarin.py

Requirements:
    - Python 3.8+
    - msal>=1.24.0 (install with: pip install msal)
    - Active internet connection
    - Valid Office 365 account credentials

What this script does:
    1. Loads environment variables (.env file)
    2. Initializes OAuth 2.0 IMAP repository
    3. Attempts to connect using Device Code Flow
    4. If successful, searches for Pulgarin emails
    5. Displays email count and first few subjects
    6. Disconnects and cleans up

Expected Flow (First Run):
    1. Script displays verification URL and device code
    2. You open browser and visit the URL
    3. You enter the device code
    4. You sign in with your Office 365 credentials
    5. You authorize IMAP permissions
    6. Script receives token and connects to IMAP
    7. Token is cached for future use

Expected Flow (Subsequent Runs):
    1. Script loads cached token
    2. Connects immediately without user interaction
    3. Searches for emails and displays results

Troubleshooting:
    - If authentication fails, delete data/oauth_token_cache.json
    - Verify IMAP is enabled in Outlook Web settings
    - Check that your account has OAuth 2.0 permissions
    - Ensure correct email address in .env file
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def main():
    """Test OAuth 2.0 IMAP connection for Pulgarin"""

    print("\n" + "="*70)
    print("  TEST: OAuth 2.0 IMAP Authentication for Pulgarin")
    print("="*70 + "\n")

    # Load environment variables
    load_dotenv()
    email = os.getenv('CORREAGRO_EMAIL')
    azure_client_id = os.getenv('AZURE_CLIENT_ID')

    if not email:
        logger.error("CORREAGRO_EMAIL not found in .env file")
        print("\n✗ ERROR: CORREAGRO_EMAIL no está configurado en el archivo .env")
        print("\nPor favor:")
        print("1. Crea un archivo .env en la raíz del proyecto")
        print("2. Agrega la línea: CORREAGRO_EMAIL=tu_email@correagro.com")
        print("3. Ejecuta este script nuevamente\n")
        return 1

    if not azure_client_id or azure_client_id == 'PENDING_REGISTRATION':
        logger.error("AZURE_CLIENT_ID not configured in .env file")
        print("\n✗ ERROR: AZURE_CLIENT_ID no está configurado en el archivo .env")
        print("\n" + "="*70)
        print("  CONFIGURACIÓN REQUERIDA: Registro de Aplicación en Azure AD")
        print("="*70 + "\n")
        print("OAuth 2.0 requiere que registres tu propia aplicación en Azure AD.")
        print("\nPasos rápidos:")
        print("1. Abre https://portal.azure.com")
        print("2. Ve a Azure Active Directory > App registrations")
        print("3. Crea una nueva aplicación")
        print("4. Copia el Application (client) ID")
        print("5. Agrégalo al archivo .env:")
        print("   AZURE_CLIENT_ID=tu-client-id-aqui")
        print("\n📖 Para instrucciones detalladas paso a paso:")
        print("   Consulta el archivo: AZURE_APP_REGISTRATION.md\n")
        return 1

    print(f"Email configurado: {email}")
    print(f"Azure Client ID: {azure_client_id[:8]}...{azure_client_id[-4:]}")
    print(f"Servidor IMAP: outlook.office365.com:993")
    print(f"Método de autenticación: OAuth 2.0 Device Code Flow\n")

    # Import OAuth2IMAPRepository
    try:
        from src.infrastructure.email.oauth2_imap_repository import OAuth2IMAPRepository
    except ImportError as e:
        logger.error(f"Failed to import OAuth2IMAPRepository: {e}")
        print("\n✗ ERROR: No se pudo importar OAuth2IMAPRepository")
        print("\nAsegúrate de que:")
        print("1. El archivo oauth2_imap_repository.py existe en src/infrastructure/email/")
        print("2. Has instalado msal con: pip install msal>=1.24.0")
        print(f"\nError técnico: {e}\n")
        return 1

    # Initialize repository
    logger.info("Initializing OAuth 2.0 IMAP repository...")
    repo = OAuth2IMAPRepository()

    # Test connection
    try:
        print("-" * 70)
        print("PASO 1: Conectando al servidor IMAP...")
        print("-" * 70 + "\n")

        # Note: password is ignored but required by interface
        connected = repo.connect(
            email_addr=email,
            password="",  # Not used with OAuth
            imap_server="outlook.office365.com"
        )

        if not connected:
            logger.error("Connection failed")
            print("\n✗ ERROR: No se pudo conectar al servidor IMAP\n")
            return 1

        print("\n✓ Conexión exitosa al servidor IMAP!")

        # Search for Pulgarin emails
        print("\n" + "-" * 70)
        print("PASO 2: Buscando correos de Pulgarin...")
        print("-" * 70 + "\n")

        search_criteria = '(UNSEEN SUBJECT "PULGARIN")'
        email_ids = repo.search_emails(search_criteria)

        print(f"\n✓ Se encontraron {len(email_ids)} correos sin leer de Pulgarin")

        # Fetch and display first few emails
        if email_ids:
            print("\n" + "-" * 70)
            print("PASO 3: Obteniendo información de los correos...")
            print("-" * 70 + "\n")

            max_display = min(5, len(email_ids))
            print(f"Mostrando los primeros {max_display} correos:\n")

            for i, email_id in enumerate(email_ids[:max_display], 1):
                try:
                    _, email_info = repo.fetch_email(email_id)
                    print(f"  {i}. Asunto: {email_info.get('subject', 'N/A')}")
                    print(f"     De: {email_info.get('from', 'N/A')}")
                    print(f"     Fecha: {email_info.get('date', 'N/A')}")
                    print()
                except Exception as e:
                    logger.error(f"Error fetching email {email_id}: {e}")
                    print(f"  {i}. Error al obtener email {email_id}: {e}\n")

        else:
            print("\n  ℹ  No hay correos sin leer de Pulgarin en este momento")
            print("     (Esto es normal si todos los correos ya fueron procesados)\n")

        # Success summary
        print("\n" + "="*70)
        print("  ✓ PRUEBA EXITOSA")
        print("="*70 + "\n")

        print("Resumen:")
        print(f"  • Autenticación OAuth 2.0: ✓ Exitosa")
        print(f"  • Conexión IMAP: ✓ Exitosa")
        print(f"  • Búsqueda de correos: ✓ Exitosa")
        print(f"  • Correos encontrados: {len(email_ids)}")

        # Check if token was cached
        cache_file = Path("data/oauth_token_cache.json")
        if cache_file.exists():
            print(f"\n  ℹ  Token OAuth guardado en: {cache_file}")
            print("     Las próximas ejecuciones no requerirán autenticación\n")

    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        print("\n" + "="*70)
        print("  ✗ ERROR DE CONEXIÓN")
        print("="*70 + "\n")
        print(str(e))
        print()
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print("\n" + "="*70)
        print("  ✗ ERROR INESPERADO")
        print("="*70 + "\n")
        print(f"Error: {str(e)}")
        print("\nPor favor revisa los logs y verifica:")
        print("  • Tu conexión a internet")
        print("  • Que IMAP esté habilitado en tu cuenta de Outlook")
        print("  • Que el email en .env sea correcto")
        print("  • Que hayas completado el flujo de autenticación\n")
        return 1

    finally:
        # Clean up
        try:
            repo.disconnect()
            logger.info("Disconnected from IMAP server")
        except:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
