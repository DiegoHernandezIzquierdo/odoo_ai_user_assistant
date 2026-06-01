# -*- coding: utf-8 -*-
{
    'name': 'AI User Assistant',
    'version': '16.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Asistente de IA contextual para resolución de dudas de usuarios',
    'description': """
        Módulo que integra un asistente de IA en el cliente web de Odoo.
        Es capaz de analizar el contexto actual de la pantalla (modelo, vista, datos) 
        y responder dudas operativas de los usuarios basándose estrictamente en hechos.
    """,
    'author': 'Diego/CCBosco',
    'website': 'https://www.tudominio.com',
    'license': 'AGPL-3', # Licencia estándar recomendada por OCA
    'depends': [
        'base', 
        'web',       # Requerido para inyectar componentes en el framework OWL
        'base_setup' # Requerido para heredar res.config.settings
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/chat_message_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        # Cargamos los recursos en el backend (interfaz interna de usuarios)
        'web.assets_backend': [
            'ai_user_assistant/static/src/scss/ai_assistant.scss',
            'ai_user_assistant/static/src/js/ai_assistant.js',
            'ai_user_assistant/static/src/xml/ai_assistant.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}