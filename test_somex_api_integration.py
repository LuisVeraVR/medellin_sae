"""Script de prueba para la integración con la API de Somex"""
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.api.somex_api_client import SomexApiClient
from src.infrastructure.database.somex_repository import SomexRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_authentication():
    """Test API authentication"""
    logger.info("=" * 60)
    logger.info("Testing Somex API Authentication")
    logger.info("=" * 60)

    api_client = SomexApiClient(logger=logger)

    success = api_client.authenticate()

    if success:
        logger.info("✓ Authentication successful!")
        logger.info(f"Token: {api_client.token[:20]}..." if api_client.token else "No token")
        return True
    else:
        logger.error("✗ Authentication failed!")
        return False


def test_get_invoice_data():
    """Test getting invoice data from API"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Get Invoice Data")
    logger.info("=" * 60)

    api_client = SomexApiClient(logger=logger)

    # Example invoice number (format: 2B-285138)
    invoice_number = "2B-285138"

    logger.info(f"Fetching data for invoice: {invoice_number}")

    invoice_data = api_client.get_invoice_data(invoice_number)

    if invoice_data:
        logger.info(f"✓ Successfully fetched {len(invoice_data)} items")
        for idx, item in enumerate(invoice_data, 1):
            logger.info(f"\nItem {idx}:")
            logger.info(f"  - Referencia: {item.get('referencia')}")
            logger.info(f"  - Cantidad Bultos: {item.get('cantidadBultos')}")
            logger.info(f"  - Cantidad Kg: {item.get('cantidadKg')}")
        return True
    else:
        logger.warning("✗ No data returned from API")
        return False


def test_repository_description_search():
    """Test repository search by description"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Repository Search by Description")
    logger.info("=" * 60)

    db_path = "data/somex_processing.db"
    repository = SomexRepository(db_path)

    # Get all items
    all_items = repository.get_all_items()
    logger.info(f"Total items in database: {len(all_items)}")

    if all_items:
        # Test search with first item
        test_item = all_items[0]
        descripcion = test_item.get('descripcion', '')

        logger.info(f"\nSearching for description: '{descripcion}'")

        found_item = repository.get_item_by_description(descripcion)

        if found_item:
            logger.info("✓ Item found by description!")
            logger.info(f"  - Código: {found_item.get('codigo_item')}")
            logger.info(f"  - Referencia: {found_item.get('referencia')}")
            logger.info(f"  - Descripción: {found_item.get('descripcion')}")
            return True
        else:
            logger.warning("✗ Item not found by description")
            return False
    else:
        logger.warning("No items in database. Import items first.")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("SOMEX API INTEGRATION TESTS")
    logger.info("=" * 60)

    results = {
        "Authentication": test_api_authentication(),
        "Get Invoice Data": test_get_invoice_data(),
        "Repository Description Search": test_repository_description_search()
    }

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{test_name}: {status}")

    total_passed = sum(1 for passed in results.values() if passed)
    total_tests = len(results)

    logger.info(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        logger.info("\n✓ All tests passed!")
        return 0
    else:
        logger.warning(f"\n✗ {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
