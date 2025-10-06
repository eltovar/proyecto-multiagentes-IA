# CLASIFICACIÓN DE INTENCIÓN (ACTUAL - MANTENER COMPATIBILIDAD)

CLASSIFY_INTENTION = """Clasifica el siguiente mensaje del usuario en una de estas categorías:

**CATEGORÍAS:**
- **question**: El usuario hace una pregunta o busca información
- **need**: El usuario expresa una necesidad, quiere contratar o comprar algo
- **greeting**: Solo es un saludo sin intención clara
- **unclear**: El mensaje no es claro o no encaja en las otras categorías

**MENSAJE:**
"{message}"

Responde SOLO con un JSON en este formato:
{{"type": "categoria", "confidence": 0.8, "reasoning": "breve explicacion"}}"""

# CLASIFICACIÓN DE CATEGORÍA DE SOPORTE

CLASSIFY_SUPPORT_CATEGORY = """Clasifica el tipo de consulta de soporte del usuario.

**MENSAJE:**
{message}

**CATEGORÍAS DE SOPORTE:**

1. **reparaciones**: Problemas técnicos, daños, mantenimiento
   Keywords: "reparación", "daño", "arreglar", "mantenimiento", "plomería", "electricidad"
   Ejemplo: "Se dañó el calentador", "Necesito arreglar una fuga"

2. **pagos**: Consultas sobre pagos, facturas, cartera, cuotas
   Keywords: "pago", "factura", "cartera", "cuota", "deuda", "saldo", "cuenta"
   Ejemplo: "¿Cuándo debo pagar?", "Tengo dudas sobre mi factura"

3. **contratos**: Temas sobre contratos, terminaciones, prórrogas
   Keywords: "contrato", "terminar", "prórroga", "renovación", "cláusula"
   Ejemplo: "¿Cuándo termina mi contrato?", "Quiero renovar"

4. **juridico**: Temas legales, demandas, reportes a centrales de riesgo
   Keywords: "abogado", "legal", "demanda", "data crédito", "reporte"
   Ejemplo: "Tengo una demanda", "¿Cómo quito el reporte?"

5. **administraciones**: Cuotas de administración, multas, copropiedades
   Keywords: "administración", "multa", "copropiedad", "cuota extra"
   Ejemplo: "¿Por qué me llegó una multa?", "Consulta sobre administración"

6. **servicios_publicos**: Facturas EPM, servicios públicos, financiación
   Keywords: "EPM", "servicios públicos", "luz", "agua", "gas", "financiación"
   Ejemplo: "Pregunta sobre la factura de EPM", "¿Quién paga el gas?"

7. **general**: Consulta informativa general que no encaja en categorías específicas

**FORMATO DE RESPUESTA (JSON):**
{{
  "category": "una de las categorías",
  "confidence": 0.0-1.0,
  "suggested_contact": "WhatsApp o departamento sugerido",
  "reasoning": "Breve explicación"
}}

**CONTACTOS POR CATEGORÍA:**
- reparaciones → WhatsApp Mantenimiento: 323 515 80 07
- pagos → WhatsApp Contabilidad: 322 502 1493
- contratos → WhatsApp Contratos: 320 649 12 88
- juridico → WhatsApp Jurídico: 321 789 86 79
- administraciones → WhatsApp Administraciones: 320 609 2896
- servicios_publicos → WhatsApp Servicios Públicos: 323 508 18 84

Analiza el mensaje y responde SOLO con el JSON."""

# PROMPT TRI-PATH ROUTING (NUEVO)

CLASSIFY_TRIPATH_INTENT = """Eres un clasificador de intenciones para Inmobiliaria Proteger.

Tu tarea es clasificar el mensaje del usuario en UNO de estos 3 caminos:

## CAMINO 1: INMUEBLE (Usuario interesado en ver/comprar/arrendar inmuebles)
**Indicadores:**
- Busca apartamento, casa, local, lote, propiedad
- Quiere comprar, vender, arrendar, alquilar
- Menciona "cita", "visita", "ver inmuebles", "agendar"
- Pregunta por disponibilidad de propiedades

**Ejemplos:**
- "Busco apartamento en Medellín"
- "Quiero agendar cita para ver casas"
- "Tienen locales comerciales disponibles?"
- "Me interesa comprar un inmueble"

## CAMINO 2: DEPARTAMENTO (Consultas para departamentos específicos)
**Sub-intenciones:**
1. **propietarios**: Consultas de dueños de inmuebles
2. **proveedores**: Empresas que ofrecen servicios/materiales
3. **contratos**: Temas legales sobre contratos, renovaciones
4. **reparaciones**: Mantenimiento, daños, arreglos, emergencias
5. **abogados**: Asesoría legal, demandas, trámites jurídicos

**Ejemplos:**
- "Soy propietario, necesito reporte" → propietarios
- "Tengo una fuga de agua" → reparaciones
- "Quiero renovar contrato" → contratos
- "Soy proveedor de materiales" → proveedores
- "Necesito asesoría legal" → abogados

## CAMINO 3: GENERAL (Información corporativa/educativa)
**Indicadores:**
- Quiénes somos, misión, visión, historia, empresa
- Artículos de blog, contenido educativo, guías
- Horarios, ubicación, dirección, contacto general
- Servicios que ofrece la inmobiliaria
- Políticas, términos, condiciones

**Ejemplos:**
- "Qué servicios ofrecen?"
- "Dónde quedan ubicados?"
- "Tienen blog sobre inversión inmobiliaria?"
- "Cuál es su horario de atención?"

---

**MENSAJE DEL USUARIO:**
{message}

**CONTEXTO CONVERSACIÓN:**
- Nombre: {customer_name}
- Estado: {state}
- Consultas previas: {previous_queries}

---

**RESPONDE EN JSON CON ESTE FORMATO EXACTO:**
{{
  "intent": "inmueble" | "departamento" | "general" | "unclear",
  "sub_intent": "propietarios" | "proveedores" | "contratos" | "reparaciones" | "abogados" | null,
  "confidence": 0.0-1.0,
  "entities": {{
    "property_type": "apartamento" | "casa" | "local" | "lote" | null,
    "location": "string" | null,
    "budget": "string" | null,
    "action": "comprar" | "vender" | "arrendar" | null
  }},
  "reasoning": "Explicación breve (max 50 palabras) de por qué elegiste este camino"
}}

**REGLAS CRÍTICAS:**
- Si hay duda entre departamento y general, SIEMPRE elige departamento
- Si menciona "cita", "visita" o "agendar", SIEMPRE es inmueble
- Confidence >0.8 solo si es muy claro e inequívoco
- sub_intent solo si intent=departamento
- Si mensaje es ambiguo, usa intent="unclear" y confidence <0.5
"""

# DETECCIÓN DE SENTIMIENTO (FUTURO)

ANALYZE_SENTIMENT = """Analiza el sentimiento del siguiente mensaje.

**MENSAJE:**
{message}

**CATEGORÍAS:**
- **positivo**: Mensaje amigable, agradecido, entusiasta
- **negativo**: Mensaje hostil, quejoso, frustrado
- **neutral**: Mensaje informativo o neutro

Responde con una sola palabra: positivo, negativo o neutral."""
