-- Ejecutar esto una vez en Supabase: Project -> SQL Editor -> New query

CREATE TABLE IF NOT EXISTS tpu_mensual (
    fecha           DATE PRIMARY KEY,      -- primer día del mes que representa el dato
    tpu_valor       NUMERIC NOT NULL,
    fuente          TEXT DEFAULT 'Caldara-Iacoviello (Fed)',
    fecha_actualizacion TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tipo_cambio_diario (
    fecha           DATE PRIMARY KEY,
    mxn_por_usd     NUMERIC NOT NULL,
    fuente          TEXT DEFAULT 'Banxico (serie SF43718)',
    fecha_actualizacion TIMESTAMPTZ DEFAULT now()
);

-- Vista de conveniencia: TPU y tipo de cambio promedio del mes, lado a lado
CREATE OR REPLACE VIEW vista_mensual_combinada AS
SELECT
    t.fecha AS mes,
    t.tpu_valor,
    AVG(fx.mxn_por_usd) AS fx_promedio_mes
FROM tpu_mensual t
LEFT JOIN tipo_cambio_diario fx
    ON date_trunc('month', fx.fecha) = date_trunc('month', t.fecha)
GROUP BY t.fecha, t.tpu_valor
ORDER BY t.fecha;
