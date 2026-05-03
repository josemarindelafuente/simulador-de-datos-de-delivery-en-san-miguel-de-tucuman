"""
Generador de dataset sintético de delivery con estructura estadística más rica:
heterogeneidad restaurante/cliente, correlaciones plausibles y reproducibilidad.
"""
from __future__ import annotations

import argparse
import math
import random
from datetime import datetime, timedelta
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = _DIR / "output_files"

# Centro aproximado San Miguel de Tucumán
LAT_CENTRO = -26.8241
LNG_CENTRO = -65.2226

# Rectángulo aproximado del ejido urbano de San Miguel de Tucumán (orden de magnitud OSM).
# Solo se usan para acotar domicilios de clientes; sur < norte en latitud.
TUCUMAN_CIUDAD_LAT_SUR = -26.872
TUCUMAN_CIUDAD_LAT_NORTE = -26.778
TUCUMAN_CIUDAD_LNG_OESTE = -65.275
TUCUMAN_CIUDAD_LNG_ESTE = -65.172

# Tipos de rubro (tabla propia) → categoría del modelo de montos/tiempos (MONTO_BASE_CATEGORIA).
CATEGORIA_TIPO_A_MODELO: dict[str, str] = {
    "Sandwicheria": "Hamburguesas",
    "Hamburguesas": "Hamburguesas",
    "Fast Food": "FastFood",
    "Panchos": "FastFood",
    "Pizzas": "Pizza",
    "Pizzas y Empanadas": "Pizza",
    "Empanadas": "Empanadas",
    "Restobar": "Parrilla",
    "Gourmet": "Internacional",
    "Cervecería / Resto": "Cerveceria",
    "Cultural / Resto": "Cerveceria",
    "Cocina Autor": "Milanesas",
    "Minutas": "Milanesas",
    "Cervecería": "Cerveceria",
    "Internacional": "Internacional",
    "Sushi / Peruano": "Sushi",
    "Sushi": "Sushi",
    "Árabe": "Comida saludable",
    "Chino": "Internacional",
    "Indú": "Internacional",
    "Wok": "Internacional",
    "Saludable": "Comida saludable",
    "Italiana": "Pastas",
    "Crepería": "Cafe",
    "Café": "Cafe",
    "Panadería": "Panaderia",
    "Pastelería": "Pasteleria",
    "Heladería": "Heladeria",
    "Pollos": "Pollos",
    "Pastas": "Pastas",
    "Sushi / Resto": "Sushi",
    "Viandas": "Comida saludable",
    "Parrilla": "Parrilla",
    "Resto / Bar": "Cerveceria",
}

