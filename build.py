"""Build script for creating executable with PyInstaller"""
import PyInstaller.__main__
import sys
import shutil
from pathlib import Path

def build():
    """Build the application executable"""

    # Get the project root directory
    root_dir = Path(__file__).parent
    main_script = root_dir / "src" / "main.py"

    # Platform-specific separator for --add-data
    separator = ';' if sys.platform == 'win32' else ':'

    # PyInstaller arguments
    args = [
        str(main_script),
        '--name=MedellinSAE',
        '--onefile',
        '--windowed',
        '--noconfirm',

        # Add data files
        f'--add-data={root_dir / "config"}{separator}config',
        f'--add-data={root_dir / "version.txt"}{separator}.',

        # Exclude unnecessary modules to reduce size
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=PIL',
        '--exclude-module=setuptools',

        # Hidden imports (modules that PyInstaller might not detect automatically)
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=msal',
        '--hidden-import=paramiko',

        # Optimization
        '--clean',
        '--optimize=2',  # Python optimization level

        # Output directory
        f'--distpath={root_dir / "dist"}',
        f'--workpath={root_dir / "build"}',
        f'--specpath={root_dir}',
    ]

    # Add icon if available
    icon_path = root_dir / "icon.ico"
    if icon_path.exists():
        args.append(f'--icon={icon_path}')

    # Add OAuth config if available (for embedded credentials in production)
    oauth_config_path = root_dir / "config" / "oauth_config.json"
    if oauth_config_path.exists():
        print(f"\n✓ Found oauth_config.json - will be included in executable")
        print("  This allows the executable to work without .env configuration")
    else:
        print(f"\n⚠ oauth_config.json not found - executable will require .env setup")
        print("  To include OAuth credentials in the executable:")
        print("  1. Copy config/oauth_config.example.json to config/oauth_config.json")
        print("  2. Edit oauth_config.json with your Azure AD credentials")
        print("  3. Run build.py again")

    print()
    print("=" * 60)
    print("Building MedellinSAE executable...")
    print("=" * 60)
    print(f"Main script: {main_script}")
    print(f"Platform: {sys.platform}")
    print()

    # Run PyInstaller
    try:
        PyInstaller.__main__.run(args)
    except Exception as e:
        print(f"\nERROR during build: {e}")
        return 1

    print()
    print("=" * 60)
    print("Build completed successfully!")
    print("=" * 60)

    exe_name = 'MedellinSAE.exe' if sys.platform == 'win32' else 'MedellinSAE'
    exe_path = root_dir / 'dist' / exe_name

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"Executable: {exe_path}")
        print(f"Size: {size_mb:.2f} MB")
        print()
        print("Next steps:")
        print("1. Test the executable by running it")
        print("2. Create installer with: python create_installer.py")
    else:
        print("ERROR: Executable not found!")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(build())
