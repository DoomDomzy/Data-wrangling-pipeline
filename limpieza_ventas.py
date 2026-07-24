import numpy as np
import pandas as pd

# ==========================================
# 1. CARGA Y DIAGNÓSTICO INICIAL
# ==========================================
file_path = "ventas_sucio.csv"
df_raw = pd.read_csv(file_path)

filas_antes = len(df_raw)
nulos_antes = df_raw.isnull().sum().sum()

print("=" * 60)
print("1. DIAGNÓSTICO INICIAL (ventas_sucio.csv)")
print("=" * 60)
print(f"Shape inicial: {df_raw.shape}\n")

print("--- Conteo de Nulos por Columna ---")
print(df_raw.isnull().sum(), "\n")

duplicados_iniciales = df_raw.duplicated().sum()
print(f"Filas duplicadas exactas: {duplicados_iniciales}\n")

print("--- Resumen Estadístico (describe) ---")
print(df_raw.describe(include=[np.number]), "\n")

print("--- Valores Únicos en Columnas de Texto ---")
cat_cols = df_raw.select_dtypes(include=["object", "string"]).columns
for col in cat_cols:
    print(f"Columna '{col}': {df_raw[col].dropna().unique()[:10]}")
print("=" * 60 + "\n")

# Copia de trabajo
df = df_raw.copy()

# ==========================================
# 2. RENOMBRAR COLUMNAS (snake_case)
# ==========================================
df.columns = (
    df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")
)

# ==========================================
# 3. ELIMINACIÓN DE DUPLICADOS
# ==========================================
filas_antes_dup = len(df)
df = df.drop_duplicates()
duplicados_eliminados = filas_antes_dup - len(df)
print(f"[INFO] Se eliminaron {duplicados_eliminados} filas duplicadas exactas.")

# ==========================================
# 4. CORRECCIÓN DE TIPOS DE DATOS & CONSERVACIÓN
# ==========================================
# Capturamos el total de fechas válidas (no nulas) antes de la conversión
fechas_validas_antes = df["fecha_registro"].notna().sum()

# Conversión con manejo de formatos mixtos y convención de día primero
df["fecha_registro"] = pd.to_datetime(
    df["fecha_registro"], format="mixed", dayfirst=True, errors="coerce"
)

fechas_validas_despues = df["fecha_registro"].notna().sum()

# Conversión de columnas numéricas
df["monto_compra"] = pd.to_numeric(df["monto_compra"], errors="coerce")
df["edad"] = pd.to_numeric(df["edad"], errors="coerce")

# ==========================================
# 5. ESTANDARIZACIÓN DE TEXTO
# ==========================================
cols_texto = ["nombre", "ciudad", "categoria"]
for col in cols_texto:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.title()

mapeo_ciudad = {
    "Bogota": "Bogotá",
    "Cdmx": "CDMX",
    "Ciudad De México": "CDMX",
}
mapeo_categoria = {"Electronica": "Electrónica"}

df["ciudad"] = df["ciudad"].replace(mapeo_ciudad)
df["categoria"] = df["categoria"].replace(mapeo_categoria)

# ==========================================
# 6. TRATAMIENTO DE VALORES INVÁLIDOS Y OUTLIERS
# ==========================================
outliers_corregidos = 0

# --- EDAD ---
mask_edad_valida = df["edad"].between(18, 100) & df["edad"].notnull()
outliers_edad = (~mask_edad_valida).sum()
outliers_corregidos += outliers_edad

mediana_edad = df.loc[mask_edad_valida, "edad"].median()
df.loc[~mask_edad_valida, "edad"] = mediana_edad

# --- MONTO DE COMPRA ---
mask_monto_valido = (
    (df["monto_compra"] > 0)
    & (df["monto_compra"] <= 5000)
    & df["monto_compra"].notnull()
)
outliers_monto = (~mask_monto_valido).sum()
outliers_corregidos += outliers_monto

mediana_monto = df.loc[mask_monto_valido, "monto_compra"].median()
df.loc[~mask_monto_valido, "monto_compra"] = mediana_monto

# Duplicados residuales tras la estandarización
duplicados_posteriores = df.duplicated().sum()
if duplicados_posteriores > 0:
    df = df.drop_duplicates().reset_index(drop=True)
    duplicados_eliminados += duplicados_posteriores

# ==========================================
# 7. VALIDACIONES CON ASSERT (TIPO + CONSERVACIÓN)
# ==========================================
# Assert 1: Sin filas duplicadas
assert df.duplicated().sum() == 0, "Error: Existen filas duplicadas."

# Assert 2: Edades dentro del rango válido [18, 100]
assert (
    df["edad"].between(18, 100).all()
), "Error: Se encontraron edades fuera del rango [18, 100]."

# Assert 3: Montos de compra positivos y no nulos
assert (
    df["monto_compra"] > 0
).all(), "Error: Existen montos de compra no válidos o nulos."

# Assert 4 (Tipo): La fecha de registro es de tipo datetime
assert pd.api.types.is_datetime64_any_dtype(
    df["fecha_registro"]
), "Error: fecha_registro no es datetime."

# Assert 5 (CONSERVACIÓN DE DATOS): Mínimo el 95% de las fechas válidas deben preservarse
assert (
    fechas_validas_despues >= fechas_validas_antes * 0.95
), f"Error: Se perdieron demasiado datos en la conversión de fechas ({fechas_validas_despues}/{fechas_validas_antes})."

print(
    f"\n[✓] Preservación de fechas: {fechas_validas_despues}/{fechas_validas_antes} registros válidos conservados."
)
print("[✓] Todas las validaciones de estructura e integridad pasaron con éxito.")

# ==========================================
# 8. GUARDAR Y RESUMEN COMPARATIVO
# ==========================================
output_file = "ventas_limpio.csv"
df.to_csv(output_file, index=False)

filas_despues = len(df)
nulos_despues = df.isnull().sum().sum()

print("\n" + "=" * 60)
print("RESUMEN COMPARATIVO CORREGIDO: ANTES vs. DESPUÉS")
print("=" * 60)
print(f"{'Métrica':<35} | {'Antes':<10} | {'Después':<10}")
print("-" * 60)
print(f"{'Total de filas':<35} | {filas_antes:<10} | {filas_despues:<10}")
print(
    f"{'Total de nulos (en todo el df)':<35} | {nulos_antes:<10} | {nulos_despues:<10}"
)
print(
    f"{'Filas duplicadas eliminadas':<35} | {duplicados_eliminados:<10} | {0:<10}"
)
print(
    f"{'Outliers / Inválidos corregidos':<35} | {outliers_corregidos:<10} | {0:<10}"
)
print("=" * 60)