# Locales de San Miguel de Tucumán: (nombre, dirección, lat, lng, categoría tipo).
_LOCALES_RAW: list[tuple[str, str, float, float, str]] = [
    ("El Turco", "Av. Aguirre 2186", -26.789999074609256, -65.22069162488603, "Sandwicheria"),
    ("Chacho (Centro)", "Maipú 440", -26.824887, -65.207865, "Sandwicheria"),
    ("El 10", "Av. Salta 332", -26.824954, -65.208541, "Sandwicheria"),
    ("Los Eléctricos", "Suipacha 950", -26.81539643994814, -65.21388484776456, "Sandwicheria"),
    ("Fiky", "Av. Mate de Luna 2650", -26.830214, -65.241587, "Sandwicheria"),
    ("Lomitos 348", "Av. Néstor Kirchner 2800", -26.848214, -65.245214, "Sandwicheria"),
    ("Big Salads & Burgers", "San Lorenzo 619", -26.833512, -65.212541, "Hamburguesas"),
    ("Burger King", "25 de Mayo 501", -26.824245, -65.202874, "Fast Food"),
    ("Mostaza", "25 de Mayo 392", -26.825874, -65.202541, "Fast Food"),
    ("McDonald's", "San Martín 601", -26.830124, -65.203841, "Fast Food"),
    ("El Lomo Loco", "Matienzo 398", -26.839812, -65.201245, "Sandwicheria"),
    ("Tío Alberto", "Av. Alem 554", -26.837512, -65.216541, "Sandwicheria"),
    ("Panchería Tato", "San Martín 490", -26.829541, -65.202541, "Panchos"),
    ("Full Sandwichería 873", "Av. Gdor. del Campo 873", -26.821245, -65.188541, "Sandwicheria"),
    ("Don Toribio", "Av. Colón 601", -26.841521, -65.228541, "Sandwicheria"),
    ("Tarantino Resto", "San Juan 652", -26.827312, -65.207841, "Pizzas"),
    ("Pizzería Popular", "Gral. Paz 522", -26.831424, -65.209541, "Pizzas"),
    ("La Mini", "Chacabuco 301", -26.834814, -65.209514, "Pizzas y Empanadas"),
    ("Empanadas El Portal", "25 de Mayo 501", -26.824214, -65.202814, "Empanadas"),
    ("Rato Empanadas", "Av. Gdor. del Campo 1110", -26.820512, -65.185214, "Empanadas"),
    ("Ché Pizza", "Balcarce 801", -26.821814, -65.206514, "Pizzas"),
    ("Pizza Full", "Santa Fe 501", -26.821914, -65.206514, "Pizzas"),
    ("La Argentina Pizzas", "25 de Mayo 498", -26.824514, -65.202514, "Pizzas"),
    ("La Lolita", "Balcarce 602", -26.822514, -65.205514, "Pizzas"),
    ("Piace Delivery", "Maipú 801", -26.821514, -65.208514, "Pizzas"),
    ("Il Barto", "Av. Mate de Luna 2100", -26.831514, -65.234114, "Pizzas"),
    ("Fugazza", "Corrientes 601", -26.822514, -65.208514, "Pizzas"),
    ("La Guitarrita", "Santa Fe 490", -26.821014, -65.203514, "Pizzas"),
    ("Pizzería El Parque", "Av. Soldati 502", -26.824514, -65.193514, "Pizzas"),
    ("Bocatto", "Av. Gdor. del Campo 951", -26.821414, -65.187314, "Pizzas"),
    ("Aurelia Restobar", "Chacabuco 401", -26.835814, -65.209214, "Restobar"),
    ("Americano Restobar", "Av. R. Paz Posse 5", -26.832214, -65.221514, "Restobar"),
    ("El Mesón (Norte)", "Italia 98", -26.819514, -65.210514, "Restobar"),
    ("Mirasoles", "Av. Mate de Luna 1801", -26.829814, -65.230514, "Gourmet"),
    ("Patagonia (Tucumán)", "Santa Fe 501", -26.821514, -65.204214, "Cervecería / Resto"),
    ("Santos Discépolo", "La Rioja 249", -26.831514, -65.212214, "Cultural / Resto"),
    ("Flor de Lino", "Balcarce 501", -26.823514, -65.206214, "Cocina Autor"),
    ("El Bodegón", "Santa Fe 601", -26.821814, -65.206214, "Minutas"),
    ("Bierhaus", "San Lorenzo 501", -26.833214, -65.208514, "Cervecería"),
    ("Porter Beer House", "Muñecas 601", -26.821214, -65.202514, "Cervecería"),
    ("Castilla Jardín", "Av. Mate de Luna 1502", -26.830214, -65.223514, "Restobar"),
    ("Sheraton Mora", "Av. Soldati 440", -26.824814, -65.193214, "Internacional"),
    ("La Cantina Lawn Tennis", "Av. Soldati s/n", -26.825514, -65.192514, "Restobar"),
    ("24 Street Abasto", "Miguel Lillo 201", -26.828514, -65.223514, "Restobar"),
    ("Arkyn", "Santa Fe 450", -26.819814, -65.204814, "Restobar"),
    ("Páru Inkas Sushi", "Santa Fe 501", -26.821814, -65.204814, "Sushi / Peruano"),
    ("Sushi 2x1", "San Lorenzo 502", -26.834214, -65.208214, "Sushi"),
    ("The Sushi Co", "Santa Fe 501", -26.821814, -65.205214, "Sushi"),
    ("Jalu Comida Árabe", "Maipú 401", -26.825514, -65.208514, "Árabe"),
    ("Búffala", "Santa Fe 401", -26.821214, -65.203514, "Internacional"),
    ("Peking Express", "San Juan 701", -26.826514, -65.208514, "Chino"),
    ("Sabores de la India", "Santiago 701", -26.824214, -65.211514, "Indú"),
    ("Wok to Walk", "Muñecas 401", -26.822214, -65.202214, "Wok"),
    ("Natural Deli", "Laprida 501", -26.820514, -65.204214, "Saludable"),
    ("Go Green", "Santa Fe 501", -26.821814, -65.204514, "Saludable"),
    ("La Pequeña Italia", "San Lorenzo 801", -26.835514, -65.211514, "Italiana"),
    ("Crepas", "Santa Fe 490", -26.821014, -65.203514, "Crepería"),
    ("Munay Panadería", "Av. Juan B. Justo 1001", -26.816514, -65.198514, "Café"),
    ("Casapan Balcarce", "Balcarce 601", -26.823514, -65.205514, "Panadería"),
    ("Casapan Lavalle", "Lavalle 501", -26.837514, -65.208514, "Panadería"),
    ("Casapan Roca", "Av. Roca 601", -26.840514, -65.208514, "Panadería"),
    ("Bonafide", "Chacabuco 401", -26.835514, -65.209514, "Café"),
    ("Tortas María Toscana", "San Lorenzo 601", -26.836214, -65.210514, "Pastelería"),
    ("Mariana Sosa", "San Lorenzo 810", -26.834814, -65.212514, "Pastelería"),
    ("Chilly Pastelería", "Av. Mate de Luna 2201", -26.831814, -65.236514, "Pastelería"),
    ("Wel Cream Café", "San Lorenzo 901", -26.836814, -65.213514, "Café"),
    ("Le Panier", "Laprida 610", -26.820124, -65.204124, "Pastelería"),
    ("Blue Bell", "Av. Mate de Luna 2001", -26.832514, -65.233514, "Heladería"),
    ("Venezia", "9 de Julio 241", -26.831814, -65.205514, "Heladería"),
    ("Aloha Heladería", "Chacabuco 301", -26.833814, -65.209514, "Heladería"),
    ("Chocorisimo", "San Lorenzo 701", -26.837214, -65.210514, "Heladería"),
    ("Plaza Sicilia", "Av. Mate de Luna 1701", -26.829514, -65.228214, "Heladería"),
    ("Heladería Dino", "Av. Brígido Terán 501", -26.831514, -65.195514, "Heladería"),
    ("Polo Helados", "24 de Septiembre 801", -26.830814, -65.213514, "Heladería"),
    ("Abuela Goye", "25 de Mayo 490", -26.824814, -65.203814, "Heladería"),
    ("Grido Gdor Campo", "Av. Gdor. del Campo 801", -26.821814, -65.189514, "Heladería"),
    ("Grido Roca", "Av. Roca 501", -26.840814, -65.207514, "Heladería"),
    ("Mundo del Pollo", "Av. Juan B. Justo 1100", -26.815512, -65.195512, "Pollos"),
    ("Nonna Pia", "Santiago 450", -26.822514, -65.203514, "Pastas"),
    ("Woot", "Santa Fe 490", -26.820514, -65.201214, "Sushi / Resto"),
    ("Punto y Coma", "Av. Alem 401", -26.836514, -65.214514, "Minutas"),
    ("Delivery Light", "Balcarce 527", -26.823514, -65.205214, "Viandas"),
    ("P9 Parrilla", "Av. Gdor. del Campo 901", -26.821214, -65.188214, "Parrilla"),
    ("Los Sabores De Cuchy", "V. 9 de Julio", -26.831514, -65.190514, "Minutas"),
    ("Cocina Gaucha", "Av. Gdor. del Campo 1201", -26.820214, -65.183514, "Minutas"),
    ("Bocanada", "Marcos Paz 601", -26.819214, -65.208514, "Pastelería"),
    ("Don Corleone", "San Martín 901", -26.830514, -65.212514, "Pizzas"),
    ("La Tonadita", "San Lorenzo 701", -26.833514, -65.213514, "Empanadas"),
    ("Sushi Feel", "Barrio Norte", -26.820514, -65.204514, "Sushi"),
    ("KFC (Shopping)", "Av. Néstor Kirchner 3400", -26.849514, -65.252514, "Fast Food"),
    ("Hell's Pizza (YB)", "Av. Perón 1800", -26.815514, -65.285514, "Pizzas"),
    ("Sr. Montero", "San Martín 801", -26.830214, -65.210514, "Sandwicheria"),
    ("Ona Saez", "25 de Mayo 501", -26.824214, -65.202514, "Café"),
    ("Petit Gourmet", "Crisóstomo Alvarez 801", -26.835214, -65.211514, "Viandas"),
    ("El Abasto", "Miguel Lillo 301", -26.828214, -65.223214, "Parrilla"),
    ("Johnny B. Good", "Av. Perón 1601", -26.816214, -65.282514, "Resto / Bar"),
    ("Lo de la Gringa", "Santa Fe 401", -26.821514, -65.204114, "Minutas"),
]

