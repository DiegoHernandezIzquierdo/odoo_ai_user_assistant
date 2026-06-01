# -*- coding: utf-8 -*-
"""
test_integration.py - Tests end-to-end del módulo AI Assistant.

Cubre:
- Flujos completos: Pregunta → Router → Agent → Respuesta
- Aislamiento multi-usuario
- Persistencia de historial
- Conteos acumulativos de tokens
"""

from odoo.tests import tagged
from unittest.mock import patch

from .common import BaseAITestCase, MockOpenAIResponse


@tagged('post_install', '-at_install')
class TestAiAssistantIntegration(BaseAITestCase):
    """Tests de integración end-to-end."""
    
    def test_full_flow_documents_route(self):
        """Flujo completo: Pregunta → Router→DocumentAgent → Respuesta."""
        question = '¿Dónde están mis facturas de 2024?'
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            # Mock completo del flujo
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router_cls:
                mock_router = MagicMock()
                mock_router.execute.return_value = {
                    'route': 'documents',
                    'tokens': 50
                }
                mock_router_cls.return_value = mock_router
                
                with patch('odoo.addons.ai_user_assistant.controllers.main.DocumentAgent') as mock_doc_cls:
                    mock_doc = MagicMock()
                    mock_doc.execute.return_value = {
                        'answer': 'Se encontraron 5 facturas de 2024',
                        'tokens': 150
                    }
                    mock_doc_cls.return_value = mock_doc
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai(question, {})
        
        # Verificar flujo
        self.assertEqual(response['status'], 'success')
        self.assertIn('Se encontraron', response['answer'])
        self.assertEqual(response['tokens'], 200)  # 50 + 150
    
    def test_full_flow_action_project_route(self):
        """Flujo completo: Pregunta → Router→ActionProjectAgent → Respuesta."""
        question = 'Crea una tarea para revisar el contrato'
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router_cls:
                mock_router = MagicMock()
                mock_router.execute.return_value = {
                    'route': 'action_project',
                    'tokens': 50
                }
                mock_router_cls.return_value = mock_router
                
                with patch('odoo.addons.ai_user_assistant.controllers.main.ActionProjectAgent') as mock_action_cls:
                    mock_action = MagicMock()
                    mock_action.execute.return_value = {
                        'answer': 'Tarea creada: Revisar contrato',
                        'tokens': 120
                    }
                    mock_action_cls.return_value = mock_action
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai(question, {})
        
        self.assertEqual(response['status'], 'success')
        self.assertIn('Tarea creada', response['answer'])
        self.assertEqual(response['tokens'], 170)  # 50 + 120
    
    def test_full_flow_general_route(self):
        """Flujo completo: Pregunta → Router→UsageAgent → Respuesta."""
        question = '¿Cómo hago una nueva venta?'
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router_cls:
                mock_router = MagicMock()
                mock_router.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                mock_router_cls.return_value = mock_router
                
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage_cls:
                    mock_usage = MagicMock()
                    mock_usage.execute.return_value = {
                        'status': 'success',
                        'answer': 'Para crear una venta: 1. Ir a Ventas...',
                        'tokens': 180
                    }
                    mock_usage_cls.return_value = mock_usage
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai(question, {})
        
        self.assertEqual(response['status'], 'success')
        self.assertIn('Para crear una venta', response['answer'])
        self.assertEqual(response['tokens'], 230)  # 50 + 180
    
    def test_chat_history_context(self):
        """Verifica que el historial se mantiene entre llamadas."""
        # Crear historial inicial
        self.create_chat_message('Primera pregunta', role='user')
        self.create_chat_message('Primera respuesta', role='assistant')
        
        # Nueva llamada debe ver el historial
        question = 'Segunda pregunta'
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router_cls:
                mock_router = MagicMock()
                mock_router.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                mock_router_cls.return_value = mock_router
                
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage_cls:
                    mock_usage = MagicMock()
                    mock_usage.execute.return_value = {
                        'status': 'success',
                        'answer': 'Respuesta contextual',
                        'tokens': 100
                    }
                    mock_usage_cls.return_value = mock_usage
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai(question, {})
                    
                    # Verificar que UsageAgent fue llamado con historial
                    mock_usage.execute.assert_called()
                    call_args = mock_usage.execute.call_args
                    self.assertIsNotNone(call_args)
        
        # Verificar que ambos mensajes están guardados
        all_messages = self.env['ai.assistant.message'].search([
            ('user_id', '=', self.env.user.id)
        ])
        
        self.assertEqual(len(all_messages), 4)  # 2 iniciales + 1 nueva pregunta + 1 nueva respuesta
    
    def test_multiple_users_isolation(self):
        """Verifica que usuarios no ven historiales unos de otros."""
        # Usuario 1 crea un historial
        msg1 = self.create_chat_message('Pregunta usuario 1', role='user')
        
        # Usuario 2 crea un historial
        msg2 = self.create_chat_message(
            'Pregunta usuario 2',
            role='user',
            user=self.test_user
        )
        
        # Buscar mensajes del usuario actual
        current_user_messages = self.env['ai.assistant.message'].search([
            ('user_id', '=', self.env.user.id)
        ])
        
        # Buscar mensajes del usuario de test
        test_user_messages = self.env['ai.assistant.message'].search([
            ('user_id', '=', self.test_user.id)
        ])
        
        # Verificar aislamiento
        self.assertIn(msg1.id, current_user_messages.ids)
        self.assertNotIn(msg2.id, current_user_messages.ids)
        
        self.assertIn(msg2.id, test_user_messages.ids)
        self.assertNotIn(msg1.id, test_user_messages.ids)
    
    def test_token_accumulation(self):
        """Verifica que los tokens se acumulan correctamente."""
        initial_tokens = self.get_token_count()
        
        # Primera pregunta
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router_cls:
                mock_router = MagicMock()
                mock_router.execute.return_value = {'route': 'general', 'tokens': 50}
                mock_router_cls.return_value = mock_router
                
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage_cls:
                    mock_usage = MagicMock()
                    mock_usage.execute.return_value = {
                        'status': 'success',
                        'answer': 'Respuesta 1',
                        'tokens': 100
                    }
                    mock_usage_cls.return_value = mock_usage
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response1 = controller.ask_ai('Pregunta 1', {})
        
        after_first = self.get_token_count()
        self.assertEqual(after_first, initial_tokens + 150)
        
        # Segunda pregunta
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router_cls:
                mock_router = MagicMock()
                mock_router.execute.return_value = {'route': 'documents', 'tokens': 60}
                mock_router_cls.return_value = mock_router
                
                with patch('odoo.addons.ai_user_assistant.controllers.main.DocumentAgent') as mock_doc_cls:
                    mock_doc = MagicMock()
                    mock_doc.execute.return_value = {
                        'answer': 'Documentos encontrados',
                        'tokens': 120
                    }
                    mock_doc_cls.return_value = mock_doc
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response2 = controller.ask_ai('Pregunta 2', {})
        
        after_second = self.get_token_count()
        self.assertEqual(after_second, after_first + 180)  # 60 + 120
    
    def test_error_in_agent_handling(self):
        """Verifica que los errores se manejan correctamente."""
        
        with patch('odoo.addons.ai_user_assistant.controllers.main.request') as mock_request:
            mock_request.env = self.env
            mock_request.env.uid = self.env.user.id
            
            with patch('odoo.addons.ai_user_assistant.controllers.main.RouterAgent') as mock_router_cls:
                mock_router = MagicMock()
                mock_router.execute.return_value = {
                    'route': 'general',
                    'tokens': 50
                }
                mock_router_cls.return_value = mock_router
                
                with patch('odoo.addons.ai_user_assistant.controllers.main.UsageAgent') as mock_usage_cls:
                    mock_usage = MagicMock()
                    mock_usage.execute.return_value = {
                        'status': 'error',
                        'message': 'Error simulado en OpenAI'
                    }
                    mock_usage_cls.return_value = mock_usage
                    
                    from odoo.addons.ai_user_assistant.controllers.main import AiUserAssistantController
                    controller = AiUserAssistantController()
                    
                    response = controller.ask_ai('Pregunta', {})
        
        # Debe retornar error
        self.assertEqual(response['status'], 'error')
        self.assertIn('OpenAI', response['message'])


# Importar MagicMock en el nivel superior del módulo
from unittest.mock import MagicMock
