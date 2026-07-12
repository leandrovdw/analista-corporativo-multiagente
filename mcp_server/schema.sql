-- Esquema sugerido para NeonDB / PostgreSQL

CREATE TABLE IF NOT EXISTS valores_modulo (
    id SERIAL PRIMARY KEY,
    fecha_desde DATE NOT NULL,
    fecha_hasta DATE NULL,
    valor NUMERIC(14,2) NOT NULL,
    acta_directorio VARCHAR(50) NOT NULL,
    vigente BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS consultas_compras (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    consulta TEXT NOT NULL,
    objeto_compra VARCHAR(200),
    monto_estimado NUMERIC(14,2),
    valor_modulo NUMERIC(14,2),
    cantidad_vm NUMERIC(14,4),
    procedimiento VARCHAR(100),
    autoridad VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO valores_modulo (fecha_desde, fecha_hasta, valor, acta_directorio, vigente)
VALUES ('2026-04-23', NULL, 106000, '360', true)
ON CONFLICT DO NOTHING;
