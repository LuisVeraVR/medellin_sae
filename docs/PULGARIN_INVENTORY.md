# Pulgarin Inventory Service

## Descripción

El servicio de inventario de Pulgarin permite importar un catálogo de productos desde Excel y usar esta información para enriquecer automáticamente las facturas procesadas con datos de peso (PESO) y unidad de medida (U/M).

## Estructura del Excel de Inventario

El archivo Excel debe tener las siguientes columnas en la primera fila:

| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| **Codigo** | Código del producto | PROD-001 |
| **Descripcion** | Nombre/descripción del producto | SAL REFINADA X 500 GR |
| **PESO** | Peso del producto (en la unidad especificada) | 0.5 |
| **U/M** | Unidad de medida (KG, LT, UN, etc.) | KG |

### Ejemplo de Estructura

```
┌────────────┬──────────────────────────────────┬────────┬──────┐
│ Codigo     │ Descripcion                      │ PESO   │ U/M  │
├────────────┼──────────────────────────────────┼────────┼──────┤
│ PROD-001   │ SAL REFINADA X 500 GR            │ 0.5    │ KG   │
│ PROD-002   │ AZUCAR BLANCA X 1000 GR          │ 1.0    │ KG   │
│ PROD-003   │ ACEITE VEGETAL X 1 LITRO         │ 0.92   │ LT   │
└────────────┴──────────────────────────────────┴────────┴──────┘
```

## Cómo Funciona

### 1. Importación del Inventario

```python
from src.application.services.pulgarin_inventory_service import PulgarinInventoryService

# Crear servicio de inventario
inventory_service = PulgarinInventoryService(logger)

# Importar desde Excel
items_count = inventory_service.import_from_excel("data/pulgarin_inventario.xlsx")
print(f"Importados {items_count} productos")
```

### 2. Integración con el Parser

```python
from src.infrastructure.xml.ubl_xml_parser import UBLXMLParser

# Crear parser con inventario
parser = UBLXMLParser(inventory_service=inventory_service)

# Usar normalmente - automáticamente busca pesos en el inventario
invoice = parser.parse_invoice(xml_content)
```

### 3. Proceso de Matching

Cuando el parser procesa una factura:

1. **Extrae el nombre del producto** del XML de la factura
   - Ejemplo: `"SAL REFINADA X 500 GR"`

2. **Busca en el inventario** por descripción
   - La búsqueda es **case-insensitive** (no distingue mayúsculas/minúsculas)
   - Elimina espacios extras al inicio y final
   - `"SAL REFINADA X 500 GR"` coincide con `"sal refinada x 500 gr"`

3. **Si encuentra el producto en el inventario:**
   - ✅ Asigna el **PESO** del inventario al `InvoiceItem`
   - ✅ Asigna la **U/M** del inventario al `InvoiceItem`

4. **Si NO encuentra el producto:**
   - ⚠️ Intenta extraer el peso del XML (si está disponible)
   - ⚠️ Usa la unidad de medida del XML

### 4. Resultado en CSV/Excel

Las columnas exportadas incluirán automáticamente:

| Columna | Origen | Ejemplo |
|---------|--------|---------|
| Nombre Producto | XML factura | SAL REFINADA X 500 GR |
| U/M | Inventario (prioritario) o XML | KG |
| **Peso** | Inventario (prioritario) o XML | 0.5 |
| Cantidad | XML factura | 100 |
| Precio Unitario | XML factura | 1500.00 |
| **Valor Total** | Calculado (Cantidad × Precio) | 150000.00 |

## Uso Práctico

### Crear Excel de Ejemplo

```bash
python examples/pulgarin_inventario_ejemplo.py
```

Esto creará `data/pulgarin_inventario_ejemplo.xlsx` con 15 productos de ejemplo.

### Ejecutar Ejemplo Completo

```bash
python examples/pulgarin_inventory_example.py
```

Este script demuestra:
- Importación del inventario
- Creación del parser con inventario
- Búsquedas de productos
- Integración completa

