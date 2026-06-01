# -*- coding: utf-8 -*-
import logging
import re
import json
import datetime
from .base_agent import BaseAgent

_logger = logging.getLogger(__name__)

class NavigationAgent(BaseAgent):
    def execute(self, question, chat_history=None):
        _logger.info("--- Iniciando NavigationAgent para: %s ---", question)
        
        # Inyectamos contexto temporal
        hoy = datetime.date.today().strftime('%Y-%m-%d')
        primer_dia_mes = datetime.date.today().strftime('%Y-%m-01')

        system_prompt = f"""Eres un experto en el frontend de Odoo 16.
Tu única misión es traducir la petición del usuario en un diccionario de acción (ir.actions.act_window) en formato JSON estricto.
NO vas a crear vistas nuevas, solo a navegar a las vistas estándar aplicando dominios (filtros).

Hoy es: {hoy}. Primer día del mes actual: {primer_dia_mes}.

ESTRUCTURA EXACTA DEL JSON ESPERADO:
{{
  "type": "ir.actions.act_window",
  "name": "Título de la pestaña (ej. Facturas de este mes)",
  "res_model": "nombre.del.modelo",
  "view_mode": "tree,form",
  "domain": [["campo", "operador", "valor"]],
  "target": "current"
}}

MODELOS Y REGLAS COMUNES:
- account.move (Facturas): Añade SIEMPRE [["move_type", "=", "out_invoice"]].
- sale.order (Ventas)
- res.partner (Contactos)
- product.template (Productos)
- sale.order.line: CUIDADO, las líneas no suelen tener vista propia fácil de navegar. Si piden "artículos vendidos", navega a 'sale.order' (Pedidos).

IMPORTANTE: El dominio SIEMPRE es una lista de listas.
"""
        try:
            # Llamamos a OpenAI
            response = self._call_openai(self.api_key, system_prompt, "", [{'role': 'user', 'content': question}])
            content = response.get('content', '')
            tokens_used = response.get('tokens', 0)

            # Buscamos el JSON en la respuesta
            match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if match:
                action_dict = json.loads(match.group(0))
                # Devolvemos un texto para el chat y el diccionario de Odoo oculto
                answer = f"Te llevo a la vista de <b>{action_dict.get('name', 'resultados')}</b>..."
                return {
                    'answer': answer, 
                    'action': action_dict, # <- ESTO ES LA MAGIA
                    'tokens': tokens_used
                }
            else:
                return {'answer': "No he podido deducir a qué pantalla de Odoo navegar.", 'tokens': tokens_used}

        except Exception as e:
            _logger.error("Error en NavigationAgent: %s", str(e))
            return {'answer': "Error técnico al intentar generar la navegación.", 'tokens': 0}