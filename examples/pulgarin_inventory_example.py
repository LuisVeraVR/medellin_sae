"""
Example: Using Pulgarin Inventory Service

This example demonstrates how to:
1. Import a Pulgarin product inventory from Excel
2. Use the inventory with UBLXMLParser to enrich invoice data with weight information
"""
import logging
from pathlib import Path
from src.application.services.pulgarin_inventory_service import PulgarinInventoryService
from src.infrastructure.xml.ubl_xml_parser import UBLXMLParser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== STEP 1: Create and import inventory =====
logger.info("=" * 60)
logger.info("STEP 1: Import Pulgarin Inventory from Excel")
logger.info("=" * 60)

# Create inventory service
inventory_service = PulgarinInventoryService(logger)

# Path to your Pulgarin inventory Excel file
# Expected columns: Codigo, Descripcion, PESO, U/M
inventory_excel_path = "data/pulgarin_inventario.xlsx"

try:
    # Import inventory
    items_count = inventory_service.import_from_excel(inventory_excel_path)
    logger.info(f"✓ Imported {items_count} products from inventory")

    # Show statistics
    stats = inventory_service.get_stats()
    logger.info(f"  - Total items: {stats['total_items']}")
    logger.info(f"  - Items with weight: {stats['items_with_weight']}")
    logger.info(f"  - Items without weight: {stats['items_without_weight']}")

except FileNotFoundError:
    logger.warning(f"⚠ Inventory file not found: {inventory_excel_path}")
    logger.warning("  Creating example inventory structure...")

    # Show example of expected Excel structure
    logger.info("\nExpected Excel structure:")
    logger.info("┌────────────┬──────────────────────────────────┬────────┬──────┐")
    logger.info("│ Codigo     │ Descripcion                      │ PESO   │ U/M  │")
    logger.info("├────────────┼──────────────────────────────────┼────────┼──────┤")
    logger.info("│ PROD-001   │ SAL REFINADA X 500 GR            │ 0.5    │ KG   │")
    logger.info("│ PROD-002   │ AZUCAR BLANCA X 1000 GR          │ 1.0    │ KG   │")
    logger.info("│ PROD-003   │ ACEITE VEGETAL X 1 LITRO         │ 0.92   │ LT   │")
    logger.info("└────────────┴──────────────────────────────────┴────────┴──────┘")

    # Continue with empty inventory for demonstration
    logger.info("\nContinuing with empty inventory for demonstration...\n")

# ===== STEP 2: Create UBL Parser with inventory =====
logger.info("=" * 60)
logger.info("STEP 2: Create UBL Parser with Inventory")
logger.info("=" * 60)

# Create parser with inventory service
parser = UBLXMLParser(inventory_service=inventory_service)
logger.info("✓ Created UBLXMLParser with inventory service")

# ===== STEP 3: Example usage =====
logger.info("\n" + "=" * 60)
logger.info("STEP 3: How it works")
logger.info("=" * 60)

logger.info("""
When parsing an invoice XML:

1. The parser extracts the product name from the XML
   Example: "SAL REFINADA X 500 GR"

2. The parser searches the inventory by product name
   - Comparison is case-insensitive and trimmed
   - "SAL REFINADA X 500 GR" matches "sal refinada x 500 gr"

3. If found in inventory:
   - Weight (PESO) is assigned from inventory
   - Unit of measure (U/M) is assigned from inventory

4. If NOT found in inventory:
   - Parser tries to extract weight from XML
   - Uses unit code from XML (e.g., KGM -> KG)

5. Result is an InvoiceItem with:
   - product_name: "SAL REFINADA X 500 GR"
   - weight: 0.5 (from inventory)
   - unit_of_measure: "KG" (from inventory)
   - total_value: quantity × unit_price (calculated)
""")

# ===== STEP 4: Test lookups =====
if inventory_service.get_stats()['total_items'] > 0:
    logger.info("=" * 60)
    logger.info("STEP 4: Testing Inventory Lookups")
    logger.info("=" * 60)

    # Example lookups
    test_products = [
        "SAL REFINADA X 500 GR",
        "AZUCAR BLANCA X 1000 GR",
        "PRODUCTO NO EXISTENTE"
    ]

    for product in test_products:
        item = inventory_service.find_by_description(product)
        if item:
            logger.info(f"✓ Found: {product}")
            logger.info(f"  - Codigo: {item.codigo}")
            logger.info(f"  - Peso: {item.peso} {item.unidad_medida}")
        else:
            logger.info(f"✗ Not found: {product}")

# ===== STEP 5: Integration with existing code =====
logger.info("\n" + "=" * 60)
logger.info("STEP 5: Integration Instructions")
logger.info("=" * 60)

logger.info("""
To integrate this in your existing code:

1. In your main application or use case:

   from src.application.services.pulgarin_inventory_service import PulgarinInventoryService
   from src.infrastructure.xml.ubl_xml_parser import UBLXMLParser

   # Load inventory
   inventory_service = PulgarinInventoryService(logger)
   inventory_service.import_from_excel("data/pulgarin_inventario.xlsx")

   # Create parser with inventory
   parser = UBLXMLParser(inventory_service=inventory_service)

   # Use parser normally - it will automatically look up weights
   invoice = parser.parse_invoice(xml_content)

2. The CSV/Excel export will automatically include the weight and U/M
   columns because InvoiceItem now has these fields populated.

3. To update inventory:
   - Simply update the Excel file
   - Re-run import_from_excel()
   - All new invoices will use the updated weights
""")

logger.info("\n" + "=" * 60)
logger.info("Example Complete!")
logger.info("=" * 60)