## Actualizar el Inventario

Para actualizar el inventario:

1. **Editar el Excel**: Abre `pulgarin_inventario.xlsx` y actualiza los productos
2. **Re-importar**: Ejecuta nuevamente `import_from_excel()`
3. **Automático**: Todas las facturas procesadas después usarán los nuevos datos

```python
# Actualizar inventario sin reiniciar la aplicación
inventory_service.import_from_excel("data/pulgarin_inventario.xlsx")
```

## Estadísticas del Inventario

```python
stats = inventory_service.get_stats()
print(f"Total de productos: {stats['total_items']}")
print(f"Productos con peso: {stats['items_with_weight']}")
print(f"Productos sin peso: {stats['items_without_weight']}")
```

## Búsqueda Manual

```python
# Buscar producto completo
item = inventory_service.find_by_description("SAL REFINADA X 500 GR")
if item:
    print(f"Código: {item.codigo}")
    print(f"Peso: {item.peso} {item.unidad_medida}")

# Obtener solo el peso
peso = inventory_service.get_weight("SAL REFINADA X 500 GR")

# Obtener solo la U/M
unidad = inventory_service.get_unit_of_measure("SAL REFINADA X 500 GR")
```

## Integración en Aplicación Existente

### Modificar el Use Case

```python
# En process_invoices_use_case.py o similar

from src.application.services.pulgarin_inventory_service import PulgarinInventoryService

class ProcessInvoicesUseCase:
    def __init__(self, ...):
        # ... existente ...

        # Agregar inventario
        self.inventory_service = PulgarinInventoryService(logger)

        # Cargar inventario al inicio
        try:
            self.inventory_service.import_from_excel("data/pulgarin_inventario.xlsx")
            logger.info("Inventario de Pulgarin cargado")
        except FileNotFoundError:
            logger.warning("Archivo de inventario no encontrado - continuando sin inventario")

    def execute(self, client, ...):
        # Crear parser con inventario para Pulgarin
        if client.id == "pulgarin":
            xml_parser = UBLXMLParser(inventory_service=self.inventory_service)
        else:
            xml_parser = UBLXMLParser()

        # ... resto del código ...
```

## Ventajas

✅ **Consistencia**: Todos los productos tienen peso y U/M consistentes
✅ **Mantenimiento**: Actualiza el Excel, no el código
✅ **Fallback**: Si no está en inventario, usa datos del XML
✅ **Case-insensitive**: Funciona con mayúsculas, minúsculas o mixto
✅ **Sin cambios en XML**: No requiere modificar las facturas XML de Pulgarin

## Notas Importantes

- El campo **Descripcion** es obligatorio (se usa como clave de búsqueda)
- El campo **PESO** es opcional (puede estar vacío)
- Los campos **Codigo** y **U/M** son opcionales pero recomendados
- La comparación de descripciones es exacta pero case-insensitive
- Si un producto tiene múltiples presentaciones, crear una fila por cada una

## Troubleshooting

### Producto no se encuentra en inventario

**Problema**: El parser no encuentra el peso del inventario

**Soluciones**:
1. Verifica que la descripción en el Excel **coincida exactamente** con la del XML
2. Revisa mayúsculas/minúsculas (deben ser iguales salvo por case)
3. Verifica espacios extra al inicio o final
4. Usa `inventory_service.find_by_description()` para probar manualmente

### Peso incorrecto en factura

**Problema**: El peso no es el esperado

**Soluciones**:
1. Verifica el archivo Excel tiene el peso correcto
2. Re-importa el inventario: `import_from_excel()`
3. Verifica que el producto se encuentra: `get_weight(nombre_producto)`

### Error al importar Excel

**Problema**: Error al leer el archivo Excel

**Soluciones**:
1. Verifica que el archivo existe en la ruta especificada
2. Asegura que tiene las columnas correctas (Codigo, Descripcion, PESO, U/M)
3. Verifica que el archivo no esté abierto en Excel
4. Revisa los logs para detalles del error
