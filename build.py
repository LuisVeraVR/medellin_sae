"""Build script for creating executable with PyInstaller"""
import PyInstaller.__main__
import sys
from pathlib import Path

def build():
    """Build the application executable"""

    # Get the project root directory
    root_dir = Path(__file__).parent
    main_script = root_dir / "src" / "main.py"

    # PyInstaller arguments
    args = [
        str(main_script),
        '--name=MedellinSAE',
        '--onefile',
        '--windowed',
        '--noconfirm',

        # Add data files
        f'--add-data={root_dir / "config"}:config',
        f'--add-data={root_dir / "version.txt"}:.',

        # Exclude unnecessary modules
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',

        # Optimization
        '--clean',

        # Output directory
        f'--distpath={root_dir / "dist"}',
        f'--workpath={root_dir / "build"}',
        f'--specpath={root_dir}',
    ]

    # Add icon if available
    icon_path = root_dir / "icon.ico"
    if icon_path.exists():
        args.append(f'--icon={icon_path}')

    print("Building MedellinSAE executable...")
    print(f"Main script: {main_script}")
    print(f"Arguments: {' '.join(args)}")

    # Run PyInstaller
    PyInstaller.__main__.run(args)

    print("\nBuild completed!")
    print(f"Executable location: {root_dir / 'dist' / 'MedellinSAE.exe'}")

if __name__ == "__main__":
    build()
