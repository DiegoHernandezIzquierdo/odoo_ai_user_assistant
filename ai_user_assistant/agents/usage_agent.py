"""
ai_user_assistant.agents.usage_agent

UsageAgent prepara el contexto visual y de vista para el asistente, construye el
prompt del sistema que se enviará al modelo de IA y delega la petición a la
función heredada `_call_openai`. Devuelve el contenido generado por la IA y el
conteo de tokens utilizados.
"""
import logging
from .base_agent import BaseAgent

_logger = logging.getLogger(__name__)


class UsageAgent(BaseAgent):

    def execute(self, question, context_data, chat_history):
        tokens_used = 0

        # Extraemos el modelo y el tipo de vista del contexto si vienen en forma de dict
        model_name = context_data.get('active_model', 'Desconocido') if isinstance(context_data, dict) else 'Desconocido'
        view_type = context_data.get('view_type', 'Desconocido') if isinstance(context_data, dict) else 'Desconocido'

        # `fields_info` es enviado por el frontend: lista de nombres de campos/etiquetas
        # que están visibles en la pantalla del usuario (puede estar vacía).
        visible_labels = context_data.get('fields_info', []) if isinstance(context_data, dict) else []

        advanced_fields_info = ""

        # Si la vista corresponde al dashboard o no se puede identificar la vista,
        # indicamos explícitamente al asistente que el usuario está en el menú principal
        # y que no debe basar sus respuestas en campos de formulario previos.
        if model_name in ['Dashboard Principal (Menú de Inicio)', 'Desconocido'] or view_type == 'Menú':
            advanced_fields_info = (
                "\n[ATENCIÓN: PANTALLA DE INICIO / SIN VISTA]\n"
                "El usuario está en el Menú de Inicio o en una pantalla genérica. "
                "No hay campos de formulario relevantes en este contexto, por lo que el asistente "
                "debe ignorar cualquier discusión previa sobre campos o registros visibles."
            )
        elif visible_labels:
            # Convertimos la lista de etiquetas en una cadena separada por comas para
            # insertar en el prompt y que la IA sepa exactamente qué campos puede usar.
            labels_str = ", ".join(visible_labels)
            advanced_fields_info = (
                f"\n[ATENCIÓN: CAMPOS VISIBLES EN PANTALLA]\n"
                f"Campos visibles en la pantalla: {labels_str}.\n"
            )
        else:
            # Si no se detectan etiquetas visibles, dejamos claro al asistente que no debe
            # inventar campos y que informe al usuario de la ausencia de campos detectados.
            advanced_fields_info = (
                "\n[ATENCIÓN: CAMPOS VISIBLES EN PANTALLA]\n"
                "No se han detectado campos de formulario visibles en la pantalla actual. "
                "Si el usuario pregunta por campos, responde que no hay campos detectados en lugar de inventarlos."
            )

        env_context = f"Modelo activo: {model_name}\nTipo de vista: {view_type}\n{advanced_fields_info}"

        # Construimos el prompt del sistema que define el comportamiento del asistente
        # (formato de salida, cuándo usar la información de pantalla y reglas para evitar
        # inventar campos que no estén en la lista proporcionada por el frontend).
        system_prompt = (
            "Eres el asistente técnico experto de Odoo 16.0. Tienes memoria del chat y un conocimiento profundo del ERP.\n\n"
            "Tu objetivo es doble:\n"
            "1. Responder consultas generales sobre cómo configurar, usar o entender Odoo (ej. servidores de correo, flujos de trabajo, permisos).\n"
            "2. Explicar la pantalla en la que se encuentra el usuario si te pregunta por ella.\n\n"
            "FORMATO: Responde SIEMPRE usando formato HTML estructurado (<b>, <br/>, <ul>, <li>). Prohibido usar sintaxis Markdown.\n\n"
            "REGLA DE ORO PARA LA PANTALLA ACTUAL: SOLO si el usuario te pregunta específicamente por la pantalla que está viendo, los campos o el formulario actual, "
            "básate ÚNICAMENTE en la lista de [CAMPOS VISIBLES EN PANTALLA] proporcionada en el contexto. "
            "No inventes campos ni menciones campos técnicos del chatter que no estén en la lista."
        )

        try:
            # Realizamos la llamada a la API de IA usando las propiedades y métodos heredados
            # desde `BaseAgent` (`self.api_key` y `self._call_openai`).
            ai_data = self._call_openai(self.api_key, system_prompt, env_context, chat_history)
            answer = ai_data['content']
            tokens_used = ai_data['tokens']

            return {'status': 'success', 'answer': answer, 'tokens': tokens_used}

        except Exception as e:
            _logger.error("Error en asistente IA (Flujo USO_APP): %s", str(e))
            return {'status': 'error', 'message': f'Fallo de OpenAI: {str(e)}'}