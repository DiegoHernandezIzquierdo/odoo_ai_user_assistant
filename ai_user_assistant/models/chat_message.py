from odoo import models, fields

class AiAssistantMessage(models.Model):
    _name = 'ai.assistant.message'
    _description = 'Historial de Chat del Asistente IA'
    _order = 'create_date asc'

    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, required=True, index=True)
    role = fields.Selection([
        ('user', 'Usuario'),
        ('assistant', 'Asistente')
    ], string='Rol', required=True)
    content = fields.Text(string='Contenido del Mensaje', required=True)