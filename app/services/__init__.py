'''
4 Servicios Externos
Tu sistema se conecta a 4 servicios externos:
    -OpenAI API (GPT-4o-mini) → Inteligencia artificial
    -WhatsApp Business API (Meta/Facebook) → Mensajería
    -Leadsales CRM API → Gestión de leads
    -SQLite Database → Base de datos local (técnicamente no es externa, pero es un servicio)

SERVICIO EXTERNO LLM

¿Qué hace?
Es el "cerebro" del sistema. Cuando un cliente escribe, este servicio lee el mensaje y decide:
    -¿Es una pregunta o una necesidad de comprar/arrendar?
    -¿Qué información quiere el cliente? (extrae: nombre, presupuesto, zona, tipo de propiedad)
    -¿Qué responder? (genera respuestas naturales usando documentos de la empresa)
'''

#---------------

'''
WHATSAPP BUSINESS API

¿Qué hace?
Conecta tu sistema con WhatsApp para recibir y enviar mensajes. ¿Cómo funciona?
Cuando un cliente te escribe por WhatsApp, Facebook te notifica (webhook)
Tu sistema procesa el mensaje
Luego envía la respuesta de vuelta por WhatsApp'''

#---------------

'''
LEADSALES CRM API

¿Qué hace?
Guarda los clientes potenciales (leads) en un sistema externo llamado "Leadsales CRM". Es como un Excel inteligente donde se registran todos los clientes interesados. 

¿Cómo funciona?
Cuando un cliente completa el flujo de conversación, el sistema envía sus datos al CRM de Leadsales con toda la información recopilada:
    -Nombre
    -WhatsApp
    -Qué busca (apartamento, casa, etc.)
    -Presupuesto
    -Zona de interés
    -Urgencia
    -Calidad del lead (score 0-100)
    -Tags automáticas (COMPRA, URGENTE, POBLADO, etc.)

Dos modos:
Modo Demo: No envía datos reales, solo simula y muestra en la terminal
Modo Producción: Envía datos reales al CRM de Leadsales vía internet

Para qué sirve:
Los asesores ven los leads en el CRM ordenados por prioridad
Pueden ver quién contactar primero
Tienen toda la información del cliente
Evita perder clientes potenciales
'''

'''
SQL DATABASE

¿Qué hace?
Guarda el historial de conversaciones localmente en tu computador/servidor, como un archivo de Excel pero más eficiente. 

¿Por qué es necesario?
Si el servidor se reinicia, el sistema recuerda dónde quedó la conversación con cada cliente. Sin esto, cada vez que el servidor se apague, perdería toda la información. 

¿Qué guarda?
- Estado de la conversación (en qué paso va)
- Nombre del cliente
- Respuestas a las 10 preguntas del flujo
- Historial completo de mensajes
- Fecha de inicio y última actualización
'''

#---------------

'''

1. Cliente envía mensaje por WhatsApp
   ↓
2. Meta (Facebook) envía webhook a tu servidor
   ↓
3. main.py recibe webhook → extrae mensaje
   ↓
4. FactoryOrchestrator procesa mensaje
   ↓
5. StateManager consulta SQLite → obtiene estado de conversación
   ↓
6. ReceptionAgent/SupportAgent/LeadsalesAgent procesa
   ↓
7. LLMService (OpenAI) clasifica intención y genera respuesta (Aqui deberia ur tambien el scoring)
   ↓
8. StateManager actualiza SQLite con nueva información
   ↓
9. Si es lead completo → LeadsalesService envía a CRM
   ↓
10. WhatsAppService envía respuesta al cliente

'''