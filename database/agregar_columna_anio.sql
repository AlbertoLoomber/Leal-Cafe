-- ============================================================================
-- AGREGAR COLUMNA AÑO A LAS TABLAS DE VENTAS
-- Esquema: "LealSilver"
-- ============================================================================

-- 1. Ventas por hora
ALTER TABLE "LealSilver".ventas_por_hora
ADD COLUMN anio INTEGER NOT NULL DEFAULT 2024 CHECK (anio BETWEEN 2020 AND 2100);

-- 2. Ventas por platillo
ALTER TABLE "LealSilver".ventas_por_platillo
ADD COLUMN anio INTEGER NOT NULL DEFAULT 2024 CHECK (anio BETWEEN 2020 AND 2100);

-- 3. Ventas por grupo
ALTER TABLE "LealSilver".ventas_por_grupo
ADD COLUMN anio INTEGER NOT NULL DEFAULT 2024 CHECK (anio BETWEEN 2020 AND 2100);

-- 4. Ventas por tipo de grupo
ALTER TABLE "LealSilver".ventas_por_tipo_grupo
ADD COLUMN anio INTEGER NOT NULL DEFAULT 2024 CHECK (anio BETWEEN 2020 AND 2100);

-- 5. Ventas por tipo de pago
ALTER TABLE "LealSilver".ventas_por_tipo_pago
ADD COLUMN anio INTEGER NOT NULL DEFAULT 2024 CHECK (anio BETWEEN 2020 AND 2100);

-- 6. Ventas por usuario
ALTER TABLE "LealSilver".ventas_por_usuario
ADD COLUMN anio INTEGER NOT NULL DEFAULT 2024 CHECK (anio BETWEEN 2020 AND 2100);

-- 7. Ventas por cajero
ALTER TABLE "LealSilver".ventas_por_cajero
ADD COLUMN anio INTEGER NOT NULL DEFAULT 2024 CHECK (anio BETWEEN 2020 AND 2100);

-- 8. Ventas por modificador
ALTER TABLE "LealSilver".ventas_por_modificador
ADD COLUMN anio INTEGER NOT NULL DEFAULT 2024 CHECK (anio BETWEEN 2020 AND 2100);

-- ============================================================================
-- ACTUALIZAR CONSTRAINTS UNIQUE PARA INCLUIR AÑO
-- ============================================================================

-- 1. Ventas por hora
ALTER TABLE "LealSilver".ventas_por_hora
DROP CONSTRAINT IF EXISTS uk_ventas_hora;

ALTER TABLE "LealSilver".ventas_por_hora
ADD CONSTRAINT uk_ventas_hora UNIQUE (sucursal, anio, mes, semana, hora);

-- 2. Ventas por platillo
ALTER TABLE "LealSilver".ventas_por_platillo
DROP CONSTRAINT IF EXISTS uk_ventas_platillo;

ALTER TABLE "LealSilver".ventas_por_platillo
ADD CONSTRAINT uk_ventas_platillo UNIQUE (sucursal, anio, mes, semana, clave_platillo);

-- 3. Ventas por grupo
ALTER TABLE "LealSilver".ventas_por_grupo
DROP CONSTRAINT IF EXISTS uk_ventas_grupo;

ALTER TABLE "LealSilver".ventas_por_grupo
ADD CONSTRAINT uk_ventas_grupo UNIQUE (sucursal, anio, mes, semana, grupo);

-- 4. Ventas por tipo de grupo
ALTER TABLE "LealSilver".ventas_por_tipo_grupo
DROP CONSTRAINT IF EXISTS uk_ventas_tipo_grupo;

ALTER TABLE "LealSilver".ventas_por_tipo_grupo
ADD CONSTRAINT uk_ventas_tipo_grupo UNIQUE (sucursal, anio, mes, semana, grupo);

-- 5. Ventas por tipo de pago
ALTER TABLE "LealSilver".ventas_por_tipo_pago
DROP CONSTRAINT IF EXISTS uk_ventas_tipo_pago;

ALTER TABLE "LealSilver".ventas_por_tipo_pago
ADD CONSTRAINT uk_ventas_tipo_pago UNIQUE (sucursal, anio, mes, semana, tipo_pago);

-- 6. Ventas por usuario
ALTER TABLE "LealSilver".ventas_por_usuario
DROP CONSTRAINT IF EXISTS uk_ventas_usuario;

ALTER TABLE "LealSilver".ventas_por_usuario
ADD CONSTRAINT uk_ventas_usuario UNIQUE (sucursal, anio, mes, semana, usuario);

-- 7. Ventas por cajero
ALTER TABLE "LealSilver".ventas_por_cajero
DROP CONSTRAINT IF EXISTS uk_ventas_cajero;

ALTER TABLE "LealSilver".ventas_por_cajero
ADD CONSTRAINT uk_ventas_cajero UNIQUE (sucursal, anio, mes, semana, cajero);

-- 8. Ventas por modificador
ALTER TABLE "LealSilver".ventas_por_modificador
DROP CONSTRAINT IF EXISTS uk_ventas_modificador;

ALTER TABLE "LealSilver".ventas_por_modificador
ADD CONSTRAINT uk_ventas_modificador UNIQUE (sucursal, anio, mes, semana, clave_platillo, grupo, tamano);

-- ============================================================================
-- CREAR ÍNDICES PARA AÑO
-- ============================================================================

CREATE INDEX idx_ventas_hora_anio ON "LealSilver".ventas_por_hora(anio);
CREATE INDEX idx_ventas_platillo_anio ON "LealSilver".ventas_por_platillo(anio);
CREATE INDEX idx_ventas_grupo_anio ON "LealSilver".ventas_por_grupo(anio);
CREATE INDEX idx_ventas_tipo_grupo_anio ON "LealSilver".ventas_por_tipo_grupo(anio);
CREATE INDEX idx_ventas_tipo_pago_anio ON "LealSilver".ventas_por_tipo_pago(anio);
CREATE INDEX idx_ventas_usuario_anio ON "LealSilver".ventas_por_usuario(anio);
CREATE INDEX idx_ventas_cajero_anio ON "LealSilver".ventas_por_cajero(anio);
CREATE INDEX idx_ventas_modificador_anio ON "LealSilver".ventas_por_modificador(anio);

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
