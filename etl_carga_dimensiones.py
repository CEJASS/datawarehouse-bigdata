"""
=============================================================
ETL - CARGA DE DIMENSIONES
DATA WAREHOUSE: Sistema de Análisis de Ventas
=============================================================
Autor:    César Jasser de Jesús  |  Matrícula: #2023-1747
Materia:  Big Data / Electiva 1  |  Profesor: Francis Ramírez
Motor BD: SQLite (portabilidad local)
          — Para producción, cambiar a conexión MySQL (ver comentarios)
=============================================================
Fuentes de datos:
  - customers.csv     → DIM_CLIENTE      (5 000 registros)
  - products.csv      → DIM_PRODUCTO     (2 000 registros)
  - orders.csv        → DIM_FECHA + FK   (20 000 registros)
  - order_details.csv → FACT_VENTAS      (60 161 registros)
  - DIM_VENDEDOR      → Faker (sin CSV disponible)
  - DIM_GEOGRAFIA     → Datos predefinidos LATAM + España
=============================================================
"""

import csv
import os
import sqlite3
import random
import time
import logging
from datetime import date, datetime, timedelta
from faker import Faker

# ── Configuración de logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Configuración de conexión ─────────────────────────────────────────────────
DB_FILE = "dw_ventas.db"          # SQLite — archivo local

# Para MySQL descomentar estas líneas e instalar: pip install mysql-connector-python
# import mysql.connector
# MYSQL_CONFIG = {
#     "host":     "localhost",
#     "user":     "root",
#     "password": "tu_contraseña",
#     "database": "dw_ventas",
# }

# ── Rutas de los archivos CSV ─────────────────────────────────────────────────
CSV_CLIENTES      = "customers.csv"
CSV_PRODUCTOS     = "products.csv"
CSV_ORDENES       = "orders.csv"
CSV_DETALLES      = "order_details.csv"

fake = Faker("es_MX")
random.seed(42)

# ── DDL - Creación de tablas ──────────────────────────────────────────────────
DDL = """
CREATE TABLE IF NOT EXISTS DIM_FECHA (
    id_fecha        INTEGER PRIMARY KEY,
    fecha           TEXT    NOT NULL,
    anio            INTEGER NOT NULL,
    trimestre       INTEGER NOT NULL,
    mes             INTEGER NOT NULL,
    nombre_mes      TEXT    NOT NULL,
    semana          INTEGER NOT NULL,
    dia             INTEGER NOT NULL,
    dia_semana      TEXT    NOT NULL,
    es_fin_semana   INTEGER NOT NULL DEFAULT 0,
    es_feriado      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS DIM_PRODUCTO (
    id_producto     INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_sku      TEXT    NOT NULL UNIQUE,
    nombre_producto TEXT    NOT NULL,
    descripcion     TEXT,
    categoria       TEXT    NOT NULL,
    subcategoria    TEXT,
    precio_base     REAL    NOT NULL,
    unidad_medida   TEXT,
    proveedor       TEXT,
    pais_origen     TEXT,
    activo          INTEGER NOT NULL DEFAULT 1,
    fecha_alta      TEXT,
    fecha_baja      TEXT,
    fuente_datos    TEXT,
    fecha_carga     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS DIM_CLIENTE (
    id_cliente      INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_cliente  TEXT    NOT NULL UNIQUE,
    nombre_cliente  TEXT    NOT NULL,
    tipo_cliente    TEXT    NOT NULL,
    segmento        TEXT,
    email           TEXT,
    telefono        TEXT,
    pais            TEXT,
    region          TEXT,
    ciudad          TEXT,
    direccion       TEXT,
    codigo_postal   TEXT,
    fecha_registro  TEXT,
    activo          INTEGER NOT NULL DEFAULT 1,
    fuente_datos    TEXT,
    fecha_carga     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS DIM_VENDEDOR (
    id_vendedor       INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_vendedor   TEXT NOT NULL UNIQUE,
    nombre_vendedor   TEXT NOT NULL,
    apellido_vendedor TEXT NOT NULL,
    email             TEXT,
    telefono          TEXT,
    region            TEXT,
    zona              TEXT,
    cargo             TEXT,
    fecha_ingreso     TEXT,
    activo            INTEGER NOT NULL DEFAULT 1,
    fecha_carga       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS DIM_GEOGRAFIA (
    id_geografia  INTEGER PRIMARY KEY AUTOINCREMENT,
    pais          TEXT NOT NULL,
    codigo_pais   TEXT NOT NULL,
    region        TEXT,
    ciudad        TEXT NOT NULL,
    codigo_postal TEXT,
    zona_horaria  TEXT,
    continente    TEXT NOT NULL,
    latitud       REAL,
    longitud      REAL
);

CREATE TABLE IF NOT EXISTS FACT_VENTAS (
    id_venta        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_fecha        INTEGER NOT NULL REFERENCES DIM_FECHA(id_fecha),
    id_producto     INTEGER NOT NULL REFERENCES DIM_PRODUCTO(id_producto),
    id_cliente      INTEGER NOT NULL REFERENCES DIM_CLIENTE(id_cliente),
    id_vendedor     INTEGER NOT NULL REFERENCES DIM_VENDEDOR(id_vendedor),
    id_geografia    INTEGER NOT NULL REFERENCES DIM_GEOGRAFIA(id_geografia),
    numero_factura  TEXT    NOT NULL,
    cantidad        INTEGER NOT NULL,
    precio_unitario REAL    NOT NULL,
    descuento       REAL    NOT NULL DEFAULT 0.0,
    subtotal        REAL    NOT NULL,
    impuesto        REAL    NOT NULL,
    total_venta     REAL    NOT NULL,
    moneda          TEXT    NOT NULL DEFAULT 'USD',
    fuente_datos    TEXT,
    fecha_carga     TEXT    NOT NULL
);
"""

