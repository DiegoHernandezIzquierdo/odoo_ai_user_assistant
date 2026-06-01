# -*- coding: utf-8 -*-
"""
Test suite para el módulo AI User Assistant.

Estructura de tests:
- test_models: Tests de modelos ORM (ai_knowledge, chat_message)
- test_controller: Tests del endpoint /ai_assistant/ask
- test_agents_base: Tests del contrato BaseAgent
- test_agents_router: Tests del RouterAgent
- test_agents_document: Tests del DocumentAgent
- test_integration: Tests end-to-end (flujos completos)
"""

from . import (
    test_models,
    test_controller,
    test_agents_base,
    test_agents_router,
    test_agents_document,
    test_integration,
)

__all__ = [
    'test_models',
    'test_controller',
    'test_agents_base',
    'test_agents_router',
    'test_agents_document',
    'test_integration',
]
