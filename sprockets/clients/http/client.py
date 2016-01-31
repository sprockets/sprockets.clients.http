import logging

from tornado import gen, httpclient, httputil, web


log = logging.getLogger(__name__)


class HTTPError(httpclient.HTTPError):
    """
    Extended Tornado HTTP Client Error.

    The standard :class:`tornado.httpclient.HTTPError` is a little
    difficult to use correctly and safely.  This sub-class makes
    HTTP failures easier to use programatically.

    .. rubric: Attributes

    .. py:attribute:: request

       :class:`tornado.httpclient.HTTPRequest` that failed

    .. py:attribute:: code

       Integer status code. This is usually a HTTP status code but
       may be one of Tornado's internal status codes (e.g, 599 for a
       timeout).

    .. py:attribute:: reason

       HTTP reason or the string ``Unknown``.

    .. py:attribute:: response

       :class:`tornado.httpclient.HTTPResponse` or :data:`None`

    """

    def __init__(self, request, code, reason=None, response=None):
        self.reason = reason or httputil.responses.get(code, 'Unknown')
        super(HTTPError, self).__init__(code, message=reason,
                                        response=response)
        self.request = request

    @classmethod
    def from_tornado_error(cls, http_request, http_error):
        """
        Convert a Tornado client error.

        :param tornado.httpclient.HTTPRequest http_request:
            the request that caused the error
        :param tornado.httpclient.HTTPError http_error:
            the underlying Tornado failure
        :return: a compatible instance of :class:`.HTTPError`

        """
        response = http_error.response
        return HTTPError(http_request, http_error.code, response=response,
                         reason=None if response is None else response.reason)

    def to_server_error(self):
        """
        Convert a client error into a :class:`tornado.web.HTTPError`

        :return: a compatible :class:`tornado.web.HTTPError` instance

        """
        if self.code == 599:  # tornado custom response code
            exc = web.HTTPError(503, 'API Timeout')
        else:
            exc = web.HTTPError(self.code)
            exc.reason = self.reason
        return exc


class HTTPClient(object):
    """
    HTTP client connector.

    :param args: passed to :class:`~tornado.httpclient.AsyncHTTPClient`
        initializer
    :param kwargs: passed to :class:`~tornado.httpclient.AsyncHTTPClient`
        initializer

    This class serves as a more intelligent version of
    :class:`~tornado.httpclient.AsyncHTTPClient`.

    """

    def __init__(self, *args, **kwargs):
        super(HTTPClient, self).__init__()
        self.client = httpclient.AsyncHTTPClient(*args, **kwargs)
        self.logger = log.getChild(self.__class__.__name__)

    @gen.coroutine
    def send_request(self, method, server, *path, **kwargs):
        """
        Send a HTTP request.

        :param tornado.httpclient.HTTPRequest request: the request to send
        :returns: :class:`tornado.httpclient.HTTPResponse` instance
        :raises: :class:`.HTTPError`

        """
        target = '{}/{}'.format(server, '/'.join(str(s) for s in path))
        request = httpclient.HTTPRequest(target, method=method, **kwargs)
        self.logger.debug('sending %s %s', request.method, request.url)
        try:
            response = yield self.client.fetch(request)
            raise gen.Return(response)

        except httpclient.HTTPError as error:
            raise HTTPError.from_tornado_error(request, error)
