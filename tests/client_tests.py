import os

from tornado import testing
import tornado.httpclient

from sprockets.clients.http import client


HTTPBIN_BASE_URL = 'http://{}:{}'.format(
    os.environ.get('HTTPBIN_HOST', 'httpbin.org'),
    os.environ.get('HTTPBIN_PORT', '80'))


class HttpClientTests(testing.AsyncTestCase):

    def setUp(self):
        super(HttpClientTests, self).setUp()
        self.client = client.HTTPClient()

    @testing.gen_test
    def test_that_builds_simple_url(self):
        response = yield self.client.send_request(
            'GET', HTTPBIN_BASE_URL, 'get')
        self.assertEqual(response.code, 200)

    @testing.gen_test
    def test_that_customized_httperror_is_raised(self):
        try:
            yield self.client.send_request('GET', HTTPBIN_BASE_URL,
                                           'status', 593)
        except tornado.httpclient.HTTPError as error:
            self.assertIsInstance(error, client.HTTPError)
            self.assertIsInstance(error.request,
                                  tornado.httpclient.HTTPRequest)
            self.assertEqual(error.request.method, 'GET')
            self.assertEqual(error.request.url,
                             '{}/status/593'.format(HTTPBIN_BASE_URL))
            self.assertEqual(error.code, 593)
            self.assertEqual(error.reason, 'UNKNOWN')

        else:
            self.fail('sprockets.clients.http.client.HTTPError was not raised')
