import logging

from tornado import gen, httpclient


log = logging.getLogger(__name__)


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
        super(HTTPClient, self).__init__(*args, **kwargs)
        self.client = httpclient.AsyncHTTPClient(*args, **kwargs)
        self.logger = log.getChild(self.__class__.__name__)

    @gen.coroutine
    def send_request(self, request):
        """
        Send a HTTP request.

        :param tornado.httpclient.HTTPRequest request: the request to send
        :returns: :class:`tornado.httpclient.HTTPResponse` instance
        :raises: :class:`tornado.httpclient.HTTPError`

        """
        self.logger.debug('sending %s %s', request.method, request.url)
        response = yield self.client.fetch(request)
        raise gen.Return(response)
