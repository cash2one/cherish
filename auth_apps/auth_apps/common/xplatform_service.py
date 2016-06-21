# coding: utf-8
# from __future__ import unicode_literals

import logging
import hashlib
import base64
import requests
try:
    import simple_json as json
except ImportError:
    import json
from pyDes import triple_des, ECB, PAD_PKCS5
from django.conf import settings

logger = logging.getLogger(__name__)


class XPlatformService(object):

    SERVICE_URL = settings.XPLATFORM_SERVICE['URL']
    APP_ID = settings.XPLATFORM_SERVICE['APP_ID']
    SERVER_KEY = settings.XPLATFORM_SERVICE['SERVER_KEY']
    TIMEOUT = settings.XPLATFORM_SERVICE['TIMEOUT']

    ERROR_MESSAGES = [
        (0, u'成功'),
        (1, u'需要验证码'),
        (2, u'验证码错误'),
        (3, u'用户被禁用'),
        (4, u'频率控制'),
        (5, u'票据错误，需要重新登陆'),
        (6, u'账号已经存在'),
        (7, u'账号格式非法'),
        (8, u'时间差距大于5分钟'),
        (9, u'域名非白名单'),
        (10, u'密码错误'),
        (11, u'参数错误'),
        (12, u'账号不存在'),
        (13, u'内部系统错误'),
        (20, u'没接口权限'),
        (21, u'IP没权限'),
    ]

    @classmethod
    def encrypt(cls, data, passwd):
        data = data.encode('utf-8')
        k = triple_des(passwd, ECB, pad=None, padmode=PAD_PKCS5)
        return base64.b64encode(k.encrypt(data))

    @classmethod
    def decrypt(cls, data, passwd):
        # data should be bytes here
        k = triple_des(passwd, ECB, pad=None, padmode=PAD_PKCS5)
        return k.decrypt(base64.b64decode(data))

    class BaseRequest:
        def __init__(self, head, body):
            send_head = head
            send_head['appId'] = XPlatformService.APP_ID
            send_head['v'] = '1'
            encrypted_body = XPlatformService.encrypt(
                json.dumps(body, ensure_ascii=False),
                XPlatformService.SERVER_KEY)
            self._data = {
                'head': send_head,
                'body': encrypted_body,
            }

        def data(self):
            return self._data

        def __unicode__(self):
            return 'data: {d}\n'.format(d=self.data())

        def __str__(self, encoding='utf-8'):
            return self.__unicode__().encode(encoding)

        def __repr__(self):
            return 'Request: ' + self.__str__()


    class BaseResponse:
        def __init__(self, data):
            assert(data)
            # data should be bytes here
            self._data = json.loads(data)

        def head(self):
            return self._data.get('head')

        def ret(self):
            return self._data.get('ret')

        def body(self):
            encrypted_body = self._data.get('body')
            if encrypted_body:
                decrypt_body = XPlatformService.decrypt(
                    encrypted_body,
                    XPlatformService.SERVER_KEY)
                try:
                    if decrypt_body:
                        return json.loads(decrypt_body)
                except:
                    logger.error('json body({b}) load error'.format(b=decrypt_body))
                    pass
            return None

        def is_success(self):
            ret = self.ret()
            return (ret and ret.get('code') == 0)

        def __unicode__(self):
            return 'head: {h}\nret: {r}\nbody: {b}\n'.format(
                h=self.head(), r=self.ret(), b=self.body()
                )

        def __str__(self, encoding='utf-8'):
            return self.__unicode__().encode(encoding)

        def __repr__(self):
            return 'Response: ' + self.__str__()

    def __init__(self):
        self.base_url = self.SERVICE_URL

    def _encode_rawpassword(self, raw_password):
        return hashlib.md5(raw_password).hexdigest().upper()

    def post(self, url, head, body):
        try:
            request= self.BaseRequest(head=head, body=body)
            logger.debug('[XPLATFORM] url: {url}, request: {r}'.format(
                url=url, r=request))
            r = requests.post(
                url, json=request.data(), timeout=XPlatformService.TIMEOUT)
            logger.debug(r.content)
            if r.content:
                response = self.BaseResponse(r.content)
                logger.debug(response)
                return response
            else:
                logger.error('[XPLATFORM] post error, status: {s}'.format(
                    s=r.status_code))
        except:
            logger.exception('[XPLATFORM] request exception')
        return None

    def backend_verify_once_token(self, userid, once_token):
        url = self.base_url + '/Login/verifyOnceToken'
        assert(userid)
        head = {
            'accountId': int(userid),
        }
        body = {
            'accountId': int(userid),
            'onceToken': once_token,
        }
        response = self.post(url, head=head, body=body)
        if not response or not response.is_success():
            # login error
            logger.error(response)
            return None
        return response.body()

    def backend_verify_get_account_info(self, userid, once_token):
        res = self.backend_verify_once_token(userid, once_token)
        user_info = None
        if res:
            user_info = self.account_info(userid=userid)
        return user_info

    def backend_verify_access_token(self, userid, access_token):
        url = self.base_url + '/Login/verifyAccessToken'
        assert(userid)
        body = {
            'accountId': int(userid),
            'accessToken': access_token,
        }
        response = self.post(url, head={}, body=body)
        if not response or not response.is_success():
            # login error
            logger.error(response)
            return None
        return response.body()

    """
        register_entry: {
            'mobile': 1234567,
            'password': 'xxxxxx',
            'nickname': 'xxxx',
        }
    """
    def backend_batch_mobile_register(self, register_entries):
        url = self.base_url + '/Login/register2ByPhone'
        user_list = [
            {
                'mobilePhone': entry.get('mobile'),
                'newPwd': entry.get('password', '').upper(),
                'nickName': entry.get('nickname'),
            }
            for entry in register_entries]
        response = self.post(url, head={}, body={'userList': user_list})
        if not response or not response.is_success():
            # login error
            logger.error(response)
            return None
        return response.body()

    """
        register_entry: {
            'username': 'xxxxx',
            'password': 'xxxxxx',
            'nickname': 'xxxx',
        }
    """
    def backend_batch_username_register(self, register_entries):
        url = self.base_url + '/Login/register2'
        user_list = [
            {
                'accountName': entry.get('username'),
                'newPwd': self._encode_rawpassword(entry.get('password')),
                'nickName': entry.get('nickname'),
            }
            for entry in register_entries]
        response = self.post(url, head={}, body={'userList': user_list})
        if not response or not response.is_success():
            # login error
            logger.error(response)
            return None
        return response.body()

    def backend_login(self, username, raw_password):
        url = self.base_url + '/Login/login2'
        body = {
            'accountName': username,
            'newPwd': self._encode_rawpassword(raw_password),
        }
        response = self.post(url, head={}, body=body)
        if not response or not response.is_success():
            # login error
            logger.error(response)
            return None
        return response.body()

    def backend_changepwd(self, userid, username, raw_password):
        if not (userid or username):
            logger.error('need userid or username')
            return False
        url = self.base_url + '/Login/changePwd2'
        body = {
            'newPwd': self._encode_rawpassword(raw_password)
        }
        if userid:
            body['accountId'] = int(userid)
        if username:
            body['accountName'] = username
        response = self.post(url, head={}, body=body)
        if not response or not response.is_success():
            # change password error
            logger.error(response)
            return False
        return True

    def account_info(self, userid=None, username=None):
        url = self.base_url + '/Login/getUserInfo'
        body = {}
        if userid:
            body['accountId'] = int(userid)
        elif username:
            body['accountName'] = username
        else:
            logger.error('need userid or username')
            return None
        response = self.post(url, head={}, body=body)
        if not response or not response.is_success():
            # get account info error
            logger.error(response)
            return None
        return response.body()

    def update_account_info(self, userid, username, mobile, nickname):
        url = self.base_url + '/Login/changeUserInfo'
        assert(userid)
        body = {
            'accountId': int(userid),
        }
        if username:
            body['accountName'] = username
        if mobile:
            body['mobilePhone'] = unicode(mobile)
        if nickname:
            body['nickName'] = nickname
        response = self.post(url, head={}, body=body)
        if not response or not response.is_success():
            # update account info error
            logger.error(response)
            return False
        return True

    # async push notify
    def push_notify(self, data, func_handler=None):
        response = self.BaseResponse(data)
        if not response:
            # TODO: ignore fail notify ?
            return None
        logger.debug(response)
        if not func_handler:
            return None
        body = response.body()
        if not body:
            # TODO: ignore fail notify ?
            return None
        userid = body.get('accountId', None)
        op_type = body.get('opType', None)
        assert(userid and op_type)
        # deal with operations
        return func_handler(int(userid), op_type)


xplatform_service = XPlatformService()
