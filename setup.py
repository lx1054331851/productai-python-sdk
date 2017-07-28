from setuptools import setup

setup(
    name='productai',
    version='0.4.2',
    url='https://github.com/MalongTech/productai-python-sdk',
    install_requires=['requests>=2.12.1', 'six>=1.10.0'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    packages=['productai']
)
