# -*- coding=utf8 -*-
import os
import csv
import tempfile
import time
import hmac
import base64
import hashlib
import string
import random
import datetime as dt
from contextlib import contextmanager

import six
import requests
from requests.adapters import HTTPAdapter

__all__ = ['Client']


SIGNATURE_LEN = 32
API_URL = os.environ.get('PRODUCTAI_API_URL', 'https://api.productai.cn')
API_VERSION = '1'


class Client(object):

    def __init__(self, access_key_id, access_key_secret, session=None):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        if not session:
            session = get_default_session()
        self.session = session
        self.lang = 'en-us'

    def get_api(self, type_, id_):
        return API(self, type_, id_)

    def get_image_search_api(self, id_):
        return API(self, 'search', id_)

    def get_batch_api(self):
        return BatchAPI(self)

    def get_image_set_api(self, image_set_id):
        return ImageSetAPI(self, image_set_id)

    def get(self, api_url, **kwargs):
        headers = self.get_headers(kwargs.get('params'))
        resp = self.session.get(
            api_url,
            headers=headers,
            timeout=30,
            **kwargs
        )
        return resp

    def post(self, api_url, data=None, files=None):
        headers = self.get_headers(data)
        resp = self.session.post(
            api_url,
            data=data,
            headers=headers,
            files=files,
            timeout=30,
        )
        return resp

    def get_auth_headers(self, data):
        headers = make_auth_headers(self.access_key_id, 'POST')
        headers['x-ca-signature'] = calc_signature(
            headers,
            data,
            self.access_key_secret
        )
        return headers

    def set_lang(self, lang):
        self.lang = lang

    def get_headers(self, data):
        headers = self.get_auth_headers(data)
        if self.lang:
            headers['Accept-Language'] = self.lang
        return headers


class API(object):

    def __init__(self, client, type_, id_):
        self.client = client
        self.type_ = type_
        self.id_ = id_

    def query(self, image, loc='0-0-1-1', count=20):
        data = {
            'loc': loc,
            'count': count,
        }
        files = None
        if isinstance(image, six.string_types):
            data['url'] = image
        elif hasattr(image, 'read'):
            files = {'search': image}
        return self.client.post(self.base_url, data=data, files=files)

    @property
    def base_url(self):
        return '/'.join([API_URL, self.type_, self.id_])


class BatchAPI(API):

    def __init__(self, client):
        self.client = client
        self.type_ = 'batch'
        self.id_ = '_1000001'

    def query(self, *args, **kwargs):
        raise NotImplementedError()

    def prepare_by_file(self, service_id, tf):
        endpoint = self.base_url + '/task/prepare'
        resp = self.client.post(
            endpoint,
            data={'service_id': service_id},
            files={'urls': tf},
        )
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    def prepare(self, service_id, images_infos):
        with tempfile.NamedTemporaryFile() as tf:
            writer = csv.writer(tf)
            writer.writerows(images_infos)
            tf.flush()
            tf.seek(0)
            return self.prepare_by_file(service_id, tf)

    def apply(self, task_id):
        endpoint = self.base_url + '/task/apply'
        resp = self.client.post(
            endpoint,
            data={'task_id': task_id},
        )
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    def get_task_info(self, task_id):
        endpoint = self.base_url + '/task/info/%s' % task_id
        resp = self.client.get(endpoint)
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    def revoke(self, task_id):
        endpoint = self.base_url + '/task/revoke/%s' % task_id
        resp = self.client.post(endpoint)
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    def get_tasks(self, start=None, end=None):
        endpoint = self.base_url + '/tasks'
        params = {}
        if start is not None:
            params['start'] = date_str(start)
        if end is not None:
            params['end'] = date_str(start)
        resp = self.client.get(endpoint, params=params)
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    def get_services(self):
        endpoint = self.base_url + '/services'
        resp = self.client.get(endpoint)
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()


class ImageSetAPI(API):

    def __init__(self, client, image_set_id):
        super(ImageSetAPI, self).__init__(
            client, 'image_sets', '_0000014'
        )
        self.image_set_id = image_set_id

    def query(self, image, loc='0-0-1-1'):
        raise NotImplementedError()

    @property
    def base_url(self):
        return '%s/%s' % (
            super(ImageSetAPI, self).base_url,
            self.image_set_id
        )

    def add_images_in_bulk(self, img_infos):
        '''批量添加图片'''
        with _normalize_images_file(img_infos) as f:
            files = {'urls_to_add': f}
        return self.client.post(self.base_url, files=files)

    def delete_images_in_bulk(self, img_infos):
        with _normalize_images_file(img_infos) as f:
            files = {'urls_to_delete': f}
        return self.client.post(self.base_url, files=files)

    def add_image(self, image_url, meta=None, tags=''):
        form = {'image_url': image_url, 'meta': meta, 'tags': tags}
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
    secret_key = to_bytes(secret_key)
    payload = get_payload_as_str(headers, form)
    signature = hmac.new(
        secret_key,
        payload,
        hashlib.sha1
    )
    return base64.b64encode(signature.digest())


def get_payload_as_str(headers, form):
    payload = dict(headers)

    if form:
        payload.update(form)

    sort_value = []
    for k in sorted(payload):
        v = to_bytes(payload.get(k, ''))
        v = v.strip()
        sort_value.append(b'%s=%s' % (to_bytes(k), v))

    return b'&'.join(sort_value)


def to_bytes(v):
    if not isinstance(v, six.binary_type):
        if not isinstance(v, six.string_types):
            v = str(v)
        if six.PY2:
            v = unicode(v)
        v = v.encode('utf8')
    return v


def get_default_session():
    s = requests.Session()
    # remount http and https adapters to config max_retries
    adapter = HTTPAdapter(
        max_retries=3,
        pool_connections=5,
        pool_maxsize=50,
        pool_block=True,
    )
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    return s


@contextmanager
def _normalize_images_file(x, tmpdir=None):
    if isinstance(x, six.string_types):
        with open(x) as f:
            yield f
    elif isinstance(x, list):
        with tempfile.NamedTemporaryFile(mode='w', dir=tmpdir) as tf:
            writer = csv.writer(tf)
            writer.writerows(x)
            tf.flush()
            with open(tf.name) as f:
                yield f
    else:
        yield x


def date_str(d):
    date_format = "%Y-%m-%d"
    if isinstance(d, six.string_types):
        dt.datetime.strptime(d, date_format)  # format check
        return d
    elif isinstance(d, (dt.date, dt.datetime)):
        return d.strftime('%Y-%m-%d')
    else:
        raise TypeError("Invalid date %r" % d)
