import logging

from .errors import NotFound, MethodNotAllowed

logger = logging.getLogger(__name__)


class MultipleRouteDefinition(Exception):
    """
    Thrown if found routes wih same path and method
    """


class Route:
    def __init__(self, path, func, method):
        self.path = path
        self.func = func
        self.method = method

    def __str__(self):
        return 'Rule({}, {}, {})'.format(self.method, self.path, self.func.__name__)


class Router:
    _routes = []

    def add_route(self, method, path, func):
        try:
            found = self.search_route(path, method)
        except (NotFound, MethodNotAllowed):
            pass
        else:
            raise MultipleRouteDefinition

        self._routes.append(Route(path=path, func=func, method=method))

    def add_get(self, path, func):
        self.add_route('GET', path, func)

    def add_post(self, path, func):
        self.add_route('POST', path, func)

    def add_put(self, path, func):
        self.add_route('PUT', path, func)

    def add_patch(self, path, func):
        self.add_route('PATCH', path, func)

    def search_route(self, path, method):
        routes = [route for route in self._routes if route.path == path]
        if not routes:
            logger.warning('Path {} not found'.format(path))
            raise NotFound(path)

        routes = [route for route in routes if route.method == method]
        if not routes:
            logger.warning('Method {} not allowed for path {}'.format(method, path))
            raise MethodNotAllowed

        logger.debug('Found route {}'.format(routes[0]))
        return routes[0].func
