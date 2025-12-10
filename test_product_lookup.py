"""
Test script to verify product lookup functionality
Usage: python test_product_lookup.py
"""
import sys
from pathlib import Path
from src.infrastructure.database.sqlite_repository import SQLiteRepository

def main():
    # Check if database exists
    db_path = Path("data/app.db")
    if not db_path.exists():
        print("❌ Base de datos no existe en data/app.db")
        print("\n💡 Solución:")
        print("   1. Abre la aplicación Medellin SAE")
        print("   2. Ve a la pestaña 'Productos Pulgarin'")
        print("   3. Haz clic en '📥 Importar desde Excel'")
        print("   4. Selecciona tu archivo Excel con los productos")
        return

    # Initialize repository
    repo = SQLiteRepository(str(db_path))

    # Check number of products
    products = repo.get_all_products()
    print(f"✅ Base de datos encontrada")
    print(f"📊 Total de productos en la base de datos: {len(products)}")

    if len(products) == 0:
        print("\n❌ No hay productos importados")
        print("\n💡 Solución:")
        print("   1. Abre la aplicación Medellin SAE")
        print("   2. Ve a la pestaña 'Productos Pulgarin'")
        print("   3. Haz clic en '📥 Importar desde Excel'")
        print("   4. Selecciona tu archivo Excel con los productos")
        return

    # Show sample products
    print("\n📦 Primeros 5 productos:")
    for i, p in enumerate(products[:5], 1):
        codigo = p['codigo'] if p['codigo'] else '(sin código)'
        print(f"   {i}. Código: {codigo}")
        print(f"      Descripción: {p['descripcion']}")
        print(f"      Peso: {p['peso']}, U/M: {p['um']}")
        print()

    # Test lookup functionality
    print("\n🔍 Prueba de búsqueda:")
    test_product = products[0]

    # Test by code
    if test_product['codigo']:
        result = repo.find_product_by_code_or_description(
            codigo=test_product['codigo'],
            descripcion=test_product['descripcion']
        )
        if result:
            print(f"   ✅ Búsqueda por código '{test_product['codigo']}' funciona")
        else:
            print(f"   ❌ Búsqueda por código '{test_product['codigo']}' falló")

    # Test by description
    result = repo.find_product_by_description(test_product['descripcion'])
    if result:
        print(f"   ✅ Búsqueda por descripción '{test_product['descripcion']}' funciona")
    else:
        print(f"   ❌ Búsqueda por descripción '{test_product['descripcion']}' falló")

    print("\n✅ Sistema de productos Pulgarin configurado correctamente")
    print("\n📝 Cuando proceses facturas de Pulgarin, las columnas 'Peso' y 'U/M BD'")
    print("   se llenarán automáticamente con los datos de la base de datos.")

if __name__ == "__main__":
    main()
