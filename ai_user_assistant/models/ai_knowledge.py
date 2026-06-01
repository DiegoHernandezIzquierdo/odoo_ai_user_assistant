from odoo import models, fields

class AiAssistantKnowledge(models.Model):
    _name = 'ai.assistant.knowledge'
    _description = 'Base de Conocimiento del Asistente IA'

    name = fields.Char(string='Descripción / Título', required=True)
    # Usamos Char para que coincida exactamente con lo que envía el JS (ej. 'res.partner')
    model_name = fields.Char(string='Nombre Técnico del Modelo', required=True, help="Ejemplo: sale.order o mi.modulo.custom")
    instructions = fields.Text(string='Instrucciones para la IA', required=True, help="Explica aquí los campos ocultos, flujos o reglas de negocio para este modelo.")