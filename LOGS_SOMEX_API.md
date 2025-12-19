# Logs Detallados - Integración API Somex

## 📋 Descripción

El sistema ahora procesa facturas siguiendo estos pasos y generando logs muy claros para cada uno:

## 🔄 Flujo de Procesamiento

### 1. Carga de Excel de Items

```
================================================================================
📁 CARGANDO EXCEL DE ITEMS: path/to/items.xlsx
================================================================================
Columnas encontradas: ['CodigoItem', 'Referencia', 'Descripcion', ...]
✅ CARGADOS 150 ITEMS EN MEMORIA
Ejemplos de items cargados:
  - Desc: 'SAL SOMEX CEBA X 40 KILOS' → Ref: '120704'
  - Desc: 'PRODUCTO EJEMPLO 2' → Ref: '120705'
  - Desc: 'PRODUCTO EJEMPLO 3' → Ref: '120706'
================================================================================
```

### 2. Procesamiento de cada Producto

Para cada producto del XML, verás estos logs:

```
====================================================================================================
📦 PRODUCTO DEL XML: 'SAL SOMEX CEBA X 40 KILOS'
📊 Cantidad original del XML: 20.00000

🔍 PASO 1: Buscando referencia en Excel para: 'SAL SOMEX CEBA X 40 KILOS'
✅ REFERENCIA ENCONTRADA EN EXCEL: '120704'

🌐 PASO 2: Consultando API Somex
   Factura: 2B-285138
   Buscando referencia: 120704
📊 API respondió con 5 items
   Referencias en la API:
      [1] Ref: 120704
      [2] Ref: 120705
      [3] Ref: 120706
      [4] Ref: 120707
      [5] Ref: 120708

🔎 PASO 3: Comparando referencia '120704' con items de API
====================================================================================================
✅✅✅ MATCH ENCONTRADO EN API ✅✅✅
   Producto: 'SAL SOMEX CEBA X 40 KILOS'
   Referencia: 120704
   cantidadBultos: 20.00
   cantidadKg: 800.00
====================================================================================================
```

### 3. Cuando NO se encuentra en la API

Si la referencia no está en la API:

```
====================================================================================================
📦 PRODUCTO DEL XML: 'PRODUCTO NO EN API'
📊 Cantidad original del XML: 10.00000

🔍 PASO 1: Buscando referencia en Excel para: 'PRODUCTO NO EN API'
✅ REFERENCIA ENCONTRADA EN EXCEL: '999999'

🌐 PASO 2: Consultando API Somex
   Factura: 2B-285138
   Buscando referencia: 999999
📊 API respondió con 5 items
   Referencias en la API:
      [1] Ref: 120704
      [2] Ref: 120705
      [3] Ref: 120706
      [4] Ref: 120707
      [5] Ref: 120708

🔎 PASO 3: Comparando referencia '999999' con items de API
❌ NO SE ENCONTRÓ la referencia '999999' en los items de la API

⚠️  USANDO MÉTODO FALLBACK (cálculo manual de kilos)
```

### 4. Cuando NO se encuentra en Excel

Si el producto no está en el Excel de items:

```
====================================================================================================
📦 PRODUCTO DEL XML: 'PRODUCTO DESCONOCIDO'
📊 Cantidad original del XML: 5.00000

🔍 PASO 1: Buscando referencia en Excel para: 'PRODUCTO DESCONOCIDO'
❌ NO SE ENCONTRÓ referencia en Excel para: 'PRODUCTO DESCONOCIDO'
⚠️  No se puede consultar API: No hay referencia

⚠️  USANDO MÉTODO FALLBACK (cálculo manual de kilos)
```

## 🎯 Indicadores Clave

### ✅ Éxito Total
- `✅✅✅ MATCH ENCONTRADO EN API ✅✅✅` - El producto se procesó correctamente con datos de la API

### ⚠️ Warnings
- `❌ NO SE ENCONTRÓ referencia en Excel` - El nombre del producto no está en el Excel de items
- `❌ NO SE ENCONTRÓ la referencia en los items de la API` - La referencia existe en Excel pero no en la API
- `⚠️ USANDO MÉTODO FALLBACK` - Se usa el cálculo manual de kilos

### ❌ Errores
- `❌ ERROR cargando Excel de items` - Error al leer el Excel
- `⚠️ API no respondió datos` - La API no respondió o hubo error de conexión

## 📁 Archivos de Log

Los logs se guardan en:
- **Consola**: Salida en tiempo real
- **Archivo**: `somex_processing_detailed.log` (si usas el script de ejemplo)
- **UI**: Panel de progreso en la interfaz gráfica

## 🔍 Cómo Interpretar los Logs

1. **Busca las líneas con `✅✅✅ MATCH ENCONTRADO`**
   - Estos productos se procesaron correctamente con la API

2. **Busca las líneas con `❌ NO SE ENCONTRÓ`**
   - Estos productos necesitan revisión:
     - ¿El nombre en el XML coincide con el Excel?
     - ¿La referencia está en la API para esa factura?

3. **Busca las líneas con `⚠️ USANDO MÉTODO FALLBACK`**
   - Estos productos se calcularon de forma manual
   - Verifica si debería estar en la API

## 📝 Ejemplo Completo

Ver el archivo `example_process_with_logs.py` para un ejemplo completo de cómo procesar facturas con logs detallados.

## 🛠️ Solución de Problemas

### Problema: No aparece la referencia en el Excel
**Solución**: Verifica que:
- El Excel tiene las columnas `Referencia` y `Descripcion`
- Los nombres coinciden (el sistema hace búsqueda case-insensitive)
- Usa búsqueda parcial si no hay coincidencia exacta

### Problema: La API no responde
**Solución**: Verifica que:
- Las credenciales de la API son correctas
- El número de factura está en formato correcto (ej: `2B-285138`)
- Hay conexión a internet

### Problema: La referencia no está en la API
**Solución**:
- Verifica que la factura tenga esa referencia en Somex
- La factura puede tener diferentes items que el Excel