LOCALES_TUCUMAN: list[dict] = [
    {
        "id": i + 1,
        "nombre": n,
        "direccion": d,
        "lat": lat,
        "lng": lng,
        "categoria": cat,
    }
    for i, (n, d, lat, lng, cat) in enumerate(_LOCALES_RAW)
]

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Sesgo temporal de demanda:
# - verano (dic/ene/feb) con mayor volumen,
# - fin de semana por encima de días hábiles,
# - picos horarios al mediodía y a la noche.
PESO_MES = {
    1: 1.35,
    2: 1.28,
    3: 1.02,
    4: 1.0,
    5: 0.97,
    6: 0.95,
    7: 0.96,
    8: 0.98,
    9: 1.0,
    10: 1.02,
    11: 1.08,
    12: 1.32,
}
PESO_DIA_SEMANA = {
    0: 0.9,   # Lunes
    1: 0.94,  # Martes
    2: 0.98,  # Miércoles
    3: 1.03,  # Jueves
    4: 1.12,  # Viernes
    5: 1.32,  # Sábado
    6: 1.26,  # Domingo
}
PESO_HORA = np.array(
    [
        0.22, 0.14, 0.08, 0.06, 0.06, 0.08,  # 00-05
        0.2, 0.35, 0.55, 0.9, 1.2, 1.45,     # 06-11
        1.55, 1.5, 1.35, 1.1, 0.95, 1.0,     # 12-17
        1.18, 1.38, 1.62, 1.54, 1.22, 0.68,  # 18-23
    ],
    dtype=float,
)

# Categorías de rubro presentes en el catálogo de locales.
CATEGORIAS_LOCALES_RAW = sorted({cat for _, _, _, _, cat in _LOCALES_RAW})

