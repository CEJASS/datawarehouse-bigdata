import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

OUTPUT = "DER_SistemaVentas.png"

AZUL_OSCURO  = "#2E4057"
AZUL_MEDIO   = "#4A7098"
VERDE        = "#2A9D5C"
NARANJA      = "#E8833A"
VIOLETA      = "#7B2D8B"
ROJO         = "#C0392B"
BLANCO       = "#FFFFFF"
GRIS_FONDO   = "#F7F9FB"
GRIS_LINEA   = "#CBD5E1"
GRIS_CAMPO   = "#EEF2F6"
AMARILLO_PK  = "#FFF3CD"
TEXTO_OSCURO = "#1A2B3C"

TABLAS = {
    "FACT_VENTAS": {
        "color": AZUL_OSCURO,
        "campos": [
            ("PK", "id_venta"),
            ("FK", "id_fecha"),
            ("FK", "id_producto"),
            ("FK", "id_cliente"),
            ("FK", "id_vendedor"),
            ("FK", "id_geografia"),
            ("",   "numero_factura"),
            ("",   "cantidad"),
            ("",   "precio_unitario"),
            ("",   "descuento"),
            ("",   "subtotal"),
            ("",   "impuesto"),
            ("",   "total_venta"),
            ("",   "moneda"),
            ("",   "fuente_datos"),
        ],
    },
    "DIM_FECHA": {
        "color": AZUL_MEDIO,
        "campos": [
            ("PK", "id_fecha"),
            ("",   "fecha"),
            ("",   "anio"),
            ("",   "trimestre"),
            ("",   "mes"),
            ("",   "nombre_mes"),
            ("",   "semana"),
            ("",   "dia"),
            ("",   "dia_semana"),
            ("",   "es_fin_semana"),
            ("",   "es_feriado"),
        ],
    },
    "DIM_PRODUCTO": {
        "color": VERDE,
        "campos": [
            ("PK", "id_producto"),
            ("",   "codigo_sku"),
            ("",   "nombre_producto"),
            ("",   "categoria"),
            ("",   "subcategoria"),
            ("",   "precio_base"),
            ("",   "unidad_medida"),
            ("",   "proveedor"),
            ("",   "pais_origen"),
            ("",   "activo"),
            ("",   "fuente_datos"),
            ("",   "fecha_carga"),
        ],
    },
    "DIM_CLIENTE": {
        "color": VIOLETA,
        "campos": [
            ("PK", "id_cliente"),
            ("",   "codigo_cliente"),
            ("",   "nombre_cliente"),
            ("",   "tipo_cliente"),
            ("",   "segmento"),
            ("",   "email"),
            ("",   "pais"),
            ("",   "region"),
            ("",   "ciudad"),
            ("",   "activo"),
            ("",   "fuente_datos"),
            ("",   "fecha_carga"),
        ],
    },
    "DIM_VENDEDOR": {
        "color": NARANJA,
        "campos": [
            ("PK", "id_vendedor"),
            ("",   "codigo_vendedor"),
            ("",   "nombre_vendedor"),
            ("",   "apellido_vendedor"),
            ("",   "email"),
            ("",   "region"),
            ("",   "zona"),
            ("",   "cargo"),
            ("",   "fecha_ingreso"),
            ("",   "activo"),
            ("",   "fecha_carga"),
        ],
    },
    "DIM_GEOGRAFIA": {
        "color": ROJO,
        "campos": [
            ("PK", "id_geografia"),
            ("",   "pais"),
            ("",   "codigo_pais"),
            ("",   "region"),
            ("",   "ciudad"),
            ("",   "zona_horaria"),
            ("",   "continente"),
            ("",   "latitud"),
            ("",   "longitud"),
        ],
    },
}

POSICIONES = {
    "FACT_VENTAS":   (0.50, 0.50),
    "DIM_FECHA":     (0.50, 0.88),
    "DIM_PRODUCTO":  (0.08, 0.60),
    "DIM_CLIENTE":   (0.08, 0.28),
    "DIM_VENDEDOR":  (0.92, 0.60),
    "DIM_GEOGRAFIA": (0.92, 0.28),
}

ROW_H    = 0.018
HDR_H    = 0.030
BOX_W    = 0.165
FONT_HDR = 7.5
FONT_ROW = 6.2


