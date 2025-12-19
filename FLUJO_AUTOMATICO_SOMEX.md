# Flujo Automático de Procesamiento Somex

## 🔄 Flujo Completo Actualizado

Cuando presionas "Procesar Todos los ZIPs", el sistema hace lo siguiente:

### 1️⃣ Conexión SFTP
```
Conectando a servidor SFTP de Somex...
✅ Conexión exitosa
```

### 2️⃣ Descarga Automática de ListadoItems.xlsx
```
================================================================================
📁 DESCARGANDO LISTADO DE ITEMS DESDE SFTP...
================================================================================
Descargando: /Items/ListadoItems.xlsx
✅ Archivo de items descargado exitosamente
```

### 3️⃣ Carga de Items en Memoria
```
📋 Cargando items en memoria...
================================================================================
📁 CARGANDO EXCEL DE ITEMS: /tmp/ListadoItems.xlsx
================================================================================
Columnas encontradas: ['CodigoItem', 'Referencia', 'Descripcion', 'IdPlan', ...]
✅ CARGADOS 150 ITEMS EN MEMORIA
Ejemplos de items cargados:
  - Desc: 'SAL SOMEX CEBA X 40 KILOS' → Ref: '120704'
  - Desc: 'PRODUCTO 2' → Ref: '120705'
  - Desc: 'PRODUCTO 3' → Ref: '120706'
================================================================================
   → Se usarán para buscar referencias por nombre de producto
   → Se compararán con la API de Somex para obtener cantidades
================================================================================
```

### 4️⃣ Procesamiento de ZIPs
```
📦 Listando archivos ZIP en /DocumentosPendientes...
Encontrados 3 archivos ZIP
Procesando ZIP 1/3: factura_001.zip...
```

### 5️⃣ Para Cada Producto en los XMLs
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

### 6️⃣ Generación de Excel Consolidado
```
Generando Excel consolidado con 15 facturas...
✅ Excel generado: output/somex/somex_facturas_consolidadas_20250101_120000.xlsx
```

### 7️⃣ Subida al SFTP
```
Subiendo Excel a SFTP: somex_facturas_consolidadas_20250101_120000.xlsx...
✓ Excel subido a /ProcesadoCorreagro/somex_facturas_consolidadas_20250101_120000.xlsx
```

## 📋 Columnas del Excel Final

El Excel consolidado incluye:

1. **N° Factura** - Número de factura
2. **Nombre Producto** - Nombre del producto del XML
3. **Codigo Subyacente** - Código del producto
4. **Unidad Medida** - Siempre "KG" para Somex
5. **Cantidad** - **cantidadKg de la API** (cantidad convertida)
6. **Precio Unitario** - Calculado: TaxableAmount / cantidadKg
7-20. Otros campos de la factura...
21. **Cantidad Original** - **cantidadBultos de la API** (cantidad en bultos)
22. **Moneda** - Siempre "1" (COP)
23. **Valor Total Línea** - Total de la línea

## 🎯 Proceso de Comparación (Paso a Paso)

### Para cada producto:

1. **Lee el nombre del producto del XML**
   - Ej: "SAL SOMEX CEBA X 40 KILOS"

2. **Busca en ListadoItems.xlsx**
   - Compara el nombre con la columna "Descripcion"
   - Obtiene la "Referencia" correspondiente
   - Ej: Referencia = "120704"

3. **Consulta la API de Somex**
   - Endpoint: `/FacturasBolsaAgro/{nroFactura}`
   - Ej: `/FacturasBolsaAgro/2B-285138`
   - Obtiene lista de items de esa factura

4. **Compara las referencias**
   - Busca en la respuesta de la API el item con la misma referencia
   - Ej: Busca referencia "120704" en los items de la API

5. **Extrae las cantidades**
   - Si encuentra match:
     - `cantidadBultos` → Cantidad Original (columna 21)
     - `cantidadKg` → Cantidad Convertida (columna 5)
   - Si NO encuentra match:
     - Usa método fallback (extracción de kilos del nombre)

## 🔍 Indicadores en los Logs

### ✅ Todo correcto
```
✅✅✅ MATCH ENCONTRADO EN API ✅✅✅
   cantidadBultos: 20.00
   cantidadKg: 800.00
```
**Significado**: El producto se procesó correctamente con datos exactos de la API

### ❌ Producto no está en ListadoItems.xlsx
```
❌ NO SE ENCONTRÓ referencia en Excel para: 'PRODUCTO X'
⚠️  No se puede consultar API: No hay referencia
⚠️  USANDO MÉTODO FALLBACK (cálculo manual de kilos)
```
**Significado**: El nombre del producto del XML no coincide con ninguna descripción en ListadoItems.xlsx

### ❌ Referencia no está en la API
```
✅ REFERENCIA ENCONTRADA EN EXCEL: '999999'
📊 API respondió con 5 items
   Referencias en la API:
      [1] Ref: 120704
      [2] Ref: 120705
❌ NO SE ENCONTRÓ la referencia '999999' en los items de la API
⚠️  USANDO MÉTODO FALLBACK
```
**Significado**: La referencia existe en ListadoItems.xlsx pero no está en esa factura específica según la API

## 🛠️ Solución de Problemas

### Problema: No se descarga ListadoItems.xlsx
**Posibles causas**:
- El archivo no existe en `/Items/ListadoItems.xlsx`
- Permisos incorrectos en el SFTP
- Problema de conexión

**Solución**:
- Verificar que el archivo existe en el SFTP
- Cargar manualmente el archivo usando "Importar Excel de Items"

### Problema: No encuentra referencias
**Posibles causas**:
- Los nombres en el XML no coinciden exactamente con los de ListadoItems.xlsx
- Hay diferencias de mayúsculas/minúsculas o espacios

**Solución**:
- El sistema hace búsqueda case-insensitive (ignora mayúsculas)
- Si no hay match exacto, hace búsqueda parcial
- Revisar los logs para ver qué producto no se encontró

### Problema: Referencia no está en la API
**Esto es NORMAL** si:
- La factura tiene productos que no están en ListadoItems.xlsx
- La referencia es correcta pero ese producto no está en esa factura específica

**Solución**:
- El sistema usa método fallback automáticamente
- Verifica los logs para confirmar qué productos usan fallback

## 📁 Archivos Importantes

- **SFTP: `/Items/ListadoItems.xlsx`** - Archivo de referencias (se descarga automáticamente)
- **SFTP: `/DocumentosPendientes/*.zip`** - ZIPs con XMLs de facturas
- **SFTP: `/ProcesadoCorreagro/*.xlsx`** - Excel consolidado generado (se sube automáticamente)
- **Local: `output/somex/*.xlsx`** - Copia local del Excel generado

## ✅ Verificación de Éxito

Busca estas líneas en los logs para verificar que todo funcionó:

1. ✅ ListadoItems.xlsx descargado
2. ✅ X ITEMS CARGADOS EN MEMORIA
3. ✅✅✅ MATCH ENCONTRADO EN API (para cada producto)
4. ✅ Excel generado
5. ✓ Excel subido a /ProcesadoCorreagro

Si ves todos estos ✅, el proceso fue 100% exitoso!
