import os

HTTPBIN_SERVER = os.environ.get('HTTPBIN_HOST', 'httpbin.org')
HTTPBIN_PORT = os.environ.get('HTTPBIN_PORT', None)
if HTTPBIN_PORT:
    HTTPBIN_URL = 'http://{}:{}'.format(HTTPBIN_SERVER, HTTPBIN_PORT)
else:
    HTTPBIN_URL = 'http://{}'.format(HTTPBIN_SERVER)
