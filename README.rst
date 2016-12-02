ProductAI SDK for Python
========================

.. image:: https://travis-ci.org/MalongTech/productai-python-sdk.svg?branch=master
    :target: https://travis-ci.org/MalongTech/productai-python-sdk

安装
----

.. code-block:: bash

    $ pip install productai

快速入门
--------

添加图片到图集
~~~~~~~~

.. code-block:: python

    from productai import Client

    cli = Client(access_key_id, access_key_secret)
    api = cli.get_image_set_api(image_set_id)
    resp = api.add_image(url, meta)


删除图集中的图片
~~~~~~~

.. code-block:: python

    from productai import Client

    cli = Client(access_key_id, access_key_secret)
    api = cli.get_image_set_api(image_set_id)
    with open("images.csv") as f:
        resp = api.delete_images(f)


搜索图片
~~~~

.. code-block:: python

    from productai import Client

    cli = Client(access_key_id, access_key_secret)
    api = cli.get_image_search_api(service_id)
    resp = api.query(image_url)


使用其他服务
~~~~~~

.. code-block:: python

    from productai import Client

    cli = Client(access_key_id, access_key_secret)
    api = cli.get_api(service_type, service_id)
    resp = api.query(image_url)
