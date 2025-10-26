-- Migration 004: Create auditoria_classificacao (Audit Log) table
-- DEPENDS ON: 003_create_regras_de_classificacao.sql (FK to regras_de_classificacao)
-- Purpose: Track every classification decision for complete auditability
-- Date: 2025-10-26
-- Status: Up

CREATE TABLE IF NOT EXISTS auditoria_classificacao (
    id SERIAL PRIMARY KEY,

    -- Which rule was applied
    id_regra INTEGER REFERENCES regras_de_classificacao(id) ON DELETE SET NULL,

    -- Product information at time of classification
    id_produto VARCHAR(100),
    descricao_produto VARCHAR(1000),
    ncm_produto VARCHAR(100),

    -- Classification result
    resultado_classificacao VARCHAR(100) NOT NULL,

    -- Which criteria matched (JSON format)
    criterios_combinados VARCHAR(1000),

    -- Execution metadata
    data_classificacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tempo_avaliacao_ms INTEGER,
    usuario_sistema VARCHAR(50) DEFAULT 'system',

    -- Constraints
    CONSTRAINT resultado_not_empty CHECK (resultado_classificacao != '')
);

-- Create indexes for query performance
CREATE INDEX IF NOT EXISTS idx_auditoria_id_produto ON auditoria_classificacao(id_produto, data_classificacao DESC);
CREATE INDEX IF NOT EXISTS idx_auditoria_id_regra ON auditoria_classificacao(id_regra, data_classificacao DESC);
CREATE INDEX IF NOT EXISTS idx_auditoria_data_classificacao ON auditoria_classificacao(data_classificacao DESC);
CREATE INDEX IF NOT EXISTS idx_auditoria_resultado ON auditoria_classificacao(resultado_classificacao);

-- Add comment for documentation
COMMENT ON TABLE auditoria_classificacao IS 'Immutable log of all product classifications (append-only for auditability)';
COMMENT ON COLUMN auditoria_classificacao.id_regra IS 'Rule that produced this classification (NULL if no match)';
COMMENT ON COLUMN auditoria_classificacao.criterios_combinados IS 'JSON object describing which criteria matched';
COMMENT ON COLUMN auditoria_classificacao.tempo_avaliacao_ms IS 'How long the evaluation took in milliseconds';
