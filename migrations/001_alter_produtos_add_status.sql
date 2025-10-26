-- Migration 001: Add status_classificacao column to produtos_tabela
-- Purpose: Track classification status of each product
-- Status values: 'pending' (never attempted), 'matched' (has categoria), 'no_match' (attempted, no rules matched)
-- Date: 2025-10-26
-- Status: Up

-- Add new column with default value 'pending'
ALTER TABLE produtos_tabela
ADD COLUMN status_classificacao VARCHAR(20) DEFAULT 'pending' NOT NULL;

-- Create index for efficient filtering
CREATE INDEX IF NOT EXISTS idx_produtos_status_classificacao
ON produtos_tabela(status_classificacao);

-- Update existing products that have categoria assigned to 'matched'
UPDATE produtos_tabela
SET status_classificacao = 'matched'
WHERE categoria IS NOT NULL;

-- Products with NULL categoria remain as 'pending' (default value)
-- This allows them to be reprocessed when new rules are added

-- Verify the update
-- SELECT status_classificacao, COUNT(*) as count FROM produtos_tabela GROUP BY status_classificacao;