# Tablas base por categoría de modelo económico.
MONTO_BASE_CATEGORIA_MODELO = {
    "Hamburguesas": 15200,
    "FastFood": 10800,
    "Pizza": 20800,
    "Sushi": 30200,
    "Empanadas": 20000,
    "Milanesas": 12000,
    "Cafe": 6200,
    "Panaderia": 7600,
    "Pasteleria": 9400,
    "Heladeria": 8900,
    "Cerveceria": 13200,
    "Parrilla": 38600,
    "Internacional": 31400,
    "Comida saludable": 15500,
    "Pollos": 15800,
    "Pastas": 9800,
}

CLIMAS = ["Despejado", "Nublado", "Lluvia", "Tormenta"]
UMBRAL_BICICLETA_KM = 3.0  # bicicleta solo bajo esta distancia
MEDIOS_PAGO = ["Efectivo", "Tarjeta", "Mercado Pago"]

# Envío prioritario (opcional): más caro en categorías más elaboradas; mayor ahorro de tiempo
# en comidas rápidas vs elaboradas; la distancia reduce el ahorro posible (más difícil acortar rutas largas).
PRIORIDAD_MULT_COSTO_MODELO = {
    "Hamburguesas": 1.0,
    "FastFood": 0.96,
    "Pizza": 1.05,
    "Empanadas": 0.92,
    "Milanesas": 1.18,
    "Cafe": 0.9,
    "Panaderia": 0.93,
    "Pasteleria": 0.97,
    "Heladeria": 0.88,
    "Cerveceria": 1.08,
    "Parrilla": 1.2,
    "Internacional": 1.26,
    "Pollos": 1.12,
    "Comida saludable": 1.22,
    "Sushi": 1.45,
    "Pastas": 1.38,
}
# Techo de minutos que el servicio puede recortar del tiempo esperado (distancia 0, escenario ideal).
PRIORIDAD_RED_MAX_MIN_MODELO = {
    "Hamburguesas": 12.0,
    "FastFood": 13.0,
    "Pizza": 11.0,
    "Empanadas": 11.5,
    "Milanesas": 8.0,
    "Cafe": 11.0,
    "Panaderia": 10.0,
    "Pasteleria": 9.0,
    "Heladeria": 9.5,
    "Cerveceria": 8.0,
    "Parrilla": 7.0,
    "Internacional": 6.5,
    "Pollos": 8.5,
    "Comida saludable": 7.5,
    "Sushi": 6.0,
    "Pastas": 6.5,
}


def _expande_por_categoria_local(tabla_modelo: dict[str, float | int]) -> dict[str, float | int]:
    """Crea una tabla que incluya categorías de modelo y categorías crudas de _LOCALES_RAW."""
    tabla = dict(tabla_modelo)
    for cat_local in CATEGORIAS_LOCALES_RAW:
        cat_modelo = CATEGORIA_TIPO_A_MODELO.get(cat_local, cat_local)
        if cat_local not in tabla and cat_modelo in tabla_modelo:
            tabla[cat_local] = tabla_modelo[cat_modelo]
    return tabla


CATEGORIAS = sorted(
    set(CATEGORIAS_LOCALES_RAW)
    | set(MONTO_BASE_CATEGORIA_MODELO)
    | set(PRIORIDAD_MULT_COSTO_MODELO)
    | set(PRIORIDAD_RED_MAX_MIN_MODELO)
)

# Precio típico por categoría (ARS ficticios; nivel medio del ticket).
MONTO_BASE_CATEGORIA = _expande_por_categoria_local(MONTO_BASE_CATEGORIA_MODELO)
PRIORIDAD_MULT_COSTO = _expande_por_categoria_local(PRIORIDAD_MULT_COSTO_MODELO)
PRIORIDAD_RED_MAX_MIN = _expande_por_categoria_local(PRIORIDAD_RED_MAX_MIN_MODELO)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def elegir_restaurante(
    cliente_lat: float,
    cliente_lng: float,
    restaurantes: list[dict],
    popularidades: np.ndarray,
    rng: np.random.Generator,
    decay_km: float = 2.8,
) -> dict:
    """P(r) proporcional a popularidad_r · exp(-dist / decay_km)."""
    dists = np.array(
        [
            haversine_km(cliente_lat, cliente_lng, r["lat_restaurante"], r["lng_restaurante"])
            for r in restaurantes
        ]
    )
    w = popularidades * np.exp(-dists / decay_km)
    w = w / w.sum()
    idx = int(rng.choice(len(restaurantes), p=w))
    return restaurantes[idx]


