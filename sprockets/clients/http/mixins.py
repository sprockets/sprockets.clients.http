import logging

from sprockets.clients.http import client
from tornado import gen


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

        The ``on_error`` function is called with three parameters: the
        handler (i.e., ``self``), the :class:`~tornado.httpclient.HTTPRequest`
        that failed, and the :class:`~sprockets.clients.http.client.HTTPError`.

        """
        port = kwargs.pop('port', None)
        on_error = kwargs.pop('on_error', None)

        try:
            response = yield self.http_client.send_request(
                method, scheme, host, *path, port=port, **kwargs)
            raise gen.Return(response)

        except client.HTTPError as error:
            if error.code < 500:
                log = self.logger.error
            else:
                log = self.logger.warn
            log('%s %s resulted in %s %s', error.request.method,
                error.request.url, error.code, error.reason)
            if on_error:
                on_error(self, error.request, error)
            else:
                self.on_http_request_error(error.request, error)

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

    def set_status(self, status_code, reason=None):
        # Overridden to remove the raising of ValueError when
        # reason is None and status is a custom code.
        try:
            super(ClientMixin, self).set_status(status_code, reason)
        except ValueError:
            super(ClientMixin, self).set_status(status_code, 'Unknown Reason')
