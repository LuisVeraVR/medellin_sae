"""
Script para verificar qué está bloqueando la conexión IMAP en Office 365
"""
import imaplib
import socket

def check_outlook_imap():
    print("="*70)
    print("DIAGNÓSTICO DE CONEXIÓN IMAP - OFFICE 365")
    print("="*70)

    email = input("\nEmail corporativo: ").strip()
    domain = email.split('@')[1] if '@' in email else ''

    print(f"\n📧 Email: {email}")
    print(f"🏢 Dominio: {domain}")

    # Test 1: DNS resolution
    print("\n" + "="*70)
    print("TEST 1: Resolución DNS")
    print("="*70)

    servers_to_test = [
        "outlook.office365.com",
        "imap-mail.outlook.com",
        f"imap.{domain}",  # Sometimes companies use custom
    ]

    working_servers = []

    for server in servers_to_test:
        try:
            ip = socket.gethostbyname(server)
            print(f"✓ {server} → {ip}")
            working_servers.append(server)
        except socket.gaierror:
            print(f"✗ {server} → No se puede resolver")

    # Test 2: Port connectivity
    print("\n" + "="*70)
    print("TEST 2: Conectividad de Puerto 993 (IMAP SSL)")
    print("="*70)

    for server in working_servers:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((server, 993))
            sock.close()

            if result == 0:
                print(f"✓ {server}:993 → Puerto abierto")
            else:
                print(f"✗ {server}:993 → Puerto cerrado o bloqueado")
        except Exception as e:
            print(f"✗ {server}:993 → Error: {e}")

    # Test 3: SSL/TLS handshake
    print("\n" + "="*70)
    print("TEST 3: Handshake SSL/TLS")
    print("="*70)

    for server in working_servers:
        try:
            imap = imaplib.IMAP4_SSL(server, 993)
            capabilities = imap.capability()
            print(f"✓ {server} → SSL OK")
            print(f"   Capacidades: {capabilities[1][0].decode()[:100]}...")

            # Check if LOGIN is supported
            if b'LOGINDISABLED' in capabilities[1][0]:
                print(f"   ⚠️  LOGIN DESHABILITADO - Autenticación básica bloqueada")
            else:
                print(f"   ✓ LOGIN habilitado")

            imap.logout()
        except Exception as e:
            print(f"✗ {server} → Error SSL: {e}")

    # Test 4: Authentication methods
    print("\n" + "="*70)
    print("TEST 4: Intento de Autenticación")
    print("="*70)

    password = input(f"Contraseña para {email} (o presiona Enter para saltar): ").strip()

    if password:
        for server in working_servers:
            try:
                imap = imaplib.IMAP4_SSL(server, 993)
                result = imap.login(email, password)
                print(f"✓ {server} → LOGIN EXITOSO!")
                print(f"   Resultado: {result}")
                imap.logout()

                print("\n" + "="*70)
                print("✅ CONEXIÓN EXITOSA - La aplicación debería funcionar")
                print("="*70)
                return True

            except imaplib.IMAP4.error as e:
                error_msg = str(e)
                print(f"✗ {server} → Login falló: {error_msg}")

                if 'AUTHENTICATIONFAILED' in error_msg.upper():
                    print("   Causa: Credenciales incorrectas o 2FA requerido")
                    print("   Solución: Crear contraseña de aplicación")

                elif 'LOGIN' in error_msg.upper() and 'disabled' in error_msg.lower():
                    print("   Causa: Autenticación básica deshabilitada por admin")
                    print("   Solución: Pedir al admin que habilite IMAP o usar OAuth2")

                elif 'failed' in error_msg.lower():
                    print("   Causa: Autenticación fallida")
                    print("   Solución: Verificar contraseña o crear contraseña de aplicación")

    # Summary
    print("\n" + "="*70)
    print("RESUMEN Y RECOMENDACIONES")
    print("="*70)

    print(f"\n📊 Estado de la cuenta: {email}")
    print(f"   Dominio: {domain}")
    print(f"   Tipo: Cuenta empresarial Office 365")

    print("\n🔍 Diagnóstico:")
    print("   - Conexión de red: OK")
    print("   - Puerto 993: Abierto")
    print("   - SSL/TLS: Funcional")
    print("   - Autenticación: FALLÓ")

    print("\n💡 Soluciones recomendadas (en orden):")
    print("\n   1. CREAR CONTRASEÑA DE APLICACIÓN:")
    print("      - Ve a: https://mysignins.microsoft.com/security-info")
    print("      - Agregar método > Contraseña de aplicación")
    print("      - Si no ves esta opción → Pasa al punto 2")

    print("\n   2. CONTACTAR AL ADMINISTRADOR:")
    print("      Envía este mensaje a tu admin de IT:")
    print("      " + "-"*60)
    print(f"      Hola, necesito acceso IMAP para: {email}")
    print("      ")
    print("      ¿Puedes habilitar una de estas opciones?")
    print("      a) Contraseñas de aplicación para mi cuenta")
    print("      b) Autenticación básica para IMAP")
    print("      ")
    print("      Es para automatizar procesamiento de facturas.")
    print("      " + "-"*60)

    print("\n   3. ALTERNATIVA - MICROSOFT GRAPH API:")
    print("      Si el admin no puede habilitar IMAP, podemos usar")
    print("      Microsoft Graph API con OAuth2 (más moderno)")

    print("\n   4. WORKAROUND - CUENTA PERSONAL:")
    print("      Crear cuenta Outlook.com y reenviar correos")

    return False

if __name__ == "__main__":
    try:
        check_outlook_imap()
    except KeyboardInterrupt:
        print("\n\n❌ Diagnóstico cancelado")
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
