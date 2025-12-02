"""
Script de prueba para conexión IMAP de Outlook
Ayuda a diagnosticar problemas de autenticación
"""
import imaplib
import sys

def test_imap_connection():
    print("=" * 60)
    print("PRUEBA DE CONEXIÓN IMAP - OUTLOOK")
    print("=" * 60)

    # Solicitar credenciales
    email = input("\nEmail: ").strip()
    password = input("Password/App Password: ").strip()

    # Servidores a probar
    servers = [
        ("outlook.office365.com", 993),
        ("imap-mail.outlook.com", 993),
    ]

    for server, port in servers:
        print(f"\n{'='*60}")
        print(f"Probando: {server}:{port}")
        print('='*60)

        try:
            # Intentar conexión
            print(f"1. Conectando a {server}...")
            imap = imaplib.IMAP4_SSL(server, port)
            print("   ✓ Conexión SSL establecida")

            # Intentar login
            print(f"2. Autenticando como {email}...")
            result = imap.login(email, password)
            print(f"   ✓ Login exitoso: {result}")

            # Listar carpetas
            print("3. Listando carpetas...")
            status, folders = imap.list()
            if status == 'OK':
                print(f"   ✓ Carpetas encontradas: {len(folders)}")
                for folder in folders[:5]:  # Mostrar primeras 5
                    print(f"      - {folder.decode()}")

            # Seleccionar INBOX
            print("4. Seleccionando INBOX...")
            status, count = imap.select('INBOX')
            if status == 'OK':
                print(f"   ✓ INBOX seleccionado: {count[0].decode()} mensajes")

            # Buscar emails
            print("5. Buscando emails no leídos...")
            status, messages = imap.search(None, 'UNSEEN')
            if status == 'OK':
                msg_ids = messages[0].split()
                print(f"   ✓ Emails no leídos: {len(msg_ids)}")

            # Cerrar conexión
            imap.close()
            imap.logout()

            print("\n" + "="*60)
            print("✅ CONEXIÓN EXITOSA!")
            print("="*60)
            print("\nEl servidor que funciona es:")
            print(f"  Servidor: {server}")
            print(f"  Puerto: {port}")
            print(f"\nActualiza config/clients.json con:")
            print(f'  "imap_server": "{server}"')

            return True

        except imaplib.IMAP4.error as e:
            print(f"   ✗ Error IMAP: {e}")
            print("\n   Posibles causas:")
            print("   1. Credenciales incorrectas")
            print("   2. Autenticación básica deshabilitada")
            print("   3. Necesitas usar contraseña de aplicación")

        except Exception as e:
            print(f"   ✗ Error: {type(e).__name__}: {e}")

    print("\n" + "="*60)
    print("❌ NO SE PUDO CONECTAR A NINGÚN SERVIDOR")
    print("="*60)
    print("\nPasos para solucionar:")
    print("\n1. HABILITAR IMAP EN OUTLOOK:")
    print("   - Ve a: https://outlook.office365.com/mail/")
    print("   - Configuración (⚙️) > Ver toda la configuración")
    print("   - Correo > Sincronizar correo electrónico")
    print("   - Activar 'Permitir que los dispositivos y aplicaciones usen POP'")
    print("   - IMPORTANTE: Activar 'Permitir que los dispositivos y aplicaciones usen IMAP'")

    print("\n2. CREAR CONTRASEÑA DE APLICACIÓN:")
    print("   a) Si tienes cuenta de trabajo/escuela (Office 365):")
    print("      - Ve a: https://mysignins.microsoft.com/security-info")
    print("      - Agregar método > Contraseña de aplicación")
    print("      - Nombrar: 'MedellinSAE' y copiar la contraseña generada")

    print("\n   b) Si tienes cuenta personal (Outlook.com/Hotmail):")
    print("      - Ve a: https://account.microsoft.com/security")
    print("      - Opciones de seguridad adicionales")
    print("      - Contraseñas de aplicación > Crear nueva")

    print("\n3. VERIFICAR AUTENTICACIÓN MODERNA:")
    print("   - Si eres administrador de Office 365:")
    print("     https://admin.microsoft.com > Configuración > Org settings")
    print("     > Modern authentication > Habilitar para IMAP")

    print("\n4. VERIFICAR 2FA:")
    print("   - Si tienes verificación en 2 pasos activa:")
    print("   - DEBES usar contraseña de aplicación, no tu contraseña normal")

    return False

if __name__ == "__main__":
    try:
        success = test_imap_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
        sys.exit(1)
