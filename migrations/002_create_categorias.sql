-- Migration 002: Create categorias (product categories) reference table
-- This table MUST be created BEFORE regras_de_classificacao (FK dependency)
-- Date: 2025-10-26
-- Status: Up

CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL UNIQUE,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_categorias_ativo_nome ON categorias(ativo, nome);
CREATE UNIQUE INDEX IF NOT EXISTS idx_categorias_nome_unique ON categorias(nome);

-- Seed base categories (will not error if they already exist due to UNIQUE constraint)
INSERT INTO categorias (nome, descricao, ativo) VALUES
    ('ELETRÔNICOS', 'Produtos eletrônicos em geral', TRUE),
    ('CABOS', 'Cabos e conectores', TRUE),
    ('ACESSÓRIOS', 'Acessórios diversos', TRUE),
    ('PERIFÉRICOS', 'Periféricos de computador', TRUE),
    ('COMPONENTES', 'Componentes internos', TRUE)
ON CONFLICT (nome) DO NOTHING;

-- Verify seeding was successful
-- SELECT COUNT(*) as categorias_count FROM categorias;
