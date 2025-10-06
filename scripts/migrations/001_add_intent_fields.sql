-- ================================================================
-- MIGRACIÓN 001: Agregar Campos para Clasificación de Intención
-- ================================================================
-- PR: #1 - Fundamentos
-- Fecha: 2025-10-02
-- Descripción: Agrega campos necesarios para extracción LLM y
--              validación de horarios laborales
-- ================================================================

BEGIN TRANSACTION;

-- Verificar que la tabla existe
-- Si no existe, el script fallará aquí
SELECT COUNT(*) FROM conversations LIMIT 1;

-- ================================================================
-- NUEVOS CAMPOS
-- ================================================================

-- 1. Intención clasificada por LLM
-- Valores: greeting, property_search, support, job, media, call_request, unclear
ALTER TABLE conversations ADD COLUMN intent TEXT;

-- 2. Datos extraídos por LLM (JSON serializado)
-- Estructura: {property_type, location, budget, rooms, bathrooms, urgency, current_situation}
ALTER TABLE conversations ADD COLUMN extracted_data TEXT;

-- 3. Validación de horario laboral
-- 1 = en horario, 0 = fuera de horario
ALTER TABLE conversations ADD COLUMN business_hours_valid INTEGER DEFAULT 1;

-- 4. Timestamp del último mensaje
-- Útil para limpieza y analytics
ALTER TABLE conversations ADD COLUMN last_message_at TIMESTAMP;

-- 5. Contador de interacciones (persistente)
-- Antes solo en memoria, ahora en BD
ALTER TABLE conversations ADD COLUMN interaction_count INTEGER DEFAULT 0;

-- 6. Datos del formulario de calificación (JSON serializado)
-- Estructura: {tiene_contrato_inmobiliaria, inmobiliaria_actual,
--              tiene_solicitud_libertador, fecha_necesidad, timestamps}
ALTER TABLE conversations ADD COLUMN form_data TEXT;

-- ================================================================
-- ACTUALIZAR VALORES INICIALES
-- ================================================================

-- Inicializar last_message_at con updated_at para registros existentes
UPDATE conversations SET last_message_at = updated_at WHERE last_message_at IS NULL;

-- ================================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ================================================================

-- Índice para búsqueda por intención
CREATE INDEX IF NOT EXISTS idx_conversations_intent ON conversations(intent);

-- Índice para búsqueda por horario
CREATE INDEX IF NOT EXISTS idx_conversations_business_hours ON conversations(business_hours_valid);

-- Índice para búsqueda por último mensaje (limpieza)
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON conversations(last_message_at);

-- Índice compuesto: estado + horario (para analytics)
CREATE INDEX IF NOT EXISTS idx_conversations_state_hours
ON conversations(state, business_hours_valid);

-- ================================================================
-- TRIGGER: Actualizar last_message_at automáticamente
-- ================================================================

-- Eliminar trigger si existe (para re-ejecutar migración)
DROP TRIGGER IF EXISTS update_last_message_at;

-- Crear trigger para actualizar last_message_at en cada UPDATE
CREATE TRIGGER update_last_message_at
AFTER UPDATE ON conversations
WHEN NEW.whatsapp_id IS NOT NULL
BEGIN
    UPDATE conversations
    SET last_message_at = CURRENT_TIMESTAMP
    WHERE whatsapp_id = NEW.whatsapp_id;
END;

-- ================================================================
-- COMMIT Y VERIFICACIÓN
-- ================================================================

COMMIT;

-- Verificar que los campos se agregaron correctamente
SELECT
    name,
    type,
    (SELECT COUNT(*) FROM conversations) as total_rows
FROM pragma_table_info('conversations')
WHERE name IN ('intent', 'extracted_data', 'business_hours_valid',
               'last_message_at', 'interaction_count', 'form_data');

-- Mostrar estadísticas finales
SELECT
    COUNT(*) as total_conversations,
    COUNT(intent) as conversations_with_intent,
    COUNT(extracted_data) as conversations_with_extracted_data,
    SUM(business_hours_valid) as conversations_in_hours,
    SUM(CASE WHEN business_hours_valid = 0 THEN 1 ELSE 0 END) as conversations_out_hours
FROM conversations;

-- ================================================================
-- RESULTADO ESPERADO
-- ================================================================
-- Si la migración fue exitosa, deberías ver:
-- - 6 filas con los nombres de los nuevos campos
-- - 4 índices creados
-- - 1 trigger creado
-- - Estadísticas de la tabla actualizada
-- ================================================================