def draw_table(ax, nombre, info, cx, cy):
    campos = info["campos"]
    n_rows = len(campos)
    total_h = HDR_H + n_rows * ROW_H + 0.006

    x = cx - BOX_W / 2
    y = cy + total_h / 2

    sombra = mpatches.FancyBboxPatch(
        (x + 0.003, y - total_h - 0.003), BOX_W, total_h,
        boxstyle="round,pad=0.004", linewidth=0,
        facecolor="#B0BEC5", alpha=0.35, zorder=1,
        transform=ax.transAxes,
    )
    ax.add_patch(sombra)

    header = mpatches.FancyBboxPatch(
        (x, y - HDR_H), BOX_W, HDR_H,
        boxstyle="round,pad=0.004", linewidth=1.2,
        edgecolor=info["color"], facecolor=info["color"], zorder=2,
        transform=ax.transAxes,
    )
    ax.add_patch(header)

    body = mpatches.FancyBboxPatch(
        (x, y - total_h), BOX_W, total_h - HDR_H,
        boxstyle="square,pad=0", linewidth=1.2,
        edgecolor=info["color"], facecolor=BLANCO, zorder=2,
        transform=ax.transAxes,
    )
    ax.add_patch(body)

    ax.text(
        cx, y - HDR_H / 2, nombre,
        ha="center", va="center",
        fontsize=FONT_HDR, fontweight="bold", color=BLANCO,
        zorder=3, transform=ax.transAxes,
        fontfamily="monospace",
    )

    for i, (badge, campo) in enumerate(campos):
        ry = y - HDR_H - (i + 0.5) * ROW_H
        row_bg = AMARILLO_PK if badge == "PK" else (GRIS_CAMPO if i % 2 == 0 else BLANCO)
        rect = mpatches.Rectangle(
            (x + 0.001, ry - ROW_H / 2), BOX_W - 0.002, ROW_H,
            facecolor=row_bg, linewidth=0, zorder=2,
            transform=ax.transAxes,
        )
        ax.add_patch(rect)

        if badge:
            badge_color = info["color"] if badge == "PK" else AZUL_MEDIO
            badge_rect = mpatches.FancyBboxPatch(
                (x + 0.004, ry - ROW_H / 2 + 0.002), 0.020, ROW_H - 0.004,
                boxstyle="round,pad=0.001", linewidth=0,
                facecolor=badge_color, alpha=0.85, zorder=3,
                transform=ax.transAxes,
            )
            ax.add_patch(badge_rect)
            ax.text(
                x + 0.014, ry, badge,
                ha="center", va="center",
                fontsize=5.0, fontweight="bold", color=BLANCO,
                zorder=4, transform=ax.transAxes,
            )
            text_x = x + 0.030
        else:
            text_x = x + 0.008

        ax.text(
            text_x, ry, campo,
            ha="left", va="center",
            fontsize=FONT_ROW, color=TEXTO_OSCURO,
            zorder=4, transform=ax.transAxes,
            fontfamily="monospace",
        )

    border = mpatches.FancyBboxPatch(
        (x, y - total_h), BOX_W, total_h,
        boxstyle="round,pad=0.004", linewidth=1.5,
        edgecolor=info["color"], facecolor="none", zorder=5,
        transform=ax.transAxes,
    )
    ax.add_patch(border)

    return x, y, total_h


def draw_arrow(ax, src_cx, src_cy, dst_cx, dst_cy, color):
    dx = dst_cx - src_cx
    dy = dst_cy - src_cy

    if abs(dx) > abs(dy):
        src_x = src_cx + (BOX_W / 2 + 0.004) * (1 if dx > 0 else -1)
        src_y = src_cy
        dst_x = dst_cx - (BOX_W / 2 + 0.004) * (1 if dx > 0 else -1)
        dst_y = dst_cy
    else:
        src_x = src_cx
        src_y = src_cy + (0.004) * (1 if dy > 0 else -1)
        dst_x = dst_cx
        dst_y = dst_cy - (0.004) * (1 if dy > 0 else -1)

    ax.annotate(
        "", xy=(dst_x, dst_y), xytext=(src_x, src_y),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=1.4,
            mutation_scale=10,
            connectionstyle="arc3,rad=0.0",
        ),
        zorder=1,
    )


def main():
    fig, ax = plt.subplots(figsize=(18, 12))
    fig.patch.set_facecolor(GRIS_FONDO)
    ax.set_facecolor(GRIS_FONDO)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.text(
        0.50, 0.965,
        "DATA WAREHOUSE — Sistema de Ventas  |  Star Schema",
        ha="center", va="center",
        fontsize=15, fontweight="bold", color=AZUL_OSCURO,
        fontfamily="sans-serif",
    )
    fig.text(
        0.50, 0.940,
        "Actividad 3.1  ·  Big Data / Electiva 1",
        ha="center", va="center",
        fontsize=9, color=AZUL_MEDIO,
        fontfamily="sans-serif",
    )

    ax.axhline(y=0.925, xmin=0.05, xmax=0.95, color=GRIS_LINEA, linewidth=1)

    for nombre, info in TABLAS.items():
        cx, cy = POSICIONES[nombre]
        draw_table(ax, nombre, info, cx, cy)

    fact_cx, fact_cy = POSICIONES["FACT_VENTAS"]
    for dim in ["DIM_FECHA", "DIM_PRODUCTO", "DIM_CLIENTE", "DIM_VENDEDOR", "DIM_GEOGRAFIA"]:
        dim_cx, dim_cy = POSICIONES[dim]
        draw_arrow(ax, fact_cx, fact_cy, dim_cx, dim_cy, TABLAS[dim]["color"])

    leyenda_items = [
        ("FACT_VENTAS",   "Tabla de Hechos",      AZUL_OSCURO),
        ("DIM_FECHA",     "Dimensión Temporal",   AZUL_MEDIO),
        ("DIM_PRODUCTO",  "Dimensión Producto",   VERDE),
        ("DIM_CLIENTE",   "Dimensión Cliente",    VIOLETA),
        ("DIM_VENDEDOR",  "Dimensión Vendedor",   NARANJA),
        ("DIM_GEOGRAFIA", "Dimensión Geografía",  ROJO),
    ]
    handles = [
        mpatches.Patch(facecolor=color, edgecolor=color, label=label)
        for _, label, color in leyenda_items
    ]
    ax.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.50, -0.04),
        ncol=6,
        fontsize=7.5,
        frameon=True,
        framealpha=0.9,
        edgecolor=GRIS_LINEA,
        facecolor=BLANCO,
    )

    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    plt.savefig(OUTPUT, dpi=180, bbox_inches="tight",
                facecolor=GRIS_FONDO, edgecolor="none")
    plt.close()
    print(f"[OK] Diagrama generado: {OUTPUT}")


if __name__ == "__main__":
    main()
