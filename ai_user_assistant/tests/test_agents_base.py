# -*- coding: utf-8 -*-
"""
test_agents_base.py - Tests para el contrato de BaseAgent.

Cubre:
- Inicialización y herencia
- Contrato execute() (debe ser override en hijos)
- Propagación de api_key y env
"""

from odoo.tests import tagged
from .common import BaseAITestCase
from odoo.addons.ai_user_assistant.agents.base_agent import BaseAgent


@tagged('at_install', '-at_install')
class TestBaseAgent(BaseAITestCase):
    """Tests para BaseAgent - clase base de todos los agentes."""
    
    def test_base_agent_init(self):
        """Verifica que BaseAgent se inicializa con env, callback y api_key."""
        def dummy_callback(*args, **kwargs):
            return {'content': 'test', 'tokens': 10}
        
        agent = BaseAgent(
            env=self.env,
            call_openai_func=dummy_callback,
            api_key='sk-test-123'
        )
        
        self.assertEqual(agent.env, self.env)
        self.assertEqual(agent._call_openai, dummy_callback)
        self.assertEqual(agent.api_key, 'sk-test-123')
    
    def test_base_agent_stores_environment(self):
        """Verifica que env se almacena correctamente."""
        def dummy_callback(*args, **kwargs):
            return {'content': 'test', 'tokens': 10}
        
        agent = BaseAgent(
            env=self.env,
            call_openai_func=dummy_callback,
            api_key='sk-test-123'
        )
        
        # El agent debe poder acceder a env.registry
        self.assertIsNotNone(agent.env.registry)
    
    def test_base_agent_stores_api_key(self):
        """Verifica que api_key se almacena correctamente."""
        def dummy_callback(*args, **kwargs):
            return {'content': 'test', 'tokens': 10}
        
        agent = BaseAgent(
            env=self.env,
            call_openai_func=dummy_callback,
            api_key='sk-test-abc-123-xyz'
        )
        
        self.assertEqual(agent.api_key, 'sk-test-abc-123-xyz')
    
    def test_base_agent_stores_callback(self):
        """Verifica que _call_openai callback se almacena correctamente."""
        def custom_callback(*args, **kwargs):
            return {'content': 'custom response', 'tokens': 50}
        
        agent = BaseAgent(
            env=self.env,
            call_openai_func=custom_callback,
            api_key='sk-test-123'
        )
        
        # El callback debe ser invocable
        result = agent._call_openai('arg1', 'arg2')
        self.assertEqual(result['content'], 'custom response')
        self.assertEqual(result['tokens'], 50)
    
    def test_base_agent_execute_not_implemented(self):
        """Verifica que execute() lanza NotImplementedError."""
        def dummy_callback(*args, **kwargs):
            return {'content': 'test', 'tokens': 10}
        
        agent = BaseAgent(
            env=self.env,
            call_openai_func=dummy_callback,
            api_key='sk-test-123'
        )
        
        # Llamar a execute() sin override debe lanzar excepción
        with self.assertRaises(NotImplementedError):
            agent.execute('test')
    
    def test_base_agent_is_abstract(self):
        """Verifica que BaseAgent funciona como clase abstracta."""
        def dummy_callback(*args, **kwargs):
            return {'content': 'test', 'tokens': 10}
        
        # Intentar llamar execute en BaseAgent debe fallar
        agent = BaseAgent(
            env=self.env,
            call_openai_func=dummy_callback,
            api_key='sk-test-123'
        )
        
        # El error debe mencionar que debe ser override
        with self.assertRaisesRegex(NotImplementedError, 'execute'):
            agent.execute()
    
    def test_subclass_can_override_execute(self):
        """Verifica que las subclases pueden hacer override de execute()."""
        
        class TestAgent(BaseAgent):
            def execute(self, question):
                return {
                    'result': f'Processed: {question}',
                    'tokens': 10
                }
        
        def dummy_callback(*args, **kwargs):
            return {'content': 'test', 'tokens': 10}
        
        agent = TestAgent(
            env=self.env,
            call_openai_func=dummy_callback,
            api_key='sk-test-123'
        )
        
        result = agent.execute('Test question')
        
        self.assertEqual(result['result'], 'Processed: Test question')
        self.assertEqual(result['tokens'], 10)
    
    def test_subclass_can_access_base_attributes(self):
        """Verifica que subclases pueden acceder a atributos de BaseAgent."""
        
        class TestAgent(BaseAgent):
            def execute(self):
                # Acceder a atributos heredados
                return {
                    'api_key_starts_with': self.api_key[:3],
                    'has_env': self.env is not None,
                    'callback_callable': callable(self._call_openai),
                }
        
        def dummy_callback(*args, **kwargs):
            return {'content': 'test', 'tokens': 10}
        
        agent = TestAgent(
            env=self.env,
            call_openai_func=dummy_callback,
            api_key='sk-test-123'
        )
        
        result = agent.execute()
        
        self.assertEqual(result['api_key_starts_with'], 'sk-')
        self.assertTrue(result['has_env'])
        self.assertTrue(result['callback_callable'])
