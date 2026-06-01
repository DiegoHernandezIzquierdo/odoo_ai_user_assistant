# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Uso de config_parameter: El ORM guarda automáticamente este valor en ir.config_parameter
    ai_assistant_api_key = fields.Char(
        string="API Key de la IA",
        config_parameter='ai_user_assistant.api_key',
        help="Clave de acceso para la API del proveedor de IA."
    )
    
    ai_assistant_provider = fields.Selection(
    [('OpenAI', 'OpenAI')], # <-- Fíjate que la clave izquierda es 'OpenAI' respetando mayúsculas
    string="Proveedor de IA",
    default='OpenAI'
)