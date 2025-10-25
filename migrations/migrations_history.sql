-- Migration History Log
-- This file tracks which migrations have been applied to the database

-- Created: 2025-10-25
-- Purpose: Track migration execution history for rollback/recovery procedures

-- Migration tracking table (optional, can be created in first migration)
-- CREATE TABLE IF NOT EXISTS migrations_applied (
--     id SERIAL PRIMARY KEY,
--     migration_name VARCHAR(255) NOT NULL UNIQUE,
--     applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     applied_by VARCHAR(50) DEFAULT 'system'
-- );

-- Migrations to execute in order:
-- 1. 001_create_regras_de_classificacao.sql     - Create rules table
-- 2. 002_create_auditoria_classificacao.sql     - Create audit log table
-- 3. 003_create_criterios_palavras_chave.sql   - Create keywords index table

-- Migration Status:
-- 001_create_regras_de_classificacao:   [ ] PENDING
-- 002_create_auditoria_classificacao:   [ ] PENDING
-- 003_create_criterios_palavras_chave:  [ ] PENDING
