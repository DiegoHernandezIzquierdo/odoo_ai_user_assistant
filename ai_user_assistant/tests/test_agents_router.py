# -*- coding: utf-8 -*-
"""
test_agents_router.py - Tests para RouterAgent.

Cubre:
- Clasificación de preguntas en categorías
- Respuestas válidas (documents, action_project, general)
- Fallback en respuestas inválidas
- Manejo de errores
- Conteo de tokens
"""

from odoo.tests import tagged
from unittest.mock import patch, MagicMock

from .common import BaseAITestCase, MockOpenAIResponse
from odoo.addons.ai_user_assistant.agents.router_agent import RouterAgent


@tagged('at_install', '-at_install')
class TestRouterAgent(BaseAITestCase):
    """Tests para RouterAgent - enrutador de preguntas."""
    
    def test_router_classifies_documents_query(self):
        """Verifica que preguntas sobre documentos se clasifican como 'documents'."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.router_response('documents', 50)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('¿Dónde está mi factura de abril?')
        
        self.assertEqual(result['route'], 'documents')
        self.assertEqual(result['tokens'], 50)
    
    def test_router_classifies_action_project_query(self):
        """Verifica que preguntas sobre tareas se clasifican como 'action_project'."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.router_response('action_project', 50)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Crea una nueva tarea para el equipo de ventas')
        
        self.assertEqual(result['route'], 'action_project')
        self.assertEqual(result['tokens'], 50)
    
    def test_router_classifies_general_query(self):
        """Verifica que preguntas generales se clasifican como 'general'."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.router_response('general', 50)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('¿Cómo creo una nueva venta?')
        
        self.assertEqual(result['route'], 'general')
        self.assertEqual(result['tokens'], 50)
    
    def test_router_returns_tokens(self):
        """Verifica que el router retorna el conteo de tokens."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.router_response('general', 75)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Test question')
        
        self.assertIn('tokens', result)
        self.assertEqual(result['tokens'], 75)
    
    def test_router_returns_route(self):
        """Verifica que el router siempre retorna un 'route'."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.router_response('documents', 50)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Any question')
        
        self.assertIn('route', result)
        self.assertIn(result['route'], ['documents', 'action_project', 'general'])
    
    def test_router_fallback_invalid_response(self):
        """Verifica que respuestas inválidas se convierten a 'general'."""
        
        def mock_openai(*args, **kwargs):
            # IA alucina una respuesta inválida
            return {'content': 'respuesta_invalida_xyz', 'tokens': 50}
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Test')
        
        # Debe forzar a 'general' si la respuesta es inválida
        self.assertEqual(result['route'], 'general')
    
    def test_router_handles_whitespace_in_response(self):
        """Verifica que el router maneja espacios/saltos de línea."""
        
        def mock_openai(*args, **kwargs):
            # OpenAI puede devolver la respuesta con espacios
            return {'content': '  documents  \n', 'tokens': 50}
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Test')
        
        # El router debe hacer strip() y convertir a lowercase
        self.assertEqual(result['route'], 'documents')
    
    def test_router_case_insensitive(self):
        """Verifica que el router maneja mayúsculas/minúsculas."""
        
        def mock_openai(*args, **kwargs):
            return {'content': 'DOCUMENTS', 'tokens': 50}
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Test')
        
        self.assertEqual(result['route'], 'documents')
    
    def test_router_handles_api_error(self):
        """Verifica que errores de OpenAI se manejan con fallback."""
        
        def mock_openai_error(*args, **kwargs):
            raise Exception('OpenAI API Error: Connection timeout')
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai_error,
            api_key='sk-test-123'
        )
        
        # Debe manejar el error y retornar fallback
        result = agent.execute('Test question')
        
        # Debe retornar 'general' como fallback
        self.assertEqual(result['route'], 'general')
        self.assertEqual(result['tokens'], 0)
    
    def test_router_with_empty_question(self):
        """Verifica que el router maneja preguntas vacías."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.router_response('general', 50)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        # Pregunta vacía
        result = agent.execute('   ')
        
        # Debe retornar una ruta válida
        self.assertIn(result['route'], ['documents', 'action_project', 'general'])
    
    def test_router_with_none_question(self):
        """Verifica que el router maneja preguntas None."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.router_response('general', 50)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        # Pregunta None
        result = agent.execute(None)
        
        # Debe retornar una ruta válida sin error
        self.assertIn(result['route'], ['documents', 'action_project', 'general'])
    
    def test_router_with_chat_history(self):
        """Verifica que el router puede recibir historial de chat."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.router_response('general', 50)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        chat_history = [
            {'role': 'user', 'content': 'Mensaje anterior'},
            {'role': 'assistant', 'content': 'Respuesta anterior'},
        ]
        
        # Llamar con historial
        result = agent.execute('Nueva pregunta', chat_history=chat_history)
        
        # Debe retornar resultado válido
        self.assertIn('route', result)
        self.assertIn('tokens', result)
    
    def test_router_response_format(self):
        """Verifica que la respuesta tiene el formato correcto."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.router_response('action_project', 100)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Test')
        
        # Estructura esperada
        self.assertIsInstance(result, dict)
        self.assertIn('route', result)
        self.assertIn('tokens', result)
        self.assertIsInstance(result['route'], str)
        self.assertIsInstance(result['tokens'], int)
    
    def test_router_multiple_calls_independent(self):
        """Verifica que múltiples llamadas al router son independientes."""
        
        responses = ['documents', 'action_project', 'general']
        call_count = 0
        
        def mock_openai_rotating(*args, **kwargs):
            nonlocal call_count
            route = responses[call_count % len(responses)]
            call_count += 1
            return MockOpenAIResponse.router_response(route, 50)
        
        agent = RouterAgent(
            env=self.env,
            call_openai_func=mock_openai_rotating,
            api_key='sk-test-123'
        )
        
        result1 = agent.execute('Question 1')
        result2 = agent.execute('Question 2')
        result3 = agent.execute('Question 3')
        
        self.assertEqual(result1['route'], 'documents')
        self.assertEqual(result2['route'], 'action_project')
        self.assertEqual(result3['route'], 'general')
