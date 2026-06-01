# AI User Assistant

Este módulo añade un asistente virtual inteligente a tu aplicación de Odoo para resolver dudas de los usuarios en tiempo real. El asistente cuenta con dos funciones principales: entender el contexto actual de la pantalla para explicar el uso de los módulos (campos específicos o flujos de trabajo) y buscar archivos adjuntos mediante filtros basados en lenguaje natural, detallando los pasos seguidos para encontrarlos.

---

## Índice

1. [Descripción](#descripción)
2. [Dependencias de Módulos](#dependencias-de-módulos)
3. [Configuración Inicial](#configuración-inicial)
   - [Parámetros del Sistema](#parámetros-del-sistema)
   - [Permisos de Usuario](#permisos-de-usuario)
4. [Funcionalidades](#funcionalidades)
   - [Asistente Virtual](#asistente-virtual)
   - [Historial de Mensajes](#historial-de-mensajes)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Posibles Fallos y Solución de Problemas](#posibles-fallos-y-solución-de-problemas)

---

## Descripción

**AI User Assistant** actúa como un guía interactivo dentro de Odoo. Está diseñado para:
- **Interactuar según el contexto:** Entiende en qué vista o formulario se encuentra el usuario y responde a preguntas sobre el funcionamiento de campos específicos o flujos completos del negocio.
- **Búsqueda Avanzada de Adjuntos:** Filtra e indexa archivos adjuntos según las peticiones en lenguaje natural del usuario, mostrando los pasos lógicos que el sistema ha seguido para localizarlos.

---

## Dependencias de Módulos

Para el correcto funcionamiento de todas las características avanzadas, el módulo requiere la instalación de complementos adicionales (Odoo nativo u OCA) que dotan a las vistas de capacidades especiales:

* **Visualizador de contenido indexado (`odx_attachment_preview_kanban`):**
  Por defecto, Odoo almacena el "Contenido indexado" de los adjuntos. Sin embargo, en documentos complejos como archivos `.pdf`, este contenido suele quedar como nulo o mostrar el texto `"application"`. Es estrictamente necesario instalar el módulo `odx_attachment_preview_kanban` para que el asistente pueda realizar consultas y filtrados precisos sobre el contenido interno de los archivos adjuntos.

---

## Configuración Inicial

Para poner en marcha el asistente, un usuario administrador debe realizar la configuración de los parámetros del sistema y la asignación de permisos correspondientes.

### Parámetros del Sistema

Navega a **Ajustes → Técnico → Parámetros del sistema** y configura las siguientes claves de forma exacta:

1. **Configurar la API Key:**
   - **Clave:** *(Utilizar el nombre de clave técnica exacto provisto por el módulo, ej. `openai_api_key`)*
   - **Valor:** Introduce tu clave API de **OpenAI** activa.
2. **Contador de tokens:**
   - **Clave:** *(Utilizar el nombre de clave técnica exacto provisto por el módulo, ej. `total_token_counter`)*
   - **Valor:** `0` (Debe inicializarse obligatoriamente en cero para comenzar la estimación de costes y el control del consumo global de los usuarios).

> ⚠️ **IMPORTANTE:** Las claves de los parámetros deben coincidir exactamente con la nomenclatura interna del módulo para que el sistema reconozca y aplique la configuración.

### Permisos de Usuario

Los grupos de permisos se instalan automáticamente con el módulo, pero la asignación a los usuarios no administradores es manual:

1. Ve a **Ajustes → Gestionar usuarios → Usuarios**.
2. Selecciona el usuario al que deseas conceder acceso.
3. Activa la casilla o grupo de **Acceso al Asistente**. 
*Sin este permiso, los usuarios no podrán visualizar los componentes del asistente en su interfaz.*

---

## Funcionalidades

### Asistente Virtual

- **Acceso:** Se despliega haciendo clic en el icono de la **varita mágica** (🪄) ubicado en la barra superior derecha de la aplicación Odoo.
- **Interfaz de Chat:** Abre una ventana lateral de conversación interactiva. 
- **Memoria por sesión:** El asistente tiene memoria contextual basada en el historial exclusivo con ese usuario específico. La memoria e información entre dos usuarios distintos nunca se comparte.
- **Contador de tokens local:** En la parte inferior del cuadro de texto se muestra un indicador en tiempo real con los tokens consumidos durante la conversación actual.

### Historial de Mensajes

- **Acceso:** Se ingresa directamente a través del icono del módulo en el tablero principal o menú lateral de Odoo.
- **Estructura:** Presenta una vista de tipo árbol (`tree view`) donde los mensajes están ordenados cronológicamente.
- **Formato:** Las respuestas generadas por la IA se registran bajo el rol de "Asistente" y se visualizan en texto plano (sin los estilos CSS o Markdown aplicados en la ventana flotante del chat).

---

## Ejemplos de Uso

* **Flujo de la aplicación:** Puedes solicitar guías paso a paso de procesos de negocio. *Ejemplo: "¿Cómo puedo generar una factura desde un pedido de venta?"* y el asistente devolverá la lista ordenada de acciones.
* **Consulta acerca de la vista actual:** Preguntas directas sobre la pantalla en la que te encuentras. El asistente analiza el modelo y los campos activos para explicar su utilidad.
* **Consulta de adjuntos:** Solicitudes como: *"Muéstrame los archivos adjuntos del módulo de contactos"*. El asistente responderá con un listado de enlaces directos para la descarga de dichos archivos y permite búsquedas cruzadas por contenido indexado.
* **Consulta directa a la base de datos:** El asistente calcula datos agregados en tiempo real. *Ejemplo: pedir el número exacto de contactos registrados*, devolviendo un valor coincidente con el total de registros del sistema.
* **Navegación inteligente:** Utilizando la palabra clave **"llévame"** (ej. *"llévame a las facturas de este mes"*), el asistente redirigirá automáticamente al usuario a la vista correspondiente con los filtros ya aplicados, sin importar el módulo donde se inició la consulta.
* **CRUD de tareas:** Flujo completo de gestión para tareas. Permite solicitar la creación de una tarea mediante comandos de voz o texto, interactuar con ella y posteriormente solicitar su eliminación.

---

## Posibles Fallos y Solución de Problemas

La mayoría de las incidencias ocurren debido a configuraciones incompletas o limitaciones actuales del modelo de IA:

| Fallo / Síntoma | Causa Probable | Solución |
| :--- | :--- | :--- |
| **Error de API Key no configurada** | El sistema no encuentra la clave de OpenAI en los parámetros técnicos. | El administrador debe verificar en Parámetros del Sistema que la clave esté bien escrita y tenga un token válido. |
| **No aparece el icono de la varita o el asistente** | El usuario activo no tiene los permisos necesarios asignados. | El administrador debe ir a la ficha del usuario en Ajustes y activar el permiso **Acceso al Asistente**. |
| **Flujos de indicaciones incorrectos** | Se está consultando sobre un módulo que tiene personalizaciones avanzadas o desarrollos a medida. | La base de conocimiento general del asistente puede requerir ajustes si el flujo estándar de Odoo fue modificado. |
| **Respuestas inadecuadas o falta de interconexión** | Los agentes especializados del asistente cumplen tareas específicas (Cálculo, Navegación, CRUD) pero aún no están totalmente interconectados entre sí. | Por ejemplo, pedir un cálculo matemático y solicitar simultáneamente a la navegación que te lleve a una vista con ese resultado exacto puede fallar. Se recomienda realizar las peticiones por separado. |
| **Fallos en el CRUD (Crear, Leer, Actualizar y Borrar)** | El agente CRUD se encuentra en fase de entrenamiento continuo para la actualización de registros. | Actualmente la función CRUD está limitada y optimizada **únicamente para el modelo de tareas**. No intente aplicar estas acciones en otros módulos de forma masiva. |
