# -*- coding: utf-8 -*-
"""
common.py - Base test case, fixtures y mocks para AI User Assistant.

Proporciona:
- BaseAITestCase: Clase base con setup común
- MockOpenAIResponse: Helper para simular respuestas OpenAI
- Fixtures: api_key, usuarios, contexto
"""

from odoo.tests import TransactionCase
from unittest.mock import MagicMock, patch
import logging

_logger = logging.getLogger(__name__)


class MockOpenAIResponse:
    """Helper para crear respuestas mockeadas de OpenAI."""
    
    @staticmethod
    def create(content, tokens=100, role='assistant'):
        """
        Crea una respuesta mock de OpenAI.
        
        Args:
            content (str): Contenido de la respuesta
            tokens (int): Cantidad de tokens usados
            role (str): Rol (assistant, user)
        
        Returns:
            dict: Respuesta en formato OpenAI
        """
        return {
            'content': content,
            'tokens': tokens,
            'role': role
        }
    
    @staticmethod
    def router_response(route='general', tokens=50):
        """Respuesta del RouterAgent (clasificación)."""
        return MockOpenAIResponse.create(route, tokens)
    
    @staticmethod
    def documents_response(answer='No se encontraron documentos', tokens=150):
        """Respuesta del DocumentAgent."""
        return MockOpenAIResponse.create(answer, tokens)
    
    @staticmethod
    def usage_response(answer='Aquí está la información solicitada', tokens=200):
        """Respuesta del UsageAgent (help/usage)."""
        return MockOpenAIResponse.create(answer, tokens)


class BaseAITestCase(TransactionCase):
    """
    Clase base para tests del módulo AI User Assistant.
    
    Proporciona:
    - Setup común (API key, usuarios, modelos)
    - Mock de OpenAI
    - Helpers para crear datos de test
    """
    
    @classmethod
    def setUpClass(cls):
        """Setup común ejecutado una sola vez para todos los tests."""
        super().setUpClass()
        
        # Crear usuario de test
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test User AI',
            'login': 'test_ai_user',
            'email': 'test_ai@example.com',
            'password': 'test123',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        
        # Configurar API Key en config
        cls.env['ir.config_parameter'].sudo().set_param(
            'ai_user_assistant.api_key',
            'sk-test-12345678901234567890'
        )
        
        # Crear registros de base de conocimiento para tests
        cls.knowledge_base = cls._create_knowledge_base()
    
    @classmethod
    def _create_knowledge_base(cls):
        """Crea registros de base de conocimiento para tests."""
        KnowledgeModel = cls.env['ai.assistant.knowledge']
        
        return {
            'sale_order': KnowledgeModel.create({
                'name': 'Documentos de Órdenes de Venta',
                'model_name': 'sale.order',
                'instructions': 'Las órdenes de venta contienen líneas de producto. '
                               'Un campo importante es el estado (borrador, confirmado, cancelado).',
            }),
            'res_partner': KnowledgeModel.create({
                'name': 'Gestión de Contactos',
                'model_name': 'res.partner',
                'instructions': 'Los contactos pueden ser clientes, proveedores o contactos generales. '
                               'Tienen campos como email, teléfono, dirección.',
            }),
            'account_move': KnowledgeModel.create({
                'name': 'Gestión de Asientos Contables',
                'model_name': 'account.move',
                'instructions': 'Los asientos contables son movimientos de contabilidad. '
                               'Pueden ser facturas de compra, de venta o asientos manuales.',
            }),
        }
    
    def setUp(self):
        """Setup ejecutado antes de cada test method."""
        super().setUp()
        
        # Cambiar usuario actual al usuario de test
        self = self.with_user(self.test_user)
    
    def create_chat_message(self, content, role='user', user=None):
        """
        Helper para crear mensajes de chat.
        
        Args:
            content (str): Contenido del mensaje
            role (str): 'user' o 'assistant'
            user (res.users): Usuario propietario (default: current user)
        
        Returns:
            ai.assistant.message: Record creado
        """
        if user is None:
            user = self.env.user
        
        return self.env['ai.assistant.message'].create({
            'user_id': user.id,
            'role': role,
            'content': content,
        })
    
    def create_multiple_messages(self, count=5):
        """
        Crea múltiples mensajes alternando entre user y assistant.
        
        Returns:
            list: Records creados
        """
        messages = []
        for i in range(count):
            role = 'user' if i % 2 == 0 else 'assistant'
            msg = self.create_chat_message(
                content=f'Mensaje {i+1} ({role})',
                role=role
            )
            messages.append(msg)
        return messages
    
    def get_chat_history(self, user=None, limit=20):
        """
        Obtiene el historial de chat para un usuario.
        
        Args:
            user (res.users): Usuario (default: current user)
            limit (int): Cantidad máxima de mensajes
        
        Returns:
            list: Lista de dicts con {role, content}
        """
        if user is None:
            user = self.env.user
        
        records = self.env['ai.assistant.message'].search(
            [('user_id', '=', user.id)],
            order='create_date desc',
            limit=limit
        )
        
        return [
            {'role': r.role, 'content': r.content}
            for r in reversed(records)
        ]
    
    def mock_openai_call(self, response_content, tokens=100):
        """
        Crea un mock para _call_openai que retorna una respuesta específica.
        
        Args:
            response_content (str): Contenido de la respuesta
            tokens (int): Cantidad de tokens
        
        Returns:
            MagicMock: Mock configurado
        """
        mock = MagicMock(return_value={
            'content': response_content,
            'tokens': tokens
        })
        return mock
    
    def get_token_count(self):
        """
        Obtiene el contador total de tokens consumidos.
        
        Returns:
            int: Total de tokens consumidos
        """
        total_str = self.env['ir.config_parameter'].sudo().get_param(
            'ai_user_assistant.total_tokens_consumed',
            default='0'
        )
        return int(total_str) if total_str.isdigit() else 0
    
    def assert_message_saved(self, content, role, user=None):
        """
        Verifica que un mensaje fue guardado correctamente.
        
        Args:
            content (str): Contenido esperado
            role (str): Rol esperado
            user (res.users): Usuario esperado
        """
        if user is None:
            user = self.env.user
        
        found = self.env['ai.assistant.message'].search([
            ('user_id', '=', user.id),
            ('role', '=', role),
            ('content', '=', content),
        ])
        
        self.assertTrue(
            found,
            f'Mensaje no encontrado: {role}={content} para usuario {user.login}'
        )
        return found
