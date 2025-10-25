-- Migration 001: Create regras_de_classificacao (Rules) table
-- Purpose: Store product classification rules with priorities and matching criteria
-- Created: 2025-10-25

CREATE TABLE IF NOT EXISTS regras_de_classificacao (
    id SERIAL PRIMARY KEY,

    -- Rule metadata
    prioridade INTEGER NOT NULL DEFAULT 0,
    nome VARCHAR(255) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    -- Matching criteria (any can be NULL = not used)
    criterio_palavras_chave VARCHAR(1000),  -- Keywords to match in description
    criterio_ncm VARCHAR(100),               -- NCM code pattern (supports wildcard *)
    criterio_tamanho_min FLOAT,              -- Minimum size
    criterio_tamanho_max FLOAT,              -- Maximum size
    criterio_quantidade_min INTEGER,         -- Minimum quantity
    criterio_quantidade_max INTEGER,         -- Maximum quantity
    criterio_categoria VARCHAR(100),         -- Category exact match

    -- Result
    resultado_classificacao VARCHAR(100) NOT NULL,

    -- Tracking
    data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT prioridade_valid CHECK (prioridade >= 0),
    CONSTRAINT nome_not_empty CHECK (nome != '')
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_regras_ativo ON regras_de_classificacao(ativo);
CREATE INDEX IF NOT EXISTS idx_regras_prioridade ON regras_de_classificacao(prioridade DESC, ativo);
CREATE INDEX IF NOT EXISTS idx_regras_data_criacao ON regras_de_classificacao(data_criacao);

-- Add comment for documentation
COMMENT ON TABLE regras_de_classificacao IS 'Product classification rules with priority ordering and flexible criteria matching';
COMMENT ON COLUMN regras_de_classificacao.prioridade IS 'Higher number = higher priority when multiple rules match';
COMMENT ON COLUMN regras_de_classificacao.ativo IS 'Rules with ativo=false are never evaluated';
COMMENT ON COLUMN regras_de_classificacao.criterio_palavras_chave IS 'Case-insensitive substring match in product description';
COMMENT ON COLUMN regras_de_classificacao.criterio_ncm IS 'Wildcard pattern matching (e.g., 8471* matches 84713090)';
