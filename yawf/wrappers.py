import json
import logging


logger = logging.getLogger(__name__)

HTTP_STATUSES_STRINGS = {
        # Information codes
        100: 'Continue',
        101: 'Switching Protocols',
        102: 'Processing',

        # Success codes
        200: 'OK',
        201: 'Created',
        202: 'Accepted',
        203: 'Non-Authoritative Information',
        204: 'No Content',
        205: 'Reset Content',
        206: 'Partial Content',
        207: 'Multi-Status',
        208: 'Already Reported',
        226: 'IM Used',

        # Redirection codes
        300: 'Multiple Choices',
        301: 'Moved Permanently',
        302: 'Found',
        303: 'See Other',
        304: 'Not Modified',
        305: 'Use Proxy',
        307: 'Temporary Redirect',
        308: 'Permanent Redirect',

        # Client error codes
        400: 'Bad Request',
        401: 'Unauthorized',
        402: 'Payment Required',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        406: 'Not Acceptable',
        407: 'Proxy Authentication Required',
        408: 'Request Timeout',
        409: 'Conflict',
        410: 'Gone',
        411: 'Length Required',
        412: 'Precondition Failed',
        413: 'Request Entity Too Large',
        414: 'Request URI Too Long',
        415: 'Unsupported Media Type',
        416: 'Requested Range Not Satisfiable',
        417: 'Expectation Failed',
        418: 'I\'m a teapot',
        422: 'Unprocessable Entity',
        423: 'Locked',
        424: 'Failed Dependency',
        426: 'Upgrade Required',
        428: 'Precondition Required',
        429: 'Too Many Requests',
        431: 'Request Header Fields Too Large',
        449: 'Retry With',
        451: 'Unavailable For Legal Reasons',

        # Server error codes
        500: 'Internal Server Error',
        501: 'Not Implemented',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
        504: 'Gateway Timeout',
        505: 'HTTP Version Not Supported',
        507: 'Insufficient Storage',
        510: 'Not Extended'
    }


class Headers:
    def __init__(self, env=None):
        if isinstance(env, Headers):
            self._headers = env._headers
        elif isinstance(env, dict):
            self._headers = [(key.replace('HTTP_', '').replace('_', '-'), val) for key, val in env.items()]
        elif isinstance(env, (list, tuple)):
            self._headers = [(key.replace('HTTP_', '').replace('_', '-'), val) for key, val in env]
        else:
            self._headers = []

    def __getitem__(self, item):
        for name, val in self._headers:
            if name.lower() == item.lower():
                return val
        raise KeyError

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def getall(self, item):
        return [val for name, val in self._headers if name.lower() == item.lower()]

    def add(self, name, val):
        self._headers.append((name, val))

    def __contains__(self, item):
        try:
            self[item]
            return True
        except KeyError:
            return False

    def __repr__(self):
        return 'Headers({})'.format(', '.join(['{}: "{}"'.format(key, val) for key, val in self._headers]))

    __str__ = __repr__

    def __eq__(self, other):
        if not isinstance(other, Headers):
            return False

        return sorted(self._headers) == sorted(other._headers)

    @property
    def raw(self):
        return self._headers

    @classmethod
    def from_wsgi_env(cls, env: dict):
        return cls({key: val for key, val in env.items() if key.upper().startswith('HTTP_')})


class Cookies(dict):
    def __init__(self, env=None):
        if isinstance(env, Cookies):
            super().__init__(env)
        elif not env:
            super().__init__()
        elif isinstance(env, str):
            self._init(env.split(';'))
        else:
            self._init(env)

    def _init(self, item):
        if isinstance(item, dict) and 'HTTP_COOKIE' in item:
            for i in item['HTTP_COOKIE'].split(';'):
                self._init(i.strip())

        elif isinstance(item, dict):
            self.update(item)

        elif isinstance(item, (list, tuple)):
            for i in item:
                self._init(i)

        elif isinstance(item, str):
            key, val = item.split('=')
            self[key] = val

    def set(self, key, val):
        self[key] = val

    @property
    def raw(self):
        return ';'.join(['{}={}'.format(key, val) for key, val in self.items()])


class Request:
    def __init__(self, environment):
        self.env = environment
        self._content = None
        self._headers = None
        self._cookies = None

    @property
    def path(self):
        return self.env['PATH_INFO']

    @property
    def method(self):
        return self.env['REQUEST_METHOD']

    @property
    def content(self):
        """
        :return: raw byte body content of request
        """
        if self._content is None:
            self._content = self.env['wsgi.input'].read(int(self.headers.get('content-length')) or 0)

        return self._content

    @property
    def text(self):
        """
        :return: decoded string body content of request
        """
        return self.content.decode('utf-8')

    @property
    def json(self):
        return json.loads(self.text)

    @property
    def headers(self):
        if self._headers is None:
            self._headers = Headers.from_wsgi_env(self.env)

        return self._headers

    @property
    def app(self):
        return self.env['app']

    @property
    def args(self):
        logger.debug('Querry url params: "{}"'.format(self.env['QUERY_STRING']))
        return dict(pair.split('=') for pair in self.env['QUERY_STRING'].split('&'))

    @property
    def cookies(self):
        if self._cookies is None:
            self._cookies = Cookies(self.env)

        return self._cookies


class Response:
    default_status = 200

    def __init__(self, response=None, headers=None, status=None, cookies=None):
        if isinstance(headers, Headers):
            self.headers = headers
        else:
            self.headers = Headers(headers)

        if response is None:
            self.response = []
        elif isinstance(response, str):
            self.response = [response.strip().encode() + b'\n']
            self.headers.add('Content-Type', 'text/plain')
            self.headers.add('Content-length', str(self.content_length))
        elif isinstance(response, (list, dict)):
            self.response = [json.dumps(response).encode()]
            self.headers.add('Content-Type', 'application/json')
            self.headers.add('Content-length', str(self.content_length))
        else:
            self.response = response

        self.status = status if status is not None else Response.default_status

        if isinstance(cookies, Cookies):
            self.cookies = cookies
        else:
            self.cookies = Cookies(cookies)

    def make_status_str(self):
        return '{} {}'.format(self.status, HTTP_STATUSES_STRINGS[self.status])

    def make_headers(self):
        if self.cookies.raw:
            return self.headers.raw + [self.cookies.raw]
        return self.headers.raw

    def __call__(self, environment, start_response):
        status = self.make_status_str()

        start_response(status, self.make_headers())
        logger.debug('[Response] returning data: "{}"'.format(self.response))
        return self.response

    @property
    def content_length(self):
        return sum(len(x) for x in self.response)
