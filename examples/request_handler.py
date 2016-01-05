from sprockets.clients import http
from tornado import gen, web


class HttpBinHandler(http.ClientMixin, web.RequestHandler):
    """Sends requests to httpbin.org."""

    @gen.coroutine
    def get(self, status_code):
        response = yield self.make_http_request(
            'http://httpbin.org', 'status', status_code,
            on_error=self.handle_api_error)

        if not self._finished:
            self.set_status(200)
            if response.body:
                if response.headers.get('Content-Type'):
                    self.set_header('Content-Type',
                                    response.headers['Content-Type'])
                self.write(response.body)
            self.finish()

    @gen.coroutine
    def post(self):
        response = yield self.make_http_request(
            'http://httpbin.org/post', method='POST',
            body=self.request.body, headers=self.request.headers)

        if not self._finished:
            self.set_status(200)
            if response.body:
                if response.headers.get('Content-Type'):
                    self.set_header('Content-Type',
                                    response.headers['Content-Type'])
                self.write(response.body)
            self.finish()

    def handle_api_error(self, _, request, error):
        """
        Call ``send_error`` based on a httpclient.HTTPError.

        :param tornado.web.RequestHandler _: handler that made the request
        :param tornado.web.HTTPRequest request: the request that was made
        :param tornado.httpclient.HTTPError error: the failure

        """
        self.send_error(error.code)


def make_application(**settings):
    return web.Application([
        web.url('/(?P<status_code>\d+)', HttpBinHandler),
        web.url('/post', HttpBinHandler),
    ], **settings)


if __name__ == '__main__':
    import sprockets.http
    sprockets.http.run(make_application)