# ── Datos de referencia ───────────────────────────────────────────────────────
NOMBRES_MES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

DIAS_SEMANA = {
    0: "Lunes", 1: "Martes", 2: "Miércoles",
    3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo",
}

# Feriados cubiertos en el rango 2023-2025
FERIADOS = {
    # 2023
    date(2023,  1,  1), date(2023,  2,  6), date(2023,  3, 20),
    date(2023,  4, 13), date(2023,  4, 14), date(2023,  5,  1),
    date(2023,  9, 16), date(2023, 11, 20), date(2023, 12, 25),
    # 2024
    date(2024,  1,  1), date(2024,  2,  5), date(2024,  3, 18),
    date(2024,  3, 28), date(2024,  3, 29), date(2024,  5,  1),
    date(2024,  9, 16), date(2024, 11, 18), date(2024, 12, 25),
    date(2024, 12, 31),
    # 2025
    date(2025,  1,  1), date(2025,  2,  3), date(2025,  3, 17),
    date(2025,  4, 17), date(2025,  4, 18), date(2025,  5,  1),
    date(2025,  9, 16), date(2025, 11, 17), date(2025, 12, 25),
}

# Mapeo de categorías (inglés CSV → español DW)
CATEGORIA_MAP = {
    "Electronics": "Electrónica",
    "Clothing":    "Ropa",
    "Food":        "Alimentos",
    "Home":        "Hogar",
    "Sports":      "Deportes",
    "Toys":        "Juguetes",
    "Books":       "Libros",
}

CATEGORIAS_SUBCAT = {
    "Electrónica": ["Smartphones", "Laptops", "Televisores", "Audio", "Cámaras"],
    "Ropa":        ["Camisetas", "Pantalones", "Vestidos", "Calzado", "Accesorios"],
    "Alimentos":   ["Lácteos", "Bebidas", "Snacks", "Granos", "Conservas"],
    "Hogar":       ["Muebles", "Decoración", "Cocina", "Baño", "Jardín"],
    "Deportes":    ["Fútbol", "Natación", "Ciclismo", "Fitness", "Outdoor"],
    "Tecnología":  ["Software", "Periféricos", "Redes", "Servidores", "IoT"],
    "Juguetes":    ["Educativos", "Acción", "Muñecas", "Construcción", "Exterior"],
    "Libros":      ["Ficción", "No Ficción", "Infantil", "Técnico", "Académico"],
}

REGIONES_VENDEDOR = ["Norte", "Sur", "Este", "Oeste", "Centro"]
ZONAS_POR_REGION = {
    "Norte": ["Zona A", "Zona B"],
    "Sur":   ["Zona C", "Zona D"],
    "Este":  ["Zona E", "Zona F"],
    "Oeste": ["Zona G", "Zona H"],
    "Centro":["Zona I", "Zona J"],
}
CARGOS = [
    "Ejecutivo de Ventas", "Gerente de Zona", "Representante Comercial",
    "Asesor de Ventas", "Director Regional",
]

