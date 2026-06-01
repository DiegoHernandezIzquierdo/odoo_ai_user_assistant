# -*- coding: utf-8 -*-
import logging
from .base_agent import BaseAgent

_logger = logging.getLogger(__name__)

class RouterAgent(BaseAgent):

    def execute(self, question, chat_history=None):
        text = question.strip() if isinstance(question, str) else ''

        # Prompt estricto actualizado con la nueva ruta de Base de Datos
        system_prompt = """Eres un enrutador inteligente para un ERP (Odoo). 
Tu única tarea es leer la petición del usuario y clasificarla en UNA de estas 4 categorías exactas.
Responde ÚNICAMENTE con la palabra de la categoría, en minúsculas, sin comillas, puntos ni texto adicional.

Categorías:
1. database: El usuario quiere consultar datos, listar registros o hacer filtros en Odoo (ej. listar facturas sin pagar, buscar clientes de una ciudad, ver ventas mayores a X cantidad, comprobar stock). Busca INFORMACIÓN en las tablas, no archivos físicos.
2. documents: El usuario busca EXPLÍCITAMENTE un archivo físico, PDF, adjunto, manual, o quiere buscar texto DENTRO de un documento subido al sistema.
3. action_project: El usuario quiere crear, modificar, actualizar, asignar o cambiar el estado de una tarea, proyecto u otro registro.
4. general: El usuario hace preguntas teóricas, pide instrucciones de uso (¿cómo hago...?), o cualquier petición puramente conversacional o de saludo.
5. navigation: SI el usuario pide explícitamente IR, NAVEGAR, MOSTRAR UNA VISTA o ABRIR una pantalla (ej. "llévame a los contactos", "abre las facturas de este mes", "quiero ver la pantalla de ventas")."""

        try:
            response = self._call_openai(
                self.api_key, 
                system_prompt, 
                "",  
                [{'role': 'user', 'content': text}]
            )
            
            # Limpiamos la respuesta de la IA
            route = response.get('content', '').strip().lower()

            # Fallback de seguridad actualizado con la nueva ruta 'database'
            if route not in ['documents', 'action_project', 'general', 'database', 'navigation']:
                _logger.warning("RouterAgent devolvió ruta inválida: %s. Forzando 'general'.", route)
                route = 'general'
                
            tokens = response.get('tokens', 0)

        except Exception as e:
            _logger.error('Error en RouterAgent: %s', e)
            route = 'general'
            tokens = 0

        _logger.debug('RouterAgent route=%s for question=%s', route, question)
        return {'route': route, 'tokens': tokens}