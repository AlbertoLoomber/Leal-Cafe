-- ============================================================================
-- TABLAS DE VENTAS - LEAL CAFÉ
-- Esquema: LealSilver
-- Descripción: 8 tablas para almacenar datos del Resumen de Ventas extraído de Excel
-- ============================================================================

-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS LealSilver;

-- ============================================================================
-- 1. VENTAS POR HORA
-- ============================================================================
CREATE TABLE IF NOT EXISTS LealSilver.ventas_por_hora (
    id SERIAL PRIMARY KEY,

    -- Metadatos de identificación
    sucursal VARCHAR(50) NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    semana INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 5),

    -- Datos de ventas
    hora VARCHAR(20) NOT NULL,
    monto DECIMAL(12, 2) NOT NULL,

    -- Auditoría
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices compuestos
    CONSTRAINT uk_ventas_hora UNIQUE (sucursal, mes, semana, hora)
);

CREATE INDEX idx_ventas_hora_sucursal ON LealSilver.ventas_por_hora(sucursal);
CREATE INDEX idx_ventas_hora_periodo ON LealSilver.ventas_por_hora(mes, semana);
CREATE INDEX idx_ventas_hora_created ON LealSilver.ventas_por_hora(created_at);


-- ============================================================================
-- 2. VENTAS POR PLATILLO
-- ============================================================================
CREATE TABLE IF NOT EXISTS LealSilver.ventas_por_platillo (
    id SERIAL PRIMARY KEY,

    -- Metadatos de identificación
    sucursal VARCHAR(50) NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    semana INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 5),

    -- Datos de ventas
    clave_platillo VARCHAR(50) NOT NULL,
    nombre_platillo VARCHAR(200) NOT NULL,
    grupo VARCHAR(100) NOT NULL,
    cantidad INTEGER NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    porcentaje DECIMAL(5, 2) NOT NULL,

    -- Auditoría
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices compuestos
    CONSTRAINT uk_ventas_platillo UNIQUE (sucursal, mes, semana, clave_platillo)
);

CREATE INDEX idx_ventas_platillo_sucursal ON LealSilver.ventas_por_platillo(sucursal);
CREATE INDEX idx_ventas_platillo_periodo ON LealSilver.ventas_por_platillo(mes, semana);
CREATE INDEX idx_ventas_platillo_grupo ON LealSilver.ventas_por_platillo(grupo);
CREATE INDEX idx_ventas_platillo_created ON LealSilver.ventas_por_platillo(created_at);


-- ============================================================================
-- 3. VENTAS POR GRUPO
-- ============================================================================
CREATE TABLE IF NOT EXISTS LealSilver.ventas_por_grupo (
    id SERIAL PRIMARY KEY,

    -- Metadatos de identificación
    sucursal VARCHAR(50) NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    semana INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 5),

    -- Datos de ventas
    grupo VARCHAR(100) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,

    -- Auditoría
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices compuestos
    CONSTRAINT uk_ventas_grupo UNIQUE (sucursal, mes, semana, grupo)
);

CREATE INDEX idx_ventas_grupo_sucursal ON LealSilver.ventas_por_grupo(sucursal);
CREATE INDEX idx_ventas_grupo_periodo ON LealSilver.ventas_por_grupo(mes, semana);
CREATE INDEX idx_ventas_grupo_created ON LealSilver.ventas_por_grupo(created_at);


-- ============================================================================
-- 4. VENTAS POR TIPO DE GRUPO
-- ============================================================================
CREATE TABLE IF NOT EXISTS LealSilver.ventas_por_tipo_grupo (
    id SERIAL PRIMARY KEY,

    -- Metadatos de identificación
    sucursal VARCHAR(50) NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    semana INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 5),

    -- Datos de ventas
    grupo VARCHAR(100) NOT NULL,
    cantidad INTEGER NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    iva DECIMAL(12, 2) NOT NULL,
    total DECIMAL(12, 2) NOT NULL,
    porcentaje DECIMAL(5, 2) NOT NULL,

    -- Auditoría
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices compuestos
    CONSTRAINT uk_ventas_tipo_grupo UNIQUE (sucursal, mes, semana, grupo)
);

CREATE INDEX idx_ventas_tipo_grupo_sucursal ON LealSilver.ventas_por_tipo_grupo(sucursal);
CREATE INDEX idx_ventas_tipo_grupo_periodo ON LealSilver.ventas_por_tipo_grupo(mes, semana);
CREATE INDEX idx_ventas_tipo_grupo_created ON LealSilver.ventas_por_tipo_grupo(created_at);


-- ============================================================================
-- 5. VENTAS POR TIPO DE PAGO
-- ============================================================================
CREATE TABLE IF NOT EXISTS LealSilver.ventas_por_tipo_pago (
    id SERIAL PRIMARY KEY,

    -- Metadatos de identificación
    sucursal VARCHAR(50) NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    semana INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 5),

    -- Datos de ventas
    tipo_pago VARCHAR(100) NOT NULL,
    total DECIMAL(12, 2) NOT NULL,
    porcentaje DECIMAL(5, 2) NOT NULL,

    -- Auditoría
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices compuestos
    CONSTRAINT uk_ventas_tipo_pago UNIQUE (sucursal, mes, semana, tipo_pago)
);

