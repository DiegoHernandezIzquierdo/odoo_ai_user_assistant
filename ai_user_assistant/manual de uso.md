# Manual de Uso - AI User Assistant

## ¿Qué es este módulo?

El módulo **AI User Assistant** agrega un asistente de inteligencia artificial dentro de Odoo para ayudar a los usuarios a resolver dudas operativas sin abandonar la aplicación.

El asistente detecta el contexto actual y ofrece respuestas prácticas basadas en el modelo, la vista y los campos visibles en la pantalla.

---

## ¿Dónde se instala?

El módulo debe estar disponible en la carpeta de addons personalizados de Odoo. En este caso, la ruta es:

`/opt/odoo/custom/addons/ai_user_assistant/`

---

## Instalación paso a paso

1. Accede a Odoo como administrador.
2. Ve a **Aplicaciones**.
3. Haz clic en **Actualizar lista de aplicaciones**.
4. Busca el módulo por su nombre: **AI User Assistant**.
5. Haz clic en **Instalar**.
6. Espera a que finalice la instalación.

> Si no encuentras el módulo, revisa que la carpeta `ai_user_assistant` esté en el directorio de addons personalizados y que el servidor de Odoo haya sido reiniciado si hace falta.

---

## Requisitos previos

Para el usuario final no hace falta instalar nada extra, pero el administrador debe configurar:

- `base`
- `web`
- `base_setup`

Además, el módulo requiere una **API Key de OpenAI** y conectividad desde el servidor de Odoo hacia `api.openai.com`.

---

## Configuración del administrador

1. Ve a **Settings**.
2. Busca la sección **Asistente de IA (Contextual)**.
3. Selecciona `OpenAI` como proveedor.
4. Ingresa la `API Key de la IA`.
5. Guarda los cambios.

Esta configuración se guarda automáticamente en los parámetros de sistema de Odoo.

---

## Permisos y accesos

- El asistente solo se muestra a usuarios con el grupo `Acceso a Asistente`.
- El grupo `Settings / Usuario del sistema` hereda este acceso.

Si un usuario no ve el icono del asistente, puede ser porque no tiene permisos.

---

## ¿Cómo usarlo?

### 1. Localiza el icono del asistente

Después de instalar el módulo, aparece un icono en la esquina superior derecha de la interfaz de Odoo.

### 2. Abre la ventana de chat

Haz clic en el icono para abrir el chat flotante.

### 3. Escribe tu pregunta

Ejemplos de preguntas:

- "¿Para qué sirve este campo?"
- "¿Cómo creo una factura?"
- "¿Qué debo hacer aquí?"
- "Busca el contrato del cliente X."

### 4. Envía tu pregunta

Presiona **Enter** o haz clic en el botón de enviar.

### 5. Revisa la respuesta

La respuesta se muestra dentro de la ventana de chat. Si la IA sugiere una acción de navegación, el sistema puede abrir automáticamente la vista relacionada.

---

## Funcionalidades destacadas

- **Contexto visual:** el asistente analiza el modelo, la vista y los campos visibles.
- **Navegación asistida:** puede abrir la vista correcta si la respuesta lo necesita.
- **Reconocimiento de voz:** si tu navegador lo soporta, puedes usar dictado para escribir la pregunta.
- **Historial de chat:** mantiene el contexto de la conversación.

---

## Problemas comunes y soluciones

### No veo el icono del asistente

- Verifica que el módulo esté instalado.
- Asegúrate de tener el grupo `Acceso a Asistente`.
- Refresca la página con `Ctrl+F5`.
- Cierra sesión y vuelve a iniciar sesión.

### El asistente no responde

- Comprueba que el administrador haya ingresado la `API Key de la IA`.
- Verifica la conectividad desde el servidor a `api.openai.com`.
- Revisa que el proveedor seleccionado sea `OpenAI`.

### La respuesta es genérica o imprecisa

- Añade más detalles en la pregunta.
- Describe el campo, vista o proceso que estás utilizando.
- Pregunta con un ejemplo concreto.

---

## Consejos para usuarios

- Usa el asistente como ayuda rápida, no como reemplazo total del proceso.
- Si la operación es compleja, confirma los pasos con tu procedimiento interno.
- Pregunta por campos, botones y flujos específicos de la vista actual.

---

## Resumen

El asistente facilita el uso de Odoo permitiendo obtener ayuda contextual sin cambiar de ventana. Solo necesitas hacer clic en el icono del asistente, escribir tu pregunta y seguir la respuesta del chat.