# Geografía real aproximada de LATAM + España
GEO_DATA = [
    ("México",    "MEX", "CDMX",             "Ciudad de México", "06600", "America/Mexico_City",  "América",  19.4326, -99.1332),
    ("México",    "MEX", "Jalisco",           "Guadalajara",      "44100", "America/Mexico_City",  "América",  20.6597, -103.3496),
    ("México",    "MEX", "Nuevo León",        "Monterrey",        "64000", "America/Monterrey",    "América",  25.6866, -100.3161),
    ("México",    "MEX", "Yucatán",           "Mérida",           "97000", "America/Merida",       "América",  20.9674, -89.5926),
    ("México",    "MEX", "Veracruz",          "Veracruz",         "91700", "America/Mexico_City",  "América",  19.1738, -96.1342),
    ("Colombia",  "COL", "Cundinamarca",      "Bogotá",           "110111","America/Bogota",       "América",   4.7110, -74.0721),
    ("Colombia",  "COL", "Antioquia",         "Medellín",         "050001","America/Bogota",       "América",   6.2442, -75.5812),
    ("Colombia",  "COL", "Valle del Cauca",   "Cali",             "760001","America/Bogota",       "América",   3.4516, -76.5320),
    ("Colombia",  "COL", "Atlántico",         "Barranquilla",     "080001","America/Bogota",       "América",  10.9685, -74.7813),
    ("Colombia",  "COL", "Santander",         "Bucaramanga",      "680001","America/Bogota",       "América",   7.1193, -73.1227),
    ("Argentina", "ARG", "Buenos Aires",      "Buenos Aires",     "C1000", "America/Argentina/Buenos_Aires","América",-34.6037,-58.3816),
    ("Argentina", "ARG", "Córdoba",           "Córdoba",          "5000",  "America/Argentina/Cordoba","América",-31.4201,-64.1888),
    ("Argentina", "ARG", "Santa Fe",          "Rosario",          "2000",  "America/Argentina/Cordoba","América",-32.9468,-60.6393),
    ("Argentina", "ARG", "Mendoza",           "Mendoza",          "5500",  "America/Argentina/Mendoza","América",-32.8908,-68.8272),
    ("Argentina", "ARG", "Tucumán",           "San Miguel de Tucumán","4000","America/Argentina/Tucuman","América",-26.8241,-65.2226),
    ("Chile",     "CHL", "Metropolitana",     "Santiago",         "8320000","America/Santiago",   "América", -33.4569,-70.6483),
    ("Chile",     "CHL", "Valparaíso",        "Valparaíso",       "2340000","America/Santiago",   "América", -33.0472,-71.6127),
    ("Chile",     "CHL", "Biobío",            "Concepción",       "4030000","America/Santiago",   "América", -36.8270,-73.0503),
    ("Chile",     "CHL", "Araucanía",         "Temuco",           "4780000","America/Santiago",   "América", -38.7359,-72.5904),
    ("Chile",     "CHL", "Los Lagos",         "Puerto Montt",     "5480000","America/Santiago",   "América", -41.4693,-72.9424),
    ("Perú",      "PER", "Lima",              "Lima",             "15001", "America/Lima",         "América",  -12.0464,-77.0428),
    ("Perú",      "PER", "Arequipa",          "Arequipa",         "04001", "America/Lima",         "América",  -16.4090,-71.5375),
    ("Perú",      "PER", "La Libertad",       "Trujillo",         "13001", "America/Lima",         "América",   -8.1116,-79.0287),
    ("Perú",      "PER", "Lambayeque",        "Chiclayo",         "14001", "America/Lima",         "América",   -6.7714,-79.8409),
    ("Perú",      "PER", "Piura",             "Piura",            "20001", "America/Lima",         "América",   -5.1945,-80.6328),
    ("España",    "ESP", "Comunidad de Madrid","Madrid",           "28001", "Europe/Madrid",        "Europa",   40.4168, -3.7038),
    ("España",    "ESP", "Cataluña",          "Barcelona",        "08001", "Europe/Madrid",        "Europa",   41.3851,  2.1734),
    ("España",    "ESP", "Andalucía",         "Sevilla",          "41001", "Europe/Madrid",        "Europa",   37.3891, -5.9845),
    ("España",    "ESP", "Comunitat Valenciana","Valencia",        "46001", "Europe/Madrid",        "Europa",   39.4699, -0.3763),
    ("España",    "ESP", "País Vasco",        "Bilbao",           "48001", "Europe/Madrid",        "Europa",   43.2630, -2.9350),
    ("Bolivia",   "BOL", "La Paz",            "La Paz",           "0101",  "America/La_Paz",       "América",  -16.5000,-68.1500),
    ("Venezuela", "VEN", "Distrito Capital",  "Caracas",          "1010",  "America/Caracas",      "América",  10.4806,-66.9036),
    ("Ecuador",   "ECU", "Pichincha",         "Quito",            "170150","America/Guayaquil",    "América",  -0.1807,-78.4678),
    ("Ecuador",   "ECU", "Guayas",            "Guayaquil",        "090101","America/Guayaquil",    "América",  -2.1962,-79.8862),
    ("Paraguay",  "PRY", "Central",           "Asunción",         "1001",  "America/Asuncion",     "América",  -25.2867,-57.6470),
    ("Uruguay",   "URY", "Montevideo",        "Montevideo",       "11000", "America/Montevideo",   "América",  -34.9011,-56.1645),
    ("Guatemala", "GTM", "Guatemala",         "Ciudad de Guatemala","01001","America/Guatemala",   "América",  14.6349,-90.5069),
    ("Costa Rica","CRI", "San José",          "San José",         "10101", "America/Costa_Rica",   "América",   9.9281,-84.0907),
    ("Panamá",    "PAN", "Panamá",            "Ciudad de Panamá", "0801",  "America/Panama",       "América",   8.9936,-79.5197),
    ("Honduras",  "HND", "Francisco Morazán", "Tegucigalpa",      "11101", "America/Tegucigalpa",  "América",  14.0723,-87.2023),
    ("El Salvador","SLV","San Salvador",      "San Salvador",     "01101", "America/El_Salvador",  "América",  13.6929,-89.2182),
    ("Nicaragua", "NIC", "Managua",           "Managua",          "14001", "America/Managua",      "América",  12.1364,-86.2816),
    ("Cuba",      "CUB", "La Habana",         "La Habana",        "10100", "America/Havana",       "América",  23.1136,-82.3666),
    ("Rep. Dom.", "DOM", "Distrito Nacional", "Santo Domingo",    "10101", "America/Santo_Domingo","América",  18.4861,-69.9312),
    ("Puerto Rico","PRI","San Juan",          "San Juan",         "00901", "America/Puerto_Rico",  "América",  18.4655,-66.1057),
    ("Brasil",    "BRA", "São Paulo",         "São Paulo",        "01310", "America/Sao_Paulo",    "América", -23.5505,-46.6333),
    ("Brasil",    "BRA", "Rio de Janeiro",    "Rio de Janeiro",   "20040", "America/Sao_Paulo",    "América", -22.9068,-43.1729),
    ("Brasil",    "BRA", "Minas Gerais",      "Belo Horizonte",   "30130", "America/Sao_Paulo",    "América", -19.9167,-43.9345),
    ("España",    "ESP", "Galicia",           "A Coruña",         "15001", "Europe/Madrid",        "Europa",   43.3623, -8.4115),
    ("España",    "ESP", "Aragón",            "Zaragoza",         "50001", "Europe/Madrid",        "Europa",   41.6561, -0.8773),
]


