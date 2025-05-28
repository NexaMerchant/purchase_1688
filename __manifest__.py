{
    'name': 'Alibaba 1688 Purchase Integration',
    'summary': 'Integrate Alibaba 1688 for purchase orders and product mapping',
    'License': 'LGPL-3',
    'author': 'Steve',
    'version': '1.0',
    'category': 'Purchases',
    'depends': ['purchase', 'queue_job'],
    'data': [
        'security/ir.model.access.csv',
        'views/alibaba_product_mapping_views.xml',
        'views/res_config_settings_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': True,
}