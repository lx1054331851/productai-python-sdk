# -*- coding:utf-8 -*-
import datetime as dt

import six
import pytest

import productai as m


def test_short_uuid():
    c = m.short_uuid(1)
    assert c.islower() or c.isdigit()


class TestGetPayloadAsStr:

    def test_should_return_bytes(self):
        headers = {'x-ca-version': '1.0'}
        form = {'k': 'v'}
        assert isinstance(
            m.get_payload_as_str(headers, form),
            six.binary_type
        )

    def test_payloads_should_be_ordered_by_name(self):
        headers = {'x-ca-version': '1.0'}
        form = {
            'image_url': 'http://httpbin.org/image',
            'meta': '头像',
            'limit': 3
        }
        res = m.get_payload_as_str(headers, form)
        if six.PY2:
            assert res == u'image_url=http://httpbin.org/image&limit=3&meta=头像&x-ca-version=1.0'.encode('utf8')
        else:
            assert res == 'image_url=http://httpbin.org/image&limit=3&meta=头像&x-ca-version=1.0'.encode('utf8')


def test_calc_signature(mocker):
    headers = {'x-ca-version': '1.0'}
    form = {'image_url': 'http://httpbin.org/image', 'meta': '头像'}
    payload = mocker.patch.object(m, 'get_payload_as_str')
    if six.PY2:
        payload.return_value = 'hello'
    else:
        payload.return_value = b'hello'
    assert isinstance(
        m.calc_signature(headers, form, 'secret'),
        six.binary_type
    )


def test_date_str():
    d = dt.date(2015, 1, 11)
    assert m.date_str(d) == '2015-01-11'
    with pytest.raises(ValueError):
        m.date_str('asdfasdf')
    assert m.date_str(dt.datetime(2017, 2, 10)) == '2017-02-10'
