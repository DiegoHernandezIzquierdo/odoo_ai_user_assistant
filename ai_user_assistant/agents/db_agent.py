# -*- coding: utf-8 -*-
import logging
import re
import json
import datetime
from .base_agent import BaseAgent

_logger = logging.getLogger(__name__)

class DbAgent(BaseAgent):
    def execute(self, question, chat_history=None):
        _logger.info("--- Iniciando DbAgent para: %s ---", question)
        
        ia_response = self._generate_odoo_domain(question)
        params = ia_response.get('data', {})
        tokens_used = ia_response.get('tokens', 0)
        
        model_name = params.get('model')
        domain = params.get('domain', [])
        fields = params.get('fields', ['display_name'])
        order = params.get('order', 'id desc')
        limit = params.get('limit', 50)
        action = params.get('action', 'list')
        target_field = params.get('target_field', 'amount_total')

        if not model_name and action != 'last_order_lines':
            return {'answer': "No he podido determinar la tabla de Odoo. Sé más específico.", 'tokens': tokens_used}

        try:
            _logger.info("IA ha generado -> Modelo: %s | Acción: %s | Dominio: %s", model_name, action, domain)

            # --- NUEVA ACCIÓN: OBTENER TODOS LOS PRODUCTOS DEL ÚLTIMO PEDIDO ---
            if action == 'last_order_lines':
                # 1. Buscamos el último pedido confirmado
                last_order = self.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done'])], order='date_order desc, id desc', limit=1)
                
                if not last_order:
                    return {'answer': "No he encontrado ningún pedido confirmado en el sistema.", 'tokens': tokens_used}
                
                # 2. Buscamos las líneas de ese pedido (ignorando anticipos y secciones)
                lines = self.env['sale.order.line'].sudo().search_read(
                    domain=[
                        ('order_id', '=', last_order.id),
                        ('is_downpayment', '=', False),
                        ('display_type', '=', False)
                    ],
                    fields=['product_id', 'product_uom_qty', 'price_unit']
                )
                
                if not lines:
                    return {'answer': f"El pedido más reciente (<b>{last_order.name}</b>) no contiene artículos válidos.", 'tokens': tokens_used}
                
                answer = f"El pedido más reciente es el <b>{last_order.name}</b>. Estos son los artículos que contiene:<br/><ul>"
                for line in lines:
                    prod_raw = line.get('product_id')
                    prod_name = str(prod_raw[1]) if isinstance(prod_raw, (list, tuple)) else str(prod_raw)
                    qty = line.get('product_uom_qty', 1.0)
                    price = line.get('price_unit', 0.0)
                    answer += f"<li>{prod_name} - <b>{qty} ud(s)</b> a <b>{price}€</b></li>"
                answer += "</ul>"
                return {'answer': answer, 'tokens': tokens_used}

            # --- BÚSQUEDA GENÉRICA PARA EL RESTO DE ACCIONES ---
            if action in ['avg', 'sum'] and target_field not in fields:
                fields.append(target_field)
            
            records = self.env[model_name].sudo().search_read(domain, fields, order=order, limit=limit)

            # --- MANEJO DE PREGUNTAS DE SÍ/NO ---
            if action == 'check':
                if records:
                    return {'answer': f"<b>Sí</b>. He encontrado registros que lo confirman en {model_name}.", 'tokens': tokens_used}
                else:
                    return {'answer': f"<b>No</b>. No he encontrado nada que coincida con esa descripción.", 'tokens': tokens_used}

            # Si no hay registros (con ayuda para fechas)
            if not records:
                if any(k in str(domain) for k in ['date', 'create_date']):
                    return {'answer': "No hay registros en ese periodo de tiempo. Prueba a preguntar por 'el último año' o 'el total histórico'.", 'tokens': tokens_used}
                return {'answer': f"No he encontrado resultados para esa consulta.", 'tokens': tokens_used}

            # --- MANEJO DE CÁLCULOS MATEMÁTICOS ---
            if action == 'avg':
                valores = [r.get(target_field, 0) for r in records if isinstance(r.get(target_field), (int, float))]
                media = sum(valores) / len(valores) if valores else 0
                return {'answer': f"La media es de <b>{media:.2f}</b> (calculado sobre {len(valores)} registros).", 'tokens': tokens_used}
                
            if action == 'sum':
                valores = [r.get(target_field, 0) for r in records if isinstance(r.get(target_field), (int, float))]
                total = sum(valores)
                return {'answer': f"El total es <b>{total:.2f}</b> (calculado sobre {len(valores)} registros).", 'tokens': tokens_used}

            if action == 'count':
                total_records = self.env[model_name].sudo().search_count(domain)
                return {'answer': f"Hay un total de <b>{total_records}</b> registros que coinciden.", 'tokens': tokens_used}

            # --- MANEJO DE LISTAS NORMALES (Limpiando Nombres) ---
            answer = f"He encontrado <b>{len(records)}</b> resultados principales:<br/><ul>"
            vistos = set()
            for rec in records:
                name_raw = rec.get('display_name') or rec.get('name') or rec.get('product_id') or str(rec.get('id'))
                name = str(name_raw[1]) if isinstance(name_raw, (list, tuple)) else str(name_raw)
                
                if name in vistos: continue
                vistos.add(name)

                extra_parts = []
                for f in fields:
                    if f not in ['display_name', 'name', 'product_id', 'id']:
                        val_raw = rec.get(f)
                        if val_raw is not False and val_raw is not None:
                            val = str(val_raw[1]) if isinstance(val_raw, (list, tuple)) else str(val_raw)
                            if f in ['amount_total', 'price_unit', 'price_total', 'list_price']:
                                val = f"{val}€"
                            extra_parts.append(f"<b>{val}</b>")
                
                extra = f" - {', '.join(extra_parts)}" if extra_parts else ""
                answer += f"<li>{name}{extra}</li>"
            answer += "</ul>"
            return {'answer': answer, 'tokens': tokens_used}

        except Exception as e:
            _logger.error("ERROR CRÍTICO EN ODOO: %s", str(e))
            return {'answer': "Error al procesar la información en la base de datos.", 'tokens': tokens_used}

    def _generate_odoo_domain(self, query):
        hoy = datetime.date.today().strftime('%Y-%m-%d')
        primer_dia_mes = datetime.date.today().strftime('%Y-%m-01')

        system_prompt = f"""Eres un experto analista de Odoo 16. Hoy es: {hoy}.

NUEVO PARÁMETRO 'action':
- "list": Lista normal de registros.
- "avg": Calcula la media (requiere 'target_field').
- "sum": Suma valores (requiere 'target_field').
- "count": Cuenta registros.
- "check": Responde Sí o No.
- "last_order_lines": ÚSALA para "¿Cuál es el último artículo vendido?", "últimos productos" o similares.

REGLAS DE FILTRADO:
- Para 'sale.order.line', añade SIEMPRE [["is_downpayment", "=", false]] para evitar anticipos.
- Para ventas reales, usa [["state", "in", ["sale", "done"]]].

JSON:
{{
  "model": "modelo",
  "domain": [["campo", "=", "valor"]],
  "fields": ["campo1", "campo2"],
  "action": "list|avg|sum|count|check|last_order_lines",
  "target_field": "campo_matemático",
  "order": "id desc",
  "limit": 50
}}"""
        try:
            response = self._call_openai(self.api_key, system_prompt, "", [{'role': 'user', 'content': query}])
            content = response.get('content', '')
            match = re.search(r'\{.*\}', content, re.DOTALL)
            return {'data': json.loads(match.group(0)) if match else {}, 'tokens': response.get('tokens', 0)}
        except Exception:
            return {'data': {}, 'tokens': 0}