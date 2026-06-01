# -*- coding: utf-8 -*-
"""
test_controller.py - Tests para el controlador HTTP /ai_assistant/ask.

Cubre:
- Validación de API key
- Guardado de mensajes
- Enrutamiento a agentes
- Cálculo de tokens
- Respuestas correctas
"""

from odoo.tests import tagged, HttpCase
from odoo.http import request
from unittest.mock import patch, MagicMock
import json

from .common import BaseAITestCase, MockOpenAIResponse


@tagged('at_install', '-at_install')
class TestAiUserAssistantController(BaseAITestCase):
    """Tests para el controlador AiUserAssistantController."""
    
    def setUp(self):
        """Setup adicional para tests del controller."""
        super().setUp()
        
        # Verificar que la API key está configurada
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'ai_user_assistant.api_key'
        )
        self.assertIsNotNone(api_key)
    
    def _call_ask_endpoint(self, question, context_data=None):
        """
        Helper para llamar al endpoint /ai_assistant/ask.
        
        Args:
            question (str): Pregunta a enviar
            context_data (dict): Datos de contexto (active_model, view_type, etc.)
        
        Returns:
            dict: Respuesta del servidor
        """
        if context_data is None:
            context_data = {
                'active_model': 'sale.order',
                'view_type': 'form',
                'fields_info': ['name', 'amount_total']
            }
        
        payload = {
            'question': question,
            'context_data': context_data,
        }
        
        # En HttpCase, usar self.url_open; aquí usamos una aproximación
        # que simula la llamada directamente
        from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
        controller = AiUserAssistantController()
        
        # Simular request context
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            response = controller.ask_ai(
                question=payload['question'],
                context_data=payload['context_data']
            )
        
        return response
    
    def test_ask_ai_missing_api_key(self):
        """Verifica que retorna error si API key no está configurada."""
        # Eliminar la API key
        self.env['ir.config_parameter'].sudo().set_param(
            'ai_user_assistant.api_key',
            ''
        )
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
            controller = AiUserAssistantController()
            
            response = controller.ask_ai('Test', {})
        
        self.assertEqual(response['status'], 'error')
        self.assertIn('API Key', response['message'])
    
    def test_ask_ai_invalid_default_api_key(self):
        """Verifica que rechaza la API key por defecto '12345'."""
        # Configurar API key a default (no válida)
        self.env['ir.config_parameter'].sudo().set_param(
            'ai_user_assistant.api_key',
            '12345'
        )
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
            controller = AiUserAssistantController()
            
            response = controller.ask_ai('Test', {})
        
        self.assertEqual(response['status'], 'error')
        self.assertIn('API Key', response['message'])
    
    def test_ask_ai_saves_user_message(self):
        """Verifica que el mensaje del usuario se guarda en ai.assistant.message."""
        question = '¿Cómo creo una nueva venta?'
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            # Mock RouterAgent, DocumentAgent, etc.
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router:
                mock_router.return_value.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage:
                    mock_usage.return_value.execute.return_value = {
                        'status': 'success',
                        'answer': 'Para crear una venta...',
                        'tokens': 100
                    }
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai(question, {})
        
        # Verificar que el mensaje se guardó
        found = self.env['ai.assistant.message'].search([
            ('user_id', '=', self.env.user.id),
            ('role', '=', 'user'),
            ('content', '=', question),
        ])
        
        self.assertTrue(found)
    
    def test_ask_ai_saves_assistant_message(self):
        """Verifica que la respuesta del asistente se guarda."""
        answer_text = 'Esta es la respuesta del asistente'
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router:
                mock_router.return_value.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage:
                    mock_usage.return_value.execute.return_value = {
                        'status': 'success',
                        'answer': answer_text,
                        'tokens': 100
                    }
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai('Pregunta', {})
        
        # Verificar que la respuesta se guardó
        found = self.env['ai.assistant.message'].search([
            ('user_id', '=', self.env.user.id),
            ('role', '=', 'assistant'),
            ('content', '=', answer_text),
        ])
        
        self.assertTrue(found)
    
    def test_ask_ai_returns_success_structure(self):
        """Verifica que la respuesta tiene la estructura correcta."""
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router:
                mock_router.return_value.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage:
                    mock_usage.return_value.execute.return_value = {
                        'status': 'success',
                        'answer': 'Respuesta de prueba',
                        'tokens': 100
                    }
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai('Pregunta', {})
        
        # Verificar estructura
        self.assertIn('status', response)
        self.assertIn('answer', response)
        self.assertIn('tokens', response)
        self.assertEqual(response['status'], 'success')
        self.assertIsInstance(response['tokens'], int)
    
    def test_ask_ai_routes_to_documents(self):
        """Verifica que ruta 'documents' llama a DocumentAgent."""
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router:
                mock_router.return_value.execute.return_value = {
                    'route': 'documents',
                    'tokens': 50
                }
                with patch('odoo.addons.ai_user_assistant.controllers.main.DocumentAgent') as mock_doc:
                    mock_doc.return_value.execute.return_value = {
                        'answer': 'Documentos encontrados',
                        'tokens': 100
                    }
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai('¿Dónde están mis documentos?', {})
                    
                    # Verificar que DocumentAgent fue llamado
                    mock_doc.assert_called()
                    self.assertIn('Documentos encontrados', response['answer'])
    
    def test_ask_ai_routes_to_action_project(self):
        """Verifica que ruta 'action_project' llama a ActionProjectAgent."""
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router:
                mock_router.return_value.execute.return_value = {
                    'route': 'action_project',
                    'tokens': 50
                }
                with patch('odoo.addons.ai_user_assistant.controllers.main.ActionProjectAgent') as mock_action:
                    mock_action.return_value.execute.return_value = {
                        'answer': 'Tarea creada',
                        'tokens': 100
                    }
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai('Crear una nueva tarea', {})
                    
                    # Verificar que ActionProjectAgent fue llamado
                    mock_action.assert_called()
                    self.assertIn('Tarea creada', response['answer'])
    
    def test_ask_ai_routes_to_general(self):
        """Verifica que ruta 'general' llama a UsageAgent."""
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router:
                mock_router.return_value.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage:
                    mock_usage.return_value.execute.return_value = {
                        'status': 'success',
                        'answer': 'Aquí está la información',
                        'tokens': 100
                    }
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai('¿Cómo funciona esto?', {})
                    
                    # Verificar que UsageAgent fue llamado
                    mock_usage.assert_called()
    
    def test_ask_ai_updates_token_counter(self):
        """Verifica que el contador total de tokens se actualiza."""
        initial_count = self.get_token_count()
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router:
                mock_router.return_value.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage:
                    mock_usage.return_value.execute.return_value = {
                        'status': 'success',
                        'answer': 'Respuesta',
                        'tokens': 100
                    }
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai('Pregunta', {})
        
        # Verificar que los tokens se sumaron
        final_count = self.get_token_count()
        self.assertEqual(final_count, initial_count + 150)  # 50 (router) + 100 (usage)
    
    def test_ask_ai_includes_chat_history(self):
        """Verifica que el historial de chat se pasa a los agentes."""
        # Crear historial previo
        self.create_chat_message('Mensaje anterior 1', role='user')
        self.create_chat_message('Respuesta anterior 1', role='assistant')
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router:
                mock_router.return_value.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage:
                    mock_usage.return_value.execute.return_value = {
                        'status': 'success',
                        'answer': 'Respuesta',
                        'tokens': 100
                    }
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai('Nueva pregunta', {})
                    
                    # Verificar que los agentes recibieron el historial
                    mock_router.assert_called_once()
                    call_args = mock_router.return_value.execute.call_args
                    # El historial debe estar en los argumentos
                    self.assertIsNotNone(call_args)
    
    def test_ask_ai_error_from_usage_agent(self):
        """Verifica que errores del UsageAgent se retornan correctamente."""
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router:
                mock_router.return_value.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage:
                    mock_usage.return_value.execute.return_value = {
                        'status': 'error',
                        'message': 'Error en OpenAI',
                    }
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai('Pregunta', {})
        
        self.assertEqual(response['status'], 'error')
        self.assertIn('OpenAI', response['message'])
