import requests
import logging

_logger = logging.getLogger(__name__)

class AlibabaAPI:

    def __init__(self, env):
        self.env = env
        self.icp = env['ir.config_parameter'].sudo()
        self.app_key = self.icp.get_param("alibaba.app_key")
        self.app_secret = self.icp.get_param("alibaba.app_secret")
        self.access_token = self.icp.get_param("alibaba.access_token")
        self.refresh_token = self.icp.get_param("alibaba.refresh_token")

    def _refresh_token(self):
        url = f"https://gw.open.1688.com/openapi/http/1/system.oauth2/getToken/{self.app_key}"
        params = {
            'grant_type': 'refresh_token',
            'client_id': self.app_key,
            'client_secret': self.app_secret,
            'refresh_token': self.refresh_token
        }
        try:
            resp = requests.get(url, params=params)
            data = resp.json()
            if 'access_token' in data:
                self.icp.set_param("alibaba.access_token", data['access_token'])
                self.access_token = data['access_token']
                _logger.info("1688 access token refreshed.")
                return True
        except Exception as e:
            _logger.exception("Token refresh failed: %s", str(e))
        return False

    def _call_api(self, method, path, data=None, retry=True):
        url = f"https://gw.open.1688.com/openapi/{path}/{self.app_key}"
        try:
            resp = requests.request(method, url, json=data, params={'access_token': self.access_token})
            if resp.status_code == 401 and retry:
                self._refresh_token()
                return self._call_api(method, path, data, retry=False)
            return resp.json()
        except Exception as e:
            _logger.exception("Alibaba API Error: %s", str(e))
            return {}

    def create_order(self, order_data):
        return self._call_api('post', 'param2/1/com.alibaba.trade/alibaba.createOrder', order_data)

    def get_order_detail(self, order_id):
        return self._call_api('get', 'param2/1/com.alibaba.trade/alibaba.trade.get.buyerView', {
            'orderId': order_id
        })

    def get_recent_orders(self):
        return self._call_api('get', 'param2/1/com.alibaba.trade/alibaba.trade.getSellerOrderList', {
            'page': 1,
            'pageSize': 10
        })

    def get_order_logistics(self, order_id):
        return self._call_api('get', 'param2/1/com.alibaba.logistics/alibaba.trade.getLogisticsInfos', {
            'orderId': order_id
        })
