import time
import hmac
import base64
import hashlib
import string
import random

import requests

__all__ = ['Client']


SIGNATURE_LEN = 32
API_URL = 'https://api.productai.cn'
API_VERSION = '1'


class Client(object):

    def __init__(self, access_key_id, access_key_secret):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    def get_api(self, type_, id_):
        return API(self, type_, id_)

    def get_image_search_api(self, image_set_id):
        return ImageSearchAPI(self, image_set_id)

    def post(self, api_url, data=None, files=None):
        headers = make_auth_headers(self.access_key_id, 'POST')
        headers['x-ca-signature'] = calc_signature(
            headers,
            data,
            self.access_key_secret
        )
        resp = requests.post(
            api_url,
            data=data,
            headers=headers,
            files=files,
            verify=False,
            timeout=30,
        )
        return resp


class API(object):

    def __init__(self, client, type_, id_):
        self.client = client
        self.type_ = type_
        self.id_ = id_

    def query(self, image, loc='0-0-1-1'):
        # TODO add support for uploading image file
        data = {
            'url': image,
            'loc': loc
        }
        return self.client.post(self.base_url, data=data)

    @property
    def base_url(self):
        return '/'.join([API_URL, self.type_, self.id_])


class ImageSearchAPI(API):

    def __init__(self, client, image_set_id):
        super(ImageSearchAPI, self).__init__(
            client, 'image_sets', '_0000014'
        )
        self.image_set_id = image_set_id

    @property
    def base_url(self):
        return '%s/%s' % (
            super(ImageSearchAPI, self).base_url,
            self.image_set_id
        )

    def add_image(self, image_url, meta=None):
        form = {'image_url': image_url, 'meta': meta}
        return self.client.post(self.base_url, data=form)

    def delete_images(self, f_urls_to_delete):
        urls_to_delete = {'urls_to_delete': f_urls_to_delete}
        return self.client.post(self.base_url, files=urls_to_delete)


def short_uuid(length):
    charset = string.ascii_lowercase + string.digits
    return ''.join([random.choice(charset) for i in range(length)])


def make_auth_headers(access_key_id, method='POST'):
    timestamp = int(time.time())
    headers = {
        'x-ca-accesskeyid': access_key_id,
        'x-ca-version': API_VERSION,
        'x-ca-timestamp': str(timestamp),
        'x-ca-signaturenonce': short_uuid(SIGNATURE_LEN),
        'requestmethod': method,
    }
    return headers


def calc_signature(headers, form, secret_key):
    payload = dict(headers)

    if form:
        payload.update(form)

    sort_value = []
    for k in sorted(payload):
        v = payload.get(k, '')
        if not isinstance(v, basestring):
            v = str(v)
        v = v.strip()
        value = '%s=%s' % (k, v)
        sort_value.append(value)

    string_to_signature = '&'.join(sort_value)
    signature = hmac.new(
        secret_key,
        string_to_signature,
        hashlib.sha1
    )
    return base64.b64encode(signature.digest())
