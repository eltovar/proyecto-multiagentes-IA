-- ================================================================
-- ROLLBACK 001: Revertir Campos de Clasificación de Intención
-- ================================================================
-- PR: #1 - Fundamentos
-- Fecha: 2025-10-02
-- Descripción: Revierte cambios de migración 001
-- USO: Solo en caso de necesitar rollback
-- ================================================================

BEGIN TRANSACTION;

-- ================================================================
-- ELIMINAR TRIGGER
-- ================================================================

DROP TRIGGER IF EXISTS update_last_message_at;

-- ================================================================
-- ELIMINAR ÍNDICES
-- ================================================================

DROP INDEX IF EXISTS idx_conversations_state_hours;
DROP INDEX IF EXISTS idx_conversations_last_message;
DROP INDEX IF EXISTS idx_conversations_business_hours;
DROP INDEX IF EXISTS idx_conversations_intent;

-- ================================================================
-- ELIMINAR COLUMNAS
-- ================================================================
-- NOTA: SQLite no soporta DROP COLUMN directamente en todas las versiones
-- Si falla, usar método alternativo (recrear tabla)

-- Método 1: Intentar DROP COLUMN (SQLite 3.35.0+)
ALTER TABLE conversations DROP COLUMN IF EXISTS form_data;
ALTER TABLE conversations DROP COLUMN IF EXISTS interaction_count;
ALTER TABLE conversations DROP COLUMN IF EXISTS last_message_at;
ALTER TABLE conversations DROP COLUMN IF EXISTS business_hours_valid;
ALTER TABLE conversations DROP COLUMN IF EXISTS extracted_data;
ALTER TABLE conversations DROP COLUMN IF EXISTS intent;

COMMIT;

-- ================================================================
-- MÉTODO ALTERNATIVO: Recrear tabla (si DROP COLUMN falla)
-- ================================================================
-- Descomentar y ejecutar si el método anterior falla

/*
BEGIN TRANSACTION;

-- Crear tabla temporal con schema original
CREATE TABLE conversations_backup (
    whatsapp_id TEXT PRIMARY KEY,
    state TEXT NOT NULL DEFAULT 'NUEVO',
    customer_name TEXT,
    customer_needs TEXT,
    lead_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Copiar datos (solo columnas originales)
INSERT INTO conversations_backup
SELECT
    whatsapp_id,
    state,
    customer_name,
    customer_needs,
    lead_id,
    created_at,
    updated_at
FROM conversations;

-- Eliminar tabla actual
DROP TABLE conversations;

-- Renombrar backup a original
ALTER TABLE conversations_backup RENAME TO conversations;

-- Recrear índices originales
CREATE INDEX IF NOT EXISTS idx_conversations_state ON conversations(state);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at);

-- Recrear trigger original
CREATE TRIGGER IF NOT EXISTS update_conversations_timestamp
AFTER UPDATE ON conversations
BEGIN
    UPDATE conversations
    SET updated_at = CURRENT_TIMESTAMP
    WHERE whatsapp_id = NEW.whatsapp_id;
END;

COMMIT;
*/

-- ================================================================
-- VERIFICACIÓN
-- ================================================================

-- Verificar que los campos fueron eliminados
SELECT name, type
FROM pragma_table_info('conversations');

-- Debe mostrar solo las columnas originales:
-- whatsapp_id, state, customer_name, customer_needs, lead_id,
-- created_at, updated_at
