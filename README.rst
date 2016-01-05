sprockets.clients.http
======================

Simplifies calling HTTP APIs from Tornado-based applications.

This library implements a mix-in class that adds a single method which
makes a HTTP request and calls a callback when an error occurs.  The
request is made using Tornado's asynchronous HTTP client so it does
not block the active IO loop.

.. code-block:: python

   from sprockets.clients import http
   from tornado import gen, web

   class MyHandler(http.ClientMixin, web.RequestHandler):

       @gen.coroutine
       def get(self):
           response = yield self.make_http_request(
               some_server_url, on_error=self.handle_api_error)
           if self._finished:
               yield gen.Return()

           # handle response as you wish
           # ...
           self.finish()

       def handle_api_error(self, request, error):
           self.send_error(error.code)

That's it.  What you do not see is asynchronous client usage and logging
that happens inside of the library.  There is some setup code in
``ClientMixin.initialize`` so make sure to call the super implementation
if you implement ``initialize`` in your request handler.
