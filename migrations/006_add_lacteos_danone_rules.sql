-- Migration 006: Add comprehensive Danone and Iogurte rules for Laticínios
-- DEPENDS ON: 003_create_regras_de_classificacao.sql
-- Date: 2025-10-26
-- Status: Up
-- Purpose: Add rules to properly classify all Danone yogurt variations and generic yogurts as Laticínios
-- NOTE: Keywords are separated by COMMA (,) NOT pipe (|)

-- First, let's check the current Laticínios rule to see if it exists
-- Category ID for LATICÍNIOS is 7

-- 1. Update existing iogurte rule to be more comprehensive
-- This rule should match all yogurt variations
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Iogurte Genérico Laticinio',
    7,
    110,
    'iogurte,iog.',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'iogurte,iog.',
    prioridade = 110,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 2. Danone Yogurt - base rule
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone Iogurte Base',
    7,
    120,
    'danone iogurte,danio,danone yogurt,iog. danone',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'danone iogurte,danio,danone yogurt,iog. danone',
    prioridade = 120,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 3. Danone Natural variants
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone Natural Laticinio',
    7,
    125,
    'danone natural,iog. danone natural,danio natural',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'danone natural,iog. danone natural,danio natural',
    prioridade = 125,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 4. Danone Fruit variants (with fruits)
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone com Fruta Laticinio',
    7,
    125,
    'danone banana,danone morango,danone frutas,danio banana,danio morango,iog. danone frutas,danone polpa',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'danone banana,danone morango,danone frutas,danio banana,danio morango,iog. danone frutas,danone polpa',
    prioridade = 125,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 5. Danone Grego (Greek yogurt style)
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone Grego Laticinio',
    7,
    130,
    'danone grego,iog. danone grego,danio grego,yogurt grego danone',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'danone grego,iog. danone grego,danio grego,yogurt grego danone',
    prioridade = 130,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 6. Danone Light/Diet variants
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone Light Diet Laticinio',
    7,
    125,
    'danone light,danone diet,iog. danone light,danio light,danio diet,danone zero',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'danone light,danone diet,iog. danone light,danio light,danio diet,danone zero',
    prioridade = 125,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 7. Danone Cremoso/Creamy
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone Cremoso Laticinio',
    7,
    125,
    'danone cremoso,danio cremoso,iog. danone cremoso,danone extra cremoso',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'danone cremoso,danio cremoso,iog. danone cremoso,danone extra cremoso',
    prioridade = 125,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 8. Danone Kids (for children)
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone Kids Laticinio',
    7,
    120,
    'danone kids,danone junior,danio kids,iog. danone kids',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'danone kids,danone junior,danio kids,iog. danone kids',
    prioridade = 120,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 9. Danone Activia (probiotic line)
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone Activia Laticinio',
    7,
    130,
    'activia,danone activia,iog. activia,activia danone,danone probiotico',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'activia,danone activia,iog. activia,activia danone,danone probiotico',
    prioridade = 130,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 10. Danone Integral (whole grain/fiber)
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone Integral Laticinio',
    7,
    125,
    'danone integral,danio integral,iog. danone integral,danone fibra',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'danone integral,danio integral,iog. danone integral,danone fibra',
    prioridade = 125,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 11. Generic yogurt with size control (for small/large packs)
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    criterio_tamanho_min,
    criterio_tamanho_max,
    ativo
) VALUES (
    'Iogurte Pequeno Laticinio',
    7,
    105,
    'iogurte,iog.',
    0.08,  -- 80ml minimum
    0.25,  -- 250ml maximum
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_tamanho_min = 0.08,
    criterio_tamanho_max = 0.25,
    data_atualizacao = CURRENT_TIMESTAMP;

-- 12. Generic yogurt for medium packs
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    criterio_tamanho_min,
    criterio_tamanho_max,
    ativo
) VALUES (
    'Iogurte Médio Laticinio',
    7,
    105,
    'iogurte,iog.',
    0.25,  -- 250ml minimum
    1.0,   -- 1000ml (1L) maximum
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_tamanho_min = 0.25,
    criterio_tamanho_max = 1.0,
    data_atualizacao = CURRENT_TIMESTAMP;

-- Log the migration completion
-- This helps track when these rules were added
SELECT 'Migration 006 completed: Added 12 comprehensive Danone and Iogurte rules for Laticínios' AS migration_status;
