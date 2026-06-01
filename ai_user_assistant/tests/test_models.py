# -*- coding: utf-8 -*-
"""
test_models.py - Tests para modelos ORM del módulo.

Cubre:
- ai.assistant.knowledge: Base de conocimiento
- ai.assistant.message: Historial de chat
"""

from odoo.tests import tagged
from .common import BaseAITestCase


@tagged('at_install', '-at_install')
class TestAiAssistantKnowledge(BaseAITestCase):
    """Tests para el modelo ai.assistant.knowledge."""
    
    def test_create_knowledge_record(self):
        """Prueba crear un registro de conocimiento básico."""
        knowledge = self.env['ai.assistant.knowledge'].create({
            'name': 'Test Knowledge',
            'model_name': 'sale.order',
            'instructions': 'Test instructions for sale orders',
        })
        
        self.assertTrue(knowledge)
        self.assertEqual(knowledge.name, 'Test Knowledge')
        self.assertEqual(knowledge.model_name, 'sale.order')
        self.assertIn('Test instructions', knowledge.instructions)
    
    def test_knowledge_name_required(self):
        """Verifica que el campo name es requerido."""
        with self.assertRaises(Exception):
            self.env['ai.assistant.knowledge'].create({
                # Sin name
                'model_name': 'sale.order',
                'instructions': 'Some instructions',
            })
    
    def test_knowledge_model_name_required(self):
        """Verifica que el campo model_name es requerido."""
        with self.assertRaises(Exception):
            self.env['ai.assistant.knowledge'].create({
                'name': 'Test Knowledge',
                # Sin model_name
                'instructions': 'Some instructions',
            })
    
    def test_knowledge_instructions_required(self):
        """Verifica que el campo instructions es requerido."""
        with self.assertRaises(Exception):
            self.env['ai.assistant.knowledge'].create({
                'name': 'Test Knowledge',
                'model_name': 'sale.order',
                # Sin instructions
            })
    
    def test_search_knowledge_by_model(self):
        """Prueba buscar conocimiento por nombre de modelo."""
        # El knowledge base fue creado en setUpClass
        found = self.env['ai.assistant.knowledge'].search([
            ('model_name', '=', 'sale.order')
        ])
        
        self.assertTrue(found)
        self.assertEqual(found[0].model_name, 'sale.order')
    
    def test_multiple_knowledge_same_model(self):
        """Verifica que se pueden crear múltiples registros para el mismo modelo."""
        # Crear dos registros para sale.order
        kb1 = self.env['ai.assistant.knowledge'].create({
            'name': 'KB 1 - Sale Orders',
            'model_name': 'sale.order',
            'instructions': 'First set of instructions',
        })
        
        kb2 = self.env['ai.assistant.knowledge'].create({
            'name': 'KB 2 - Sale Orders Advanced',
            'model_name': 'sale.order',
            'instructions': 'Advanced instructions',
        })
        
        found = self.env['ai.assistant.knowledge'].search([
            ('model_name', '=', 'sale.order')
        ])
        
        # Debe haber al menos 2 (puede haber más si setUpClass creo alguno)
        self.assertGreaterEqual(len(found), 2)
        self.assertIn(kb1.id, found.ids)
        self.assertIn(kb2.id, found.ids)
    
    def test_knowledge_char_model_name(self):
        """Verifica que model_name acepta nombres técnicos como strings."""
        # Casos de uso: 'res.partner', 'sale.order', 'account.move', 'custom.module.model'
        test_models = ['res.partner', 'custom.mi.modulo', 'ir.attachment']
        
        for model_name in test_models:
            knowledge = self.env['ai.assistant.knowledge'].create({
                'name': f'KB for {model_name}',
                'model_name': model_name,
                'instructions': f'Instructions for {model_name}',
            })
            
            self.assertEqual(knowledge.model_name, model_name)
    
    def test_knowledge_long_instructions(self):
        """Verifica que instructions puede almacenar textos largos."""
        long_text = 'Esta es una instrucción larga. ' * 100
        
        knowledge = self.env['ai.assistant.knowledge'].create({
            'name': 'Long Instructions Test',
            'model_name': 'test.model',
            'instructions': long_text,
        })
        
        self.assertEqual(knowledge.instructions, long_text)
        self.assertGreater(len(knowledge.instructions), 1000)


