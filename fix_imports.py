"""
Script to fix import statements in Medellin SAE project
Run this if git pull doesn't work
"""
import re
from pathlib import Path

def fix_imports():
    # Get project root
    project_root = Path(__file__).parent

    # Fix run.py
    run_py = project_root / "run.py"
    if run_py.exists():
        content = run_py.read_text()
        content = content.replace("from main import main", "from src.main import main")
        run_py.write_text(content)
        print("✓ Fixed run.py")

    # Fix src/main.py
    main_py = project_root / "src" / "main.py"
    if main_py.exists():
        content = main_py.read_text()
        content = content.replace("from presentation.main_window", "from src.presentation.main_window")
        main_py.write_text(content)
        print("✓ Fixed src/main.py")

    # Fix all Python files in src/
    src_path = project_root / "src"
    for py_file in src_path.rglob("*.py"):
        content = py_file.read_text()
        original = content

        # Replace relative imports with absolute
        content = re.sub(r'from \.\.\.(\w+)', r'from src.\1', content)
        content = re.sub(r'from \.\.(\w+)', r'from src.\1', content)

        if content != original:
            py_file.write_text(content)
            print(f"✓ Fixed {py_file.relative_to(project_root)}")

    print("\n✅ All imports fixed!")
    print("\nNow you can run: python run.py")

if __name__ == "__main__":
    fix_imports()
