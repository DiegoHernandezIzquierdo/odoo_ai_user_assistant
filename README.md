
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
