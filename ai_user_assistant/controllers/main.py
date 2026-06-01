# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import requests
import logging
import json

from odoo.addons.ai_user_assistant.agents.router_agent import RouterAgent
from odoo.addons.ai_user_assistant.agents.action_project_agent import ActionProjectAgent
from odoo.addons.ai_user_assistant.agents.usage_agent import UsageAgent
from odoo.addons.ai_user_assistant.agents.document_agent import DocumentAgent
from odoo.addons.ai_user_assistant.agents.db_agent import DbAgent
from odoo.addons.ai_user_assistant.agents.navigation_agent import NavigationAgent 

_logger = logging.getLogger(__name__)

class AiUserAssistantController(http.Controller):

    @http.route('/ai_assistant/ask', type='json', auth='user')
    def ask_ai(self, question, context_data):
        api_key_raw = request.env['ir.config_parameter'].sudo().get_param('ai_user_assistant.api_key')
        api_key = api_key_raw.strip() if api_key_raw else None

        if not api_key or api_key == '12345':
            return {'status': 'error', 'message': 'API Key no configurada.'}

        MessageModel = request.env['ai.assistant.message'].sudo()
        MessageModel.create({'user_id': request.env.uid, 'role': 'user', 'content': question})

        recent_history_records = MessageModel.search(
            [('user_id', '=', request.env.uid)], order='create_date desc', limit=20
        )
        chat_history = [{'role': r.role, 'content': r.content} for r in reversed(recent_history_records)]

        try:
            router = RouterAgent(request.env, self._call_openai, api_key)
            route_data = router.execute(question, chat_history)
            route = route_data.get('route', 'general')
            tokens_used_intent = route_data.get('tokens', 0)
            _logger.info('🤖 Enrutador decidió la ruta: %s', route)
        except Exception as e:
            _logger.error('Error en el Enrutador: %s', str(e))
            route = 'general'
            tokens_used_intent = 0

        tokens_used_total = tokens_used_intent
        answer = ''
        action_dict = None # NUEVO: Variable para guardar la orden de navegación
        tokens_used_main = 0

        # --- BLOQUES DE ENRUTAMIENTO ---

        if route == 'documents':
            _logger.info('Iniciando flujo DOCUMENTS...')
            agente = DocumentAgent(request.env, self._call_openai, api_key)
            resultado = agente.execute(question, chat_history)
            answer = resultado.get('answer', 'Error obteniendo respuesta.')
            tokens_used_main = resultado.get('tokens', 0)

        elif route == 'database':
            _logger.info('Iniciando flujo DATABASE...')
            agente = DbAgent(request.env, self._call_openai, api_key)
            resultado = agente.execute(question, chat_history)
            answer = resultado.get('answer', 'Error obteniendo respuesta.')
            tokens_used_main = resultado.get('tokens', 0)

        elif route == 'action_project':
            _logger.info('Iniciando flujo ACTION/PROJECT...')
            agente = ActionProjectAgent(request.env, self._call_openai, api_key)
            resultado = agente.execute(question, chat_history)
            answer = resultado.get('answer', 'Error obteniendo respuesta.')
            tokens_used_main = resultado.get('tokens', 0)

        # NUEVO BLOQUE: Flujo para la Navegación
        elif route == 'navigation':
            _logger.info('Iniciando flujo NAVIGATION...')
            agente = NavigationAgent(request.env, self._call_openai, api_key)
            resultado = agente.execute(question, chat_history)
            answer = resultado.get('answer', 'Error obteniendo respuesta de navegación.')
            action_dict = resultado.get('action') # Capturamos el diccionario de Odoo
            tokens_used_main = resultado.get('tokens', 0)

        else:
            _logger.info('Iniciando flujo GENERAL...')
            agente = UsageAgent(request.env, self._call_openai, api_key)
            resultado = agente.execute(question, context_data, chat_history)
            if resultado.get('status') == 'error':
                return {'status': 'error', 'message': resultado.get('message')}
            answer = resultado.get('answer', 'Error obteniendo respuesta.')
            tokens_used_main = resultado.get('tokens', 0)

        # --- GUARDADO Y RETORNO ---

        try:
            tokens_used_total += tokens_used_main
            MessageModel.create({'user_id': request.env.uid, 'role': 'assistant', 'content': answer})

            IrConfigParameter = request.env['ir.config_parameter'].sudo()
            current_total_str = IrConfigParameter.get_param('ai_user_assistant.total_tokens_consumed', default='0')
            current_total = int(current_total_str) if current_total_str.isdigit() else 0
            IrConfigParameter.set_param('ai_user_assistant.total_tokens_consumed', str(current_total + tokens_used_total))

            # NUEVO: Preparamos la respuesta final incluyendo el 'action' si existe
            response_data = {
                'status': 'success', 
                'answer': answer, 
                'tokens': tokens_used_total
            }
            if action_dict:
                response_data['action'] = action_dict
                
            return response_data
            
        except Exception as e:
            return {'status': 'error', 'message': f'Error interno guardando la respuesta: {str(e)}'}

    def _call_openai(self, api_key, system_prompt, env_context, chat_history):
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}

        messages = [{'role': 'system', 'content': f'{system_prompt}\n\n[Contexto actual extraído de Odoo]:\n{env_context}'}]
        for msg in chat_history:
            if msg.get('content'):
                messages.append({'role': msg['role'], 'content': msg['content']})

        payload = {'model': 'gpt-4o-mini', 'messages': messages, 'temperature': 0.2}
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code != 200:
            raise Exception(f'Error HTTP {response.status_code}: {response.text}')

        resp_json = response.json()
        return {'content': resp_json['choices'][0]['message']['content'], 'tokens': resp_json.get('usage', {}).get('total_tokens', 0)}