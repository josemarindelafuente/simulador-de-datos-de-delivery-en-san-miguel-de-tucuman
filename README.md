# Generador de dataset delivery (simulado)

Script en Python que genera un conjunto de datos **sintético semi-realista** de pedidos de delivery alrededor de **San Miguel de Tucumán** (Argentina). Los locales salen del catálogo **`LOCALES_TUCUMAN`** en `dataset.py` (nombres, direcciones y coordenadas aproximadas). La simulación incluye heterogeneidad por cliente, elección del local ponderada por **popularidad y distancia**, dependencias entre **clima, tráfico, horario**, montos con **distribución lognormal**, tiempos de entrega **Gamma** positivos y estado/calificación ligados al **retraso**. Ideal para trabajos de estadística sin datos personales reales.

## Requisitos

- **Python** 3.10 o superior (recomendado).

## Entorno virtual (opcional y recomendado)

En PowerShell, desde esta carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si aparece error de política de ejecución:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Instalación de dependencias

Con el entorno activado:

```powershell
python -m pip install -r requirements.txt
```

Dependencias principales: `pandas`, `numpy`, `openpyxl` (para exportar `.xlsx`).

## Ejecución

Comando básico:

```powershell
python dataset.py
```

El script genera los archivos en `output_files/` y, por defecto, usa:

- `--seed 42`
- `--pedidos 10000`
- `--restaurantes 97`
- `--clientes 500`
- `--fecha-desde 2025-11-01`
- `--fecha-hasta 2026-05-01`

Por defecto se generan **10 000** pedidos con fechas entre **2025-11-01** y **2026-05-01** (el día final inclusive hasta las 23:59:59).

### Parámetros principales

- `--pedidos`: cantidad total de filas/pedidos a generar.
  - ejemplo: `--pedidos 5000` genera un dataset más chico (más rápido).
  - ejemplo: `--pedidos 50000` genera más volumen para análisis más robustos.
- `--seed`: semilla aleatoria para reproducibilidad.
  - si usás la misma semilla y los mismos parámetros, obtenés el mismo dataset.
  - si cambiás la semilla, cambia la muestra simulada (manteniendo la lógica del modelo).

### Parámetros disponibles en `dataset.py`

- `--seed` (int): semilla del generador aleatorio.
- `--pedidos` (int): cantidad de pedidos.
- `--restaurantes` (int): cantidad de locales a usar desde el catálogo.
- `--clientes` (int): cantidad de clientes únicos simulados.
- `--fecha-desde` (YYYY-MM-DD): inicio del rango de fechas.
- `--fecha-hasta` (YYYY-MM-DD): fin del rango (inclusive).

### Ejemplos de uso

Generación estándar (valores por defecto):

```powershell
python dataset.py
```

Menos pedidos para pruebas rápidas:

```powershell
python dataset.py --pedidos 2000
```

Más pedidos y semilla personalizada:

```powershell
python dataset.py --pedidos 30000 --seed 123
```

Mismo tamaño, distinta muestra simulada (cambia solo seed):

```powershell
python dataset.py --pedidos 30000 --seed 999
```

Ejemplo completo con varios parámetros:

```powershell
python dataset.py --seed 123 --pedidos 5000 --restaurantes 30 --clientes 500 --fecha-desde 2025-11-01 --fecha-hasta 2026-05-01
```

Nota: `--fecha-desde` debe ser menor o igual que `--fecha-hasta`.

Columnas útiles para análisis además de las habituales: **`tiempo_esperado_min`** (valor esperado determinístico antes del shock aleatorio), **`retraso_exceso_min`** (tiempo real menos esperado si es positivo). **`dia_semana`** está en español.

Las **`lat_cliente` / `lng_cliente`** se generan solo dentro de un rectángulo aproximado del ejido urbano de **San Miguel de Tucumán** (constantes `TUCUMAN_CIUDAD_*` en `dataset.py`).

## Limpieza para muestra (ANOVA)

Si querés una muestra balanceada para análisis, ejecutá:

```powershell
python limpieza_datos_para_muestra.py
```

Este script:

- toma como entrada `output_files/dataset_delivery_simulado.csv`
- filtra `envio_prioritario == "Si"`
- selecciona las 5 categorías con más casos
- balancea la muestra con igual cantidad por categoría
- guarda `output_files/datos_limpios_anova.csv`

## Mapa Leaflet + dashboard (`dashboard_app/index.html`)

Después de generar los datos, el archivo **`dashboard_app/index.html`** descarga **`output_files/dataset_delivery_simulado.json`** y muestra un mapa (Leaflet) con restaurantes y puntos de entrega, filtros de búsqueda y KPIs. En el mapa, **hacé clic en un punto verde (entrega)** para trazar una sola ruta hasta el restaurante de ese pedido (línea recta o por calles con **OSRM**, según el selector lateral).

El panel de filtros incluye **periodo por fecha de pedido** (desde / hasta). Al abrir la página, el mapa y los indicadores parten de los **últimos 30 días** respecto al pedido más reciente del archivo; podés ampliar el rango manualmente, usar **«Todo el periodo»** o volver con **«Últimos 30 días»**.

Los navegadores bloquean `fetch()` desde `file:///`. Abrí la carpeta del proyecto con un servidor HTTP local:

```powershell
python -m http.server 8080
```

En el navegador: **`http://localhost:8080/dashboard_app/index.html`**

Opcionalmente (PowerShell):

```powershell
Start-Process "http://localhost:8080/dashboard_app/index.html"
```

## Salida

Después de correr `python dataset.py`, dentro de `output_files/` se crean:

| Archivo | Descripción |
|---------|-------------|
| `output_files/dataset_delivery_simulado.csv` | Dataset en CSV, codificación UTF-8 con BOM |
| `output_files/dataset_delivery_simulado.xlsx` | Mismo contenido en Excel |
| `output_files/dataset_delivery_simulado.json` | Registros en JSON (`orient="records"`) para el mapa |

Si además corrés `python limpieza_datos_para_muestra.py`, también se genera:

| Archivo | Descripción |
|---------|-------------|
| `output_files/datos_limpios_anova.csv` | Muestra balanceada para análisis ANOVA |

Campos relacionados con **envío prioritario** (opcional): `envio_prioritario` (`Si`/`No`), `costo_prioritario` (0 si no aplica), `ahorro_tiempo_esperado_min` (minutos recortados del tiempo esperado base). El **`monto_total`** incluye compra + envío + adicional prioritario.

Si el `.xlsx` está abierto en Excel, Windows puede impedir sobrescribirlo; el script igualmente guarda **CSV** y **JSON** y muestra un aviso en consola.

## Estructura del proyecto

```
generador-dataset-01/
├── dataset.py           # Script generador
├── limpieza_datos_para_muestra.py  # Limpieza y muestra balanceada
├── dashboard_app/
│   └── index.html       # Mapa Leaflet + dashboard (carga JSON)
├── output_files/        # Archivos generados (CSV/XLSX/JSON)
├── requirements.txt    # Dependencias pip
├── README.md
└── .venv/              # Entorno virtual (si lo creaste)
```

## Licencia y uso docente

Los datos son **ficticios**; úsalos solo con fines educativos o de prueba.