# ── Funciones auxiliares ──────────────────────────────────────────────────────

def _leer_csv(filepath: str) -> list[dict]:
    """Lee un CSV y devuelve lista de dicts. Lanza FileNotFoundError si no existe."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV no encontrado: {filepath}")
    with open(filepath, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _fecha_a_id(fecha_str: str) -> int:
    """Convierte 'YYYY-MM-DD' al entero YYYYMMDD usado como id_fecha."""
    return int(fecha_str.replace("-", ""))


def _fecha_row(d: date) -> tuple:
    """Construye la tupla completa para DIM_FECHA dado un objeto date."""
    id_fecha  = int(d.strftime("%Y%m%d"))
    trimestre = (d.month - 1) // 3 + 1
    semana    = d.isocalendar()[1]
    dia_idx   = d.weekday()
    return (
        id_fecha,
        d.isoformat(),
        d.year,
        trimestre,
        d.month,
        NOMBRES_MES[d.month],
        semana,
        d.day,
        DIAS_SEMANA[dia_idx],
        1 if dia_idx >= 5 else 0,
        1 if d in FERIADOS else 0,
    )


# ── Funciones de generación / carga ──────────────────────────────────────────

def generar_dim_fecha_desde_csv(orders_filepath: str) -> list[tuple]:
    """
    Lee orders.csv, extrae fechas únicas de OrderDate y genera un registro
    por cada día en el rango mínimo–máximo encontrado.
    Si el CSV no existe, cae al rango 2024 completo (366 días).
    """
    if not os.path.exists(orders_filepath):
        log.warning("orders.csv no encontrado — generando DIM_FECHA solo para 2024.")
        inicio = date(2024, 1, 1)
        fin    = date(2024, 12, 31)
    else:
        filas = _leer_csv(orders_filepath)
        fechas = set()
        for r in filas:
            try:
                fechas.add(date.fromisoformat(r["OrderDate"]))
            except (KeyError, ValueError):
                pass
        if not fechas:
            inicio = date(2024, 1, 1)
            fin    = date(2024, 12, 31)
        else:
            # Expandir al primer y último día del mes para mayor cobertura
            min_f = min(fechas)
            max_f = max(fechas)
            inicio = date(min_f.year, min_f.month, 1)
            fin    = date(max_f.year, max_f.month,
                          [31,28+int(max_f.year%4==0),31,30,31,30,
                           31,31,30,31,30,31][max_f.month-1])

    log.info(f"Generando DIM_FECHA — {inicio} a {fin}...")
    registros = []
    delta = (fin - inicio).days + 1
    for i in range(delta):
        registros.append(_fecha_row(inicio + timedelta(days=i)))
    return registros


def cargar_dim_producto_csv(filepath: str) -> list[tuple]:
    """
    Carga DIM_PRODUCTO desde products.csv.
    Campos CSV: ProductID, ProductName, Category, Price, Stock
    """
    log.info(f"Cargando DIM_PRODUCTO desde {filepath}...")
    filas    = _leer_csv(filepath)
    paises   = ["China", "México", "Estados Unidos", "Alemania", "India",
                "Brasil", "España", "Japón", "Corea del Sur", "Italia"]
    unidades = ["Pieza", "Kg", "Litro", "Caja", "Par", "Paquete", "Unidad"]
    registros = []
    ahora = datetime.now().isoformat(timespec="seconds")
    for r in filas:
        cat_en  = r.get("Category", "").strip()
        cat_es  = CATEGORIA_MAP.get(cat_en, cat_en or "General")
        subcats = CATEGORIAS_SUBCAT.get(cat_es, ["General"])
        fecha_alta = fake.date_between(
            start_date=date(2018, 1, 1), end_date=date(2023, 12, 31)
        ).isoformat()
        registros.append((
            f"SKU-{int(r['ProductID']):05d}",          # codigo_sku
            r["ProductName"].strip(),                   # nombre_producto
            fake.sentence(nb_words=8),                  # descripcion
            cat_es,                                     # categoria
            random.choice(subcats),                     # subcategoria
            round(float(r["Price"]), 2),                # precio_base
            random.choice(unidades),                    # unidad_medida
            fake.company(),                             # proveedor
            random.choice(paises),                      # pais_origen
            1,                                          # activo
            fecha_alta,                                 # fecha_alta
            None,                                       # fecha_baja
            "CSV",                                      # fuente_datos
            ahora,                                      # fecha_carga
        ))
    return registros


def cargar_dim_cliente_csv(filepath: str) -> list[tuple]:
    """
    Carga DIM_CLIENTE desde customers.csv.
    Campos CSV: CustomerID, FirstName, LastName, Email, Phone, City, Country
    """
    log.info(f"Cargando DIM_CLIENTE desde {filepath}...")
    filas     = _leer_csv(filepath)
    tipos     = ["Persona Física", "Empresa"]
    segmentos = ["Premium", "VIP", "Estándar", "Corporativo", "Minorista"]
    registros = []
    ahora = datetime.now().isoformat(timespec="seconds")
    for r in filas:
        nombre = f"{r['FirstName'].strip()} {r['LastName'].strip()}"
        registros.append((
            f"CLI-{int(r['CustomerID']):05d}",          # codigo_cliente
            nombre,                                     # nombre_cliente
            random.choice(tipos),                       # tipo_cliente
            random.choice(segmentos),                   # segmento
            r["Email"].strip(),                         # email
            r["Phone"].strip(),                         # telefono
            r["Country"].strip(),                       # pais
            fake.state(),                               # region
            r["City"].strip(),                          # ciudad
            fake.street_address(),                      # direccion
            fake.postcode(),                            # codigo_postal
            fake.date_between(
                start_date=date(2015, 1, 1),
                end_date=date(2023, 12, 31)
            ).isoformat(),                              # fecha_registro
            1,                                          # activo
            "CSV",                                      # fuente_datos
            ahora,                                      # fecha_carga
        ))
    return registros


def generar_dim_vendedor(n: int = 30) -> list[tuple]:
    """Genera n vendedores con Faker (sin CSV disponible)."""
    log.info(f"Generando DIM_VENDEDOR con Faker — {n} registros...")
    registros = []
    ahora = datetime.now().isoformat(timespec="seconds")
    for i in range(1, n + 1):
        region   = random.choice(REGIONES_VENDEDOR)
        zona     = random.choice(ZONAS_POR_REGION[region])
        cargo    = random.choice(CARGOS)
        nombre   = fake.first_name()
        apellido = fake.last_name()
        registros.append((
            f"VEN-{i:04d}",
            nombre,
            apellido,
            f"{nombre.lower().replace(' ','')}.{apellido.lower().replace(' ','')}@empresa.com",
            fake.phone_number(),
            region,
            zona,
            cargo,
            fake.date_between(
                start_date=date(2010, 1, 1), end_date=date(2023, 6, 30)
            ).isoformat(),
            1,
            ahora,
        ))
    return registros


def generar_dim_geografia() -> list[tuple]:
    """Usa los 50 registros predefinidos con coordenadas reales."""
    log.info("Cargando DIM_GEOGRAFIA — 50 registros predefinidos...")
    return [
        (pais, cod, region, ciudad, cp, tz, continente, lat, lon)
        for pais, cod, region, ciudad, cp, tz, continente, lat, lon in GEO_DATA
    ]


def cargar_fact_ventas_csv(
    orders_filepath: str,
    details_filepath: str,
    cur,
) -> list[tuple]:
    """
    Construye FACT_VENTAS uniendo orders.csv y order_details.csv.

    Campos orders:        OrderID, CustomerID, OrderDate, Status
    Campos order_details: OrderID, ProductID, Quantity, TotalPrice

    FK resueltas consultando las dimensiones ya cargadas en la BD.
    id_vendedor  → asignado aleatoriamente
    id_geografia → asignado aleatoriamente
    """
    log.info(f"Cargando FACT_VENTAS desde {orders_filepath} + {details_filepath}...")

    # ── Lookups desde la BD ───────────────────────────────────────
    # codigo_cliente (CLI-XXXXX) → id_cliente
    cli_map = {
        row[0]: row[1]
        for row in cur.execute(
            "SELECT codigo_cliente, id_cliente FROM DIM_CLIENTE"
        ).fetchall()
    }

    # codigo_sku (SKU-XXXXX) → (id_producto, precio_base)
    prod_map = {
        row[0]: (row[1], row[2])
        for row in cur.execute(
            "SELECT codigo_sku, id_producto, precio_base FROM DIM_PRODUCTO"
        ).fetchall()
    }

    ids_vendedor  = [r[0] for r in cur.execute(
        "SELECT id_vendedor FROM DIM_VENDEDOR").fetchall()]
    ids_geografia = [r[0] for r in cur.execute(
        "SELECT id_geografia FROM DIM_GEOGRAFIA").fetchall()]

    # ── Leer orders → dict {OrderID: {CustomerID, OrderDate}} ────
    orders_raw = _leer_csv(orders_filepath)
    orders_dict: dict[str, dict] = {}
    for r in orders_raw:
        orders_dict[r["OrderID"]] = {
            "CustomerID": r["CustomerID"],
            "OrderDate":  r["OrderDate"],
        }

    # ── Leer order_details y construir registros ─────────────────
    details_raw = _leer_csv(details_filepath)
    registros   = []
    ahora       = datetime.now().isoformat(timespec="seconds")
    omitidos    = 0

    for r in details_raw:
        order_id   = r["OrderID"]
        product_id = r["ProductID"]
        order_info = orders_dict.get(order_id)
        if not order_info:
            omitidos += 1
            continue

        codigo_cli  = f"CLI-{int(order_info['CustomerID']):05d}"
        codigo_sku  = f"SKU-{int(product_id):05d}"
        id_cliente  = cli_map.get(codigo_cli)
        prod_entry  = prod_map.get(codigo_sku)

        if id_cliente is None or prod_entry is None:
            omitidos += 1
            continue

        id_producto, precio_base = prod_entry
        cantidad        = int(r["Quantity"])
        total_precio    = round(float(r["TotalPrice"]), 2)
        precio_unitario = round(total_precio / cantidad, 2) if cantidad else precio_base
        subtotal        = total_precio
        impuesto        = round(subtotal * 0.18, 2)
        total_venta     = round(subtotal + impuesto, 2)
        id_fecha        = _fecha_a_id(order_info["OrderDate"])
        id_vendedor     = random.choice(ids_vendedor)
        id_geografia    = random.choice(ids_geografia)

        registros.append((
            id_fecha,
            id_producto,
            id_cliente,
            id_vendedor,
            id_geografia,
            f"FAC-{order_id.zfill(7)}",  # numero_factura
            cantidad,
            precio_unitario,
            0.0,                          # descuento (no disponible en CSV)
            subtotal,
            impuesto,
            total_venta,
            "USD",
            "CSV",
            ahora,
        ))

    if omitidos:
        log.warning(f"  {omitidos} registros de order_details omitidos (FK no resuelta).")
    return registros


# ── Función principal ─────────────────────────────────────────────────────────

def main():
    inicio_total = time.perf_counter()
    resumen = {}

    log.info("=" * 60)
    log.info("  ETL - CARGA DE DIMENSIONES - DW VENTAS")
    log.info("  Fuente: CSV (customers / products / orders / order_details)")
    log.info("=" * 60)

    # ── Conexión SQLite ───────────────────────────────────────────
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        log.info(f"Conexión establecida → {DB_FILE}")
    except Exception as e:
        log.error(f"No se pudo conectar a la base de datos: {e}")
        raise

    try:
        cur = conn.cursor()

        # ── Crear tablas ──────────────────────────────────────────
        log.info("Creando tablas (si no existen)...")
        for stmt in DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
        conn.commit()

        # ── DIM_FECHA (desde fechas de orders.csv) ────────────────
        t0 = time.perf_counter()
        try:
            filas = generar_dim_fecha_desde_csv(CSV_ORDENES)
            cur.executemany(
                "INSERT OR IGNORE INTO DIM_FECHA VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                filas,
            )
            conn.commit()
            resumen["DIM_FECHA"] = (len(filas), "OK Completado")
            log.info(f"  DIM_FECHA cargada: {len(filas)} registros ({time.perf_counter()-t0:.2f}s)")
        except Exception as e:
            conn.rollback()
            resumen["DIM_FECHA"] = (0, f"Error: {e}")
            log.error(f"Error en DIM_FECHA: {e}")

        # ── DIM_PRODUCTO (desde products.csv) ─────────────────────
        t0 = time.perf_counter()
        try:
            filas = cargar_dim_producto_csv(CSV_PRODUCTOS)
            cur.executemany(
                """INSERT OR IGNORE INTO DIM_PRODUCTO
                   (codigo_sku,nombre_producto,descripcion,categoria,subcategoria,
                    precio_base,unidad_medida,proveedor,pais_origen,activo,
                    fecha_alta,fecha_baja,fuente_datos,fecha_carga)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                filas,
            )
            conn.commit()
            resumen["DIM_PRODUCTO"] = (len(filas), "OK Completado")
            log.info(f"  DIM_PRODUCTO cargada: {len(filas)} registros ({time.perf_counter()-t0:.2f}s)")
        except Exception as e:
            conn.rollback()
            resumen["DIM_PRODUCTO"] = (0, f"Error: {e}")
            log.error(f"Error en DIM_PRODUCTO: {e}")

        # ── DIM_CLIENTE (desde customers.csv) ─────────────────────
        t0 = time.perf_counter()
        try:
            filas = cargar_dim_cliente_csv(CSV_CLIENTES)
            cur.executemany(
                """INSERT OR IGNORE INTO DIM_CLIENTE
                   (codigo_cliente,nombre_cliente,tipo_cliente,segmento,email,telefono,
                    pais,region,ciudad,direccion,codigo_postal,fecha_registro,activo,
                    fuente_datos,fecha_carga)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                filas,
            )
            conn.commit()
            resumen["DIM_CLIENTE"] = (len(filas), "OK Completado")
            log.info(f"  DIM_CLIENTE cargada: {len(filas)} registros ({time.perf_counter()-t0:.2f}s)")
        except Exception as e:
            conn.rollback()
            resumen["DIM_CLIENTE"] = (0, f"Error: {e}")
            log.error(f"Error en DIM_CLIENTE: {e}")

        # ── DIM_VENDEDOR (Faker — sin CSV disponible) ─────────────
        t0 = time.perf_counter()
        try:
            filas = generar_dim_vendedor(30)
            cur.executemany(
                """INSERT OR IGNORE INTO DIM_VENDEDOR
                   (codigo_vendedor,nombre_vendedor,apellido_vendedor,email,telefono,
                    region,zona,cargo,fecha_ingreso,activo,fecha_carga)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                filas,
            )
            conn.commit()
            resumen["DIM_VENDEDOR"] = (len(filas), "OK Completado")
            log.info(f"  DIM_VENDEDOR cargada: {len(filas)} registros ({time.perf_counter()-t0:.2f}s)")
        except Exception as e:
            conn.rollback()
            resumen["DIM_VENDEDOR"] = (0, f"Error: {e}")
            log.error(f"Error en DIM_VENDEDOR: {e}")

        # ── DIM_GEOGRAFIA (datos predefinidos) ────────────────────
        t0 = time.perf_counter()
        try:
            filas = generar_dim_geografia()
            cur.executemany(
                """INSERT OR IGNORE INTO DIM_GEOGRAFIA
                   (pais,codigo_pais,region,ciudad,codigo_postal,zona_horaria,
                    continente,latitud,longitud)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                filas,
            )
            conn.commit()
            resumen["DIM_GEOGRAFIA"] = (len(filas), "OK Completado")
            log.info(f"  DIM_GEOGRAFIA cargada: {len(filas)} registros ({time.perf_counter()-t0:.2f}s)")
        except Exception as e:
            conn.rollback()
            resumen["DIM_GEOGRAFIA"] = (0, f"Error: {e}")
            log.error(f"Error en DIM_GEOGRAFIA: {e}")

        # ── FACT_VENTAS (orders.csv + order_details.csv) ──────────
        t0 = time.perf_counter()
        try:
            filas = cargar_fact_ventas_csv(CSV_ORDENES, CSV_DETALLES, cur)
            cur.executemany(
                """INSERT OR IGNORE INTO FACT_VENTAS
                   (id_fecha,id_producto,id_cliente,id_vendedor,id_geografia,
                    numero_factura,cantidad,precio_unitario,descuento,subtotal,
                    impuesto,total_venta,moneda,fuente_datos,fecha_carga)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                filas,
            )
            conn.commit()
            resumen["FACT_VENTAS"] = (len(filas), "OK Completado")
            log.info(f"  FACT_VENTAS cargada: {len(filas)} registros ({time.perf_counter()-t0:.2f}s)")
        except Exception as e:
            conn.rollback()
            resumen["FACT_VENTAS"] = (0, f"Error: {e}")
            log.error(f"Error en FACT_VENTAS: {e}")

    finally:
        conn.close()

    # ── Resumen de carga ──────────────────────────────────────────
    tiempo_total = time.perf_counter() - inicio_total
    sep = "+" + "-"*22 + "+" + "-"*10 + "+" + "-"*16 + "+"
    hdr = f"| {'Tabla':<21}| {'Registros':>9}| {'Estado':<15}|"
    out = [sep, hdr, sep]
    for tabla, (registros, estado) in resumen.items():
        out.append(f"| {tabla:<21}| {registros:>9}| {estado:<15}|")
    out.append(sep)
    bloque = "\n".join(out)
    try:
        print()
        print(bloque)
    except UnicodeEncodeError:
        import sys
        sys.stdout.buffer.write((bloque + "\n").encode("utf-8", errors="replace"))
    print(f"  Tiempo total de carga: {tiempo_total:.2f} segundos")
    print()
    log.info("ETL finalizado correctamente.")


if __name__ == "__main__":
    main()
