# EXTRACCIÓN COMPLETA: INTENCIÓN + ENTIDADES

EXTRACT_INTENT_AND_ENTITIES = """Analiza el mensaje del usuario y extrae la intención principal y entidades relevantes.

**MENSAJE DEL USUARIO:**
{message}

**CONTEXTO DE LA CONVERSACIÓN:**
{context}

**INSTRUCCIONES:**
1. Identifica la intención principal del usuario
2. Extrae todas las entidades mencionadas
3. Asigna un nivel de confianza (0.0-1.0)
4. Proporciona razonamiento breve

**CATEGORÍAS DE INTENCIÓN:**
- **greeting**: Saludo simple sin necesidad específica
  Ejemplo: "Hola", "Buenos días", "¿Cómo estás?"

- **property_search**: Búsqueda de inmueble para compra/arriendo
  Ejemplo: "Busco apartamento", "Quiero comprar casa"

- **support**: Consulta informativa, problema técnico, ayuda
  Ejemplo: "Tengo un problema", "¿Cómo funciona...?", "Necesito ayuda"

- **job**: Búsqueda de empleo, postulación
  Ejemplo: "Busco trabajo", "¿Tienen vacantes?", "Quiero aplicar"

- **media**: Usuario envió imagen, video, audio o documento
  Ejemplo: "Te envío una foto", mensaje contiene URL

- **call_request**: Usuario solicita llamada telefónica
  Ejemplo: "Llámenme", "Prefiero hablar por teléfono"

- **unclear**: Mensaje ambiguo o insuficiente información
  Ejemplo: "Ok", "No sé", mensajes muy cortos

**ENTIDADES A EXTRAER:**
- **nombre**: Nombre de la persona (si se presenta)
- **property_type**: Tipo de inmueble (apartamento, casa, local, lote, etc.)
- **location**: Ubicación o zona mencionada
- **budget**: Presupuesto o rango de precio mencionado (en número)
- **rooms**: Número de habitaciones
- **bathrooms**: Número de baños
- **urgency**: Timeframe o urgencia (ej: "para marzo", "urgente", "1-3 meses")
- **current_situation**: Situación actual (ej: "tengo contrato vigente")

**NIVEL DE CONFIANZA:**
- 0.9-1.0: Muy alta confianza, mensaje claro y específico
- 0.75-0.89: Alta confianza, intención evidente
- 0.5-0.74: Media confianza, intención probable pero ambigua
- 0.0-0.49: Baja confianza, mensaje poco claro

**FORMATO DE RESPUESTA (JSON obligatorio):**
{{
  "nombre": "string o null",
  "intent": "una de las categorías",
  "confidence": 0.0-1.0,
  "entities": {{
    "property_type": "string o null",
    "location": "string o null",
    "budget": "number o null",
    "rooms": "number o null",
    "bathrooms": "number o null",
    "urgency": "string o null",
    "current_situation": "string o null"
  }},
  "reasoning": "Breve explicación de la clasificación (1-2 líneas)"
}}

**EJEMPLOS:**

Mensaje: "Hola, soy Carlos y busco apartamento en Chapinero de 2 habitaciones"
{{
  "nombre": "Carlos",
  "intent": "property_search",
  "confidence": 0.95,
  "entities": {{
    "property_type": "apartamento",
    "location": "Chapinero",
    "budget": null,
    "rooms": 2,
    "bathrooms": null,
    "urgency": null,
    "current_situation": null
  }},
  "reasoning": "Usuario se presenta y expresa búsqueda específica con tipo, ubicación y características"
}}

Mensaje: "Tengo un problema con el pago de mi arriendo"
{{
  "nombre": null,
  "intent": "support",
  "confidence": 0.88, 
  "entities": {{}},
  "reasoning": "Usuario reporta problema relacionado con pagos, requiere soporte administrativo"
}}

Ahora analiza el mensaje proporcionado y responde SOLO con el JSON."""

# EXTRACCIÓN SOLO NOMBRE
EXTRACT_NAME_ONLY = """Extrae ÚNICAMENTE el nombre de la persona del siguiente mensaje.

**MENSAJE:**
{message}

**INSTRUCCIONES:**
- Si el mensaje contiene un nombre, extráelo completo
- Si hay presentación formal (ej: "Soy Carlos", "Me llamo María"), extrae el nombre
- Si NO hay nombre, responde con null
- Devuelve solo el nombre, sin títulos ni apellidos adicionales innecesarios

**FORMATO DE RESPUESTA (JSON):**
{{
  "nombre": "string o null",
  "confidence": 0.0-1.0
}}

**EJEMPLOS:**

Mensaje: "Hola, soy Carlos"
{{"nombre": "Carlos", "confidence": 0.95}}

Mensaje: "Me llamo María Fernanda"
{{"nombre": "María Fernanda", "confidence": 0.95}}

Mensaje: "El Sr. Rodríguez te escribe"
{{"nombre": "Rodríguez", "confidence": 0.80}}

Mensaje: "Busco apartamento"
{{"nombre": null, "confidence": 0.0}}

Ahora analiza el mensaje y responde SOLO con el JSON."""

# EXTRACCIÓN DE CARACTERÍSTICAS DE INMUEBLE

EXTRACT_PROPERTY_FEATURES = """Extrae las características del inmueble mencionadas en el mensaje.

**MENSAJE:**
{message}

**CARACTERÍSTICAS A EXTRAER:**
- Tipo de inmueble (apartamento, casa, local comercial, lote, etc.)
- Ubicación o zona
- Presupuesto (convertir a número si es posible)
- Número de habitaciones
- Número de baños
- Características especiales (parqueadero, balcón, piscina, etc.)
- Urgencia o timeframe

**FORMATO DE RESPUESTA (JSON):**
{{
  "property_type": "string o null",
  "location": "string o null",
  "budget": "number o null",
  "rooms": "number o null",
  "bathrooms": "number o null",
  "special_features": ["array de strings"],
  "urgency": "string o null"
}}

**CONVERSIÓN DE PRESUPUESTO:**
- "2 millones" → 2000000
- "500 mil" → 500000
- "1.5M" → 1500000
- "entre 1 y 2 millones" → 1500000 (punto medio)

Responde SOLO con el JSON."""
