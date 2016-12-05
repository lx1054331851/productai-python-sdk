import productai as m


class TestQuery:

    def test_should_upload_file_like_obj(self, mocker):
        api = m.API(mocker.Mock(), 'classify_fashion', '_0000001')
        f = mocker.Mock()
        f.read = lambda: b'1111'

        api.query(f, '0-0-1-1')

        api.client.post.assert_called_with(
            api.base_url,
            data={'loc': '0-0-1-1'},
            files={'search': f}
        )

    def test_should_accept_image_url(self, mocker):
        api = m.API(mocker.Mock(), 'classify_fashion', '_0000001')
        image = 'http://httpbin.org/image'

        api.query(image, '0-0-1-1')

        api.client.post.assert_called_with(
            api.base_url,
            data={'loc': '0-0-1-1', 'url': image},
            files=None,
        )
