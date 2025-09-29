# 🤖 Agente IA Multiagentes para Automatización de Leads

## 📋 Descripción del Proyecto

Este proyecto desarrolla un **sistema inteligente de automatización** para empresas que utilizan WhatsApp Business como canal principal de atención al cliente. El sistema elimina los procesos manuales de transferencia de información y acelera significativamente el tiempo de respuesta a los clientes potenciales.

### 🎯 ¿Qué Problema Resuelve?

**Situación Actual:**
- Los clientes escriben a WhatsApp Business
- Un chatbot (Chatling) recopila información básica
- **Una persona debe revisar manualmente** cada conversación
- Esa persona transfiere los datos al CRM Leadsales
- Finalmente se asigna un asesor especializado

**Problema:** Este proceso manual genera **retrasos significativos** y cuellos de botella que afectan la experiencia del cliente y la eficiencia del equipo de ventas.

### ✨ Nuestra Solución

Desarrollamos un **sistema de múltiples agentes de IA especializados** que automatiza completamente el flujo de atención:

🎭 **Agente de Recepción**
- Saluda y recopila datos básicos del cliente
- Clasifica automáticamente las consultas

📚 **Agente de Soporte**  
- Responde preguntas usando base de conocimiento (RAG)
- Proporciona información instantánea y precisa

💼 **Agente de Leadsales**
- Crea automáticamente leads en el CRM
- Activa transferencia inmediata a asesores humanos

### 🚀 Beneficios

✅ **Respuesta Instantánea**: De minutos/horas a segundos  
✅ **Eliminación de Trabajo Manual**: 100% automatizado  
✅ **Mejor Experiencia de Cliente**: Atención 24/7 sin demoras  
✅ **Eficiencia del Equipo**: Asesores se enfocan en cerrar ventas  
✅ **Escalabilidad**: Maneja múltiples conversaciones simultáneamente  

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python + FastAPI
- **IA**: gpt - 4o - mini
- **Base de Conocimiento**: RAG (Retrieval Augmented Generation)
- **Comunicación**: WhatsApp Business API (Meta)
- **CRM**: Integración directa con Leadsales API
- **Despliegue**: Railway.app
- **Base de Datos**: SQLite + Vector Database

## 📊 Arquitectura del Sistema

El sistema utiliza una **arquitectura de microservicios** con múltiples agentes especializados:

```
Usuario WhatsApp → Orquestador Central → Agentes Especializados → CRM/Respuesta
```

Cada agente tiene una responsabilidad específica y trabaja de manera coordinada para proporcionar la mejor experiencia posible.

## 🎯 Estado Actual del Proyecto

### ✅ Completado
- **Fase 0**: Investigación y validación técnica
- **Fase 1**: Planeación y diseño de arquitectura
- **Infraestructura**: Estructura de carpetas y configuración inicial

### 🔄 En Desarrollo
- **Implementación de Agentes**: Desarrollo de los 3 agentes especializados
- **Integración con APIs**: WhatsApp, Gemini y Leadsales
- **Sistema RAG**: Base de conocimiento vectorial

### 📅 Próximamente
- **Testing Completo**: Pruebas end-to-end
- **Despliegue en Railway**: Puesta en producción
- **Optimización**: Mejoras de rendimiento y costos

## 🚦 Cómo Funciona

1. **Cliente envía mensaje** por WhatsApp Business
2. **Orquestador** recibe y analiza el mensaje
3. **Agente de Recepción** saluda y recopila datos básicos
4. **Clasificación inteligente**:
   - Si es pregunta → **Agente de Soporte** responde con RAG
   - Si es necesidad → **Agente de Leadsales** crea lead automáticamente
5. **Transferencia a humano**: Asesor especializado toma control
6. **Seguimiento**: Gestión completa en CRM Leadsales

## 💰 Impacto Empresarial

**Métricas Objetivo:**
- **Tiempo de respuesta**: De 2-24 horas → < 3 segundos
- **Procesamiento**: ~70 mensajes/día automatizados
- **Eficiencia**: 100% eliminación de trabajo manual
- **Disponibilidad**: 24/7 sin interrupciones

## 🔐 Consideraciones de Seguridad

- Validación de webhooks con firma HMAC
- Variables de entorno para credenciales
- Protocolo de handoff robusto
- Logs detallados para auditoría

## 👥 Equipo de Desarrollo

Este proyecto está siendo desarrollado como una solución moderna, escalable y orientada al futuro para empresas que buscan automatizar sus procesos de atención al cliente sin perder la calidad humana en la experiencia final.

---

**Estado del Proyecto**: 🔄 En Desarrollo Activo  
**Última Actualización**: Septiembre 2024  
**Licencia**: Propietario
