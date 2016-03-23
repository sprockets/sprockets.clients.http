import logging
try:
    from urllib import parse
except ImportError:
    import urllib as parse


from tornado import concurrent, httpclient, httputil, web


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
        if not exc.reason:
            exc.reason = httputil.responses.get(self.code, 'Unknown')
        return exc


class HTTPClient(object):
    """
    HTTP client connector.

    :param args: passed to :class:`~tornado.httpclient.AsyncHTTPClient`
        initializer
    :param kwargs: passed to :class:`~tornado.httpclient.AsyncHTTPClient`
        initializer

    This class serves as a more intelligent version of
    :class:`~tornado.httpclient.AsyncHTTPClient`.  You can access the
    underlying ``AsyncHTTPClient`` instance using the :attr:`.client`
    attribute if need be.

    .. attribute:: headers

       :class:`tornado.httputil.HTTPHeaders` instance that is sent with
       each HTTP Request.

    """

    def __init__(self, *args, **kwargs):
        super(HTTPClient, self).__init__()
        self._client_args = args
        self._client_kwargs = kwargs
        self._client = None
        self.headers = httputil.HTTPHeaders()
        self.logger = log.getChild(self.__class__.__name__)

    @property
    def client(self):
        """Underlying :class:`tornado.httpclient.AsyncHTTPClient` instance"""
        if self._client is None:
            self._client = httpclient.AsyncHTTPClient(*self._client_args,
                                                      **self._client_kwargs)
        return self._client

    @property
    def io_loop(self):
        """
        :class:`tornado.ioloop.IOLoop` instance used by the client.

        This is useful if you want to add callbacks to the same IOLoop
        that the HTTP client is going to use.  If you need to control
        which IOLoop is used for whatever reason, pass a custom IOLoop
        to the initializer as the ``io_loop`` keyword parameter.

        """
        return self.client.io_loop

    def send_request(self, method, scheme, host, *path, **kwargs):
        """
        Send a HTTP request.

        :param str method: HTTP method to invoke
        :param str scheme: URL scheme for the request
        :param str host: host to send the request to.  This can be
            a formatted IP address literal or DNS name.
        :param path: resource path to request.  Elements of the path
            are quoted as URL path segments and then joined by a ``/``
            to form the resource path.
        :keyword port: port to send the request to.  If omitted, the
            port will be chosen based on the scheme.
        :param kwargs: additional keyword arguments are passed to the
            :class:`tornado.httpclient.HTTPRequest` initializer.

        :returns: :class:`tornado.concurrent.Future` that resolves to
            a :class:`tornado.httpclient.HTTPResponse` instance
        :raises: :class:`.HTTPError`

        """
        port = kwargs.pop('port', None)
        netloc = host if port is None else '{}:{}'.format(host, port)
        target = '{}://{}/{}'.format(scheme, netloc,
                                     '/'.join(parse.quote(str(s), safe='')
                                              for s in path))
        if 'headers' in kwargs:
            headers = self.headers.copy()
            headers.update(kwargs.pop('headers'))
            kwargs['headers'] = headers
        else:
            kwargs['headers'] = self.headers

        request = httpclient.HTTPRequest(target, method=method, **kwargs)
        self.logger.debug('sending %s %s', request.method, request.url)

        future = concurrent.TracebackFuture()

        def handle_future(f):
            exc = f.exception()
            if isinstance(exc, httpclient.HTTPError):
                if exc.code == 599:
                    future.set_exception(HTTPError(request, 503, 'API Timeout',
                                                   response=exc.response))
                else:
                    future.set_exception(HTTPError.from_tornado_error(
                        request, exc))
            elif exc:
                future.set_exception(exc)
            else:
                future.set_result(f.result())

        coro = self.client.fetch(request)
        self.io_loop.add_future(coro, handle_future)

        return future
