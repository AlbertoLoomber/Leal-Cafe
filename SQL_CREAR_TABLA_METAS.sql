-- ========================================
-- TABLA DE METAS MENSUALES POR SUCURSAL
-- ========================================

CREATE TABLE IF NOT EXISTS "LealSilver".metas_mensuales (
    id SERIAL PRIMARY KEY,
    sucursal VARCHAR(50) NOT NULL CHECK (sucursal IN ('Centro', 'LM', 'Auditorio', 'Ahumada')),
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    anio INTEGER NOT NULL CHECK (anio >= 2020),
    meta_monto DECIMAL(12, 2) NOT NULL CHECK (meta_monto > 0),
    tipo_meta VARCHAR(20) DEFAULT 'ventas' CHECK (tipo_meta IN ('ventas', 'rentabilidad')),
    activa BOOLEAN DEFAULT TRUE,
    usuario_id INTEGER REFERENCES "LealSilver".usuarios(id),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comentarios TEXT,

    -- Constraint único: una sola meta por sucursal/mes/año/tipo
    CONSTRAINT uk_meta_sucursal_periodo UNIQUE (sucursal, mes, anio, tipo_meta)
);

-- Índices para búsquedas rápidas
CREATE INDEX idx_metas_sucursal ON "LealSilver".metas_mensuales(sucursal);
CREATE INDEX idx_metas_periodo ON "LealSilver".metas_mensuales(mes, anio);
CREATE INDEX idx_metas_activas ON "LealSilver".metas_mensuales(activa) WHERE activa = TRUE;

-- Trigger para actualizar fecha_modificacion
CREATE OR REPLACE FUNCTION actualizar_fecha_modificacion_metas()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_modificacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_actualizar_fecha_modificacion_metas
    BEFORE UPDATE ON "LealSilver".metas_mensuales
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_modificacion_metas();

-- Comentarios
COMMENT ON TABLE "LealSilver".metas_mensuales IS 'Metas mensuales de ventas por sucursal';
COMMENT ON COLUMN "LealSilver".metas_mensuales.meta_monto IS 'Monto objetivo para el período';
COMMENT ON COLUMN "LealSilver".metas_mensuales.tipo_meta IS 'Tipo de meta: ventas o rentabilidad';
COMMENT ON COLUMN "LealSilver".metas_mensuales.activa IS 'Indica si la meta está vigente';
