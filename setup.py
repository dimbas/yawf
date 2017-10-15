# coding=utf-8
from setuptools import find_packages, setup

with open('yawf/__init__.py') as fd:
    for line in fd:
        if line.startswith('__version__'):
            version = line.strip().split('=')[1].strip(' \'"')
            break
    else:
        version = 'develop'

with open('README.rst', 'rb') as fd:
    README = fd.read().decode()

with open('dev-requirements.txt') as fd:
    TEST_REQUIREMENTS = [x.strip() for x in fd.readlines()]

setup(
    name='yawf',
    version=version,
    description='',
    long_description=README,
    author='Tambovcev D.A.',
    author_email='tambovcev.dmitry@yandex.ru',
    maintainer='Tambovcev D.A.',
    maintainer_email='tambovcev.dmitry@yandex.ru',
    url='https://github.com/dimbas/yawf',
    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],

    tests_require=TEST_REQUIREMENTS,

    packages=find_packages(),
)
