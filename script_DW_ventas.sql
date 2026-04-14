-- =============================================================
-- DATA WAREHOUSE - SISTEMA DE ANÁLISIS DE VENTAS
-- Star Schema - MySQL 8.x
-- Base de datos: dw_ventas
-- Autor: César Jasser de Jesús | Matrícula: #2023-1747
-- Materia: Big Data / Electiva 1 | Profesor: Francis Ramírez
-- =============================================================

CREATE DATABASE IF NOT EXISTS dw_ventas
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE dw_ventas;

-- ============================================================
-- DIMENSIONES
-- ============================================================

-- DIM_FECHA
CREATE TABLE IF NOT EXISTS DIM_FECHA (
    id_fecha        INT             NOT NULL COMMENT 'Formato YYYYMMDD',
    fecha           DATE            NOT NULL,
    anio            SMALLINT        NOT NULL,
    trimestre       TINYINT         NOT NULL,
    mes             TINYINT         NOT NULL,
    nombre_mes      VARCHAR(20)     NOT NULL,
    semana          TINYINT         NOT NULL,
    dia             TINYINT         NOT NULL,
    dia_semana      VARCHAR(15)     NOT NULL,
    es_fin_semana   BIT(1)          NOT NULL DEFAULT 0,
    es_feriado      BIT(1)          NOT NULL DEFAULT 0,
    PRIMARY KEY (id_fecha)
) ENGINE=InnoDB COMMENT='Dimensión temporal con granularidad diaria';

-- DIM_PRODUCTO
CREATE TABLE IF NOT EXISTS DIM_PRODUCTO (
    id_producto     INT             NOT NULL AUTO_INCREMENT,
    codigo_sku      VARCHAR(20)     NOT NULL,
    nombre_producto VARCHAR(150)    NOT NULL,
    descripcion     TEXT,
    categoria       VARCHAR(50)     NOT NULL,
    subcategoria    VARCHAR(50),
    precio_base     DECIMAL(10,2)   NOT NULL,
    unidad_medida   VARCHAR(20),
    proveedor       VARCHAR(100),
    pais_origen     VARCHAR(50),
    activo          BIT(1)          NOT NULL DEFAULT 1,
    fecha_alta      DATE,
    fecha_baja      DATE,
    fuente_datos    VARCHAR(20),
    fecha_carga     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_producto),
    UNIQUE KEY uq_sku (codigo_sku)
) ENGINE=InnoDB COMMENT='Dimensión de productos con SCD Tipo 1';

-- DIM_CLIENTE
CREATE TABLE IF NOT EXISTS DIM_CLIENTE (
    id_cliente      INT             NOT NULL AUTO_INCREMENT,
    codigo_cliente  VARCHAR(20)     NOT NULL,
    nombre_cliente  VARCHAR(150)    NOT NULL,
    tipo_cliente    VARCHAR(30)     NOT NULL,
    segmento        VARCHAR(30),
    email           VARCHAR(120),
    telefono        VARCHAR(25),
    pais            VARCHAR(50),
    region          VARCHAR(50),
    ciudad          VARCHAR(80),
    direccion       VARCHAR(200),
    codigo_postal   VARCHAR(15),
    fecha_registro  DATE,
    activo          BIT(1)          NOT NULL DEFAULT 1,
    fuente_datos    VARCHAR(20),
    fecha_carga     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_cliente),
    UNIQUE KEY uq_cod_cliente (codigo_cliente)
) ENGINE=InnoDB COMMENT='Dimensión de clientes con SCD Tipo 1';

-- DIM_VENDEDOR
CREATE TABLE IF NOT EXISTS DIM_VENDEDOR (
    id_vendedor     INT             NOT NULL AUTO_INCREMENT,
    codigo_vendedor VARCHAR(20)     NOT NULL,
    nombre_vendedor VARCHAR(80)     NOT NULL,
    apellido_vendedor VARCHAR(80)   NOT NULL,
    email           VARCHAR(120),
    telefono        VARCHAR(25),
    region          VARCHAR(50),
    zona            VARCHAR(50),
    cargo           VARCHAR(60),
    fecha_ingreso   DATE,
    activo          BIT(1)          NOT NULL DEFAULT 1,
    fecha_carga     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_vendedor),
    UNIQUE KEY uq_cod_vendedor (codigo_vendedor)
) ENGINE=InnoDB COMMENT='Dimensión de vendedores';

-- DIM_GEOGRAFIA
CREATE TABLE IF NOT EXISTS DIM_GEOGRAFIA (
    id_geografia    INT             NOT NULL AUTO_INCREMENT,
    pais            VARCHAR(60)     NOT NULL,
    codigo_pais     CHAR(3)         NOT NULL,
    region          VARCHAR(60),
    ciudad          VARCHAR(80)     NOT NULL,
    codigo_postal   VARCHAR(15),
    zona_horaria    VARCHAR(40),
    continente      VARCHAR(20)     NOT NULL,
    latitud         DECIMAL(9,6),
    longitud        DECIMAL(9,6),
    PRIMARY KEY (id_geografia)
) ENGINE=InnoDB COMMENT='Dimensión geográfica de cobertura';

-- ============================================================
-- TABLA DE HECHOS
-- ============================================================

