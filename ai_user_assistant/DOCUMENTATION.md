# Documentación Funcional - Módulo AI User Assistant
## Asistente de IA Contextual e Inteligente para Odoo 16.0

**Versión:** 16.0.1.0.0  
**Categoría:** Productivity  
**Licencia:** AGPL-3  
**Autor:** Diego / CCBosco

---

## 📋 Tabla de Contenidos

1. [Introducción y Problema de Negocio](#introducción-y-problema-de-negocio)
2. [Arquitectura y Componentes](#arquitectura-y-componentes)
3. [Requisitos Técnicos](#requisitos-técnicos)
4. [Instalación del Módulo](#instalación-del-módulo)
5. [Guía de Configuración](#guía-de-configuración)
6. [Menús, Vistas y Navegación](#menús-vistas-y-navegación)
7. [Guía de Uso para Usuarios Finales](#guía-de-uso-para-usuarios-finales)
8. [Gestión de Conocimiento (Base de Datos)](#gestión-de-conocimiento-base-de-datos)
9. [Flujos de Negocio y Agentes](#flujos-de-negocio-y-agentes)
10. [Historial de Chat](#historial-de-chat)
11. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción y Problema de Negocio

### ¿Qué es el Asistente de IA Contextual?

El módulo **AI User Assistant** integra un asistente de inteligencia artificial en la interfaz web de Odoo. El asistente responde dudas operativas sin que el usuario tenga que salir de la aplicación.

### Problema de Negocio que Resuelve

- **Interrupción de flujos de trabajo** al buscar información externa.
- **Respuestas genéricas** sin relación con la pantalla actual.
- **Carga extra en soporte** por preguntas repetitivas.
- **Pérdida de productividad** por abandonar el proceso.

### Solución Proporcionada

Este módulo ofrece:

- **Asistente disponible en la systray** del cliente web.
- **Respuestas contextuales** según modelo, vista y campos visibles.
- **Rutas inteligentes** para preguntas de documentos, datos, acciones y navegación.
- **Gestión de conocimiento personalizada** por modelo.
- **Historial de chat** para mantener coherencia en la conversación.
- **Navegación asistida**, cuando la IA sugiere una acción de Odoo.

---

## Arquitectura y Componentes

### Estructura General

```
┌─────────────────────────────────────────────────────────┐
│                    INTERFAZ WEB (OWL)                   │
│              - Icono flotante en la systray            │
│              - Chat draggable y responsive              │
└──────────────────────┬──────────────────────────────────┘
                       │ JSON Request
                       ▼
┌─────────────────────────────────────────────────────────┐
│                CONTROLADOR (main.py)                    │
│            /ai_assistant/ask (route JSON)               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    RouterAgent                │
        │  Clasifica la pregunta en:    │
        │  • documents                  │
        │  • database                   │
        │  • action_project             │
        │  • navigation                 │
        │  • general                    │
        └──────────────────────────────┘
              │        │         │         │        
       ┌──────▼─┐  ┌───▼───┐   ┌──▼──────┐ ┌──▼────────┐
       │Documents│  │Database│   │Action │ │Navigation │
       │ Agent   │  │ Agent   │   │Project│ │Agent      │
       └────┬────┘  └───┬───┘   └────┬────┘ └────┬───────┘
           │            │           │           │
           ▼            ▼           ▼           ▼
      Busca      Consulta     Gestiona    Navega
      archivos    datos       proyectos   la UI
```

### Agentes Especializados

#### RouterAgent
- Clasifica la intención del usuario.
- Decide la ruta del procesamiento.
- Rutas: `documents`, `database`, `action_project`, `navigation`, `general`.

#### DocumentAgent
- Busca documentos y archivos adjuntos.
- Trabaja contra `ir.attachment`.
- Extrae fragmentos y enlaces relevantes.

#### DbAgent
- Resuelve consultas directas sobre registros de Odoo.
- Accede a datos y relaciones.

#### ActionProjectAgent
- Gestiona tareas y proyectos.
- Opera sobre `project.task` y `project.project`.
- Puede sugerir estados y asignaciones.

#### NavigationAgent
- Devuelve acciones de Odoo para navegar la interfaz.
- Genera `ir.actions.act_window` compatibles con el frontend.

#### UsageAgent
- Responde preguntas de uso y procedimientos.
- Captura el contexto visual: modelo activo, tipo de vista y labels visibles.
- Utiliza el historial de chat para coherencia.

---

## Requisitos Técnicos

- **Odoo 16.0 o superior**.
- **Dependencias:** `base`, `web`, `base_setup`.
- **Proveedor de IA:** OpenAI.
- **Conectividad outbound:** `api.openai.com`.

### Permisos

- Grupo `Acceso a Asistente` (`ai_user_assistant.group_ai_assistant_user`).
- El grupo `Settings / Usuario del sistema` (`base.group_system`) hereda el acceso.

---

## Instalación del Módulo

1. Copia la carpeta `ai_user_assistant` al directorio de addons personalizados de Odoo.
2. Reinicia el servidor Odoo si hace falta.
3. En Odoo, ve a **Apps** y actualiza la lista de aplicaciones.
4. Busca **AI User Assistant**.
5. Instala el módulo.
6. Verifica que aparezcan los recursos del módulo en la systray.

---

## Guía de Configuración

### Configuración de OpenAI

1. Ve a **Settings**.
2. Busca la sección **Asistente de IA (Contextual)**.
3. Selecciona `OpenAI` como proveedor.
4. Ingresa la `API Key de la IA`.
5. Guarda los cambios.

> La clave se almacena en `ir.config_parameter` como `ai_user_assistant.api_key`.

### Parámetros adicionales

- `ai_user_assistant.total_tokens_consumed`: contador de tokens usados.

---

## Menús, Vistas y Navegación

### Configuración

- El formulario de configuración se agrega a **Settings > General Settings**.
- Incluye campos para el proveedor de IA y la API Key.

### Interfaz del asistente

- Se muestra un icono emergente en la esquina superior derecha.
- La ventana de chat es draggable y responsive.
- El icono solo se activa para usuarios con permisos.

---

## Guía de Uso para Usuarios Finales

### Abrir el asistente

1. Haz clic en el icono del asistente en la systray.
2. Se abre la ventana de chat flotante.

### Enviar una pregunta

1. Escribe tu duda.
2. Presiona **Enter** o el botón de enviar.
3. Lee la respuesta en el mismo chat.
4. Si la IA sugiere una acción, el sistema puede navegar automáticamente.

### Ejemplos de uso

- "¿Para qué sirve este campo?"
- "¿Cómo creo una factura?"
- "¿Qué opciones tiene este formulario?"
- "Busca el contrato del cliente X."
- "Muestra las tareas del proyecto Ventas."

### Funcionalidades adicionales

- **Navegación asistida** en acciones de Odoo.
- **Reconocimiento de voz** en navegadores compatibles.
- **Historial de chat** para coherencia.

---

## Gestión de Conocimiento (Base de Datos)

### Modelo `ai.assistant.knowledge`

- `name`: título descriptivo.
- `model_name`: nombre técnico del modelo Odoo.
- `instructions`: instrucciones especiales para la IA.

### Uso recomendado

- Documenta reglas de negocio personalizadas.
- Describe campos ocultos o flujos específicos.
- Aclara variaciones de proceso para la instalación.

---

## Flujos de Negocio y Agentes

### Proceso de consulta

1. El usuario hace una pregunta.
2. El `RouterAgent` decide la ruta.
3. El agente especializado responde.
4. El controlador registra la conversación.
5. El frontend muestra la respuesta y ejecuta acciones si aplica.

### Rutas disponibles

- `documents`: búsqueda de archivos.
- `database`: consultas de datos.
- `action_project`: gestión de proyectos/tareas.
- `navigation`: navegación en el cliente.
- `general`: preguntas de uso.

---

## Historial de Chat

- Se guarda en `ai.assistant.message`.
- Registra `user_id`, `role` y `content`.
- Recupera los últimos 20 mensajes por usuario.
- Mantiene contexto en conversaciones multi-turno.

---

## Preguntas Frecuentes

### ¿Por qué no responde el asistente?

- No se configuró la API Key.
- El servidor no tiene acceso a `api.openai.com`.
- El usuario no pertenece al grupo `Acceso a Asistente`.

### ¿Por qué no aparece el icono?

- El módulo no está instalado.
- El usuario no tiene permisos.
- La página no se actualizó.

### ¿Qué proveedor puedo usar?

- Actualmente el módulo soporta OpenAI.

### ¿Dónde se guarda el historial?

- En el modelo `ai.assistant.message` de la base de datos.