def sample_trafico(rng: np.random.Generator, hora: int, dia_idx: int, clima: str) -> str:
    """Tráfico depende de hora pico, fin de semana y clima."""
    base_alto = 0.14
    base_medio = 0.42
    if dia_idx >= 5:
        base_alto -= 0.03
        base_medio -= 0.05
    if 12 <= hora <= 14 or 19 <= hora <= 22:
        base_alto += 0.18
        base_medio += 0.12
    elif 8 <= hora <= 11 or 15 <= hora <= 18:
        base_medio += 0.06

    if clima == "Lluvia":
        base_alto += 0.08
        base_medio += 0.05
    elif clima == "Tormenta":
        base_alto += 0.15
        base_medio += 0.07

    base_alto = float(np.clip(base_alto, 0.05, 0.55))
    base_medio = float(np.clip(base_medio, 0.25, 0.62))
    p_alto = base_alto
    p_medio = base_medio * (1.0 - p_alto)
    p_bajo = max(0.0, 1.0 - p_alto - p_medio)
    s = p_bajo + p_medio + p_alto
    p_bajo, p_medio, p_alto = p_bajo / s, p_medio / s, p_alto / s
    return rng.choice(["Bajo", "Medio", "Alto"], p=np.array([p_bajo, p_medio, p_alto]))


def sample_clima(rng: np.random.Generator, mes: int) -> str:
    """Lluvia/tormenta algo más probables en meses de verano lluvioso (DJF sur)."""
    w = np.array([52.0, 26.0, 14.0, 8.0])
    if mes in (12, 1, 2):
        w[2] += 6
        w[3] += 3
    elif mes in (6, 7, 8):
        w[2] -= 3
    w = np.maximum(w, 1.0)
    w /= w.sum()
    return rng.choice(CLIMAS, p=w)


def sample_vehiculo(rng: np.random.Generator, distancia_km: float, clima: str) -> str:
    """Solo Moto o Bicicleta. La bicicleta solo se usa si la distancia es menor a UMBRAL_BICICLETA_KM."""
    if distancia_km >= UMBRAL_BICICLETA_KM:
        return "Moto"
    # Distancia corta: reparto entre moto y bici según clima y cercanía
    rel = max(0.0, distancia_km / UMBRAL_BICICLETA_KM)
    p_bici = 0.58 - 0.35 * rel
    if clima == "Lluvia":
        p_bici -= 0.22
    elif clima == "Tormenta":
        p_bici -= 0.38
    elif clima == "Despejado":
        p_bici += 0.06
    p_bici = float(np.clip(p_bici, 0.06, 0.88))
    return "Bicicleta" if rng.random() < p_bici else "Moto"


def sample_prioritario(
    rng: np.random.Generator,
    distancia_km: float,
    monto_compra: float,
) -> bool:
    """Probabilidad creciente con distancia y ticket (quien paga más a veces pide prioridad)."""
    p = (
        0.11
        + 0.05 * logistic((distancia_km - 2.8) / 2.2)
        + 0.04 * logistic((monto_compra - 8500) / 4200)
        + rng.normal(0, 0.04)
    )
    p = float(np.clip(p, 0.04, 0.36))
    return bool(rng.random() < p)


def costo_prioritario_ars(
    rng: np.random.Generator,
    categoria: str,
    distancia_km: float,
) -> float:
    """Adicional ARS ficticios; sube con distancia y con mult de categoría."""
    mult = PRIORIDAD_MULT_COSTO.get(categoria, 1.15)
    base = 420.0 + distancia_km * 88.0 + distancia_km**1.15 * 12.0
    raw = base * mult * rng.lognormal(mean=0.0, sigma=0.11)
    return round(float(np.clip(raw, 250.0, 5200.0)), 2)


def reduccion_tiempo_prioritario_min(
    rng: np.random.Generator,
    categoria: str,
    distancia_km: float,
) -> float:
    """
    Minutos que se restan del tiempo esperado base (hasta un techo por categoría).
    Distancia mayor => factor multiplicador menor (menos margen real de aceleración).
    """
    red_max = float(PRIORIDAD_RED_MAX_MIN.get(categoria, 7.0))
    # 1 en distancia ~0; cae con la lejanía (asintótico ~0.25)
    factor_dist = float(
        np.clip(
            math.exp(-0.11 * distancia_km) - 0.02 * max(0.0, distancia_km - 6.0),
            0.22,
            1.0,
        )
    )
    jitter = float(rng.uniform(0.52, 1.0))
    return float(np.clip(red_max * factor_dist * jitter, 0.0, red_max))


def sample_medio_pago(rng: np.random.Generator, monto_total: float) -> str:
    """Tickets altos tienden a más tarjeta / Mercado Pago."""
    z = (monto_total - 14000) / 6500
    p_tarjeta = logistic(z - 0.2) * 0.38
    p_mp = logistic(z + 0.1) * 0.38
    p_efectivo = max(0.08, 1.0 - p_tarjeta - p_mp)
    s = p_efectivo + p_tarjeta + p_mp
    return rng.choice(MEDIOS_PAGO, p=np.array([p_efectivo, p_tarjeta, p_mp]) / s)


def gamma_from_mean_sd(rng: np.random.Generator, mean: float, sd: float) -> float:
    """Muestreo Gamma con media y desvío aproximadas; siempre positivo."""
    mean = max(mean, 1.0)
    sd = max(sd, 0.5)
    shape = (mean / sd) ** 2
    scale = (sd**2) / mean
    return float(rng.gamma(shape, scale))


