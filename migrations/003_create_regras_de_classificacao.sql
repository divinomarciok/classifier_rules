-- Migration 003: Create regras_de_classificacao (classification rules) table
-- DEPENDS ON: 002_create_categorias.sql (FK to categorias)
-- Date: 2025-10-26
-- Status: Up

CREATE TABLE IF NOT EXISTS regras_de_classificacao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL UNIQUE,
    ativo BOOLEAN DEFAULT TRUE,
    prioridade INTEGER DEFAULT 100,
    criterio_palavras_chave VARCHAR(255),
    criterio_ncm VARCHAR(255),
    criterio_tamanho_min FLOAT,
    criterio_tamanho_max FLOAT,
    criterio_quantidade_min INTEGER,
    criterio_quantidade_max INTEGER,
    criterio_categoria VARCHAR(255),
    categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_regras_prioridade ON regras_de_classificacao(prioridade DESC);
CREATE INDEX IF NOT EXISTS idx_regras_ativa ON regras_de_classificacao(ativo);
CREATE INDEX IF NOT EXISTS idx_regras_categoria_id ON regras_de_classificacao(categoria_id);
CREATE INDEX IF NOT EXISTS idx_regras_data_criacao ON regras_de_classificacao(data_criacao);

-- Add constraints for data integrity
ALTER TABLE regras_de_classificacao
  ADD CONSTRAINT regras_prioridade_not_null CHECK (prioridade IS NOT NULL),
  ADD CONSTRAINT regras_nome_not_null CHECK (nome IS NOT NULL),
  ADD CONSTRAINT regras_categoria_id_not_null CHECK (categoria_id IS NOT NULL);
