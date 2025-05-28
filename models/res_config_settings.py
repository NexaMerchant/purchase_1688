from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alibaba_app_key = fields.Char(string="1688 App Key")
    alibaba_app_secret = fields.Char(string="1688 App Secret")
    alibaba_access_token = fields.Char(string="Access Token")
    alibaba_refresh_token = fields.Char(string="Refresh Token")

    def set_values(self):
        super().set_values()
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param("alibaba.app_key", self.alibaba_app_key)
        icp.set_param("alibaba.app_secret", self.alibaba_app_secret)
        icp.set_param("alibaba.access_token", self.alibaba_access_token)
        icp.set_param("alibaba.refresh_token", self.alibaba_refresh_token)

    @api.model
    def get_values(self):
        icp = self.env['ir.config_parameter'].sudo()
        return super().get_values().update({
            'alibaba_app_key': icp.get_param("alibaba.app_key"),
            'alibaba_app_secret': icp.get_param("alibaba.app_secret"),
            'alibaba_access_token': icp.get_param("alibaba.access_token"),
            'alibaba_refresh_token': icp.get_param("alibaba.refresh_token"),
        })

    def action_get_alibaba_authorization_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        redirect_uri = f"{base_url}/alibaba/oauth/callback"
        auth_url = (
            f"https://oauth.1688.com/authorize"
            f"?client_id={self.alibaba_app_key}"
            f"&site=1688"
            f"&redirect_uri={redirect_uri}"
            f"&state=odoo1688"
        )
        return {
            'type': 'ir.actions.act_url',
            'url': auth_url,
            'target': 'self',
        }