CREATE TABLE IF NOT EXISTS FACT_VENTAS (
    id_venta        BIGINT          NOT NULL AUTO_INCREMENT,
    id_fecha        INT             NOT NULL,
    id_producto     INT             NOT NULL,
    id_cliente      INT             NOT NULL,
    id_vendedor     INT             NOT NULL,
    id_geografia    INT             NOT NULL,
    numero_factura  VARCHAR(30)     NOT NULL,
    cantidad        INT             NOT NULL,
    precio_unitario DECIMAL(10,2)   NOT NULL,
    descuento       DECIMAL(5,2)    NOT NULL DEFAULT 0.00,
    subtotal        DECIMAL(12,2)   NOT NULL,
    impuesto        DECIMAL(12,2)   NOT NULL,
    total_venta     DECIMAL(12,2)   NOT NULL,
    moneda          CHAR(3)         NOT NULL DEFAULT 'USD',
    fuente_datos    VARCHAR(20),
    fecha_carga     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_venta),
    CONSTRAINT fk_venta_fecha      FOREIGN KEY (id_fecha)     REFERENCES DIM_FECHA(id_fecha),
    CONSTRAINT fk_venta_producto   FOREIGN KEY (id_producto)  REFERENCES DIM_PRODUCTO(id_producto),
    CONSTRAINT fk_venta_cliente    FOREIGN KEY (id_cliente)   REFERENCES DIM_CLIENTE(id_cliente),
    CONSTRAINT fk_venta_vendedor   FOREIGN KEY (id_vendedor)  REFERENCES DIM_VENDEDOR(id_vendedor),
    CONSTRAINT fk_venta_geografia  FOREIGN KEY (id_geografia) REFERENCES DIM_GEOGRAFIA(id_geografia),
    INDEX idx_fecha    (id_fecha),
    INDEX idx_producto (id_producto),
    INDEX idx_cliente  (id_cliente)
) ENGINE=InnoDB COMMENT='Tabla de hechos — transacciones de venta';

-- ============================================================
-- VISTAS ANALÍTICAS
-- ============================================================

CREATE OR REPLACE VIEW VW_VENTAS_POR_PRODUCTO AS
SELECT
    p.codigo_sku,
    p.nombre_producto,
    p.categoria,
    COUNT(f.id_venta)          AS num_transacciones,
    SUM(f.cantidad)            AS unidades_vendidas,
    SUM(f.total_venta)         AS ingresos_totales,
    AVG(f.precio_unitario)     AS precio_promedio
FROM FACT_VENTAS f
JOIN DIM_PRODUCTO p ON f.id_producto = p.id_producto
GROUP BY p.id_producto, p.codigo_sku, p.nombre_producto, p.categoria;

CREATE OR REPLACE VIEW VW_VENTAS_POR_CLIENTE AS
SELECT
    c.codigo_cliente,
    c.nombre_cliente,
    c.segmento,
    c.pais,
    COUNT(f.id_venta)  AS num_compras,
    SUM(f.total_venta) AS total_gastado,
    MAX(d.fecha)       AS ultima_compra
FROM FACT_VENTAS f
JOIN DIM_CLIENTE  c ON f.id_cliente = c.id_cliente
JOIN DIM_FECHA    d ON f.id_fecha   = d.id_fecha
GROUP BY c.id_cliente, c.codigo_cliente, c.nombre_cliente, c.segmento, c.pais;

CREATE OR REPLACE VIEW VW_TENDENCIA_MENSUAL AS
SELECT
    d.anio,
    d.mes,
    d.nombre_mes,
    COUNT(f.id_venta)  AS num_ventas,
    SUM(f.total_venta) AS ingresos_mes,
    AVG(f.total_venta) AS ticket_promedio
FROM FACT_VENTAS f
JOIN DIM_FECHA d ON f.id_fecha = d.id_fecha
GROUP BY d.anio, d.mes, d.nombre_mes
ORDER BY d.anio, d.mes;

CREATE OR REPLACE VIEW VW_VENTAS_POR_REGION AS
SELECT
    g.pais,
    g.region,
    g.continente,
    COUNT(f.id_venta)  AS num_ventas,
    SUM(f.total_venta) AS ingresos_totales
FROM FACT_VENTAS f
JOIN DIM_GEOGRAFIA g ON f.id_geografia = g.id_geografia
GROUP BY g.pais, g.region, g.continente;

CREATE OR REPLACE VIEW VW_TOP5_PRODUCTOS AS
SELECT
    p.nombre_producto,
    p.categoria,
    SUM(f.total_venta) AS ingresos_totales
FROM FACT_VENTAS f
JOIN DIM_PRODUCTO p ON f.id_producto = p.id_producto
GROUP BY p.id_producto, p.nombre_producto, p.categoria
ORDER BY ingresos_totales DESC
LIMIT 5;

CREATE OR REPLACE VIEW VW_TOP5_CLIENTES AS
SELECT
    c.nombre_cliente,
    c.segmento,
    c.pais,
    SUM(f.total_venta) AS total_gastado
FROM FACT_VENTAS f
JOIN DIM_CLIENTE c ON f.id_cliente = c.id_cliente
GROUP BY c.id_cliente, c.nombre_cliente, c.segmento, c.pais
ORDER BY total_gastado DESC
LIMIT 5;
