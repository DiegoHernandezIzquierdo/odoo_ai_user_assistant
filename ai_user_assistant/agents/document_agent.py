# -*- coding: utf-8 -*-
import logging
import re
import json
import html as html_lib
from urllib.parse import quote
from .base_agent import BaseAgent

_logger = logging.getLogger(__name__)

class DocumentAgent(BaseAgent):
    def execute(self, question, chat_history):
        query = question.strip() if isinstance(question, str) else ''
        
        # 1. Recuperamos datos y tokens de la IA
        ia_response = self._analyze_query_with_ai(query)
        parsed_data = ia_response.get('data', {})
        tokens_used = ia_response.get('tokens', 0) 
        
        _logger.debug("DocumentAgent AI Parsed Data: %s | Tokens: %s", parsed_data, tokens_used)
        
        terms = parsed_data.get('terms', [])
        exclude = parsed_data.get('exclude_terms', [])
        
        domain = self._build_domain(parsed_data, query)

        search_term = None
        if terms:
            search_term = terms[0]

        model = 'ir.attachment'
        results = []

        if model in self.env.registry.models:
            try:
                raw_results = self.env[model].sudo().search_read(
                    domain,
                    ['id', 'name', 'res_model', 'res_id', 'mimetype', 'type', 'index_content'],
                    limit=40
                )
                
                for record in raw_results:
                    record['related_name'] = self._get_related_name(record.get('res_model'), record.get('res_id'))
                    
                    if exclude and any(ex.lower() in record['related_name'].lower() for ex in exclude):
                        continue
                    
                    contenido = record.get('index_content') or ''
                    record['fragmento'] = ""
                    
                    if search_term and contenido:
                        match = re.search(re.escape(search_term), contenido, re.IGNORECASE)
                        if match:
                            inicio = max(0, match.start() - 60)
                            fin = min(len(contenido), match.end() + 60)
                            fragmento_bruto = contenido[inicio:fin]
                            
                            fragmento_escapado = html_lib.escape(fragmento_bruto)
                            termino_escapado = html_lib.escape(search_term)
                            
                            record['fragmento'] = re.sub(
                                f"({re.escape(termino_escapado)})", 
                                r"<mark><strong>\1</strong></mark>", 
                                fragmento_escapado, 
                                flags=re.IGNORECASE
                            )
                    
                    record.pop('index_content', None)
                    results.append(record)
                    
                    if len(results) >= 20:
                        break

            except Exception as e:
                _logger.warning('DocumentAgent search error: %s', e)
                results = []

        answer = self._render_answer(results, search_term)
        
        # Devolvemos los tokens reales en lugar de la estimación matemática
        return {'answer': answer, 'tokens': tokens_used}

    def _analyze_query_with_ai(self, query):
        if not query: return {'data': {}, 'tokens': 0}
        
        system_prompt = """Eres un experto extractor de parámetros para el buscador de Odoo. Extrae a JSON ESTRICTO.
REGLAS DE ORO:
1. 'model': Mapea conceptos a modelos técnicos. Usa null si no hay concepto claro.
2. 'terms': Lista de palabras clave RELEVANTES para buscar DENTRO del archivo. 
3. 'exclude_terms': Palabras a omitir en la búsqueda (ej. "borrador").
Responde ÚNICAMENTE con el JSON.
Ejemplo: {"model": null, "terms": ["Quebec"], "exclude_terms": []}"""
        
        try:
            response = self._call_openai(self.api_key, system_prompt, "", [{'role': 'user', 'content': query}])
            content = response.get('content', '').strip()
            tokens = response.get('tokens', 0) 
            
            if content.startswith('```'):
                content = re.sub(r'^```[a-zA-Z]*\n', '', content)
                content = re.sub(r'\n```$', '', content)
                
            # Devolvemos un diccionario con los datos parseados y los tokens
            return {'data': json.loads(content), 'tokens': tokens}
            
        except Exception as e:
            _logger.error('Error JSON IA en DocumentAgent: %s', e)
            return {'data': {"model": None, "terms": [], "exclude_terms": []}, 'tokens': 0}

    def _build_domain(self, parsed_data, query):
        domain = [('type', '=', 'binary'), ('name', 'not ilike', '.js'), ('name', 'not ilike', '.css'), ('name', 'not ilike', '.scss'), ('name', 'not ilike', '.xml'), ('name', 'not ilike', 'web.assets')]
        model = parsed_data.get('model')
        terms = parsed_data.get('terms', [])
        exclude = parsed_data.get('exclude_terms', [])

        keywords_to_clean = {'account.move': ['factura', 'facturas', 'invoice'], 'res.partner': ['contacto', 'cliente', 'proveedor'], 'sale.order': ['venta', 'presupuesto']}
        if model and model in keywords_to_clean:
            terms = [t for t in terms if t.lower() not in keywords_to_clean[model]]

        if model: domain.append(('res_model', '=', model))
        for ex in exclude: domain.append(('name', 'not ilike', ex))

        for term in terms:
            domain.append('|')
            domain.append(('name', 'ilike', term))
            domain.append(('index_content', 'ilike', term))
            
        if not model and not terms:
            palabras = [w for w in query.split() if len(w) > 3 and w.lower() not in ['para', 'este', 'como', 'sobre', 'desde']]
            if palabras:
                mejor_palabra = max(palabras, key=len)
                domain.append('|')
                domain.append(('name', 'ilike', mejor_palabra))
                domain.append(('index_content', 'ilike', mejor_palabra))
            else:
                domain.append(('id', '=', 0))
        return domain

    def _get_related_name(self, res_model, res_id):
        if not res_model or not res_id: return 'Sin relación'
        try:
            if res_model in self.env:
                obj = self.env[res_model].sudo().browse(res_id)
                if obj.exists():
                    display_name = None
                    try: display_name = obj.name_get()[0][1]
                    except Exception: display_name = getattr(obj, 'display_name', None)
                    if not display_name: display_name = getattr(obj, 'name', None) or f"ID {res_id}"
                    return f"{res_model} {display_name}"
        except Exception: pass
        return f"{res_model} #{res_id}"

    def _render_answer(self, results, search_term=None):
        html_parts = ["<b>Documentos encontrados:</b><br/>"]
        if results:
            html_parts.append('<ul style="list-style-type: none; padding-left: 0;">')
            for record in results:
                url = f"/web/content/{record['id']}"
                if search_term: url += f"#search={quote(search_term)}"
                belongs = record.get('related_name', 'Sin relación')
                label = html_lib.escape(record.get('name') or f"Adjunto {record['id']}")
                
                fragmento_html = ""
                if record.get('fragmento'):
                    fragmento_html = f"<div style='margin: 5px 0 15px 15px; font-style: italic; color: #555; font-size: 0.9em; border-left: 3px solid #ccc; padding-left: 10px;'>... {record['fragmento']} ...</div>"
                else:
                    fragmento_html = "<div style='margin-bottom: 10px;'></div>"
                
                html_parts.append(
                    f"<li>📄 <a href='{html_lib.escape(url)}' target='_blank'><b>{label}</b></a> <span style='color: #888; font-size: 0.85em;'>({html_lib.escape(record.get('mimetype') or 'desconocido')})</span><br/>"
                    f"<span style='font-size: 0.85em; color: #666;'>Asociado a: {html_lib.escape(belongs)}</span>{fragmento_html}</li>"
                )
            html_parts.append('</ul>')
        else:
            html_parts.append('<b>No se encontraron documentos con esos criterios.</b>')
        return ''.join(html_parts)