def build_restaurantes(rng: np.random.Generator, n_locales: int) -> tuple[list[dict], np.ndarray]:
    """Construye locales desde LOCALES_TUCUMAN (rubro en catálogo; modelo económico vía CATEGORIA_TIPO_A_MODELO)."""
    n_max = len(LOCALES_TUCUMAN)
    n_use = min(max(1, n_locales), n_max)
    catalog = LOCALES_TUCUMAN[:n_use]
    popularidades = rng.dirichlet(np.full(n_use, 2.4))
    lista: list[dict] = []
    for loc in catalog:
        tipo = loc["categoria"]
        cat_modelo = CATEGORIA_TIPO_A_MODELO.get(tipo)
        if cat_modelo is None or cat_modelo not in MONTO_BASE_CATEGORIA:
            raise ValueError(f"Categoría de catálogo sin mapeo válido id={loc['id']}: {tipo!r}")
        lista.append(
            {
                "id_restaurante": int(loc["id"]),
                "nombre_restaurante": loc["nombre"],
                "direccion_restaurante": loc["direccion"],
                "categoria_restaurante": tipo,
                "categoria_modelo": cat_modelo,
                "lat_restaurante": float(loc["lat"]),
                "lng_restaurante": float(loc["lng"]),
                "factor_prep_min": float(rng.normal(1.0, 0.12)),
                "factor_precio_ticket": float(rng.lognormal(mean=0.0, sigma=0.08)),
            }
        )
    return lista, popularidades


def build_clientes(rng: np.random.Generator, n: int) -> list[dict]:
    """Clientes con domicilio persistente; coordenadas solo dentro de San Miguel de Tucumán ciudad."""
    lat_lo = min(TUCUMAN_CIUDAD_LAT_SUR, TUCUMAN_CIUDAD_LAT_NORTE)
    lat_hi = max(TUCUMAN_CIUDAD_LAT_SUR, TUCUMAN_CIUDAD_LAT_NORTE)
    lng_lo = min(TUCUMAN_CIUDAD_LNG_OESTE, TUCUMAN_CIUDAD_LNG_ESTE)
    lng_hi = max(TUCUMAN_CIUDAD_LNG_OESTE, TUCUMAN_CIUDAD_LNG_ESTE)

    rho = 0.35
    sig_lat = 0.018
    sig_lng = 0.016
    clientes: list[dict] = []
    for j in range(n):
        lat_c = lng_c = None
        for _ in range(800):
            z1, z2 = rng.standard_normal(2)
            dx = z1 * sig_lat + rho * z2 * (sig_lat * 0.35)
            dy = z2 * sig_lng + rho * z1 * (sig_lng * 0.35)
            lat = LAT_CENTRO + dx
            lng = LNG_CENTRO + dy
            if lat_lo <= lat <= lat_hi and lng_lo <= lng <= lng_hi:
                lat_c, lng_c = lat, lng
                break
        if lat_c is None:
            lat_c = float(rng.uniform(lat_lo, lat_hi))
            lng_c = float(rng.uniform(lng_lo, lng_hi))
        clientes.append(
            {
                "id_cliente": j + 1,
                "lat_cliente": lat_c,
                "lng_cliente": lng_c,
            }
        )
    return clientes


def parse_fecha_arg(s: str, fin_del_dia: bool) -> datetime:
    """Acepta YYYY-MM-DD."""
    d = datetime.strptime(s.strip(), "%Y-%m-%d")
    if fin_del_dia:
        return d.replace(hour=23, minute=59, second=59, microsecond=999999)
    return d.replace(hour=0, minute=0, second=0, microsecond=0)


