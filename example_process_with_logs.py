"""
Script de ejemplo para ver los logs detallados del procesamiento Somex

Este script muestra cómo:
1. Cargar el Excel de items en memoria
2. Procesar un ZIP con XMLs
3. Ver los logs detallados del proceso de comparación
"""
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.database.somex_repository import SomexRepository
from src.application.services.somex_processor_service import SomexProcessorService

# Configure logging con formato muy visible
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Solo el mensaje, sin timestamp ni nivel
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('somex_processing_detailed.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Procesar ZIPs con logs detallados"""

    # Configuración
    ITEMS_EXCEL_PATH = "path/to/your/items.xlsx"  # ⬅️ CAMBIAR ESTO
    ZIP_FILE_PATH = "path/to/your/invoice.zip"    # ⬅️ CAMBIAR ESTO

    logger.info("\n" + "=" * 100)
    logger.info("PROCESAMIENTO SOMEX CON LOGS DETALLADOS")
    logger.info("=" * 100)

    # Inicializar repositorio
    db_path = "data/somex_processing.db"
    repository = SomexRepository(db_path)

    # Inicializar servicio procesador
    logger.info("\n📋 Inicializando servicio procesador...")
    processor = SomexProcessorService(
        repository=repository,
        logger=logger,
        output_dir="output/somex"
    )

    # Cargar Excel de items
    if Path(ITEMS_EXCEL_PATH).exists():
        logger.info(f"\n📂 Cargando Excel de items: {ITEMS_EXCEL_PATH}")
        count = processor.load_items_excel(ITEMS_EXCEL_PATH)
        logger.info(f"✅ {count} items cargados en memoria\n")
    else:
        logger.error(f"❌ No se encuentra el archivo: {ITEMS_EXCEL_PATH}")
        logger.error("Por favor, actualiza ITEMS_EXCEL_PATH con la ruta correcta")
        return 1

    # Procesar ZIP
    if Path(ZIP_FILE_PATH).exists():
        logger.info("\n" + "=" * 100)
        logger.info(f"🗜️  PROCESANDO ZIP: {ZIP_FILE_PATH}")
        logger.info("=" * 100)

        results = processor.process_zip_file(ZIP_FILE_PATH)

        logger.info("\n" + "=" * 100)
        logger.info("📊 RESUMEN DEL PROCESAMIENTO")
        logger.info("=" * 100)
        logger.info(f"Total XMLs: {results['total_xmls']}")
        logger.info(f"XMLs procesados: {results['processed_xmls']}")
        logger.info(f"XMLs omitidos: {results['skipped_xmls']}")
        logger.info(f"XMLs con error: {results['failed_xmls']}")
        logger.info(f"Facturas generadas: {len(results['invoices'])}")

        # Generar Excel consolidado
        if results['invoices']:
            logger.info("\n📑 Generando Excel consolidado...")
            excel_path = processor.create_consolidated_excel(results['invoices'])
            logger.info(f"✅ Excel generado: {excel_path}")
        else:
            logger.warning("⚠️  No se generaron facturas")

    else:
        logger.error(f"❌ No se encuentra el archivo: {ZIP_FILE_PATH}")
        logger.error("Por favor, actualiza ZIP_FILE_PATH con la ruta correcta")
        return 1

    logger.info("\n" + "=" * 100)
    logger.info("✅ PROCESAMIENTO COMPLETADO")
    logger.info("=" * 100)
    logger.info(f"\nLos logs detallados se guardaron en: somex_processing_detailed.log")

    return 0


if __name__ == "__main__":
    sys.exit(main())
