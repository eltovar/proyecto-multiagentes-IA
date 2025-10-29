"""
Prompts para clasificación de clientes mediante LLM.
Responsabilidad: Templates de prompts para detección de profesión, sofisticación, perfil.
"""

# System prompt para clasificación de cliente
CLIENT_CLASSIFICATION_SYSTEM = """Eres un experto clasificador de perfiles de clientes inmobiliarios.

Tu tarea es analizar el mensaje del cliente y clasificar su perfil profesional y nivel de sofisticación.

PERFILES PROFESIONALES:
1. **inversionista**: Compra para inversión, múltiples propiedades, ROI, flujo de caja, plusvalía
2. **arquitecto**: Menciona diseño, espacios, planos, remodelación, especificaciones técnicas
3. **ingeniero**: Enfoque técnico, estructuras, materiales, análisis detallado
4. **corredor**: Intermediario, comisión, cartera de clientes, captación
5. **empresario**: Negocio, empresa, locales comerciales, oficinas, expansión
6. **familia**: Hogar, hijos, colegios, parques, zona residencial, seguridad familiar
7. **individual**: Comprador individual sin características especiales
8. **desconocido**: No hay suficiente información para clasificar

NIVELES DE SOFISTICACIÓN:
- **alto**: Vocabulario técnico, conocimiento del mercado, análisis financiero, experiencia previa
- **medio**: Conocimiento básico, investigó opciones, tiene criterios definidos
- **bajo**: Primera vez, poco conocimiento, consultas muy generales

INSTRUCCIONES:
- Analiza el mensaje completo considerando vocabulario, intención y contexto
- Prioriza señales explícitas (ej: "soy arquitecto", "para inversión")
- Si hay ambigüedad, clasifica como perfil más probable
- Retorna SIEMPRE JSON válido con el formato especificado
- Se conciso en reasoning (máximo 2 líneas)
"""

# User prompt para clasificación
CLIENT_CLASSIFICATION_USER = """Clasifica el perfil del siguiente cliente:

**MENSAJE DEL CLIENTE:**
{customer_message}

**CONTEXTO ADICIONAL:**
{additional_context}

**RESPONDE EN FORMATO JSON:**
{{
    "profile": "inversionista|arquitecto|ingeniero|corredor|empresario|familia|individual|desconocido",
    "sophistication_level": "alto|medio|bajo",
    "confidence": 0.85,
    "reasoning": "Breve explicación de por qué se asignó este perfil",
    "detected_keywords": ["palabra1", "palabra2"],
    "profession_explicit": true
}}

**NOTAS:**
- `profession_explicit`: true si menciona explícitamente su profesión, false si es inferencia
- `confidence`: 0-1, confianza en la clasificación
- `detected_keywords`: Palabras clave que justifican la clasificación
"""

# Prompt para detección de capacidad económica (opcional, para futuro)
ECONOMIC_CAPACITY_PROMPT = """Analiza la capacidad económica estimada del cliente:

**MENSAJE DEL CLIENTE:**
{customer_message}

**INDICADORES:**
- Mención de presupuesto específico
- Rango de precios de interés
- Tipo de propiedad (casa vs apartamento, zona exclusiva)
- Vocabulario relacionado con inversión/dinero

**RESPONDE EN JSON:**
{{
    "capacity_level": "alta|media|baja|desconocida",
    "estimated_budget_range": "< 200M|200M-500M|500M-1000M|> 1000M|N/A",
    "confidence": 0.75,
    "indicators": ["presupuesto mencionado: 400M", "zona exclusiva: Poblado"]
}}
"""

# Prompt para análisis de urgencia de compra (complementario a scoring)
URGENCY_ANALYSIS_PROMPT = """Analiza la urgencia real de compra del cliente:

**MENSAJE DEL CLIENTE:**
{customer_message}

**CONVERSACIÓN PREVIA:**
{conversation_history}

**FACTORES DE URGENCIA:**
- Timeframes mencionados ("este mes", "urgente", "ya")
- Razones de urgencia (mudanza, trabajo, familia)
- Nivel de investigación previa (conoce el mercado = más urgente)
- Disponibilidad para ver propiedades

**RESPONDE EN JSON:**
{{
    "urgency_score": 0.8,
    "urgency_category": "muy_urgente|urgente|moderado|exploratorio",
    "reasoning": "Cliente menciona mudanza laboral en 2 semanas",
    "estimated_decision_timeframe": "< 1 semana|1-4 semanas|1-3 meses|> 3 meses"
}}
"""