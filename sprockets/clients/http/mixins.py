import logging

from sprockets.clients.http import client
from tornado import concurrent, gen


class ClientMixin(object):
    """
    Mix this in to add the ``make_http_request`` method.

    .. attribute:: http_client

       The :class:`~sprockets.clients.http.client.HTTPClient` instance
       that :meth:`.make_http_request` uses.

    """

    def initialize(self):
        super(ClientMixin, self).initialize()
        self.http_client = client.HTTPClient()
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(self.__class__.__name__)

    @gen.coroutine
    def prepare(self):
        maybe_future = super(ClientMixin, self).prepare()
        if concurrent.is_future(maybe_future):
            yield maybe_future

        if hasattr(self, 'correlation_id'):
            self.http_client.headers['Correlation-ID'] = self.correlation_id

    def make_http_request(self, method, scheme, host, *path, **kwargs):
        """
        Make a HTTP request and process the response.

        :param str method: HTTP method to invoke
        :param str scheme: URL scheme for the request
        :param str host: host to send the request to.  This can be
            a formatted IP address literal or DNS name.
        :param path: resource path to request.  Elements of the path
            are quoted as URL path segments and then joined by a ``/``
            to form the resource path.
        :keyword on_error: function to call if an error occurs.  If
            unspecified, :func:`.default_error_handler` is called.
        :keyword port: port to send the request to.  If omitted, the
            port will be chosen based on the scheme.
        :param kwargs: additional keyword arguments are passed to the
            :class:`tornado.httpclient.HTTPRequest` initializer.

        :returns: a :class:`tornado.concurrent.Future` that resolves
            to a :class:`tornado.httpclient.HTTPResponse` instance

        If a error occurs, then the ``on_error`` function is called with
        three parameters: the handler (i.e., ``self``),
        the :class:`~tornado.httpclient.HTTPRequest` that failed, and the
        :class:`~sprockets.clients.http.client.HTTPError`.  If no ``on_error``
        function is specified, then :meth:`.on_http_request_error` is
        called when a request error occurs.

        """
        future = concurrent.TracebackFuture()
        on_error = kwargs.pop('on_error', None)

        def handle_response(f):
            error = f.exception()
            if error:
                if error.code < 500:
                    log = self.logger.error
                else:
                    log = self.logger.warn
                log('%s %s resulted in %s %s', error.request.method,
                    error.request.url, error.code, error.reason)
                try:
                    if on_error:
                        on_error(self, error.request, error)
                    else:
                        self.on_http_request_error(error.request, error)
                    future.set_exception(error)
                except Exception as exc:
                    future.set_exception(exc)
            else:
                future.set_result(f.result())

        coro = self.http_client.send_request(method, scheme, host, *path,
                                             **kwargs)
        self.http_client.io_loop.add_future(coro, handle_response)

        return future

    def on_http_request_error(self, request, error):
        """
        Translates a HTTP client error to a server error.

        :param tornado.httpclient.HTTPRequest request:
            the HTTP request that failed
        :param sprockets.clients.http.client.HTTPError error:
            the error that was returned

        This is the default error handler for :class:`.ClientMixin`.
        It simply translates `error` into a :class:`tornado.web.HTTPError`
        that the server framework expects.

        """
        raise error.to_server_error()
