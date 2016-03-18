import json
import logging
import uuid

from tornado import gen, testing, web

from examples import request_handler
from sprockets.clients.http import mixins

from tests import HTTPBIN_PORT, HTTPBIN_SERVER, HTTPBIN_URL


class RecordingHandler(logging.Handler):
    """Log handler that records what was logged."""
    def __init__(self, *args, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        self.records = []
        self.lines = []

    def emit(self, record):
        self.records.append(record)
        self.lines.append(self.format(record))


class TestingHandler(mixins.ClientMixin, web.RequestHandler):

    def initialize(self):
        self.logger = logging.getLogger('testing')
        super(TestingHandler, self).initialize()

    @gen.coroutine
    def get(self, status_code):
        kwargs = {}
        server = self.get_query_argument('server', HTTPBIN_SERVER)
        port = self.get_query_argument('port', HTTPBIN_PORT)
        conn_timeout = self.get_query_argument('connect_timeout', None)
        if conn_timeout is not None:
            kwargs['connect_timeout'] = float(conn_timeout)
        response = yield self.make_http_request('GET', 'http', server,
                                                'status', status_code,
                                                port=port, **kwargs)
        self.logger.info('got it')
        self.set_status(response.code)


class LoggingTests(testing.AsyncHTTPTestCase):
    LOGGERS = ['HttpBinHandler',
               'sprockets.clients.http.client.HTTPClient',
               'testing']

    def setUp(self):
        super(LoggingTests, self).setUp()
        self.log_handler = RecordingHandler(level=logging.DEBUG)
        for logger in self.LOGGERS:
            logging.getLogger(logger).addHandler(self.log_handler)

    def tearDown(self):
        super(LoggingTests, self).tearDown()
        for logger in self.LOGGERS:
            logging.getLogger(logger).removeHandler(self.log_handler)

    def get_app(self):
        app = request_handler.make_application(server=HTTPBIN_SERVER,
                                               port=HTTPBIN_PORT)
        app.add_handlers(r'.*', [
            web.url('/testing/(?P<status_code>\d+)', TestingHandler),
        ])
        return app

    def find_log_line_containing(self, value):
        for index, line in enumerate(self.log_handler.lines):
            if value in line:
                return index
        self.fail('Did not find log line containing "{}" in {!r}'.format(
            value, self.log_handler.lines))

    def test_that_requests_are_logged_at_debug_level(self):
        self.fetch('/200')
        log_index = self.find_log_line_containing('sending GET ')
        self.assertEqual(self.log_handler.records[log_index].levelno,
                         logging.DEBUG)
        self.assertIn('GET {}/status/200'.format(HTTPBIN_URL),
                      self.log_handler.lines[log_index])

    def test_that_client_errors_are_logged_at_error_level(self):
        self.fetch('/400')
        log_index = self.find_log_line_containing(
            'GET {}/status/400 resulted in'.format(HTTPBIN_URL))
        self.assertEqual(self.log_handler.records[log_index].levelno,
                         logging.ERROR)

    def test_that_server_errors_are_logged_at_warning_level(self):
        self.fetch('/500')
        expected = 'GET {}/status/500 resulted in'.format(HTTPBIN_URL)
        log_index = self.find_log_line_containing(expected)
        self.assertEqual(self.log_handler.records[log_index].levelno,
                         logging.WARN)

    def test_that_logger_attribute_is_preserved(self):
        self.fetch('/testing/200')
        self.find_log_line_containing('got it')

    def test_that_default_handler_reports_error(self):
        response = self.fetch('/testing/500')
        self.assertEqual(response.code, 500)


class MixinTests(testing.AsyncHTTPTestCase):

    def get_app(self):
        app = request_handler.make_application(server=HTTPBIN_SERVER,
                                               port=HTTPBIN_PORT)
        app.add_handlers(r'.*', [
            web.url('/testing/(?P<status_code>\d+)', TestingHandler),
        ])
        return app

    def test_that_response_is_returned(self):
        uid = str(uuid.uuid4())
        response = self.fetch('/post', method='POST',
                              body=json.dumps({'uid': uid}),
                              headers={'Content-Type': 'application/json'})
        self.assertEqual(response.code, 200)

        body = json.loads(response.body.decode('utf-8'))
        self.assertEqual(body['json']['uid'], uid)

    def test_that_mixin_supports_custom_response_codes(self):
        response = self.fetch('/601')
        self.assertEqual(response.code, 601)

    def test_that_mixin_translates_timeouts_to_503(self):
        # sending a HTTP request to example.com:7 reliably times out
        response = self.fetch('/testing/200'
                              '?server=example.com&port=7'
                              '&connect_timeout=0.1')
        self.assertEqual(response.code, 503)
