import logging

from sprockets.clients.http import client
from tornado import gen


def default_error_handler(handler_, request_, error):
    """
    Translates a HTTP client error to a server error.

    :param tornado.web.RequestHandler handler_:
        the request hander that made the request
    :param tornado.httpclient.HTTPRequest request_:
        the HTTP request that failed
    :param sprockets.clients.http.client.HTTPError error:
        the error that was returned

    This is the default error handler for :class:`.ClientMixin`.
    It simply translates `error` into a :class:`tornado.web.HTTPError`
    that the server framework expects.

    """
    raise error.to_server_error()


class ClientMixin(object):
    """Mix this in to add the ``make_http_request`` method."""

    def initialize(self):
        super(ClientMixin, self).initialize()
        self.__client = client.HTTPClient()
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(self.__class__.__name__)

    @gen.coroutine
    def make_http_request(self, method, server, *path, **kwargs):
        """
        Make a HTTP request and process the response.

        :param str method: HTTP method to invoke
        :param str server: the host to send the request to
        :param path: resource path to request
        :keyword on_error: function to call if an error occurs.  If
            unspecified, :func:`.default_error_handler` is called.
        :param kwargs: additional keyword arguments are passed to the
            :class:`tornado.httpclient.HTTPRequest` initializer.

        The ``on_error`` function is called with three parameters: the
        handler (i.e., ``self``), the :class:`~tornado.httpclient.HTTPRequest`
        that failed, and the :class:`~sprockets.clients.http.client.HTTPError`.

        """
        on_error = kwargs.pop('on_error', default_error_handler)
        try:
            response = yield self.__client.send_request(method, server,
                                                        *path, **kwargs)
            raise gen.Return(response)

        except client.HTTPError as error:
            if error.code < 500:
                log = self.logger.error
            else:
                log = self.logger.warn
            log('%s %s resulted in %s %s', error.request.method,
                error.request.url, error.code, error.reason)
            on_error(self, error.request, error)

    def set_status(self, status_code, reason=None):
        # Overridden to remove the raising of ValueError when
        # reason is None and status is a custom code.
        try:
            super(ClientMixin, self).set_status(status_code, reason)
        except ValueError:
            super(ClientMixin, self).set_status(status_code, 'Unknown Reason')
