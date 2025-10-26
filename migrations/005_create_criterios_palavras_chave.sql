-- Migration 005: Create criterios_palavras_chave (Keywords Index) table
-- DEPENDS ON: 003_create_regras_de_classificacao.sql (FK to regras_de_classificacao)
-- Purpose: Optional normalized keyword storage for advanced keyword matching
-- Date: 2025-10-26
-- Status: Up

CREATE TABLE IF NOT EXISTS criterios_palavras_chave (
    id SERIAL PRIMARY KEY,

    -- Reference to rule
    id_regra INTEGER NOT NULL REFERENCES regras_de_classificacao(id) ON DELETE CASCADE,

    -- Keyword data
    palavra_chave VARCHAR(255) NOT NULL,
    peso FLOAT DEFAULT 1.0,  -- For future weighted matching

    -- Tracking
    data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT palavra_chave_not_empty CHECK (palavra_chave != ''),
    CONSTRAINT peso_valid CHECK (peso > 0)
);

-- Create indexes for performance
CREATE UNIQUE INDEX IF NOT EXISTS idx_criterios_regra_palavra ON criterios_palavras_chave(id_regra, palavra_chave);
CREATE INDEX IF NOT EXISTS idx_criterios_palavra_chave ON criterios_palavras_chave(palavra_chave);

-- Add comment for documentation
COMMENT ON TABLE criterios_palavras_chave IS 'Optional normalized keyword index for advanced matching (denormalization of regras_de_classificacao.criterio_palavras_chave)';
COMMENT ON COLUMN criterios_palavras_chave.peso IS 'Weight for future weighted keyword matching (currently unused)';
