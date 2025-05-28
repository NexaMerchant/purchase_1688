from odoo import http
from odoo.http import request
import logging
import requests

_logger = logging.getLogger(__name__)

class AlibabaAuthController(http.Controller):

    @http.route('/alibaba/oauth/callback', type='http', auth='public', csrf=False)
    def alibaba_auth_callback(self, **kw):
        code = kw.get('code')
        if not code:
            return "Missing authorization code from 1688."

        icp = request.env['ir.config_parameter'].sudo()
        app_key = icp.get_param("alibaba.app_key")
        app_secret = icp.get_param("alibaba.app_secret")
        redirect_uri = request.httprequest.base_url

        token_url = f"https://gw.open.1688.com/openapi/http/1/system.oauth2/getToken/{app_key}"
        payload = {
            'grant_type': 'authorization_code',
            'need_refresh_token': 'true',
            'client_id': app_key,
            'client_secret': app_secret,
            'code': code,
            'redirect_uri': redirect_uri
        }

        try:
            response = requests.post(token_url, data=payload, timeout=15)
            result = response.json()
            if 'access_token' in result:
                icp.set_param("alibaba.access_token", result['access_token'])
                icp.set_param("alibaba.refresh_token", result['refresh_token'])
                return "<h2>授权成功！现在你可以开始同步1688订单了。</h2>"
            else:
                _logger.error("Token exchange failed: %s", result)
                return "<h2>授权失败，请检查日志。</h2>"

        except Exception as e:
            _logger.exception("Authorization failed")
            return f"<h2>授权出错: {str(e)}</h2>"
