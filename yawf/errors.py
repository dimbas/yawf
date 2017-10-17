from .wrappers import HTTP_STATUSES_STRINGS, Response
from .utils import escape


err_template = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>{code} {name}</title>
<h1>{name}</h1>
{description}
"""


class HttpError(Exception):
    code = None
    description = None

    def __init__(self, description=None, response=None):
        if description is not None:  # pragma: no cover
            self.description = description

        self.response = response

    @property
    def name(self):
        """The status name."""
        return HTTP_STATUSES_STRINGS.get(self.code, 'Unknown Error')

    def get_description(self, environ):
        return '<p>{}</p>'.format(escape(self.description))

    def get_body(self, environ):
        return err_template.format(
                code=self.code,
                name=escape(self.name),
                description=self.get_description(environ)
            )

    def get_headers(self, environ=None):
        return [('Content-type', 'text/html')]

    def get_response(self, environ):
        if self.response is not None:  # pragma: no cover
            return self.response

        h = self.get_headers(environ)
        b = self.get_body(environ)
        return Response(b, headers=h, status=self.code)

    def __call__(self, environ, start_response):
        response = self.get_response(environ)
        return response(environ, start_response)

    def __repr__(self):  # pragma: no cover
        return '{name}({args})'\
            .format(name=self.__class__.__name__,
                    args=', '.join(['{}="{}"'.format(key, val) for key, val in self.__dict__.items()]))

    __str__ = __repr__


class NotFound(HttpError):
    code = 404
    description = 'The requested URL was not found on the server.'

    def __init__(self, path, *args, **kwargs):
        HttpError.__init__(self, *args, **kwargs)
        self.path = path


class MethodNotAllowed(HttpError):
    code = 405
    description = 'The method is not allowed for the requested URL.'


class InternalServerError(HttpError):
    code = 500
    description = 'The server encountered an internal error and was unable to complete your request.'
