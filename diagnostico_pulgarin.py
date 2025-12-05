#!/usr/bin/env python3
"""
Script de Diagnóstico para Pulgarin
====================================

Este script te ayudará a diagnosticar por qué el CSV está vacío.
Muestra paso a paso qué está pasando en el proceso.
"""

import os
import sys
import logging
import zipfile
import io
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()


def main():
    print("\n" + "="*70)
    print("  DIAGNÓSTICO: Procesamiento de Correos Pulgarin")
    print("="*70 + "\n")

    # Import repositories
    try:
        from src.infrastructure.email.oauth2_imap_repository import OAuth2IMAPRepository
        from src.infrastructure.xml.ubl_xml_parser import UBLXMLParser
    except ImportError as e:
        print(f"✗ Error importando módulos: {e}")
        return 1

    # Get credentials
    email = os.getenv('CORREAGRO_EMAIL')
    azure_client_id = os.getenv('AZURE_CLIENT_ID')

    if not email:
        print("✗ ERROR: CORREAGRO_EMAIL no configurado en .env")
        return 1

    if not azure_client_id or azure_client_id == 'PENDING_REGISTRATION':
        print("✗ ERROR: AZURE_CLIENT_ID no configurado en .env")
        return 1

    print(f"✓ Email: {email}")
    print(f"✓ Azure Client ID: {azure_client_id[:8]}...{azure_client_id[-4:]}\n")

    # Initialize repositories
    print("-" * 70)
    print("PASO 1: Conectando al servidor IMAP...")
    print("-" * 70)

    email_repo = OAuth2IMAPRepository()

    try:
        connected = email_repo.connect(
            email_addr=email,
            password="",  # Not used with OAuth
            imap_server="outlook.office365.com"
        )

        if not connected:
            print("✗ No se pudo conectar al servidor IMAP")
            return 1

        print("✓ Conexión exitosa!\n")

    except Exception as e:
        print(f"✗ Error conectando: {e}")
        return 1

    # Search for emails
    print("-" * 70)
    print("PASO 2: Buscando correos de Pulgarin...")
    print("-" * 70)

    search_criteria = '(UNSEEN SUBJECT "PULGARIN")'
    print(f"Criterio de búsqueda: {search_criteria}\n")

    try:
        email_ids = email_repo.search_emails(search_criteria)
        print(f"✓ Se encontraron {len(email_ids)} correos\n")

        if len(email_ids) == 0:
            print("⚠️  No hay correos sin leer que coincidan con el criterio")
            print("\nPosibles soluciones:")
            print("1. Verifica que haya correos sin leer con 'PULGARIN' en el asunto")
            print("2. Marca un correo como 'No leído' en Outlook y vuelve a intentar")
            print("3. Cambia el criterio de búsqueda si el asunto es diferente")
            print("4. Usa el checkbox 'Permitir reprocesar' en la app para procesar correos ya leídos\n")

            # Try searching for ALL emails with PULGARIN
            print("Buscando TODOS los correos (leídos y no leídos) con PULGARIN...")
            all_search = '(SUBJECT "PULGARIN")'
            all_email_ids = email_repo.search_emails(all_search)
            print(f"✓ Total de correos con PULGARIN (incluyendo leídos): {len(all_email_ids)}\n")

            if len(all_email_ids) > 0:
                print("💡 SOLUCIÓN: Hay correos pero están marcados como leídos.")
                print("   Opciones:")
                print("   a) Marca algunos como 'No leído' en Outlook")
                print("   b) Usa el checkbox 'Permitir reprocesar correos ya procesados' en la app\n")

            return 0

    except Exception as e:
        print(f"✗ Error buscando correos: {e}")
        return 1

    # Process each email
    print("-" * 70)
    print("PASO 3: Analizando correos encontrados...")
    print("-" * 70)

    xml_parser = UBLXMLParser()
    total_zips = 0
    total_xmls = 0
    total_invoices = 0

    for i, email_id in enumerate(email_ids[:5], 1):  # Analyze first 5 emails
        print(f"\n📧 Correo {i}/{min(len(email_ids), 5)} (ID: {email_id})")
        print("-" * 50)

        try:
            # Fetch email
            email_data, email_info = email_repo.fetch_email(email_id)
            print(f"  Asunto: {email_info.get('subject', 'N/A')}")
            print(f"  De: {email_info.get('from', 'N/A')}")
            print(f"  Fecha: {email_info.get('date', 'N/A')}")

            # Extract attachments
            attachments = email_repo.extract_attachments(email_data)
            print(f"  Adjuntos: {len(attachments)}")

            if len(attachments) == 0:
                print("  ⚠️  Este correo NO tiene archivos adjuntos")
                continue

            # List attachments
            for filename, content in attachments:
                print(f"    - {filename} ({len(content)} bytes)")

                if filename.lower().endswith('.zip'):
                    total_zips += 1
                    print(f"      📦 Es un ZIP, extrayendo...")

                    try:
                        with zipfile.ZipFile(io.BytesIO(content)) as zf:
                            xml_files = [f for f in zf.namelist() if f.lower().endswith('.xml')]
                            print(f"      XMLs dentro del ZIP: {len(xml_files)}")

                            if len(xml_files) == 0:
                                print(f"      ⚠️  El ZIP no contiene archivos XML")
                                continue

                            for xml_file in xml_files:
                                total_xmls += 1
                                print(f"        - {xml_file}")

                                try:
                                    xml_content = zf.read(xml_file)
                                    print(f"          Tamaño XML: {len(xml_content)} bytes")

                                    # Try to parse
                                    invoice = xml_parser.parse_invoice(xml_content)

                                    if invoice:
                                        total_invoices += 1
                                        print(f"          ✓ Factura parseada exitosamente!")
                                        print(f"            N° Factura: {invoice.invoice_number}")
                                        print(f"            Fecha: {invoice.invoice_date}")
                                        print(f"            Vendedor: {invoice.seller_name}")
                                        print(f"            Comprador: {invoice.buyer_name}")
                                        print(f"            Items: {len(invoice.items)}")

                                        if len(invoice.items) > 0:
                                            item = invoice.items[0]
                                            print(f"            Primer item:")
                                            print(f"              - Producto: {item.product_name}")
                                            print(f"              - Subyacente: {item.subyacente_code}")
                                            print(f"              - Cantidad: {item.quantity}")
                                            print(f"              - Precio: {item.unit_price}")
                                    else:
                                        print(f"          ✗ Error: parse_invoice() retornó None")

                                except Exception as e:
                                    print(f"          ✗ Error parseando XML: {e}")

                    except zipfile.BadZipFile:
                        print(f"      ✗ Error: El archivo no es un ZIP válido")
                    except Exception as e:
                        print(f"      ✗ Error procesando ZIP: {e}")

        except Exception as e:
            print(f"  ✗ Error procesando correo: {e}")

    # Summary
    print("\n" + "="*70)
    print("  RESUMEN DEL DIAGNÓSTICO")
    print("="*70)
    print(f"\n  Correos encontrados: {len(email_ids)}")
    print(f"  Archivos ZIP encontrados: {total_zips}")
    print(f"  Archivos XML encontrados: {total_xmls}")
    print(f"  Facturas parseadas exitosamente: {total_invoices}")

    if total_invoices == 0:
        print("\n  ⚠️  PROBLEMA DETECTADO: No se parsearon facturas")
        print("\n  Posibles causas:")
        print("    1. Los correos no tienen archivos adjuntos ZIP")
        print("    2. Los ZIPs están vacíos o corruptos")
        print("    3. Los ZIPs no contienen archivos XML")
        print("    4. Los XMLs tienen un formato diferente al esperado (no UBL 2.1)")
        print("    5. Hay un error en el parser XML")
    else:
        print(f"\n  ✓ El proceso está funcionando correctamente!")
        print(f"    Se parsearon {total_invoices} facturas de {total_xmls} XMLs")

    # Cleanup
    try:
        email_repo.disconnect()
    except:
        pass

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
