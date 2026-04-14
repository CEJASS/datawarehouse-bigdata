# Data Warehouse — Sistema de Análisis de Ventas

**Actividad 3.1 — Modelado BD Sistema de Ventas**

| | |
|---|---|
| **Estudiante** | César Jasser de Jesús |
| **Matrícula** | #2023-1747 |
| **Materia** | Big Data / Electiva 1 |
| **Profesor** | Francis Ramírez |

---

## Descripción

Implementación de un **Data Warehouse** con modelo **Star Schema** para el análisis multidimensional de ventas comerciales. El proyecto incluye el diseño completo del esquema, un proceso ETL automatizado y la generación de un informe PDF profesional.

### Modelo de datos

```
         DIM_FECHA
             │
DIM_VENDEDOR─┤
             ├──► FACT_VENTAS ◄──┬── DIM_PRODUCTO
DIM_CLIENTE──┤                   │
             │                   └── DIM_GEOGRAFIA
             └── (todas conectadas por FK)
```

**5 Dimensiones + 1 Tabla de Hechos + 6 Vistas Analíticas**

---

## Estructura del proyecto

```
proyecto-datawarehouse-bigdata/
│
├── etl_carga_dimensiones.py      # Script ETL — crea tablas y carga datos de prueba
├── generar_informe_pdf.py        # Generador del informe PDF profesional
├── script_DW_ventas.sql          # DDL completo para MySQL 8.x
├── DER_SistemaVentas.png         # Diagrama Entidad-Relación (Star Schema)
├── Informe_Carga_DW_Ventas.pdf   # Informe de actividad (generado)
├── requirements.txt              # Dependencias Python
├── .gitignore                    # Exclusiones de Git
└── README.md                     # Este archivo
```

---

## Requisitos

- Python 3.9 o superior
- Pip

```bash
pip install -r requirements.txt
```

Dependencias:
- `faker` >= 24.0.0 — generación de datos sintéticos (DIM_VENDEDOR)
- `reportlab` >= 4.1.0 — generación del PDF
- `Pillow` >= 10.0.0 — manejo de imágenes en el PDF
- `matplotlib` >= 3.7.0 — generación del diagrama DER

---

## Uso

### Paso 1 — Cargar dimensiones y tabla de hechos

```bash
python etl_carga_dimensiones.py
```

Requiere los archivos CSV en la misma carpeta:
`customers.csv`, `products.csv`, `orders.csv`, `order_details.csv`

Esto genera `dw_ventas.db` (SQLite) con:

| Tabla          | Registros  | Fuente                     |
|----------------|------------|----------------------------|
| DIM_FECHA      | 760        | Derivado de `orders.csv`   |
| DIM_PRODUTO    | 2 000      | `products.csv`             |
| DIM_CLIENTE    | 5 000      | `customers.csv`            |
| DIM_VENDEDOR   | 30         | Faker (sin CSV disponible) |
| DIM_GEOGRAFIA  | 50         | Datos predefinidos LATAM   |
| FACT_VENTAS    | ~60 000    | `orders.csv` + `order_details.csv` |
| **TOTAL**      | **~67 840**|                            |

### Paso 2 — Generar el informe PDF

```bash
python generar_informe_pdf.py
```

Genera `Informe_Carga_DW_Ventas.pdf` con portada, descripción de tablas,
diagrama ER, estadísticas ETL, vistas analíticas y conclusiones.

---

## Esquema de la base de datos

### Dimensiones

| Dimensión | Descripción | Registros |
|-----------|-------------|-----------|
| `DIM_FECHA` | Calendario Sep 2023–Sep 2025 con indicadores de feriados y fines de semana | 760 |
| `DIM_PRODUCTO` | Catálogo de 2 000 productos en 7 categorías con precio y proveedor (desde CSV) | 2 000 |
| `DIM_CLIENTE` | 5 000 clientes de múltiples países segmentados por tipo y perfil (desde CSV) | 5 000 |
| `DIM_VENDEDOR` | 30 vendedores organizados por región y zona | 30 |
| `DIM_GEOGRAFIA` | 50 ciudades de LATAM y España con coordenadas reales | 50 |

### Tabla de hechos

`FACT_VENTAS` — ~60 000 transacciones reales con métricas: cantidad, precio, descuento, subtotal, impuesto y total. Generada uniendo `orders.csv` y `order_details.csv`.

### Vistas analíticas

| Vista | Propósito |
|-------|-----------|
| `VW_VENTAS_POR_PRODUCTO` | Ingresos y unidades por producto |
| `VW_VENTAS_POR_CLIENTE` | Historial y valor por cliente |
| `VW_TENDENCIA_MENSUAL` | Evolución mensual de ventas |
| `VW_VENTAS_POR_REGION` | Distribución geográfica de ingresos |
| `VW_TOP5_PRODUCTOS` | Ranking de productos más rentables |
| `VW_TOP5_CLIENTES` | Ranking de clientes de mayor valor |

---

## Migración a MySQL

El script ETL usa SQLite para portabilidad local. Para producción con MySQL 8.x:

1. Crear la base de datos: ejecutar `script_DW_ventas.sql` en MySQL
2. En `etl_carga_dimensiones.py`, descomentar el bloque MySQL y comentar SQLite:

```python
# SQLite (comentar para producción)
# conn = sqlite3.connect(DB_FILE)

# MySQL (descomentar para producción)
import mysql.connector
conn = mysql.connector.connect(**MYSQL_CONFIG)
```

3. Instalar el driver: `pip install mysql-connector-python`

---

## Fuentes de datos simuladas

Los datos de prueba replican tres orígenes de datos heterogéneos:

- **CSV** — archivos planos exportados desde sistemas legados
- **API** — endpoints REST de sistemas externos
- **BD_EXTERNA** — bases de datos relacionales de terceros

---

## Licencia

MIT — libre uso para fines académicos y educativos.
