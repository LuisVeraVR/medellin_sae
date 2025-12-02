"""
Script para probar conexión específica a imap.correagro.com
"""
import imaplib
import getpass

def test_correagro_imap():
    print("="*70)
    print("PRUEBA DE CONEXIÓN - imap.correagro.com")
    print("="*70)

    email = "inteligenciadenegocios@correagro.com"

    print(f"\nEmail: {email}")
    print("Servidor: imap.correagro.com")
    print("Puerto: 993 (SSL)")

    print("\n" + "="*70)
    print("IMPORTANTE:")
    print("="*70)
    print("Este es el servidor PROPIO de Correagro, NO es Office 365.")
    print("Debes usar tu CONTRASEÑA NORMAL de correo, NO la de aplicación.")
    print("="*70)

    password = getpass.getpass("\nIngresa tu contraseña NORMAL de correo: ")

    print("\nIntentando conectar...")

    try:
        # Conectar
        print("1. Estableciendo conexión SSL...")
        imap = imaplib.IMAP4_SSL("imap.correagro.com", 993)
        print("   ✓ Conexión SSL establecida")

        # Autenticar
        print(f"2. Autenticando {email}...")
        result = imap.login(email, password)
        print(f"   ✓ LOGIN EXITOSO: {result}")

        # Listar carpetas
        print("3. Listando carpetas...")
        status, folders = imap.list()
        if status == 'OK':
            print(f"   ✓ Carpetas encontradas: {len(folders)}")
            print("\n   Primeras 10 carpetas:")
            for i, folder in enumerate(folders[:10], 1):
                print(f"      {i}. {folder.decode()}")

        # Seleccionar INBOX
        print("\n4. Seleccionando INBOX...")
        status, count = imap.select('INBOX')
        if status == 'OK':
            msg_count = int(count[0])
            print(f"   ✓ INBOX: {msg_count} mensajes totales")

        # Buscar no leídos
        print("5. Buscando correos no leídos...")
        status, messages = imap.search(None, 'UNSEEN')
        if status == 'OK':
            unread = messages[0].split()
            print(f"   ✓ Correos no leídos: {len(unread)}")

        # Buscar con "TRIPLE A"
        print('6. Buscando "TRIPLE A" en asunto...')
        status, messages = imap.search(None, 'SUBJECT', '"TRIPLE A"')
        if status == 'OK':
            triple_a = messages[0].split()
            print(f"   ✓ Correos con 'TRIPLE A': {len(triple_a)}")

            if len(triple_a) > 0:
                print(f"\n   Mostrando primeros 3 correos:")
                for i, msg_id in enumerate(triple_a[:3], 1):
                    status, data = imap.fetch(msg_id, '(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])')
                    if status == 'OK':
                        print(f"\n   Correo #{i} (ID: {msg_id.decode()}):")
                        print(f"   {data[0][1].decode()}")

        # Cerrar
        imap.close()
        imap.logout()

        print("\n" + "="*70)
        print("✅ ¡CONEXIÓN EXITOSA!")
        print("="*70)
        print("\nConfigura la aplicación así:")
        print("\n1. En config/clients.json:")
        print('   "imap_server": "imap.correagro.com"')
        print("\n2. En .env:")
        print(f"   CORREAGRO_EMAIL={email}")
        print("   CORREAGRO_PASSWORD=TuContraseñaNormal")
        print("\n3. Ejecuta: python run.py")

        return True

    except imaplib.IMAP4.error as e:
        print(f"\n✗ Error IMAP: {e}")
        print("\nPosibles causas:")
        print("1. Contraseña incorrecta")
        print("2. IMAP deshabilitado para tu cuenta")
        print("3. Firewall bloqueando la conexión")
        print("\nContacta al administrador de IT de Correagro")
        return False

    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    try:
        test_correagro_imap()
    except KeyboardInterrupt:
        print("\n\nCancelado por el usuario")
