# Guía de Uso: Gestión de Inventario en Pulgarin (Interfaz Gráfica)

## 📋 Descripción

La pestaña de Pulgarin ahora incluye una sección de **Gestión de Inventario** que permite importar un catálogo de productos desde Excel. Este inventario se usa automáticamente para asignar peso (PESO) y unidad de medida (U/M) a los productos en las facturas procesadas.

## 🖥️ Ubicación en la Interfaz

1. Abre la aplicación **Medellin SAE**
2. Ve a la pestaña **"Pulgarin"**
3. Verás una sección nueva llamada **"Gestión de Inventario (Pulgarin)"**

## 📊 Estructura de la Sección de Inventario

La sección incluye:

### Botones
- **📁 Importar Inventario desde Excel**: Abre un diálogo para seleccionar el archivo Excel de inventario
- **📝 Crear Excel de Ejemplo**: Genera un archivo Excel de ejemplo con la estructura correcta

### Estadísticas
- **Estado**: Muestra si el inventario está cargado o no
- **Productos**: Cantidad total de productos en el inventario
- **Con peso**: Cantidad de productos que tienen peso definido

### Información
- Texto informativo explicando cómo funciona el inventario

## 🚀 Cómo Usar

### Opción 1: Crear Excel de Ejemplo

1. **Click en "📝 Crear Excel de Ejemplo"**
   - Se abrirá un diálogo para guardar el archivo
   - Por defecto se guarda en: `data/pulgarin_inventario_ejemplo.xlsx`
   - El sistema preguntará si deseas abrir el archivo

2. **Edita el archivo Excel**
   - Abre el archivo en Excel/LibreOffice
   - Verás 5 productos de ejemplo
   - **Reemplaza** los productos de ejemplo con tus productos reales
   - Mantén la estructura de columnas: `Codigo`, `Descripcion`, `PESO`, `U/M`

3. **Guarda el archivo**
   - Guárdalo como `pulgarin_inventario.xlsx` en la carpeta `data/`
   - O con cualquier nombre que prefieras

4. **Importa el inventario**
   - Sigue los pasos de la Opción 2

### Opción 2: Importar Inventario Existente

1. **Click en "📁 Importar Inventario desde Excel"**
   - Se abrirá un diálogo de selección de archivo
   - Por defecto busca en la carpeta `data/`

2. **Selecciona tu archivo de inventario**
   - Debe ser un archivo Excel (.xlsx o .xls)
   - Debe tener las columnas: `Codigo`, `Descripcion`, `PESO`, `U/M`

3. **Verifica la importación**
   - En el log aparecerá: `✓ Inventario importado exitosamente: X productos`
   - Las estadísticas se actualizarán:
     - Estado cambiará a "✓ Cargado" (en verde)
     - Se mostrará el número de productos
     - Se mostrará cuántos tienen peso

4. **Procesa facturas normalmente**
   - Ahora cuando proceses facturas, el peso y U/M se asignarán automáticamente
   - El sistema comparará el "Nombre Producto" de la factura con la "Descripcion" del inventario
   - La comparación es case-insensitive (no distingue mayúsculas/minúsculas)

## 📝 Estructura del Excel de Inventario

```
┌────────────┬──────────────────────────────────┬────────┬──────┐
│ Codigo     │ Descripcion                      │ PESO   │ U/M  │
├────────────┼──────────────────────────────────┼────────┼──────┤
│ PROD-001   │ SAL REFINADA X 500 GR            │ 0.5    │ KG   │
│ PROD-002   │ SAL REFINADA X 1000 GR           │ 1.0    │ KG   │
│ PROD-003   │ AZUCAR BLANCA X 500 GR           │ 0.5    │ KG   │
│ PROD-004   │ AZUCAR BLANCA X 1000 GR          │ 1.0    │ KG   │
│ PROD-005   │ ACEITE VEGETAL X 1 LITRO         │ 0.92   │ LT   │
└────────────┴──────────────────────────────────┴────────┴──────┘
```

### Columnas

