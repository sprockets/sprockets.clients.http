try:
    from sprockets.clients.http.mixins import ClientMixin

except ImportError as error:
    def ClientMixin(*args, **kwargs):
        raise error

version_info = (0, 0, 0)
__version__ = '.'.join(str(v) for v in version_info)
__all__ = ['version', '__version__', 'ClientMixin']
