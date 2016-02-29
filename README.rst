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
               'GET', some_server_url, on_error=self.handle_api_error)
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

Running Tests
-------------
The test cases use the most excellent httpbin.org site to poke an HTTP API
that responds to errors in a reliable manner. However this can cause failures
if you happen to get rate limited by httpbin.org. If you want to be nice to
the maintainers of httpbin.org, you can run a version in `docker`_ and point
the tests at it instead.  The following snippet shows how to do this using
`docker-machine`_ installed via `docker-toolbox`_:

.. code-block:: bash

   $ eval "$(docker-machine env default)"
   $ machine_id=$(docker run -d -p 8000 citizenstig/httpbin)
   $ export HTTPBIN_HOST=$(docker-machine ip default)
   $ export HTTPBIN_PORT=$(docker port $machine_id 8000 | cut -d: -f2)
   $ env/bin/nosetests
   ........
   ----------------------------------------------------------------------
   Ran 8 tests in 0.255s

   OK
   $ docker stop $machine_id | xargs docker rm

.. _docker: https://www.docker.com
.. _docker-machine: https://www.docker.com/products/docker-machine
.. _docker-toolbox: https://www.docker.com/products/docker-toolbox
