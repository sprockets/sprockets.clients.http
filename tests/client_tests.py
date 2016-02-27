import json

from tornado import httpserver, testing, web
import tornado.httpclient

from sprockets.clients.http import client

from tests import HTTPBIN_PORT, HTTPBIN_SERVER, HTTPBIN_URL


class EchoHandler(web.RequestHandler):

    def get(self, *path, **kwargs):
        self.write(json.dumps({
            'path': path,
            'kwargs': kwargs,
        }).encode('utf-8'))
        self.set_status(200)


class HttpClientTests(testing.AsyncTestCase):

    def setUp(self):
        super(HttpClientTests, self).setUp()
        self.client = client.HTTPClient()

    def start_application(self, app):
        server = httpserver.HTTPServer(request_callback=app,
                                       io_loop=self.io_loop)
        server.listen(0, address='127.0.0.1')
        socks = list(server._sockets.keys())
        return server._sockets[socks[0]].getsockname()

    @testing.gen_test
    def test_that_builds_simple_url(self):
        response = yield self.client.send_request(
            'GET', 'http', HTTPBIN_SERVER, 'get', port=HTTPBIN_PORT)
        self.assertEqual(response.code, 200)

    @testing.gen_test
    def test_that_customized_httperror_is_raised(self):
        try:
            yield self.client.send_request('GET', 'http', HTTPBIN_SERVER,
                                           'status', 593, port=HTTPBIN_PORT)
        except tornado.httpclient.HTTPError as error:
            self.assertIsInstance(error, client.HTTPError)
            self.assertIsInstance(error.request,
                                  tornado.httpclient.HTTPRequest)
            self.assertEqual(error.request.method, 'GET')
            self.assertEqual(error.request.url,
                             '{}/status/593'.format(HTTPBIN_URL))
            self.assertEqual(error.code, 593)
            self.assertEqual(error.reason, 'UNKNOWN')

        else:
            self.fail('sprockets.clients.http.client.HTTPError was not raised')

    @testing.gen_test
    def test_that_path_elements_are_url_encoded(self):
        app = web.Application([
            web.url('/(?P<one>.*)/(?P<two>.*)', EchoHandler),
        ])
        server_ip, server_port = self.start_application(app)

        response = yield self.client.send_request(
            'GET', 'http', server_ip, 'with spaces ', 'and/with/slashes',
            port=server_port,
        )
        self.assertEqual(response.code, 200)
        body = json.loads(response.body.decode('utf-8'))
        self.assertEqual(body['kwargs'], {'one': 'with spaces ',
                                          'two': 'and/with/slashes'})

    def test_that_client_is_cached(self):
        self.assertIs(self.client.client, self.client.client)
