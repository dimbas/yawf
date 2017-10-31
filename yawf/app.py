import sys
import typing as t
import logging

from .router import Router
from .wrappers import Request, Response
from .errors import HttpError, InternalServerError


logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s %(module)s] [%(lineno)s] %(message)s',
    level=logging.ERROR,
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class YAWF:
    def __init__(self, request_class=Request):
        self.router = Router()
        self._request_class = request_class

    def make_request(self, environment) -> Request:
        environment['app'] = self
        return self._request_class(environment)

    def find_handler(self, request: Request) -> t.Callable:
        return self.router.search_route(path=request.path, method=request.method)

    def before_response(self, request: Request) -> Request:
        return request

    def after_response(self, response: Response) -> Response:
        return response

    def make_response(self, environment) -> Response:
        logger.debug('Creating request from wsgi environment')
        request = self.make_request(environment)

        logger.debug('Preprocessing request with before_response method')
        request = self.before_response(request)

        handler, args = self.find_handler(request)
        response = handler(request, **args)

        logger.debug('Postprocessing response with after_response method')
        response = self.after_response(response)

        return response

    def __call__(self, environment, start_response):
        try:
            response = self.make_response(environment)
        except HttpError as error:
            response = error
        except Exception:
            logger.exception('Unknown error', exc_info=True)
            response = InternalServerError()
        finally:
            return response(environment, start_response)
