Examples
========

Tornado Request Handler
-----------------------
This is a simple `tornado`_ request handler that calls
:meth:`~tornado.web.RequestHandler.send_error` based on the
:class:`tornado.httpclient.HTTPError` from the server.

.. literalinclude:: ../examples/request_handler.py
   :pyobject: HttpBinHandler

Rejected Consumer
-----------------
This is a simple `rejected`_ consumer that handles HTTP 400 errors by telling
rejected to drop the message when a HTTP client error (4xx) is returned and to
retry the message when a HTTP server error (5xx) is returned.

.. literalinclude:: ../examples/rejected.py
   :pyobject: Consumer

.. _rejected: http://rejected.readthedocs.org/
.. _tornado: http://www.tornadoweb.org/