def sample_fecha_pedido(rng: np.random.Generator, dt_min: datetime, dt_max: datetime) -> datetime:
    """Momento aleatorio ponderado por mes, día de semana y hora."""
    if dt_max <= dt_min:
        return dt_min

    fecha_min = dt_min.date()
    fecha_max = dt_max.date()
    n_dias = (fecha_max - fecha_min).days + 1
    if n_dias <= 1:
        delta_seg = max(0.0, (dt_max - dt_min).total_seconds())
        return dt_min + timedelta(seconds=float(rng.uniform(0.0, delta_seg)))

    dias = [fecha_min + timedelta(days=i) for i in range(n_dias)]
    pesos_dias = np.array(
        [PESO_MES.get(d.month, 1.0) * PESO_DIA_SEMANA.get(d.weekday(), 1.0) for d in dias],
        dtype=float,
    )
    if not np.isfinite(pesos_dias).all() or float(pesos_dias.sum()) <= 0.0:
        pesos_dias = np.full(n_dias, 1.0 / n_dias)
    else:
        pesos_dias = pesos_dias / pesos_dias.sum()

    pesos_hora = PESO_HORA.astype(float)
    if pesos_hora.shape[0] != 24 or not np.isfinite(pesos_hora).all() or float(pesos_hora.sum()) <= 0.0:
        pesos_hora = np.ones(24, dtype=float)
    pesos_hora = pesos_hora / pesos_hora.sum()

    for _ in range(5000):
        idx_dia = int(rng.choice(n_dias, p=pesos_dias))
        d = dias[idx_dia]
        hora = int(rng.choice(24, p=pesos_hora))
        minuto = int(rng.integers(0, 60))
        segundo = int(rng.integers(0, 60))
        fecha = datetime(
            year=d.year,
            month=d.month,
            day=d.day,
            hour=hora,
            minute=minuto,
            second=segundo,
        )
        if dt_min <= fecha <= dt_max:
            return fecha

    # Fallback defensivo (rangos muy estrechos en extremos del intervalo).
    delta_seg = max(0.0, (dt_max - dt_min).total_seconds())
    return dt_min + timedelta(seconds=float(rng.uniform(0.0, delta_seg)))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Genera dataset delivery simulado (CSV/XLSX/JSON).")
    p.add_argument("--seed", type=int, default=42, help="Semilla para reproducibilidad.")
    p.add_argument("--pedidos", type=int, default=10000, help="Cantidad de filas/pedidos.")
    p.add_argument(
        "--restaurantes",
        type=int,
        default=97,
        help="Cantidad de locales a usar desde el catálogo LOCALES_TUCUMAN (máx. 97).",
    )
    p.add_argument("--clientes", type=int, default=500, help="Cantidad de clientes únicos.")
    p.add_argument(
        "--fecha-desde",
        type=str,
        default="2025-11-01",
        help="Inicio del rango de fechas de pedido (YYYY-MM-DD).",
    )
    p.add_argument(
        "--fecha-hasta",
        type=str,
        default="2026-05-01",
        help="Fin del rango inclusive (YYYY-MM-DD).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    random.seed(args.seed)

    dt_pedido_min = parse_fecha_arg(args.fecha_desde, fin_del_dia=False)
    dt_pedido_max = parse_fecha_arg(args.fecha_hasta, fin_del_dia=True)
    if dt_pedido_min > dt_pedido_max:
        raise SystemExit("Error: --fecha-desde debe ser anterior o igual a --fecha-hasta.")

    n_cat = len(LOCALES_TUCUMAN)
    if args.restaurantes > n_cat:
        print(
            f"Aviso: el catálogo tiene {n_cat} locales; se usan {n_cat} "
            f"(se ignora --restaurantes {args.restaurantes})."
        )

    restaurantes, popularidades = build_restaurantes(rng, args.restaurantes)
    clientes = build_clientes(rng, args.clientes)
    cliente_ids_weights = rng.dirichlet(np.full(args.clientes, 1.3))

    datos: list[dict] = []

    for i in range(args.pedidos):
        cliente_idx = int(rng.choice(args.clientes, p=cliente_ids_weights))
        c = clientes[cliente_idx]

        restaurante = elegir_restaurante(
            c["lat_cliente"], c["lng_cliente"], restaurantes, popularidades, rng
        )

        distancia = haversine_km(
            restaurante["lat_restaurante"],
            restaurante["lng_restaurante"],
            c["lat_cliente"],
            c["lng_cliente"],
        )

        fecha = sample_fecha_pedido(rng, dt_pedido_min, dt_pedido_max)
        hora = fecha.hour
        dia_idx = fecha.weekday()
        dia_semana_es = DIAS_ES[dia_idx]
        mes = fecha.month

        clima = sample_clima(rng, mes)
        trafico = sample_trafico(rng, hora, dia_idx, clima)
        vehiculo = sample_vehiculo(rng, distancia, clima)

        cantidad_productos = int(rng.integers(1, 7))
        if rng.random() < logistic((distancia - 4.0) / 3.0) * 0.35:
            cantidad_productos = min(6, cantidad_productos + 1)

        base_cat = MONTO_BASE_CATEGORIA[restaurante["categoria_modelo"]]
        ticket_latente = (
            base_cat
            * restaurante["factor_precio_ticket"]
            * rng.lognormal(mean=0.0, sigma=0.22)
            * (1.0 + 0.035 * distancia + 0.12 * max(0, cantidad_productos - 2))
        )
        monto_compra = round(float(np.clip(ticket_latente, 1200.0, 48000.0)), 2)

        costo_envio_base = 520.0 + distancia * 265.0 + rng.normal(0, 65)
        costo_envio = round(float(np.clip(costo_envio_base, 350.0, 9500.0)), 2)

        cat = restaurante["categoria_modelo"]
        envio_prioritario = sample_prioritario(rng, distancia, monto_compra)
        costo_prioritario = (
            costo_prioritario_ars(rng, cat, distancia) if envio_prioritario else 0.0
        )

        monto_total = round(monto_compra + costo_envio + costo_prioritario, 2)
        medio_pago = sample_medio_pago(rng, monto_total)

        tiempo_prep = (8.0 + 5.8 * distancia) * float(
            np.clip(restaurante["factor_prep_min"], 0.72, 1.35)
        )

        extra_clima = {"Lluvia": 9.0, "Tormenta": 17.0}.get(clima, 0.0)
        extra_trafico = {"Medio": 6.5, "Alto": 13.5}.get(trafico, 0.0)

        extra_veh = 0.0
        if vehiculo == "Bicicleta":
            extra_veh += distancia * 2.1 + rng.normal(0, 2)
        else:
            extra_veh += rng.normal(0.9, 1.2)

        tiempo_esperado_base = float(
            np.clip(tiempo_prep + extra_clima + extra_trafico + extra_veh, 7.0, 240.0)
        )

        if envio_prioritario:
            reduc = reduccion_tiempo_prioritario_min(rng, cat, distancia)
            tiempo_esperado = max(7.0, tiempo_esperado_base - reduc)
        else:
            reduc = 0.0
            tiempo_esperado = tiempo_esperado_base

        sd_shock = 5.5 + 0.35 * distancia + (4.0 if clima == "Tormenta" else 0.0)
        if envio_prioritario:
            sd_shock *= 0.86
        tiempo_real = gamma_from_mean_sd(rng, mean=tiempo_esperado, sd=sd_shock)

        retraso_exceso = max(0.0, tiempo_real - tiempo_esperado)

        z_cancel = (
            -3.8
            + 0.09 * retraso_exceso
            + (0.9 if clima == "Tormenta" else 0.0)
            + (0.35 if trafico == "Alto" else 0.0)
            + rng.normal(0, 0.65)
        )
        p_cancel = float(np.clip(logistic(z_cancel), 0.01, 0.45))

        z_demora = (
            -1.9
            + 0.07 * retraso_exceso
            + (0.35 if clima == "Lluvia" else 0.0)
            + (0.45 if trafico == "Alto" else 0.0)
            + rng.normal(0, 0.55)
        )
        p_demora = float(np.clip(logistic(z_demora), 0.02, 0.55))

        if rng.random() < p_cancel:
            estado_pedido = "Cancelado"
        elif rng.random() < p_demora / max(1e-6, 1.0 - p_cancel * 0.3):
            estado_pedido = "Demorado"
        else:
            estado_pedido = "Entregado"

        if estado_pedido == "Cancelado":
            calif_mu = rng.normal(2.1, 0.85)
        elif estado_pedido == "Demorado":
            calif_mu = 3.9 - 0.11 * retraso_exceso + rng.normal(0, 0.55)
        else:
            calif_mu = (
                4.55
                - 0.08 * retraso_exceso
                - 0.22 * logistic((distancia - 6) / 2)
                + rng.normal(0, 0.55)
            )
        calificacion_cliente = int(np.clip(round(calif_mu), 1, 5))

        franja = "Noche" if hora >= 20 else "Tarde" if hora >= 12 else "Mañana"

        datos.append(
            {
                "id_pedido": i + 1,
                "fecha_pedido": fecha.date(),
                "hora_pedido": fecha.time().strftime("%H:%M:%S"),
                "dia_semana": dia_semana_es,
                "mes": mes,
                "franja_horaria": franja,
                "id_restaurante": restaurante["id_restaurante"],
                "nombre_restaurante": restaurante["nombre_restaurante"],
                "direccion_restaurante": restaurante["direccion_restaurante"],
                "categoria_restaurante": restaurante["categoria_restaurante"],
                "lat_restaurante": restaurante["lat_restaurante"],
                "lng_restaurante": restaurante["lng_restaurante"],
                "id_cliente": c["id_cliente"],
                "lat_cliente": c["lat_cliente"],
                "lng_cliente": c["lng_cliente"],
                "distancia_km": round(distancia, 2),
                "clima": clima,
                "trafico": trafico,
                "tipo_vehiculo": vehiculo,
                "monto_compra": monto_compra,
                "costo_envio": costo_envio,
                "envio_prioritario": "Si" if envio_prioritario else "No",
                "costo_prioritario": costo_prioritario,
                "ahorro_tiempo_esperado_min": round(tiempo_esperado_base - tiempo_esperado, 2),
                "monto_total": monto_total,
                "medio_pago": medio_pago,
                "cantidad_productos": cantidad_productos,
                "tiempo_esperado_min": round(tiempo_esperado, 2),
                "tiempo_real_entrega_min": round(tiempo_real, 1),
                "retraso_exceso_min": round(retraso_exceso, 2),
                "estado_pedido": estado_pedido,
                "calificacion_cliente": calificacion_cliente,
            }
        )

    df = pd.DataFrame(datos)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "dataset_delivery_simulado.csv"
    json_path = OUTPUT_DIR / "dataset_delivery_simulado.json"
    xlsx_path = OUTPUT_DIR / "dataset_delivery_simulado.xlsx"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    df_mapa = df.copy()
    df_mapa["fecha_pedido"] = df_mapa["fecha_pedido"].astype(str)
    df_mapa.to_json(
        json_path,
        orient="records",
        force_ascii=False,
        date_format="iso",
        indent=2,
    )

    try:
        df.to_excel(xlsx_path, index=False)
    except PermissionError:
        print(
            f"Aviso: no se pudo escribir {xlsx_path.name} "
            "(cerralo si esta abierto en Excel). CSV y JSON ya se guardaron."
        )


if __name__ == "__main__":
    main()
