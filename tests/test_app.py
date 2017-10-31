import json
import typing as t
from io import BytesIO
from wsgiref.handlers import SimpleHandler

import pytest

from yawf.router import MultipleRouteDefinition
from yawf.wrappers import Cookies, Headers


from ._app import app


def create_base_env():
    return {
        'HTTP_HOST': 'localhost:8080',
        'HTTP_USER_AGENT': 'test client',
        'REMOTE_ADDR': '127.0.0.1',
        'REMOTE_PORT': '29899',
        'REQUEST_METHOD': None,
        'SCRIPT_NAME': '',
        'SERVER_NAME': 'test server',
        'SERVER_PORT': '8080',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'UWSGI_ROUTER': 'http',
        'uwsgi.node': b'test server',
        'uwsgi.version': b'2.0.15',
        'wsgi.input': BytesIO(),
    }.copy()


def create_request(path: str, method: str,
                   params: dict=None,
                   body: bytes=None,
                   headers: t.Union[Headers, t.Dict]=None,
                   cookies=None):

    env = create_base_env()

    if cookies is not None:
        env['HTTP_COOKIE'] = Cookies(cookies).wsgi_header_value

    if headers is not None:
        if isinstance(headers, dict):
            headers_iter = lambda: headers.items()
        elif isinstance(headers, Headers):
            headers_iter = lambda: headers.wsgi_headers
        else:
            raise TypeError('Headers must be Headers instance or dict')

        for key, val in headers_iter():
            key = 'HTTP_' + key.replace('-', '_').replace(' ', '_').upper()
            env[key] = val

    if body is not None:
        length = env['wsgi.input'].write(body)
        # env['wsgi.input'].flush()
        env['wsgi.input'].seek(0)
        env['HTTP_CONTENT_LENGTH'] = str(length)

    if params is not None:
        env['QUERY_STRING'] = '&'.join(['{}={}'.format(key, val) for key, val in params.items()])
    else:
        env['QUERY_STRING'] = ''

    env['PATH_INFO'] = path
    env['REQUEST_URI'] = path + ('' if params is None else '?'+env['QUERY_STRING'])

    env['REQUEST_METHOD'] = method.upper()

    return env


def do_request(env):
    handler = SimpleHandler(environ=env, stdin=env['wsgi.input'], stdout=env['wsgi.input'], stderr=BytesIO())

    return app(env, handler.start_response)[0].decode().strip()


def test_index():
    env = create_request('/', 'GET')
    response = do_request(env)

    assert response == 'Hello World!!!'


def test_add_data():
    env = create_request('/data', 'POST', params={'add': 'data', 'and': 'some more'})
    response = do_request(env)

    assert '2' in response
    assert 'Added' in response


def test_get_data():
    params = {'add': 'data', 'and': 'some more'}
    env = create_request('/data', 'POST', params=params)

    do_request(env)

    env = create_request('/data', 'GET')
    response = do_request(env)

    assert 'Stored data' in response
    assert json.loads(response.replace('Stored data: ', '').replace("'", '"')) == params


def test_get_body():
    body = b'hello!!!'
    env = create_request('/body', 'GET', body=body)

    response = do_request(env)

    assert response == 'Received text data: "{}"'.format(body.decode())

    env['wsgi.input'].seek(0)
    assert env['wsgi.input'].read().decode().strip() in response


def test_get_json():
    data = {'some': 'interesting data', 'and': 'more'}
    body = json.dumps(data).encode()
    env = create_request('/json', 'GET', body=body)

    response = do_request(env)
    resp_json = json.loads(response)

    assert resp_json == data


def test_get_headers():
    env = create_request('/headers', 'GET', headers={'I-AM': 'terminator!!!'})
    response = do_request(env)

    assert 'terminator' in response


def test_get_error():
    env = create_request('/error', 'GET')
    response = do_request(env)

    assert '500' in response


def test_not_found():
    env = create_request('/not_found', 'GET')
    response = do_request(env)

    assert '404' in response


def test_multiple_route_def():
    app.router.add_get('/some', lambda x: x)

    with pytest.raises(MultipleRouteDefinition):
        app.router.add_get('/some', lambda x: x)


def test_cookies():
    cookies = {'user': 'me', 'token': 'super secret'}

    env = create_request('/cookies', 'PUT', params=cookies)
    response = do_request(env)

    assert str(len(cookies)) in response

    env = create_request('/cookies', 'GET', cookies=cookies)
    response = do_request(env)

    assert 'not equals' not in response

    for key, val in cookies.items():
        assert key in response
        assert val in response

    c = Cookies({'some': 'data'})
    cc = Cookies(c)

    assert c == cc
    assert 'data' in str(c)

    c.set('one', 'more')
    assert 'one' in c


def test_header_obj():
    h = Headers({'some': 'data'})

    assert 'some' in h

    with pytest.raises(KeyError):
        hh = h['not existing key']

    assert h.get('not existing key') is None
    assert h.get('not existing key', 'exists') == 'exists'

    h.add('some', 'more')

    assert h.getall('some') == ['data', 'more']
    assert 'not existing' not in h


def test_headers():
    h = Headers({'I-Am': 'terminator'})
    hh = Headers(h)

    assert h == hh
    assert 'terminator' in str(h)

    h.add('Some', 'val')
    h.add('Some', 'more')

    assert len(h.getall('Some')) == 2


def test_url_args():
    env = create_request('/prod/11/read', 'GET')
    response = do_request(env)

    assert '11' in response
    assert 'read' in response
