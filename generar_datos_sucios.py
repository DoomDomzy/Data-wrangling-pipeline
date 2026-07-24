import pandas as pd
import numpy as np

np.random.seed(42)

n = 500

nombres = ["ana garcía", "Luis Pérez", "MARÍA LÓPEZ", "juan Torres", "Sofía Ramírez",
           "Pedro gómez", "  Carla Díaz  ", "andres Silva", "Valentina Cruz", "diego Morales"]

ciudades = ["Lima", "lima", "LIMA", "Bogotá", "bogota", "Bogotá ", "CDMX", "Ciudad de México",
            "Santiago", "santiago"]

datos = {
    "id_cliente": list(range(1, n + 1)),
    "nombre": np.random.choice(nombres, n),
    "ciudad": np.random.choice(ciudades, n),
    "edad": np.random.choice(list(range(18, 70)) + [-5, 150, np.nan], n),  # edades inválidas y nulos a propósito
    "fecha_registro": np.random.choice(
        ["2023-01-15", "15/02/2023", "2023.03.10", "10-04-2023", None], n
    ),
    "monto_compra": np.random.choice(
        list(np.random.normal(150, 50, 50)) + [np.nan, -20, 99999], n
    ),
    "categoria": np.random.choice(["Electrónica", "electronica", "ELECTRONICA", "Ropa", "ropa",
                                     "Hogar", "hogar "], n),
}

df = pd.DataFrame(datos)

# Insertar duplicados a propósito (copiando 30 filas al final)
duplicados = df.sample(30, random_state=1)
df = pd.concat([df, duplicados], ignore_index=True)

df.to_csv("ventas_sucio.csv", index=False)
print(f"Dataset generado: {df.shape[0]} filas, {df.shape[1]} columnas -> ventas_sucio.csv")