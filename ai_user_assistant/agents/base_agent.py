# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

class BaseAgent:
    """
    Clase Padre para todos los agentes de IA del asistente.
    Maneja la inicialización común y define las reglas estrictas.
    """
    def __init__(self, env, call_openai_func, api_key):
        self.env = env
        self._call_openai = call_openai_func
        self.api_key = api_key

    def execute(self, *args, **kwargs):
        """
        Función obligatoria. 
        Si un agente hijo no la sobreescribe, el sistema lanzará un error.
        Esto actúa como un "Contrato" arquitectónico.
        """
        raise NotImplementedError("¡Error de Arquitectura! Todos los agentes hijos deben crear su propia función execute()")