@tagged('at_install', '-at_install')
class TestAiAssistantMessage(BaseAITestCase):
    """Tests para el modelo ai.assistant.message (chat history)."""
    
    def test_create_message_user_role(self):
        """Prueba crear un mensaje con rol user."""
        message = self.create_chat_message('¿Cómo hago una venta?', role='user')
        
        self.assertTrue(message)
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.content, '¿Cómo hago una venta?')
        self.assertEqual(message.user_id.id, self.env.user.id)
    
    def test_create_message_assistant_role(self):
        """Prueba crear un mensaje con rol assistant."""
        message = self.create_chat_message('Para hacer una venta...', role='assistant')
        
        self.assertTrue(message)
        self.assertEqual(message.role, 'assistant')
        self.assertEqual(message.content, 'Para hacer una venta...')
    
    def test_message_requires_role(self):
        """Verifica que role es requerido y válido."""
        with self.assertRaises(Exception):
            self.env['ai.assistant.message'].create({
                'user_id': self.env.user.id,
                # Sin role
                'content': 'Test message',
            })
    
    def test_message_invalid_role(self):
        """Verifica que role debe ser 'user' o 'assistant'."""
        with self.assertRaises(Exception):
            self.env['ai.assistant.message'].create({
                'user_id': self.env.user.id,
                'role': 'invalid_role',  # No es 'user' ni 'assistant'
                'content': 'Test message',
            })
    
    def test_message_requires_content(self):
        """Verifica que content es requerido."""
        with self.assertRaises(Exception):
            self.env['ai.assistant.message'].create({
                'user_id': self.env.user.id,
                'role': 'user',
                # Sin content
            })
    
    def test_message_user_link(self):
        """Verifica que el mensaje se vincula al usuario correcto."""
        message = self.create_chat_message('Test', role='user', user=self.test_user)
        
        self.assertEqual(message.user_id.id, self.test_user.id)
        self.assertEqual(message.user_id.login, 'test_ai_user')
    
    def test_message_ordering_by_create_date(self):
        """Verifica que los mensajes se ordenan por create_date asc."""
        # Crear varios mensajes
        messages = self.create_multiple_messages(5)
        
        # Buscar en orden asc
        found = self.env['ai.assistant.message'].search(
            [('user_id', '=', self.env.user.id)],
            order='create_date asc'
        )
        
        # Verificar que el primer mensaje es el más antiguo
        self.assertEqual(found[0].content, 'Mensaje 1 (user)')
        self.assertEqual(found[-1].content, 'Mensaje 5 (user)')
    
    def test_chat_history_retrieval(self):
        """Prueba recuperar historial de chat para un usuario."""
        # Crear mensajes
        self.create_multiple_messages(5)
        
        # Obtener historial
        history = self.get_chat_history(limit=20)
        
        self.assertEqual(len(history), 5)
        self.assertEqual(history[0]['role'], 'user')
        self.assertEqual(history[0]['content'], 'Mensaje 1 (user)')
        self.assertEqual(history[1]['role'], 'assistant')
        self.assertEqual(history[1]['content'], 'Mensaje 2 (assistant)')
    
    def test_chat_history_limit(self):
        """Prueba que el límite de historial funciona."""
        # Crear 25 mensajes
        self.create_multiple_messages(25)
        
        # Obtener solo los últimos 10
        history = self.get_chat_history(limit=10)
        
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0]['content'], 'Mensaje 16 (user)')
    
    def test_multi_user_isolation(self):
        """Verifica que usuarios no ven mensajes unos de otros."""
        # Usuario 1 crea mensajes
        msg1 = self.create_chat_message('Mensaje del usuario 1', role='user')
        
        # Usuario 2 crea mensajes
        msg2 = self.create_chat_message(
            'Mensaje del usuario 2',
            role='user',
            user=self.test_user
        )
        
        # Buscar mensajes del usuario actual (no test_user)
        current_messages = self.env['ai.assistant.message'].search([
            ('user_id', '=', self.env.user.id)
        ])
        
        self.assertIn(msg1.id, current_messages.ids)
        self.assertNotIn(msg2.id, current_messages.ids)
    
    def test_message_default_user(self):
        """Verifica que el usuario por defecto es el usuario actual."""
        message = self.env['ai.assistant.message'].create({
            'role': 'user',
            'content': 'Test message',
            # Sin especificar user_id (debe asignarse automáticamente)
        })
        
        self.assertEqual(message.user_id.id, self.env.user.id)
    
    def test_message_long_content(self):
        """Verifica que content puede almacenar textos largos."""
        long_content = 'Este es un mensaje largo. ' * 500
        
        message = self.create_chat_message(long_content, role='user')
        
        self.assertEqual(message.content, long_content)
        self.assertGreater(len(message.content), 5000)