CREATE INDEX idx_ventas_tipo_pago_sucursal ON LealSilver.ventas_por_tipo_pago(sucursal);
CREATE INDEX idx_ventas_tipo_pago_periodo ON LealSilver.ventas_por_tipo_pago(mes, semana);
CREATE INDEX idx_ventas_tipo_pago_created ON LealSilver.ventas_por_tipo_pago(created_at);


-- ============================================================================
-- 6. VENTAS POR USUARIO
-- ============================================================================
CREATE TABLE IF NOT EXISTS LealSilver.ventas_por_usuario (
    id SERIAL PRIMARY KEY,

    -- Metadatos de identificación
    sucursal VARCHAR(50) NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    semana INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 5),

    -- Datos de ventas
    usuario VARCHAR(100) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    iva DECIMAL(12, 2) NOT NULL,
    total DECIMAL(12, 2) NOT NULL,
    num_cuentas INTEGER NOT NULL,
    ticket_promedio DECIMAL(12, 2) NOT NULL,
    num_personas INTEGER NOT NULL,
    promedio_por_persona DECIMAL(12, 2) NOT NULL,
    porcentaje DECIMAL(5, 2) NOT NULL,

    -- Auditoría
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices compuestos
    CONSTRAINT uk_ventas_usuario UNIQUE (sucursal, mes, semana, usuario)
);

CREATE INDEX idx_ventas_usuario_sucursal ON LealSilver.ventas_por_usuario(sucursal);
CREATE INDEX idx_ventas_usuario_periodo ON LealSilver.ventas_por_usuario(mes, semana);
CREATE INDEX idx_ventas_usuario_created ON LealSilver.ventas_por_usuario(created_at);


-- ============================================================================
-- 7. VENTAS POR CAJERO
-- ============================================================================
CREATE TABLE IF NOT EXISTS LealSilver.ventas_por_cajero (
    id SERIAL PRIMARY KEY,

    -- Metadatos de identificación
    sucursal VARCHAR(50) NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    semana INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 5),

    -- Datos de ventas
    cajero VARCHAR(100) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    iva DECIMAL(12, 2) NOT NULL,
    total DECIMAL(12, 2) NOT NULL,
    cantidad_transacciones INTEGER NOT NULL,
    porcentaje DECIMAL(5, 2) NOT NULL,

    -- Auditoría
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices compuestos
    CONSTRAINT uk_ventas_cajero UNIQUE (sucursal, mes, semana, cajero)
);

CREATE INDEX idx_ventas_cajero_sucursal ON LealSilver.ventas_por_cajero(sucursal);
CREATE INDEX idx_ventas_cajero_periodo ON LealSilver.ventas_por_cajero(mes, semana);
CREATE INDEX idx_ventas_cajero_created ON LealSilver.ventas_por_cajero(created_at);


-- ============================================================================
-- 8. VENTAS POR MODIFICADOR
-- ============================================================================
CREATE TABLE IF NOT EXISTS LealSilver.ventas_por_modificador (
    id SERIAL PRIMARY KEY,

    -- Metadatos de identificación
    sucursal VARCHAR(50) NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    semana INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 5),

    -- Datos de ventas
    grupo VARCHAR(100) NOT NULL,
    clave_platillo VARCHAR(50) NOT NULL,
    nombre_platillo VARCHAR(200) NOT NULL,
    tamano VARCHAR(50),
    cantidad INTEGER NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,

    -- Auditoría
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices compuestos (sin unique constraint porque puede haber duplicados)
    CONSTRAINT uk_ventas_modificador UNIQUE (sucursal, mes, semana, clave_platillo, grupo, tamano)
);

CREATE INDEX idx_ventas_modificador_sucursal ON LealSilver.ventas_por_modificador(sucursal);
CREATE INDEX idx_ventas_modificador_periodo ON LealSilver.ventas_por_modificador(mes, semana);
CREATE INDEX idx_ventas_modificador_grupo ON LealSilver.ventas_por_modificador(grupo);
CREATE INDEX idx_ventas_modificador_created ON LealSilver.ventas_por_modificador(created_at);


-- ============================================================================
-- COMENTARIOS EN LAS TABLAS
-- ============================================================================

COMMENT ON SCHEMA LealSilver IS 'Esquema para datos procesados de ventas - Leal Café';

COMMENT ON TABLE LealSilver.ventas_por_hora IS 'Ventas agregadas por hora del día';
COMMENT ON TABLE LealSilver.ventas_por_platillo IS 'Ventas detalladas por platillo/artículo';
COMMENT ON TABLE LealSilver.ventas_por_grupo IS 'Ventas agregadas por grupo de productos';
COMMENT ON TABLE LealSilver.ventas_por_tipo_grupo IS 'Ventas por tipo de grupo con IVA';
COMMENT ON TABLE LealSilver.ventas_por_tipo_pago IS 'Ventas por método de pago';
COMMENT ON TABLE LealSilver.ventas_por_usuario IS 'Ventas por usuario/mesero con métricas';
COMMENT ON TABLE LealSilver.ventas_por_cajero IS 'Ventas por cajero con transacciones';
COMMENT ON TABLE LealSilver.ventas_por_modificador IS 'Ventas por modificadores de platillos';


-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
