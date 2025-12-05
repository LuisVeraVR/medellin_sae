#!/usr/bin/env python3
"""
Script de Diagnóstico - Verifica por qué el CSV está vacío
"""

import csv
from pathlib import Path

def main():
    print("\n" + "="*70)
    print("  DIAGNÓSTICO: CSV Vacío")
    print("="*70 + "\n")

    # Find the most recent CSV
    output_dir = Path("output/pulgarin")

    if not output_dir.exists():
        print("✗ El directorio output/pulgarin no existe")
        return 1

    csv_files = list(output_dir.glob("*.csv"))

    if not csv_files:
        print("✗ No se encontraron archivos CSV en output/pulgarin")
        return 1

    # Get the most recent file
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)

    print(f"Archivo más reciente: {latest_csv.name}")
    print(f"Tamaño: {latest_csv.stat().st_size} bytes")
    print()

    # Read and analyze the CSV
    with open(latest_csv, 'r', encoding='utf-8-sig') as f:
        # Count lines
        lines = f.readlines()
        print(f"Total de líneas en el archivo: {len(lines)}")
        print(f"  - Cabecera: 1 línea")
        print(f"  - Datos: {len(lines) - 1} líneas")
        print()

        # Show first few lines
        print("Primeras 3 líneas del archivo:")
        print("-" * 70)
        for i, line in enumerate(lines[:3], 1):
            print(f"{i}: {line[:100]}...")  # First 100 chars
        print()

        # Parse CSV
        f.seek(0)
        reader = csv.reader(f, delimiter=';')

        headers = next(reader)
        print(f"Columnas detectadas: {len(headers)}")
        print("Cabeceras:")
        for i, h in enumerate(headers, 1):
            print(f"  {i}. {h}")
        print()

        # Count data rows
        data_rows = list(reader)
        print(f"Filas de datos: {len(data_rows)}")

        if len(data_rows) == 0:
            print("\n⚠️  EL CSV NO TIENE DATOS")
            print("\nPosibles causas:")
            print("  1. Los items de las facturas están vacíos (invoice.items = [])")
            print("  2. Hay un error en el método export_invoices()")
            print("  3. Las facturas se parsearon pero sin items")
            print()
            print("Ejecuta el script de diagnóstico para ver los items:")
            print("  python diagnostico_pulgarin.py")
        else:
            print("\n✓ El CSV tiene datos!")
            print(f"\nPrimera fila de datos:")
            print("-" * 70)
            for i, (header, value) in enumerate(zip(headers, data_rows[0]), 1):
                print(f"  {header}: {value}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
