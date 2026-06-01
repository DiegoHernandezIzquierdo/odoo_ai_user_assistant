# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import logging
import json
import re
import base64
import html as html_lib
from .base_agent import BaseAgent

_logger = logging.getLogger(__name__)

class ActionProjectAgent(BaseAgent):

    def execute(self, question, chat_history):
        query = question.strip() if isinstance(question, str) else ''
        
        # 1. Analizar intención
        plan = self._analyze_action_with_ai(query, chat_history)
        model = plan.get('model', 'project.task')
        action = plan.get('action', 'search')

        # 2. Construir dominio
        domain = self._build_domain(plan, model)
        
        # --- BLOQUE DE SEGURIDAD CRÍTICO ---
        # Si la acción es borrar o actualizar y el dominio está vacío, abortamos.
        if action in ['delete', 'update'] and not domain:
            return {
                'answer': "⚠️ <b>Acción cancelada por seguridad:</b> No he podido identificar exactamente qué registros quieres modificar o borrar. Por favor, dime el nombre o sé más específico.",
                'tokens': 0
            }
        # ------------------------------------

        try:
            if action == 'search':
                fields = self._get_fields_for_model(model)
                results = self.env[model].search_read(domain, fields, limit=20)
                return {'answer': self._render_search_results(plan, results), 'tokens': 0}

            elif action == 'create':
                new_record = self.env[model].create({'name': plan.get('name_value', 'Nuevo registro')})
                return {'answer': f"✅ Tarea creada: <b>{new_record.name}</b>", 'tokens': 0}

            elif action in ['update', 'delete', 'export']:
                records = self.env[model].search(domain, limit=20)
                
                if not records:
                    return {'answer': "No he encontrado registros con ese criterio para actuar.", 'tokens': 0}

                if action == 'delete':
                    nombres = ", ".join(records.mapped('name'))
                    count = len(records)
                    records.unlink()
                    return {'answer': f"🗑️ He eliminado {count} registros: <i>{nombres}</i>", 'tokens': 0}

                elif action == 'update':
                    records.write(plan.get('update_fields', {}))
                    return {'answer': f"✏️ He actualizado {len(records)} registros.", 'tokens': 0}

                elif action == 'export':
                    return {'answer': self._generate_export_file(records, model), 'tokens': 0}

        except Exception as e:
            _logger.error("Error ActionAgent: %s", e)
            return {'answer': f"❌ Error: {str(e)}", 'tokens': 0}

    def _analyze_action_with_ai(self, query, chat_history):
        if not query:
            return {}

        # Convertimos el historial en un texto simple para que la IA tenga contexto
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-4:]]) if chat_history else "Sin historial."

        system_prompt = f"""Eres un experto analista de acciones para el ERP Odoo.
Tu tarea es leer la petición del usuario y extraer la intención en un formato JSON ESTRICTO.
Usa el historial reciente para entender el contexto.

Historial reciente:
{history_text}

Reglas de extracción:
- 'action': 'create' (crear), 'update' (modificar/archivar), 'delete' (borrar), 'search' (buscar), 'export' (generar archivo/informe).
- 'model': 'project.task' o 'project.project'.
- 'is_mine': booleano. True si pide "mis" tareas o "propias".
- 'status': 'to_do', 'in_progress', 'done', 'cancelled', o null.
- 'name_value': Título del registro si es 'create'. null en caso contrario.
- 'update_fields': Diccionario con campos a cambiar si es 'update'. (ej. para archivar usa {{"active": false}}). Si no, {{}}.
- 'search_terms': Lista de palabras clave para buscar.

⚠️ REGLA DE ORO DE SEGURIDAD ⚠️: 
Si el usuario pide borrar, actualizar o archivar usando pronombres (ej. "bórrala", "archívalo", "elimínalos"), DEBES buscar obligatoriamente en el 'Historial reciente' de qué registro se estaba hablando y poner su nombre EXACTO dentro de 'search_terms'. NUNCA dejes 'search_terms' vacío en un 'delete' o 'update' si la información está en el historial.

Responde ÚNICAMENTE con el JSON. Ejemplo de update (archivar):
{{"action": "update", "model": "project.task", "is_mine": false, "status": null, "name_value": null, "update_fields": {{"active": false}}, "search_terms": ["urgente"]}}"""

        try:
            response = self._call_openai(self.api_key, system_prompt, "", [{'role': 'user', 'content': query}])
            content = response.get('content', '').strip()
            
            if content.startswith('```'):
                content = re.sub(r'^```[a-zA-Z]*\n', '', content)
                content = re.sub(r'\n```$', '', content)
                
            return json.loads(content)
        except Exception as e:
            _logger.error('Error JSON IA en ActionProjectAgent: %s', e)
            return {"action": "search", "model": "project.task", "is_mine": False, "status": None, "name_value": None, "update_fields": {}, "search_terms": []}

    def _build_domain(self, plan, model):
        domain = []
        if plan.get('is_mine'):
            if model == 'project.task':
                domain.append(('user_ids', 'in', [self.env.uid]))
            elif model == 'project.project':
                domain.append(('user_id', '=', self.env.uid))

        status_map = {'to_do': 'to do', 'in_progress': 'in progress', 'done': 'done', 'cancelled': 'cancelled'}
        status_key = plan.get('status')
        if status_key and status_key in status_map:
            domain.append(('stage_id.name', 'ilike', status_map[status_key]))

        terms = plan.get('search_terms', [])
        if terms:
            search_value = ' '.join(terms)
            # Gracias a la Regla de Oro, si es un borrado por contexto,
            # 'search_value' tendrá el nombre exacto de la tarea y filtrará correctamente.
            domain.extend(['|', ('name', 'ilike', search_value), ('description', 'ilike', search_value)])
            
        return domain

    def _build_values(self, plan, action):
        if action == 'create':
            return {'name': plan.get('name_value') or 'Nuevo registro generado por IA'}
        if action == 'update':
            # La IA nos pasa los campos a actualizar (ej. {'active': False} para archivar)
            return plan.get('update_fields', {})
        return {}

    def _get_fields_for_model(self, model):
        if model == 'project.task': return ['id', 'name', 'stage_id', 'project_id'] #, 'user_ids'
        if model == 'project.project': return ['id', 'name', 'user_id', 'description']
        return ['id', 'display_name']

    def _render_search_results(self, plan, results):
        if not results:
            return '<b>No encontré registros que coincidan con tu petición.</b>'
            
        html_parts = [f"He encontrado <b>{len(results)}</b> registros:<br/><ul>"]
        for record in results:
            line = f"{record.get('name', 'Sin nombre')}"
            if record.get('project_id'):
                line += f" <i>({record['project_id'][1]})</i>"
            html_parts.append(f"<li>{html_lib.escape(line)}</li>")
        html_parts.append('</ul>')
        return ''.join(html_parts)

    def _generate_export_file(self, records, model):
        # 1. Generamos un contenido CSV sencillo
        csv_lines = []
        fields = self._get_fields_for_model(model)
        
        # Cabecera
        csv_lines.append(";".join(fields))
        
        # Filas
        for rec in records:
            row = []
            for f in fields:
                val = getattr(rec, f, '')
                # Si es un campo relacional (Many2one), extraemos el nombre
                if hasattr(val, 'display_name') and val:
                    val = val.display_name
                elif hasattr(val, 'name') and val:
                    val = val.name
                row.append(str(val).replace(';', ',')) # Evitar romper el CSV
            csv_lines.append(";".join(row))
            
        csv_content = "\n".join(csv_lines)
        
        # 2. Codificamos en Base64
        b64_content = base64.b64encode(csv_content.encode('utf-8'))
        
        # 3. Creamos el archivo adjunto en Odoo
        attachment = self.env['ir.attachment'].create({
            'name': f'exportacion_{model}.csv',
            'type': 'binary',
            'datas': b64_content,
            'mimetype': 'text/csv',
            'res_model': model,
            'res_id': 0,
        })
        
        # 4. Devolvemos el HTML con el enlace de descarga
        download_url = f"/web/content/{attachment.id}?download=true"
        return f"📊 ¡Tu reporte está listo!<br/><br/>👉 <a href='{download_url}' target='_blank'><b>Descargar archivo CSV</b></a>"