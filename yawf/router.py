import re
import logging

from .errors import NotFound, MethodNotAllowed

logger = logging.getLogger(__name__)


class MultipleRouteDefinition(Exception):
    """
    Thrown if found routes wih same path and method
    """


class Route:
    def __init__(self, path: str, method, handler):
        if not path.startswith('^'):
            path = '^' + path

        if not path.endswith('$'):
            path += '$'

        self.path = re.compile(path)
        self.method = method
        self.handler = handler

    def __str__(self):
        return 'Rule({}, {}, {})'.format(self.method, self.path, self.handler.__name__)

    __repr__ = __str__

    def match_path(self, path):
        return self.path.match(path)

    def get_url_args(self, path):
        return self.match_path(path).groupdict()


class Router:
    _routes = {}

    def add_route(self, method, path, handler):
        try:
            found = self.search_route(path, method)
        except (NotFound, MethodNotAllowed):
            pass
        else:
            raise MultipleRouteDefinition

        self._routes[path, method] = (Route(path=path, method=method, handler=handler))

    def add_get(self, path, func):
        self.add_route('GET', path, func)

    def add_post(self, path, func):
        self.add_route('POST', path, func)

    def add_put(self, path, func):
        self.add_route('PUT', path, func)

    def add_patch(self, path, func):
        self.add_route('PATCH', path, func)

    def search_route(self, path, method):
        routes = [route for route in self._routes.values() if route.match_path(path)]
        if not routes:
            logger.warning('Path {} not found'.format(path))
            raise NotFound(path)

        routes = [route for route in routes if route.method == method]
        if not routes:
            logger.warning('Method {} not allowed for path {}'.format(method, path))
            raise MethodNotAllowed

        route = routes[0]
        logger.debug('Found route {}'.format(route))
        return route.handler, route.get_url_args(path)
