# -*- coding: utf-8 -*-
"""
test_agents_document.py - Tests para DocumentAgent.

Cubre:
- Búsqueda en base de conocimiento
- Retorno de respuestas
- Manejo de casos sin resultados
- Manejo de errores API
- Formateo de respuestas
"""

from odoo.tests import tagged
from unittest.mock import patch, MagicMock

from .common import BaseAITestCase, MockOpenAIResponse
from odoo.addons.ai_user_assistant.agents.db_agent import DocumentAgent


@tagged('at_install', '-at_install')
class TestDocumentAgent(BaseAITestCase):
    """Tests para DocumentAgent - búsqueda de documentos."""
    
    def test_document_agent_returns_answer_and_tokens(self):
        """Verifica que DocumentAgent retorna estructura {answer, tokens}."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.documents_response(
                'Se encontraron 3 documentos relevantes',
                150
            )
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('¿Dónde están mis facturas?', [])
        
        self.assertIn('answer', result)
        self.assertIn('tokens', result)
        self.assertIsInstance(result['answer'], str)
        self.assertIsInstance(result['tokens'], int)
    
    def test_document_agent_accepts_chat_history(self):
        """Verifica que DocumentAgent acepta historial de chat."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.documents_response('Respuesta', 100)
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        chat_history = [
            {'role': 'user', 'content': 'Pregunta anterior'},
            {'role': 'assistant', 'content': 'Respuesta anterior'},
        ]
        
        # Debe aceptar historial sin error
        result = agent.execute('Nueva pregunta', chat_history)
        
        self.assertIn('answer', result)
        self.assertIsInstance(result['answer'], str)
    
    def test_document_agent_handles_empty_question(self):
        """Verifica que DocumentAgent maneja preguntas vacías."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.documents_response(
                'No se realizó búsqueda (pregunta vacía)',
                50
            )
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('   ', [])
        
        # No debe lanzar error
        self.assertIn('answer', result)
        self.assertIn('tokens', result)
    
    def test_document_agent_handles_none_question(self):
        """Verifica que DocumentAgent maneja preguntas None."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.documents_response('Respuesta por defecto', 50)
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        # No debe lanzar error con None
        result = agent.execute(None, [])
        
        self.assertIn('answer', result)
    
    def test_document_agent_handles_api_error(self):
        """Verifica que DocumentAgent maneja errores de OpenAI."""
        
        def mock_openai_error(*args, **kwargs):
            raise Exception('OpenAI API Error: Rate limit exceeded')
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai_error,
            api_key='sk-test-123'
        )
        
        result = agent.execute('¿Dónde están mis documentos?', [])
        
        # Debe retornar respuesta válida (posiblemente con error)
        self.assertIn('answer', result)
        self.assertIn('tokens', result)
    
    def test_document_agent_formats_answer(self):
        """Verifica que DocumentAgent formatea la respuesta adecuadamente."""
        
        answer_text = '<b>Documentos encontrados:</b><br/><ul><li>Factura 001</li></ul>'
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.documents_response(answer_text, 120)
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Buscar documentos', [])
        
        # La respuesta debe contener HTML
        self.assertIn('<b>', result['answer'])
        self.assertIn('<br/>', result['answer'])
    
    def test_document_agent_token_calculation(self):
        """Verifica que DocumentAgent calcula tokens apropiadamente."""
        
        long_answer = 'Esta es una respuesta larga. ' * 50  # ~1500 caracteres
        
        def mock_openai(*args, **kwargs):
            # OpenAI retorna token count
            return {'content': long_answer, 'tokens': 400}
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Pregunta', [])
        
        # Los tokens deben ser razonables
        self.assertGreater(result['tokens'], 0)
    
    def test_document_agent_with_knowledge_base(self):
        """Verifica que DocumentAgent puede acceder a la base de conocimiento."""
        
        # Verificar que la base de conocimiento existe
        knowledge = self.env['ai.assistant.knowledge'].search([
            ('model_name', '=', 'sale.order')
        ])
        
        self.assertTrue(knowledge)
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.documents_response(
                'Información de base de conocimiento utilizada',
                100
            )
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Información sobre órdenes de venta', [])
        
        self.assertIn('answer', result)
    
    def test_document_agent_multiple_queries(self):
        """Verifica que DocumentAgent puede ejecutarse múltiples veces."""
        
        responses = [
            'Resultado búsqueda 1',
            'Resultado búsqueda 2',
            'Resultado búsqueda 3',
        ]
        call_count = 0
        
        def mock_openai_rotating(*args, **kwargs):
            nonlocal call_count
            response = responses[call_count % len(responses)]
            call_count += 1
            return MockOpenAIResponse.documents_response(response, 100)
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai_rotating,
            api_key='sk-test-123'
        )
        
        result1 = agent.execute('Pregunta 1', [])
        result2 = agent.execute('Pregunta 2', [])
        result3 = agent.execute('Pregunta 3', [])
        
        self.assertIn('Resultado búsqueda 1', result1['answer'])
        self.assertIn('Resultado búsqueda 2', result2['answer'])
        self.assertIn('Resultado búsqueda 3', result3['answer'])
    
    def test_document_agent_handles_special_characters(self):
        """Verifica que DocumentAgent maneja caracteres especiales en preguntas."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.documents_response('Respuesta', 100)
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        special_questions = [
            '¿Dónde están los documentos con "comillas"?',
            'Busca documentos con caracteres: < > &',
            'Pregunta con acentos: áéíóú',
        ]
        
        for question in special_questions:
            result = agent.execute(question, [])
            self.assertIn('answer', result)
    
    def test_document_agent_response_structure(self):
        """Verifica que la respuesta tiene la estructura correcta."""
        
        def mock_openai(*args, **kwargs):
            return MockOpenAIResponse.documents_response('Test answer', 150)
        
        agent = DocumentAgent(
            env=self.env,
            call_openai_func=mock_openai,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Test', [])
        
        # Estructura esperada
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)  # Solo 'answer' y 'tokens'
        self.assertIn('answer', result)
        self.assertIn('tokens', result)
        self.assertNotIn('error', result)
        self.assertNotIn('status', result)
