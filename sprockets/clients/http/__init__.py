try:
    from sprockets.clients.http.client import HTTPClient, HTTPError
    from sprockets.clients.http.mixins import ClientMixin

except ImportError as error:
    def ClientMixin(*args, **kwargs):
        raise error

    def HTTPClient(*args, **kwargs):
        raise error

    def HTTPError(*args, **kwargs):
        raise error

version_info = (0, 0, 0)
__version__ = '.'.join(str(v) for v in version_info)
__all__ = ['version_info', '__version__',
           'ClientMixin', 'HTTPClient', 'HTTPError']
