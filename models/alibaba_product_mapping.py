from odoo import models, fields

class AlibabaProductMapping(models.Model):
    _name = 'alibaba.product.mapping'
    _description = '1688 Product Mapping'

    product_id = fields.Many2one('product.product', required=True)
    alibaba_product_id = fields.Char(required=True)
    alibaba_sku_id = fields.Char()