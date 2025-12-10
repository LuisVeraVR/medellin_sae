"""Script para crear instalador de Windows con Inno Setup"""
import subprocess
import sys
from pathlib import Path
import os

def find_inno_setup():
    """Encuentra la instalación de Inno Setup en Windows"""
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None

def create_installer():
    """Crea el instalador de Windows usando Inno Setup"""

    # Verificar que estamos en Windows
    if sys.platform != 'win32':
        print("ERROR: Este script solo funciona en Windows")
        print("El instalador se debe crear en una máquina Windows con Inno Setup instalado")
        return 1

    # Verificar que existe el ejecutable
    root_dir = Path(__file__).parent
    exe_path = root_dir / "dist" / "MedellinSAE.exe"

    if not exe_path.exists():
        print("ERROR: No se encontró el ejecutable MedellinSAE.exe")
        print("Primero ejecuta: python build.py")
        return 1

    # Buscar Inno Setup
    iscc_path = find_inno_setup()

    if not iscc_path:
        print("ERROR: No se encontró Inno Setup instalado")
        print()
        print("Por favor, descarga e instala Inno Setup desde:")
        print("https://jrsoftware.org/isdl.php")
        print()
        print("Después de instalarlo, ejecuta este script nuevamente")
        return 1

    # Script de Inno Setup
    iss_script = root_dir / "installer.iss"

    if not iss_script.exists():
        print("ERROR: No se encontró el archivo installer.iss")
        return 1

    print("=" * 60)
    print("Creando instalador de Windows...")
    print("=" * 60)
    print(f"Inno Setup: {iscc_path}")
    print(f"Script: {iss_script}")
    print(f"Ejecutable: {exe_path}")
    print()

    # Compilar el instalador
    try:
        result = subprocess.run(
            [iscc_path, str(iss_script)],
            capture_output=True,
            text=True,
            cwd=str(root_dir)
        )

        print(result.stdout)

        if result.returncode != 0:
            print("ERROR al compilar el instalador:")
            print(result.stderr)
            return 1

        # Buscar el instalador generado
        output_dir = root_dir / "installer_output"
        installers = list(output_dir.glob("MedellinSAE_Setup_*.exe"))

        if installers:
            installer_path = installers[0]
            size_mb = installer_path.stat().st_size / (1024 * 1024)

            print()
            print("=" * 60)
            print("Instalador creado exitosamente!")
            print("=" * 60)
            print(f"Archivo: {installer_path}")
            print(f"Tamaño: {size_mb:.2f} MB")
            print()
            print("Ahora puedes distribuir este instalador a los usuarios")
        else:
            print("ADVERTENCIA: No se encontró el instalador generado")
            print(f"Busca en: {output_dir}")

        return 0

    except Exception as e:
        print(f"ERROR al ejecutar Inno Setup: {e}")
        return 1

def main():
    """Punto de entrada principal"""
    return create_installer()

if __name__ == "__main__":
    sys.exit(main())
