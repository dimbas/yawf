import logging.config


from yawf import YAWF, Request, Response


logging.basicConfig(level=logging.DEBUG)
logging.config.dictConfig({
    'version': 1,
    'root': {
         'level': logging.DEBUG,
         'handlers': ['console']
    },
    'handlers': {
         'console': {
            'class': 'logging.StreamHandler',
            'level': logging.DEBUG,
            'formatter': 'console'
         }
    },
    'formatters': {
        'console': {
            'format': '[%(asctime)s] [%(levelname)s %(module)s] %(message)s'
        }
    },
    'loggers': {
        'yawf.app': {
            'level': logging.DEBUG,
            'handlers': ['console'],
            'propagate': False
        },
        'yawf.wrappers': {
            'level': logging.DEBUG,
            'handlers': ['console'],
            'propagate': False
        },
        'test.app': {
            'level': logging.INFO,
            'handlers': ['console'],
            'propagate': False
        }
    }
})

logger = logging.getLogger(__name__)

cookies_storage = dict()


def index(request: Request) -> Response:
    logger.info('[APP] calling index')
    return Response('Hello World!!!')


def add_data(request: Request) -> Response:
    """
    adds querry parameters to app.data attr
    """
    logger.info('[APP] calling add data')
    count = 0
    for key, val in request.args.items():
        request.app.data[key] = val
        count += 1

    return Response('Added {} arguments'.format(count))


def get_data(request: Request) -> Response:
    logger.info('[APP] calling get data')
    return Response('Stored data: {}'.format(request.app.data))


def get_body(request: Request) -> Response:
    logger.info('[APP] calling get body')
    data = request.text
    return Response('Received text data: "{}"'.format(data))


def get_headers(request: Request) -> Response:
    logger.info('[APP] calling get headers')
    h = request.headers
    return Response('Received headers: {}'.format(h.wsgi_headers), headers=request.headers)


def get_json(request: Request) -> Response:
    logger.info('[APP] calling get json')
    j = request.json
    return Response(j)


def exception(request: Request) -> Response:
    logger.info('[APP] calling exception')
    1 / 0


def set_cookies(request: Request) -> Response:
    counter = 0
    for key, val in request.args.items():
        cookies_storage[key] = val
        counter += 1

    return Response('Received {count} values for cookies.'.format(count=counter))


def get_cookies(request: Request) -> Response:
    cookies = request.cookies
    return Response('Received cookies: "{}", and {} to cookie storage'
                    .format(cookies, 'equals' if cookies == cookies_storage else 'not equals'))


def process_url_args(request: Request, id, action) -> Response:
    return Response('Received action {} to id {}'.format(action, id))


app = YAWF()
app.data = {}
app.router.add_get(r'/$', index)
app.router.add_post(r'/data$', add_data)
app.router.add_get(r'^/data$', get_data)
app.router.add_get(r'^/body$', get_body)
app.router.add_get(r'^/headers$', get_headers)
app.router.add_get(r'^/json$', get_json)
app.router.add_get(r'^/error$', exception)
app.router.add_put(r'^/cookies$', set_cookies)
app.router.add_get(r'^/cookies$', get_cookies)
app.router.add_get('/prod/(?P<id>\d+)/(?P<action>[a-zA-Z]+)', process_url_args)
