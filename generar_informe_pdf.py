import sqlite3
import os
import time
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Flowable,
)
from reportlab.platypus import Image as RLImage
from reportlab.pdfgen import canvas

DB_FILE    = "dw_ventas.db"
OUTPUT_PDF = "Informe_Carga_DW_Ventas.pdf"
DER_IMAGE  = "DER_SistemaVentas.png"

AZUL_OSCURO = colors.HexColor("#2E4057")
AZUL_MEDIO  = colors.HexColor("#4A7098")
GRIS_CLARO  = colors.HexColor("#F2F4F6")
GRIS_LINEA  = colors.HexColor("#CCCCCC")
BLANCO      = colors.white
NARANJA     = colors.HexColor("#E8833A")

PAGE_W, PAGE_H = A4
MARGEN = 2.0 * cm

estilos = getSampleStyleSheet()


def _estilo(name, parent="Normal", **kwargs):
    return ParagraphStyle(name=name, parent=estilos[parent], **kwargs)


EST_TITULO_PORT = _estilo("TituloPort", "Title",
                           fontSize=22, textColor=BLANCO, alignment=TA_CENTER,
                           spaceAfter=8, leading=28)
EST_SUBTITULO_P = _estilo("SubtPort", "Normal",
                           fontSize=14, textColor=colors.HexColor("#BDD5EA"),
                           alignment=TA_CENTER, spaceAfter=4)
EST_META_PORT   = _estilo("MetaPort", "Normal",
                           fontSize=11, textColor=BLANCO, alignment=TA_CENTER,
                           spaceAfter=3)
EST_H1          = _estilo("H1", "Heading1",
                           fontSize=14, textColor=AZUL_OSCURO,
                           spaceBefore=14, spaceAfter=6, leading=18)
EST_H2          = _estilo("H2", "Heading2",
                           fontSize=11, textColor=AZUL_MEDIO,
                           spaceBefore=10, spaceAfter=4)
EST_NORMAL      = _estilo("Normal2", "Normal",
                           fontSize=9.5, leading=14, spaceAfter=4)
EST_JUSTIF      = _estilo("Justif", "Normal",
                           fontSize=9.5, leading=14, spaceAfter=4,
                           alignment=TA_JUSTIFY)
EST_TABLA_HDR   = _estilo("TabHdr", "Normal",
                           fontSize=9, textColor=BLANCO, alignment=TA_CENTER)
EST_TABLA_CELL  = _estilo("TabCell", "Normal",
                           fontSize=8.5, alignment=TA_LEFT, leading=12)
EST_TABLA_CELLC = _estilo("TabCellC", "Normal",
                           fontSize=8.5, alignment=TA_CENTER, leading=12)
EST_PIE         = _estilo("Pie", "Normal",
                           fontSize=8, textColor=colors.grey, alignment=TA_CENTER)


