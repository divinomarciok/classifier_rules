-- Migration 002b: Alter regras_de_classificacao to add categoria_id
-- This migration updates existing regras_de_classificacao table to support FK
-- DEPENDS ON: 002_create_categorias.sql
-- Date: 2025-10-26
-- Status: Up

-- Check if regras_de_classificacao exists and needs migration
-- If it already has categoria_id, this will do nothing
ALTER TABLE IF EXISTS regras_de_classificacao
ADD COLUMN IF NOT EXISTS categoria_id INTEGER REFERENCES categorias(id) ON DELETE RESTRICT ON UPDATE CASCADE;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_regras_categoria_id ON regras_de_classificacao(categoria_id);
