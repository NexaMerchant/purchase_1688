from odoo import models, fields, api
from odoo.addons.queue_job.job import job
from .alibaba_api import AlibabaAPI
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    alibaba_order_id = fields.Char("1688 Order ID")

    def button_sync_to_alibaba(self):
        for order in self:
            order.with_delay().job_send_order_to_alibaba()

    @job
    def job_send_order_to_alibaba(self):
        api = AlibabaAPI(self.env)
        for order in self:
            lines = []
            for line in order.order_line:
                mapping = self.env['alibaba.product.mapping'].search([
                    ('product_id', '=', line.product_id.id)
                ], limit=1)
                if not mapping:
                    continue
                lines.append({
                    'offerId': mapping.alibaba_product_id,
                    'specId': mapping.alibaba_sku_id,
                    'quantity': int(line.product_qty),
                    'price': float(line.price_unit),
                })
            payload = {
                'orderEntries': lines,
                'addressParam': {
                    'address': order.partner_id.street or '',
                    'contactPerson': order.partner_id.name,
                    'mobile': order.partner_id.phone or '',
                }
            }
            result = api.create_order(payload)
            if result and result.get('orderId'):
                order.alibaba_order_id = result['orderId']
                _logger.info("1688 order created: %s", result['orderId'])

    @job
    def job_sync_alibaba_order_status(self):
        api = AlibabaAPI(self.env)
        orders = self.search([('alibaba_order_id', '!=', False)])
        for order in orders:
            result = api.get_order_detail(order.alibaba_order_id)
            if result:
                order.message_post(body=f"1688 状态更新：{result.get('status') or '未知'}")

    @job
    def job_auto_create_orders_from_alibaba(self):
        api = AlibabaAPI(self.env)
        result = api.get_recent_orders()
        if not result:
            return
        for item in result.get('orderList', []):
            ext_order_id = item.get('orderId')
            exists = self.search([('alibaba_order_id', '=', ext_order_id)], limit=1)
            if exists:
                continue
            lines = []
            for item_line in item.get('orderEntries', []):
                sku_id = item_line.get('specId')
                mapping = self.env['alibaba.product.mapping'].search([
                    ('alibaba_sku_id', '=', sku_id)
                ], limit=1)
                if not mapping:
                    continue
                lines.append((0, 0, {
                    'product_id': mapping.product_id.id,
                    'product_qty': item_line.get('quantity', 1),
                    'price_unit': item_line.get('price', 0),
                }))
            if lines:
                self.create({
                    'partner_id': self.env.ref('base.res_partner_1').id,  # replace with your supplier
                    'order_line': lines,
                    'alibaba_order_id': ext_order_id,
                    'origin': '1688平台自动导入',
                })

    @job(retry_pattern=[10, 30, 60])
    def job_sync_alibaba_shipping(self):
        """同步发货物流信息"""
        api = AlibabaAPI(self.env)
        for order in self.filtered(lambda o: o.alibaba_order_id):
            logistics_data = api.get_order_logistics(order.alibaba_order_id)
            if not logistics_data or 'logisticsOrderList' not in logistics_data:
                continue

            for logi in logistics_data['logisticsOrderList']:
                company_name = logi.get('logisticsCompanyName')
                tracking_no = logi.get('logisticsBillNo')
                status = logi.get('status')

                picking = order.picking_ids.filtered(lambda p: p.picking_type_code == 'incoming' and p.state not in ('done', 'cancel'))
                if picking:
                    picking = picking[0]
                    picking.carrier_tracking_ref = tracking_no
                    picking.carrier_id = self.env['delivery.carrier'].search([('name', 'ilike', company_name)], limit=1).id
                    picking.message_post(body=f"1688 发货信息已同步：{company_name} / {tracking_no}")
                    if status == '已发货' and picking.state not in ('done', 'cancel'):
                        picking.action_confirm()
                        picking.action_assign()
