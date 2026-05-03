"""
Para abordar tu trabajo de la Maestría en Estadística Aplicada con el archivo dataset_delivery_simulado.csv, 
debemos estructurar los datos de manera que permitan aplicar desde un ANOVA simple hasta un Diseño Factorial.

Tu pregunta de investigación es: ¿Varía la disposición del cliente a pagar recargos de envío altos 
dependiendo del tipo de comida?

Aquí tienes los pasos sugeridos para la limpieza y preparación:
1. Definición de Variables

Para cumplir con los contenidos de tu materia, definiremos:

    Variable Respuesta (Y): costo_prioritario. Esta variable representa el recargo adicional que el cliente 
    aceptó pagar para su pedido con envío prioritario. Es el indicador directo de "disposición a pagar recargos".

    Factor A: categoria_restaurante (Tipo de comida).

    Factor B (para experimentos de dos factores): trafico o clima. Esto te permitirá analizar interacciones 
    (ej. ¿la gente paga más recargo por Sushi cuando hay mucho tráfico?).

2. Limpieza de Datos

Dado que tienes muchos registros, lo ideal es no usar todos, sino filtrar para que los supuestos de varianza 
y equilibrio se cumplan mejor.

    Filtrado por Categorías Principales: Elegir las 5 categorías con más pedidos (con envío prioritario).

    Selección de Casos con Recargo: Filtrar envio_prioritario == 'Si' para analizar el monto del recargo 
    (costo_prioritario).

    Tratamiento de Outliers: (Opcional) criterio 1.5×IQR sobre costo_prioritario.

3. Muestra y diseño balanceado

    Se toma el mismo número de filas por categoría: hasta 100 por grupo, o menos si alguna categoría no 
    alcanza ese número (se usa el mínimo común posible).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Rutas respecto a este script (funciona aunque ejecutes desde otra carpeta)
_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = _DIR / "output_files"
ENTRADA = OUTPUT_DIR / "dataset_delivery_simulado.csv"
SALIDA = OUTPUT_DIR / "datos_limpios_anova.csv"

# Objetivo de filas por categoría (balanceo); se reduce si algún grupo tiene menos casos
N_POR_CATEGORIA = 100


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not ENTRADA.is_file():
        raise SystemExit(
            f"No se encontró {ENTRADA.name}. Generá el dataset con: python dataset.py"
        )

    df = pd.read_csv(ENTRADA, encoding="utf-8-sig")

    if "envio_prioritario" not in df.columns or "categoria_restaurante" not in df.columns:
        raise SystemExit("El CSV no tiene las columnas esperadas (envio_prioritario, categoria_restaurante).")

    df_clean = df[df["envio_prioritario"] == "Si"].copy()
    if len(df_clean) == 0:
        raise SystemExit("No hay pedidos con envío prioritario; no se puede armar la muestra.")

    top_categorias = df_clean["categoria_restaurante"].value_counts().nlargest(5).index
    df_final = df_clean[df_clean["categoria_restaurante"].isin(top_categorias)]

    conteos = df_final.groupby("categoria_restaurante", observed=True).size()
    n_max = int(conteos.min())
    n_tomar = min(N_POR_CATEGORIA, n_max)
    if n_tomar == 0:
        raise SystemExit("Tras filtrar por las 5 categorías top, no quedan filas.")

    partes: list[pd.DataFrame] = []
    for cat, grupo in df_final.groupby("categoria_restaurante", observed=True):
        partes.append(grupo.sample(n=n_tomar, random_state=42, replace=False))

    df_balanced = pd.concat(partes, ignore_index=True)
    df_balanced.to_csv(SALIDA, index=False, encoding="utf-8-sig")

    print(
        f"Listo: {SALIDA.name} ({len(df_balanced)} filas, "
        f"{n_tomar} por categoría, {len(top_categorias)} categorías)."
    )


if __name__ == "__main__":
    main()