| Columna | Obligatoria | Descripción | Ejemplo |
|---------|-------------|-------------|---------|
| **Codigo** | No | Código único del producto | PROD-001 |
| **Descripcion** | **SÍ** | Nombre del producto (debe coincidir con factura) | SAL REFINADA X 500 GR |
| **PESO** | No | Peso del producto en la unidad especificada | 0.5 |
| **U/M** | No | Unidad de medida (KG, LT, UN, etc.) | KG |

**Importante**:
- La columna **Descripcion** es obligatoria y se usa para hacer el matching con los productos de la factura
- La descripción debe coincidir **exactamente** con el nombre del producto en la factura (salvo por mayúsculas/minúsculas)

## 🔄 Carga Automática al Inicio

Si existe un archivo `data/pulgarin_inventario.xlsx`, el sistema lo cargará **automáticamente** al iniciar la aplicación.

Esto significa que:
- No necesitas importar el inventario cada vez que abres la aplicación
- Solo importa manualmente cuando actualices el inventario

## 📈 Flujo de Trabajo Completo

```
1. [Primera vez] Crear Excel de ejemplo
   ↓
2. Editar el Excel con tus productos
   ↓
3. Guardar como data/pulgarin_inventario.xlsx
   ↓
4. [Automático] El sistema carga el inventario al iniciar
   ↓
5. Click en "Procesar Ahora"
   ↓
6. [Automático] Para cada producto en la factura:
      - Busca en inventario por nombre
      - Si encuentra → Asigna PESO y U/M del inventario
      - Si NO encuentra → Usa datos del XML (si existen)
   ↓
7. CSV/Excel generado incluye columnas PESO, U/M y Valor Total
```

## ⚙️ Actualizar el Inventario

Para actualizar el inventario:

1. **Edita el archivo Excel** con los nuevos productos o cambios
2. **Guarda el archivo**
3. **En la aplicación**: Click en "📁 Importar Inventario desde Excel"
4. **Selecciona el archivo** actualizado
5. **Listo**: Las próximas facturas procesadas usarán el inventario actualizado

No necesitas reiniciar la aplicación.

## 🔍 Verificación

Para verificar que el inventario se está usando:

1. **Revisa el log** en la pestaña de Pulgarin
   - Debe aparecer: `"Using XML parser with inventory for Pulgarin (X items)"`

2. **Revisa las estadísticas**
   - Estado debe estar en verde: "✓ Cargado"
   - Número de productos debe ser mayor a 0

3. **Procesa una factura de prueba**
   - En el CSV/Excel generado, la columna "Peso" debe tener valores
   - Verifica que los pesos coincidan con tu inventario

## ⚠️ Solución de Problemas

### Inventario no se carga al inicio
**Solución**:
- Verifica que el archivo existe en `data/pulgarin_inventario.xlsx`
- Revisa el log en la pestaña "Logs" para ver si hay errores

### Productos sin peso en el CSV
**Posibles causas**:
1. **El nombre no coincide**: La descripción en el inventario debe ser **exactamente** igual al nombre en la factura
2. **Inventario no cargado**: Verifica que las estadísticas muestren productos cargados
3. **Producto no existe en inventario**: Agrega el producto al Excel e importa nuevamente

### Error al importar Excel
**Posibles causas**:
1. **Archivo abierto**: Cierra el Excel antes de importar
2. **Columnas incorrectas**: Verifica que tenga las columnas correctas
3. **Formato incorrecto**: Usa el botón "Crear Excel de Ejemplo" para obtener la estructura correcta

## 💡 Consejos

1. **Nombres exactos**: Asegúrate que los nombres en el inventario coincidan exactamente con los de las facturas
2. **Prueba con pocos productos**: Comienza con 5-10 productos para verificar que funciona
3. **Revisa los logs**: Siempre revisa el log después de procesar para verificar el matching
4. **Mantén backup**: Guarda una copia del Excel de inventario antes de hacer cambios grandes
5. **Usa el ejemplo**: Si tienes dudas de la estructura, crea un Excel de ejemplo para verificar

## 📚 Documentación Adicional

Para más información técnica sobre el servicio de inventario, consulta:
- `docs/PULGARIN_INVENTORY.md` - Documentación completa
- `examples/pulgarin_inventory_example.py` - Ejemplo de uso programático