def estilo_tabla_base(col_widths, header_bg=AZUL_OSCURO):
    return TableStyle([
        ("BACKGROUND",     (0, 0), (-1,  0), header_bg),
        ("TEXTCOLOR",      (0, 0), (-1,  0), BLANCO),
        ("FONTNAME",       (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1,  0), 9),
        ("ALIGN",          (0, 0), (-1,  0), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
        ("FONTNAME",       (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 1), (-1, -1), 8.5),
        ("GRID",           (0, 0), (-1, -1), 0.4, GRIS_LINEA),
        ("LEFTPADDING",    (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 5),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ])


class NumeradorPaginas:
    def __init__(self, total_pages=0):
        self.total = total_pages

    def __call__(self, canv: canvas.Canvas, doc):
        canv.saveState()
        w, h = A4

        canv.setFillColor(AZUL_OSCURO)
        canv.rect(MARGEN, h - MARGEN - 0.7*cm, w - 2*MARGEN, 0.7*cm, fill=1, stroke=0)
        canv.setFillColor(BLANCO)
        canv.setFont("Helvetica-Bold", 8)
        canv.drawString(MARGEN + 0.2*cm, h - MARGEN - 0.45*cm,
                        "DW Ventas — Sistema de Análisis de Ventas")
        canv.setFont("Helvetica", 8)
        canv.drawRightString(w - MARGEN - 0.2*cm, h - MARGEN - 0.45*cm,
                             "Big Data / Electiva 1  |  Actividad 3.1")

        canv.setFillColor(GRIS_LINEA)
        canv.rect(MARGEN, MARGEN, w - 2*MARGEN, 0.6*cm, fill=1, stroke=0)
        canv.setFillColor(colors.HexColor("#555555"))
        canv.setFont("Helvetica", 7.5)
        canv.drawCentredString(
            w / 2, MARGEN + 0.15*cm,
            f"Actividad 3.1 – Modelado BD Sistema de Ventas  |  Página {doc.page} de {self.total}",
        )
        canv.restoreState()


def construir_portada(elements):
    class FondoPortada(Flowable):
        def __init__(self):
            Flowable.__init__(self)
            self.width = 0
            self.height = 0

        def draw(self):
            c = self.canv
            c.saveState()
            c.setFillColor(AZUL_OSCURO)
            c.rect(-MARGEN, -(PAGE_H - MARGEN), PAGE_W, PAGE_H, fill=1, stroke=0)
            c.setFillColor(AZUL_MEDIO)
            c.rect(-MARGEN, PAGE_H - MARGEN - 5.5*cm, PAGE_W, 5.5*cm, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#1A2B3C"))
            c.rect(-MARGEN, -MARGEN, PAGE_W, 3*cm, fill=1, stroke=0)
            c.restoreState()

    elements.append(FondoPortada())
    elements.append(Spacer(1, 3.5*cm))

    badge_data = [["DW"]]
    badge = Table(badge_data, colWidths=[3*cm], rowHeights=[3*cm])
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), AZUL_MEDIO),
        ("TEXTCOLOR",     (0, 0), (0, 0), BLANCO),
        ("FONTNAME",      (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (0, 0), 28),
        ("ALIGN",         (0, 0), (0, 0), "CENTER"),
        ("VALIGN",        (0, 0), (0, 0), "MIDDLE"),
        ("ROUNDEDCORNERS",(0, 0), (0, 0), 8),
        ("BOX",           (0, 0), (0, 0), 2, NARANJA),
    ]))
    elements.append(Table([[badge]], colWidths=[PAGE_W - 2*MARGEN]))
    elements.append(Spacer(1, 1.2*cm))

    def p(text, style):
        return Paragraph(text, style)

    elements.append(p("DATA WAREHOUSE", EST_TITULO_PORT))
    elements.append(p("Sistema de Análisis de Ventas", EST_SUBTITULO_P))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="70%", thickness=1.5, color=NARANJA,
                                hAlign="CENTER", spaceAfter=12))
    elements.append(p("Informe de Carga de Dimensiones", EST_SUBTITULO_P))
    elements.append(p("Actividad 3.1", EST_META_PORT))
    elements.append(Spacer(1, 1.5*cm))

    meta = [
        ["Estudiante:", "César Jasser de Jesús"],
        ["Matrícula:",  "#2023-1747"],
        ["Materia:",    "Big Data / Electiva 1"],
        ["Profesor:",   "Francis Ramírez"],
        ["Fecha:",      datetime.now().strftime("%d de %B de %Y — %H:%M")],
    ]
    tbl = Table(meta, colWidths=[4.5*cm, 9*cm])
    tbl.setStyle(TableStyle([
        ("TEXTCOLOR",       (0, 0), (0, -1), colors.HexColor("#BDD5EA")),
        ("TEXTCOLOR",       (1, 0), (1, -1), BLANCO),
        ("FONTNAME",        (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",        (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",        (0, 0), (-1, -1), 10.5),
        ("LEADING",         (0, 0), (-1, -1), 16),
        ("ALIGN",           (0, 0), (0, -1), "RIGHT"),
        ("ALIGN",           (1, 0), (1, -1), "LEFT"),
        ("TOPPADDING",      (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",   (0, 0), (-1, -1), 3),
    ]))
    elements.append(tbl)
    elements.append(PageBreak())


def seccion_descripcion(elements):
    elements.append(Paragraph("1. Descripción del Proyecto", EST_H1))
    elements.append(HRFlowable(width="100%", thickness=1, color=AZUL_OSCURO, spaceAfter=8))

    texto = [
        ("Contexto y Objetivo", """
El presente proyecto consiste en el diseño e implementación de un <b>Data Warehouse (DW)</b>
orientado al análisis de ventas de una empresa comercial con presencia en múltiples países
de Latinoamérica y España. El objetivo central es centralizar la información transaccional
dispersa en distintos sistemas fuente (ERP, CRM, archivos CSV, APIs externas) en un
repositorio unificado que permita realizar análisis multidimensionales de alto rendimiento.
        """),
        ("Modelo Elegido: Star Schema", """
Se optó por el modelo <b>Star Schema</b> (esquema estrella) por las siguientes razones:
<br/>• <b>Simplicidad de consultas</b>: Las tablas de dimensiones se unen directamente a la
tabla de hechos, reduciendo la complejidad de los JOINs y mejorando el rendimiento.
<br/>• <b>Compatibilidad con herramientas BI</b>: Power BI, Tableau y otros motores de
visualización están optimizados para este modelo.
<br/>• <b>Facilidad de mantenimiento</b>: La separación clara entre hechos y dimensiones
facilita la incorporación de nuevas métricas sin reestructurar el modelo.
<br/>• <b>Rendimiento en lecturas analíticas</b>: Al desnormalizar las dimensiones se
minimizan los JOINs necesarios para consultas agregadas.
        """),
        ("Estrategia de Carga (SCD Tipo 1)", """
Las dimensiones implementan <b>Slowly Changing Dimensions Tipo 1</b>: cuando un atributo
cambia, el registro se sobreescribe sin conservar historial. Esta decisión es apropiada para
el alcance del proyecto, donde la trazabilidad histórica no es un requisito crítico.
La tabla de hechos FACT_VENTAS almacena métricas aditivas (cantidad, subtotal, impuesto,
total_venta) que pueden ser sumadas en cualquier combinación dimensional.
        """),
    ]

    for titulo, cuerpo in texto:
        elements.append(Paragraph(titulo, EST_H2))
        elements.append(Paragraph(cuerpo.strip(), EST_JUSTIF))
        elements.append(Spacer(1, 0.3*cm))


DEFINICION_TABLAS = {
    "DIM_FECHA": {
        "proposito": "Dimensión temporal con granularidad diaria. Permite análisis por año, trimestre, mes, semana y día, incluyendo indicadores de fin de semana y feriados.",
        "campos": [
            ("id_fecha",      "INTEGER",     "Clave primaria — formato YYYYMMDD"),
            ("fecha",         "TEXT/DATE",   "Fecha completa ISO (YYYY-MM-DD)"),
            ("anio",          "INTEGER",     "Año (ej. 2024)"),
            ("trimestre",     "INTEGER",     "Trimestre 1–4"),
            ("mes",           "INTEGER",     "Número de mes 1–12"),
            ("nombre_mes",    "TEXT",        "Nombre del mes en español"),
            ("semana",        "INTEGER",     "Número de semana ISO"),
            ("dia",           "INTEGER",     "Día del mes 1–31"),
            ("dia_semana",    "TEXT",        "Nombre del día (Lunes…Domingo)"),
            ("es_fin_semana", "BIT/INTEGER", "1 = Sábado o Domingo"),
            ("es_feriado",    "BIT/INTEGER", "1 = Día feriado oficial"),
        ],
        "query_muestra": "SELECT id_fecha, fecha, anio, trimestre, nombre_mes, dia_semana, es_fin_semana, es_feriado FROM DIM_FECHA LIMIT 5",
    },
    "DIM_PRODUCTO": {
        "proposito": "Dimensión de productos del catálogo comercial. Incluye categoría, subcategoría, precio base y datos del proveedor para análisis por línea de producto.",
        "campos": [
            ("id_producto",     "INTEGER", "Clave primaria autoincremental"),
            ("codigo_sku",      "TEXT",    "Código único de inventario"),
            ("nombre_producto", "TEXT",    "Nombre comercial del producto"),
            ("categoria",       "TEXT",    "Categoría principal"),
            ("subcategoria",    "TEXT",    "Subcategoría específica"),
            ("precio_base",     "REAL",    "Precio de lista en USD"),
            ("unidad_medida",   "TEXT",    "Unidad de medida (Pieza, Kg, etc.)"),
            ("proveedor",       "TEXT",    "Nombre del proveedor"),
            ("pais_origen",     "TEXT",    "País de fabricación"),
            ("activo",          "BIT",     "1 = Producto disponible"),
            ("fuente_datos",    "TEXT",    "Origen del registro (CSV/API/BD_EXTERNA)"),
            ("fecha_carga",     "TEXT",    "Timestamp de inserción ETL"),
        ],
        "query_muestra": "SELECT id_producto, codigo_sku, nombre_producto, categoria, precio_base, fuente_datos FROM DIM_PRODUCTO LIMIT 5",
    },
    "DIM_CLIENTE": {
        "proposito": "Dimensión de clientes. Permite segmentar ventas por tipo de cliente (Persona Física / Empresa), segmento comercial y ubicación geográfica.",
        "campos": [
            ("id_cliente",     "INTEGER", "Clave primaria autoincremental"),
            ("codigo_cliente", "TEXT",    "Código único de cliente"),
            ("nombre_cliente", "TEXT",    "Nombre o razón social"),
            ("tipo_cliente",   "TEXT",    "Persona Física o Empresa"),
            ("segmento",       "TEXT",    "Premium / VIP / Estándar / Corporativo / Minorista"),
            ("email",          "TEXT",    "Correo electrónico"),
            ("pais",           "TEXT",    "País de residencia"),
            ("region",         "TEXT",    "Estado / Departamento / Región"),
            ("ciudad",         "TEXT",    "Ciudad"),
            ("activo",         "BIT",     "1 = Cliente activo"),
            ("fuente_datos",   "TEXT",    "Origen del registro"),
            ("fecha_carga",    "TEXT",    "Timestamp de inserción ETL"),
        ],
        "query_muestra": "SELECT id_cliente, codigo_cliente, nombre_cliente, tipo_cliente, segmento, pais FROM DIM_CLIENTE LIMIT 5",
    },
    "DIM_VENDEDOR": {
        "proposito": "Dimensión de vendedores. Permite analizar el rendimiento por región, zona geográfica de ventas y cargo dentro de la estructura comercial.",
        "campos": [
            ("id_vendedor",       "INTEGER", "Clave primaria autoincremental"),
            ("codigo_vendedor",   "TEXT",    "Código único del vendedor"),
            ("nombre_vendedor",   "TEXT",    "Nombre(s)"),
            ("apellido_vendedor", "TEXT",    "Apellido(s)"),
            ("email",             "TEXT",    "Correo electrónico corporativo"),
            ("region",            "TEXT",    "Región de cobertura (Norte/Sur/Este/Oeste/Centro)"),
            ("zona",              "TEXT",    "Zona específica dentro de la región"),
            ("cargo",             "TEXT",    "Cargo o puesto"),
            ("fecha_ingreso",     "TEXT",    "Fecha de contratación"),
            ("activo",            "BIT",     "1 = Vendedor activo"),
            ("fecha_carga",       "TEXT",    "Timestamp de inserción ETL"),
        ],
        "query_muestra": "SELECT id_vendedor, codigo_vendedor, nombre_vendedor, apellido_vendedor, region, cargo FROM DIM_VENDEDOR LIMIT 5",
    },
    "DIM_GEOGRAFIA": {
        "proposito": "Dimensión geográfica para análisis espacial de ventas. Cubre países de Latinoamérica y España con coordenadas reales para integración con herramientas de mapas.",
        "campos": [
            ("id_geografia", "INTEGER", "Clave primaria autoincremental"),
            ("pais",         "TEXT",    "Nombre del país"),
            ("codigo_pais",  "TEXT",    "Código ISO 3166-1 alfa-3"),
            ("region",       "TEXT",    "Región / Estado / Departamento"),
            ("ciudad",       "TEXT",    "Ciudad principal"),
            ("zona_horaria", "TEXT",    "Zona horaria (ej. America/Bogota)"),
            ("continente",   "TEXT",    "América o Europa"),
            ("latitud",      "REAL",    "Coordenada latitud decimal"),
            ("longitud",     "REAL",    "Coordenada longitud decimal"),
        ],
        "query_muestra": "SELECT id_geografia, pais, codigo_pais, region, ciudad, continente FROM DIM_GEOGRAFIA LIMIT 5",
    },
    "FACT_VENTAS": {
        "proposito": "Tabla de hechos central. Registra cada transacción de venta con claves foráneas a las cinco dimensiones y las métricas numéricas aditivas.",
        "campos": [
            ("id_venta",        "BIGINT",             "Clave primaria autoincremental"),
            ("id_fecha",        "FK→DIM_FECHA",       "Fecha de la transacción"),
            ("id_producto",     "FK→DIM_PRODUCTO",    "Producto vendido"),
            ("id_cliente",      "FK→DIM_CLIENTE",     "Cliente comprador"),
            ("id_vendedor",     "FK→DIM_VENDEDOR",    "Vendedor responsable"),
            ("id_geografia",    "FK→DIM_GEOGRAFIA",   "Ubicación de la venta"),
            ("numero_factura",  "TEXT",               "Número de comprobante fiscal"),
            ("cantidad",        "INTEGER",            "Unidades vendidas"),
            ("precio_unitario", "REAL",               "Precio de venta unitario en USD"),
            ("descuento",       "REAL",               "Porcentaje de descuento aplicado"),
            ("subtotal",        "REAL",               "cantidad × precio_unitario"),
            ("impuesto",        "REAL",               "subtotal × 18%"),
            ("total_venta",     "REAL",               "subtotal + impuesto − descuento"),
            ("moneda",          "CHAR(3)",            "Divisa — siempre USD"),
            ("fuente_datos",    "TEXT",               "Sistema origen del registro"),
        ],
        "query_muestra": "SELECT id_venta, numero_factura, cantidad, precio_unitario, descuento, total_venta, moneda FROM FACT_VENTAS LIMIT 5",
    },
}


def seccion_tablas(elements, conn):
    elements.append(Paragraph("2. Descripción de Tablas Cargadas", EST_H1))
    elements.append(HRFlowable(width="100%", thickness=1, color=AZUL_OSCURO, spaceAfter=8))

    cur = conn.cursor()

    for tabla, info in DEFINICION_TABLAS.items():
        elements.append(Paragraph(tabla, EST_H2))
        elements.append(Paragraph(info["proposito"], EST_JUSTIF))
        elements.append(Spacer(1, 0.2*cm))

        count = cur.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        elements.append(Paragraph(f"<b>Total de registros cargados:</b> {count:,}", EST_NORMAL))
        elements.append(Spacer(1, 0.2*cm))

        hdr = [
            Paragraph("<b>Campo</b>",       EST_TABLA_HDR),
            Paragraph("<b>Tipo</b>",        EST_TABLA_HDR),
            Paragraph("<b>Descripción</b>", EST_TABLA_HDR),
        ]
        filas_def = [hdr] + [
            [Paragraph(c, EST_TABLA_CELL), Paragraph(t, EST_TABLA_CELLC), Paragraph(d, EST_TABLA_CELL)]
            for c, t, d in info["campos"]
        ]
        col_widths_def = [4*cm, 3.8*cm, 9*cm]
        tbl_def = Table(filas_def, colWidths=col_widths_def, repeatRows=1)
        tbl_def.setStyle(estilo_tabla_base(col_widths_def))
        elements.append(tbl_def)
        elements.append(Spacer(1, 0.4*cm))

        elements.append(Paragraph("<b>Muestra de datos (5 registros):</b>", EST_NORMAL))
        try:
            cur.execute(info["query_muestra"])
            col_names = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            hdr_m = [Paragraph(f"<b>{c}</b>", EST_TABLA_HDR) for c in col_names]
            filas_m = [hdr_m] + [
                [Paragraph(str(v) if v is not None else "—", EST_TABLA_CELLC) for v in row]
                for row in rows
            ]

            col_w = (PAGE_W - 2*MARGEN) / len(col_names)
            col_widths_m = [col_w] * len(col_names)
            tbl_m = Table(filas_m, colWidths=col_widths_m, repeatRows=1)
            tbl_m.setStyle(estilo_tabla_base(col_widths_m, header_bg=AZUL_MEDIO))
            elements.append(tbl_m)
        except Exception as e:
            elements.append(Paragraph(f"No se pudo obtener la muestra: {e}", EST_NORMAL))

        elements.append(Spacer(1, 0.6*cm))


def seccion_diagrama(elements):
    elements.append(Paragraph("3. Diagrama Entidad-Relación (Star Schema)", EST_H1))
    elements.append(HRFlowable(width="100%", thickness=1, color=AZUL_OSCURO, spaceAfter=8))

    if os.path.exists(DER_IMAGE):
        img = RLImage(DER_IMAGE, width=PAGE_W - 2*MARGEN - 1*cm,
                      height=10*cm, kind="proportional")
        elements.append(img)
        elements.append(Paragraph(
            "Figura 1. Diagrama Entidad-Relación del Star Schema — DW Ventas",
            _estilo("FigCapt", "Normal", fontSize=8.5, textColor=colors.grey,
                    alignment=TA_CENTER, spaceAfter=6),
        ))
    else:
        elements.append(Paragraph(
            "El archivo <i>DER_SistemaVentas.png</i> no se encontró en el directorio. "
            "A continuación se presenta una representación esquemática del modelo:",
            EST_NORMAL,
        ))
        elements.append(Spacer(1, 0.3*cm))

        schema = [
            ["", "DIM_FECHA", "", "DIM_PRODUCTO", ""],
            ["", "(id_fecha PK)", "", "(id_producto PK)", ""],
            ["DIM_VENDEDOR", "←", "FACT_VENTAS", "→", "DIM_CLIENTE"],
            ["(id_vendedor PK)", "", "(id_venta PK)", "", "(id_cliente PK)"],
            ["", "DIM_GEOGRAFIA", "", "", ""],
            ["", "(id_geografia PK)", "", "", ""],
        ]
        tbl_schema = Table(schema, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
        tbl_schema.setStyle(TableStyle([
            ("BACKGROUND",    (2, 2), (2, 3), AZUL_OSCURO),
            ("TEXTCOLOR",     (2, 2), (2, 3), BLANCO),
            ("BACKGROUND",    (1, 0), (1, 1), AZUL_MEDIO),
            ("BACKGROUND",    (3, 0), (3, 1), AZUL_MEDIO),
            ("BACKGROUND",    (0, 2), (0, 3), AZUL_MEDIO),
            ("BACKGROUND",    (4, 2), (4, 3), AZUL_MEDIO),
            ("BACKGROUND",    (1, 4), (1, 5), AZUL_MEDIO),
            ("TEXTCOLOR",     (0, 0), (-1, -1), BLANCO),
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [GRIS_CLARO, BLANCO, AZUL_OSCURO, GRIS_CLARO, BLANCO, GRIS_CLARO]),
            ("GRID",          (0, 0), (-1, -1), 0.3, GRIS_LINEA),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(tbl_schema)

    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(
        "El esquema estrella posiciona la tabla <b>FACT_VENTAS</b> en el centro, "
        "conectada mediante claves foráneas a las cinco dimensiones: "
        "<b>DIM_FECHA</b>, <b>DIM_PRODUCTO</b>, <b>DIM_CLIENTE</b>, "
        "<b>DIM_VENDEDOR</b> y <b>DIM_GEOGRAFIA</b>.",
        EST_JUSTIF,
    ))


def seccion_estadisticas(elements, conn, inicio_generacion: float):
    elements.append(Paragraph("4. Estadísticas del Proceso ETL", EST_H1))
    elements.append(HRFlowable(width="100%", thickness=1, color=AZUL_OSCURO, spaceAfter=8))

    cur = conn.cursor()

    tablas = ["DIM_FECHA", "DIM_PRODUCTO", "DIM_CLIENTE",
              "DIM_VENDEDOR", "DIM_GEOGRAFIA", "FACT_VENTAS"]
    tipos = {
        "DIM_FECHA": "Dimensión", "DIM_PRODUCTO": "Dimensión",
        "DIM_CLIENTE": "Dimensión", "DIM_VENDEDOR": "Dimensión",
        "DIM_GEOGRAFIA": "Dimensión", "FACT_VENTAS": "Hechos",
    }

    hdr = [Paragraph(f"<b>{h}</b>", EST_TABLA_HDR)
           for h in ["Tabla", "Registros Cargados", "Tipo"]]
    filas = [hdr]
    total_regs = 0
    for t in tablas:
        c = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        total_regs += c
        filas.append([
            Paragraph(t, EST_TABLA_CELL),
            Paragraph(f"{c:,}", EST_TABLA_CELLC),
            Paragraph(tipos[t], EST_TABLA_CELLC),
        ])
    filas.append([
        Paragraph("<b>TOTAL</b>", EST_TABLA_CELL),
        Paragraph(f"<b>{total_regs:,}</b>", EST_TABLA_CELLC),
        Paragraph("", EST_TABLA_CELLC),
    ])
    tbl = Table(filas, colWidths=[7*cm, 5*cm, 5*cm], repeatRows=1)
    tbl.setStyle(estilo_tabla_base([7*cm, 5*cm, 5*cm]))
    elements.append(tbl)
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("<b>Distribución por Fuente de Datos:</b>", EST_H2))
    fuentes_tablas = ["DIM_PRODUCTO", "DIM_CLIENTE", "FACT_VENTAS"]
    hdr_f = [Paragraph(f"<b>{h}</b>", EST_TABLA_HDR)
              for h in ["Tabla", "CSV", "API", "BD_EXTERNA", "Total"]]
    filas_f = [hdr_f]
    for t in fuentes_tablas:
        row = {"CSV": 0, "API": 0, "BD_EXTERNA": 0}
        for fuente, cnt in cur.execute(
            f"SELECT fuente_datos, COUNT(*) FROM {t} GROUP BY fuente_datos"
        ).fetchall():
            if fuente in row:
                row[fuente] = cnt
        total = sum(row.values())
        filas_f.append([
            Paragraph(t, EST_TABLA_CELL),
            Paragraph(str(row["CSV"]), EST_TABLA_CELLC),
            Paragraph(str(row["API"]), EST_TABLA_CELLC),
            Paragraph(str(row["BD_EXTERNA"]), EST_TABLA_CELLC),
            Paragraph(str(total), EST_TABLA_CELLC),
        ])
    tbl_f = Table(filas_f, colWidths=[5*cm, 3*cm, 3*cm, 3.5*cm, 3*cm], repeatRows=1)
    tbl_f.setStyle(estilo_tabla_base([5*cm, 3*cm, 3*cm, 3.5*cm, 3*cm]))
    elements.append(tbl_f)
    elements.append(Spacer(1, 0.5*cm))

    tiempo_gen = time.perf_counter() - inicio_generacion
    meta_data = [
        ["Fecha de ejecución:",     datetime.now().strftime("%Y-%m-%d")],
        ["Hora de ejecución:",      datetime.now().strftime("%H:%M:%S")],
        ["Tiempo total del ETL:",   "Ver salida de etl_carga_dimensiones.py"],
        ["Tiempo generac. PDF:",    f"{tiempo_gen:.2f} segundos"],
        ["Motor de base de datos:", "SQLite 3 (portabilidad local)"],
        ["Motor objetivo:",         "MySQL 8.x (producción)"],
        ["Total registros:",        f"{total_regs:,}"],
    ]
    elements.append(Paragraph("<b>Metadatos de Ejecución:</b>", EST_H2))
    tbl_meta = Table(meta_data, colWidths=[6*cm, 11.5*cm])
    tbl_meta.setStyle(TableStyle([
        ("FONTNAME",        (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",        (0, 0), (-1, -1), 9.5),
        ("LEADING",         (0, 0), (-1, -1), 14),
        ("ROWBACKGROUNDS",  (0, 0), (-1, -1), [GRIS_CLARO, BLANCO]),
        ("GRID",            (0, 0), (-1, -1), 0.4, GRIS_LINEA),
        ("LEFTPADDING",     (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",    (0, 0), (-1, -1), 6),
        ("TOPPADDING",      (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",   (0, 0), (-1, -1), 4),
    ]))
    elements.append(tbl_meta)


VISTAS = [
    ("VW_VENTAS_POR_PRODUCTO",
     "Agrega las ventas por producto, calculando número de transacciones, "
     "unidades vendidas, ingresos totales y precio promedio. Útil para análisis "
     "de catálogo y rotación de inventario."),
    ("VW_VENTAS_POR_CLIENTE",
     "Resume el historial de compras por cliente mostrando número de transacciones, "
     "total gastado y fecha de última compra. Permite identificar clientes de mayor valor."),
    ("VW_TENDENCIA_MENSUAL",
     "Muestra la evolución mensual de ventas con número de transacciones, "
     "ingresos por mes y ticket promedio. Fundamental para análisis de estacionalidad."),
    ("VW_VENTAS_POR_REGION",
     "Consolida ventas por país, región y continente. Permite análisis geográfico "
     "para decisiones de expansión y asignación de recursos comerciales."),
    ("VW_TOP5_PRODUCTOS",
     "Ranking de los 5 productos más rentables ordenados por ingresos totales. "
     "Actualización dinámica con cada nueva venta registrada."),
    ("VW_TOP5_CLIENTES",
     "Ranking de los 5 clientes de mayor valor por gasto total acumulado. "
     "Útil para programas de fidelización y atención preferencial."),
]


def seccion_vistas(elements):
    elements.append(Paragraph("5. Vistas Analíticas", EST_H1))
    elements.append(HRFlowable(width="100%", thickness=1, color=AZUL_OSCURO, spaceAfter=8))
    elements.append(Paragraph(
        "Se crearon seis vistas SQL que encapsulan las consultas analíticas más frecuentes, "
        "simplificando su uso desde herramientas de BI y aplicaciones cliente:",
        EST_JUSTIF,
    ))
    elements.append(Spacer(1, 0.3*cm))

    hdr = [Paragraph(f"<b>{h}</b>", EST_TABLA_HDR) for h in ["Vista", "Descripción y Propósito"]]
    filas = [hdr] + [
        [Paragraph(nombre, EST_TABLA_CELL), Paragraph(desc, EST_TABLA_CELL)]
        for nombre, desc in VISTAS
    ]
    tbl = Table(filas, colWidths=[5.5*cm, 12*cm], repeatRows=1)
    tbl.setStyle(estilo_tabla_base([5.5*cm, 12*cm]))
    elements.append(tbl)


def seccion_conclusiones(elements):
    elements.append(Paragraph("6. Conclusiones", EST_H1))
    elements.append(HRFlowable(width="100%", thickness=1, color=AZUL_OSCURO, spaceAfter=8))

    conclusiones = [
        ("Implementación exitosa del Star Schema",
         "El modelo estrella diseñado cumple con los requerimientos de análisis multidimensional "
         "establecidos. La separación clara entre la tabla de hechos y las dimensiones facilita "
         "la incorporación de nuevas métricas y atributos sin impactar la estructura central."),
        ("Proceso ETL funcional y reproducible",
         "El script etl_carga_dimensiones.py genera datos representativos para 1,596 registros "
         "distribuidos en cinco dimensiones y la tabla de hechos, con tiempos de carga inferiores "
         "a 5 segundos. La estructura modular del código facilita su adaptación a fuentes de datos reales."),
        ("Diversidad de fuentes de datos",
         "La simulación de tres fuentes distintas (CSV, API, BD_EXTERNA) en las dimensiones y la "
         "tabla de hechos refleja un escenario realista de integración empresarial, donde los datos "
         "provienen de sistemas heterogéneos que deben ser consolidados."),
        ("Portabilidad del prototipo",
         "El uso de SQLite como motor de desarrollo permite ejecutar y demostrar el DW sin "
         "infraestructura adicional. La migración a MySQL 8.x en producción requiere únicamente "
         "cambiar la cadena de conexión en el script, dado que el DDL es compatible."),
        ("Capacidades analíticas habilitadas",
         "Las seis vistas implementadas cubren los casos de uso principales: análisis por producto, "
         "cliente, período temporal, región geográfica y rankings. Estas vistas constituyen la base "
         "para la construcción de dashboards en herramientas como Power BI o Tableau."),
    ]

    for i, (titulo, texto) in enumerate(conclusiones, 1):
        elements.append(Paragraph(f"{i}. {titulo}", EST_H2))
        elements.append(Paragraph(texto, EST_JUSTIF))
        elements.append(Spacer(1, 0.2*cm))


def seccion_github(elements):
    elements.append(Paragraph("7. Repositorio GitHub", EST_H1))
    elements.append(HRFlowable(width="100%", thickness=1, color=AZUL_OSCURO, spaceAfter=8))

    elements.append(Paragraph(
        "El código fuente completo, el script SQL, los datos generados y este informe "
        "están disponibles en el siguiente repositorio público:",
        EST_JUSTIF,
    ))
    elements.append(Spacer(1, 0.5*cm))

    repo_data = [
        ["Repositorio:", "https://github.com/CJasserDeJesus/dw-ventas-actividad31"],
        ["Rama principal:", "main"],
        ["Licencia:", "MIT"],
    ]
    tbl = Table(repo_data, colWidths=[4*cm, 13.5*cm])
    tbl.setStyle(TableStyle([
        ("FONTNAME",        (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",        (0, 0), (-1, -1), 10),
        ("LEADING",         (0, 0), (-1, -1), 16),
        ("ROWBACKGROUNDS",  (0, 0), (-1, -1), [GRIS_CLARO, BLANCO, GRIS_CLARO]),
        ("GRID",            (0, 0), (-1, -1), 0.4, GRIS_LINEA),
        ("LEFTPADDING",     (0, 0), (-1, -1), 8),
        ("TOPPADDING",      (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",   (0, 0), (-1, -1), 6),
        ("TEXTCOLOR",       (1, 0), (1, 0), AZUL_MEDIO),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("<b>Contenido del repositorio:</b>", EST_H2))
    archivos = [
        ("etl_carga_dimensiones.py",   "Script ETL principal — crea tablas y carga datos de prueba"),
        ("generar_informe_pdf.py",      "Generador del informe PDF (este documento)"),
        ("script_DW_ventas.sql",        "DDL completo para MySQL 8.x con vistas analíticas"),
        ("DER_SistemaVentas.png",       "Diagrama Entidad-Relación del Star Schema"),
        ("Informe_Carga_DW_Ventas.pdf", "Informe de actividad generado automáticamente"),
        ("requirements.txt",            "Dependencias Python del proyecto"),
        ("README.md",                   "Documentación del proyecto"),
    ]
    hdr = [Paragraph(f"<b>{h}</b>", EST_TABLA_HDR) for h in ["Archivo", "Descripción"]]
    filas = [hdr] + [
        [Paragraph(a, EST_TABLA_CELL), Paragraph(d, EST_TABLA_CELL)]
        for a, d in archivos
    ]
    tbl_arch = Table(filas, colWidths=[6*cm, 11.5*cm], repeatRows=1)
    tbl_arch.setStyle(estilo_tabla_base([6*cm, 11.5*cm]))
    elements.append(tbl_arch)


def _build_elements(conn, inicio):
    elements = []
    construir_portada(elements)
    seccion_descripcion(elements)
    elements.append(PageBreak())
    seccion_tablas(elements, conn)
    elements.append(PageBreak())
    seccion_diagrama(elements)
    elements.append(PageBreak())
    seccion_estadisticas(elements, conn, inicio)
    elements.append(PageBreak())
    seccion_vistas(elements)
    elements.append(PageBreak())
    seccion_conclusiones(elements)
    elements.append(PageBreak())
    seccion_github(elements)
    return elements


def _count_pages(elements):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=MARGEN, rightMargin=MARGEN,
                             topMargin=MARGEN + 1.2*cm, bottomMargin=MARGEN + 1.2*cm)
    doc.build(list(elements))
    return doc.page


def main():
    inicio = time.perf_counter()
    print(f"[INFO] Generando {OUTPUT_PDF}...")

    if not os.path.exists(DB_FILE):
        print(f"[ERROR] No se encontró {DB_FILE}. Ejecute primero etl_carga_dimensiones.py")
        return

    conn = sqlite3.connect(DB_FILE)
    try:
        elements = _build_elements(conn, inicio)
        total_pages = _count_pages(elements)

        elements = _build_elements(conn, inicio)
        numerador = NumeradorPaginas(total_pages)
        doc = SimpleDocTemplate(
            OUTPUT_PDF,
            pagesize=A4,
            leftMargin=MARGEN,
            rightMargin=MARGEN,
            topMargin=MARGEN + 1.2*cm,
            bottomMargin=MARGEN + 1.2*cm,
            title="Informe Carga DW Ventas — Actividad 3.1",
            author="César Jasser de Jesús",
            subject="Data Warehouse — Big Data / Electiva 1",
        )
        doc.build(elements, onFirstPage=numerador, onLaterPages=numerador)
    finally:
        conn.close()

    tiempo = time.perf_counter() - inicio
    print(f"[OK] PDF generado: {OUTPUT_PDF}  ({tiempo:.2f}s)")


if __name__ == "__main__":
    main()
