# Documentación del Pipeline de Limpieza de Datos

## 📌 Resumen General

Este documento explica el diagnóstico inicial, las decisiones de transformación y la justificación técnica empleada en el script de *data wrangling* sobre `ventas_sucio.csv` para generar la versión limpia de producción: `ventas_limpio.csv`.

---

## 🛠️ Registro de Problemas, Decisiones y Justificaciones

### 1. Registros Duplicados Exactos
* **Qué se encontró:** Se identificaron filas 100% idénticas (mismo `id_cliente`, nombre, ciudad, fecha, monto, etc.) producto de reintentos en el sistema de captura o duplicación en la ingesta.
* **Qué decisión se tomó:** Se eliminaron las filas duplicadas mediante `df.drop_duplicates()` al inicio del pipeline y se realizó un *re-check* final tras estandarizar el texto.
* **Por qué:** Conservar filas duplicadas infla artificialmente el volumen de transacciones, distorsiona los ingresos totales y genera sesgos en los indicadores por cliente.

---

### 2. Inconsistencias en Columnas de Texto (`nombre`, `ciudad`, `categoria`)
* **Qué se encontró:** 
  * Espacios en blanco innecesarios al inicio y final de las cadenas (ej. `'  Carla Díaz  '`, `'bogota '`).
  * Mezcla arbitraria de mayúsculas y minúsculas (ej. `'MARÍA LÓPEZ'`, `'electronica'`, `'Ropa'`).
  * Nombres de ciudades y categorías mal escritos, sin tildes o con abreviaturas no unificadas (ej. `'Bogota'`, `'Cdmx'`, `'Ciudad De México'`).
* **Qué decisión se tomó:**
  1. Se eliminaron espacios extras y se aplicó formato tipo título con `.str.strip().str.title()`.
  2. Se aplicó un **mapeo manual explícito** mediante `.replace()` para los casos que `.title()` no resuelve adecuadamente:
     * `'Bogota'`, `'Ciudad De México'`, `'Cdmx'` → `'CDMX'` / `'Bogotá'`
     * `'Electronica'` → `'Electrónica'`
* **Por qué:** La función `.title()` convierte siglas como `CDMX` en `Cdmx` y no restituye tildes omitidas. Sin esta estandarización, consultas analíticas o agrupaciones (`GROUP BY`) tratarían a `"CDMX"` y `"Cdmx"` como entidades distintas.

---

### 3. Formato y Tipos de Datos en Fechas (`fecha_registro`)
* **Qué se encontró:** La columna contenía fechas representadas como texto con formatos mixtos (`YYYY.MM.DD`, `DD-MM-YYYY`, `DD/MM/YYYY`, `YYYY-MM-DD`) y valores verdaderamente ausentes/corruptos.
* **Qué decisión se tomó:**
  1. Se utilizó `pd.to_datetime(df['fecha_registro'], format='mixed', dayfirst=True, errors='coerce')`.
  2. Se implementó un **assert de conservación** comparando el conteo de registros no nulos antes vs. después de la transformación:

> **Criterio de Aserción:** `fechas_después >= fechas_antes * 0.95`

* **Por qué:**
  * Sin `format='mixed'`, Pandas fuerza un único formato global para toda la columna; las filas con una sintaxis distinta fallan de forma silenciosa y se convierten en `NaT` al usar `errors='coerce'`.
  * `dayfirst=True` resuelve la ambigüedad en notaciones como `10-04-2023` (10 de abril vs. 4 de octubre), alineándola con la convención del dataset.
  * El *assert de conservación* garantiza de forma automatizada que no existan purgas masivas no deseadas durante conversiones de tipo.

---

### 4. Valores Inválidos y Outliers en Edad (`edad`)
* **Qué se encontró:** 
  * Edades negativas (ej. `-5`).
  * Outliers atípicos biológicamente imposibles para clientes activos (ej. `150`).
  * Presencia de valores nulos (`NaN`).
* **Qué decisión se tomó:**
  1. Se estableció el rango válido para un cliente en **18 a 100 años**.
  2. Todos los valores fuera de este rango y los nulos se imputaron con la **mediana** de las edades válidas.
* **Por qué:**
  * Edades negativas o de 150 años corresponden a errores tipográficos.
  * Se eligió la **mediana** sobre el promedio porque es una medida de tendencia central inmune a valores extremos, preservando la distribución original del dataset.

---

### 5. Valores Inválidos y Outliers en Monto de Compra (`monto_compra`)
* **Qué se encontró:**
  * Montos de compra negativos o iguales a cero (ej. `-20.00`).
  * Outliers atípicos extremos (ej. `$99,999.00`).
  * Valores nulos (`NaN`) o textos no numéricos.
* **Qué decisión se tomó:**
  1. Se realizó la conversión limpia a numérico mediante `pd.to_numeric(..., errors='coerce')`.
  2. Se estableció como rango de transacción válida: **$0 < monto_compra <= $5,000**.
  3. Los valores fuera del rango, nulos e inviables fueron sustituidos por la **mediana** de las ventas válidas.
* **Por qué:** 
  * Transacciones con monto <= 0 no corresponden a ventas válidas.
  * Montos de $99,999.00 corresponden a valores "centinela" o errores de captura que distorsionan gravemente el ticket promedio del negocio. La imputación por mediana protege la integridad estadística de los indicadores financieros.

---

## 📊 Matriz Resumen de Reglas de Negocio

| Variable | Diagnóstico / Problema | Rango / Criterio Válido | Estrategia de Solución | Justificación Técnica |
| :--- | :--- | :--- | :--- | :--- |
| **Duplicados** | Filas 100% idénticas | 1 registro por evento | `drop_duplicates()` | Garantizar unicidad y no inflar métricas. |
| **Texto** | Espacios, minúsculas, falta de tildes | Formato unificado | `strip()` + `title()` + `replace()` manual | Permitir agrupaciones (`GROUP BY`) consistentes. |
| **Fechas** | Mezcla de formatos y texto libre | Tipo `datetime64` | `pd.to_datetime(..., errors='coerce')` | Habilitar análisis temporal y convertir errores a `NaT`. |
| **Edad** | Negativos, > 100 años y `NaN` | `18 <= edad <= 100` | Imputación por mediana válida | Corregir errores sin sesgar la tendencia central. |
| **Monto Compra** | Montos <= 0, $99,999 y `NaN` | `$0 < monto <= $5,000` | Imputación por mediana válida | Proteger el cálculo del ticket promedio. |

---

## 🔍 Controles de Calidad Automatizados (`assert`)

El script ejecuta los siguientes controles de aserciones de calidad antes de exportar el archivo final:

```python
# 1. Sin duplicados
assert df.duplicated().sum() == 0

# 2. Edades en rango
assert df['edad'].between(18, 100).all()

# 3. Montos positivos
assert (df['monto_compra'] > 0).all()

# 4. Formato de fecha
assert pd.api.types.is_datetime64_any_dtype(df['fecha_registro'])