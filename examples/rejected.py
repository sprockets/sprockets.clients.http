from rejected import consumer
from sprockets.clients import http
from tornado import gen


class Consumer(http.ClientMixin, consumer.Consumer):
    """
    Makes requests against httpbin.org.

    The message format that this consumer accepts is simply the
    status code to request from ``http://httpbin.org/status/:code``
    as a plain text body.

    """

    @gen.coroutine
    def process(self):
        yield self.make_http_request(
            'GET', 'http', 'httpbin.org', 'status', self.body,
            headers={'Accept': 'application/json'},
            on_error=self.translate_http_error)

    def translate_http_error(self, request, error):
        """
        Raise the appropriate rejected failure to handle a HTTP error.

        :param tornado.web.HTTPRequest request: the request that failed
        :param tornado.httpclient.HTTPError error: the failure

        """
        if error.code < 500:
            self.logger.error('%s %s failed: %r',
                              request.method, request.url, error)
            raise consumer.MessageException

        self.logger.warning('%s %s failed with %r, retrying',
                            request.method, request.url, error)
        raise consumer.ProcessingException
