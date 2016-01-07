import json
import logging
import uuid

from tornado import testing

from examples import request_handler


class RecordingHandler(logging.Handler):
    """Log handler that records what was logged."""
    def __init__(self, *args, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        self.records = []
        self.lines = []

    def emit(self, record):
        self.records.append(record)
        self.lines.append(self.format(record))


class LoggingTests(testing.AsyncHTTPTestCase):

    def setUp(self):
        super(LoggingTests, self).setUp()
        self.log_handler = RecordingHandler(level=logging.DEBUG)
        logger = logging.getLogger('HttpBinHandler')
        logger.addHandler(self.log_handler)

    def tearDown(self):
        super(LoggingTests, self).tearDown()
        logger = logging.getLogger('HttpBinHandler')
        logger.removeHandler(self.log_handler)

    def get_app(self):
        return request_handler.make_application()

    def find_log_line_containing(self, value):
        for index, line in enumerate(self.log_handler.lines):
            if value in line:
                return index
        self.fail('Did not find log line containing "{}"'.format(value))

    def test_that_requests_are_logged_at_debug_level(self):
        self.fetch('/200')
        log_index = self.find_log_line_containing('sending GET ')
        self.assertEqual(self.log_handler.records[log_index].levelno,
                         logging.DEBUG)
        self.assertIn('GET http://httpbin.org/status/200',
                      self.log_handler.lines[log_index])

    def test_that_client_errors_are_logged_at_error_level(self):
        self.fetch('/400')
        log_index = self.find_log_line_containing(
            'GET http://httpbin.org/status/400 resulted in')
        self.assertEqual(self.log_handler.records[log_index].levelno,
                         logging.ERROR)

    def test_that_server_errors_are_logged_at_warning_level(self):
        self.fetch('/500')
        log_index = self.find_log_line_containing(
            'GET http://httpbin.org/status/500 resulted in')
        self.assertEqual(self.log_handler.records[log_index].levelno,
                         logging.WARN)


class MixinTests(testing.AsyncHTTPTestCase):

    def get_app(self):
        app = request_handler.make_application()
        return app

    def test_that_response_is_returned(self):
        uid = str(uuid.uuid4())
        response = self.fetch('/post', method='POST',
                              body=json.dumps({'uid': uid}),
                              headers={'Content-Type': 'application/json'})
        self.assertEqual(response.code, 200)

        body = json.loads(response.body.decode('utf-8'))
        self.assertEqual(body['json']['uid'], uid)
