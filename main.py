import json
import hashlib
from urllib import urlencode
from urlparse import urlparse, urlunparse, parse_qs
from functools import partial

import tornado.ioloop
import tornado.web
import tornado.httputil
from tornado.httpclient import AsyncHTTPClient

INCOMING_PORT = 8006
OUTGOING_PORT = 8080

http_client = AsyncHTTPClient()
cache = {}


def get_request_hash(url, body):
    m = hashlib.md5()

    # hash the url
    u = urlparse(url)
    query = parse_qs(u.query)

    # remove cache busting query param
    query.pop('_', None)

    # sort the query params
    u = u._replace(query=urlencode(sorted(query.items()), True))
    m.update(urlunparse(u))

    if body:
        m.update(json.dumps(body, sort_keys=True))

    return m.hexdigest()


class ReverseProxyHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.fetch()

    @tornado.web.asynchronous
    def post(self):
        self.fetch()

    def fetch(self):
        method = self.request.method
        body = self.request.body if method == 'POST' else None
        new_url = self.convert_url(self.request)

        key = get_request_hash(new_url, body)

        if key in cache:
            self.on_response(None, cache[key])
        else:
            http_client.fetch(
                new_url,
                callback=partial(self.on_response, key),
                headers=self.request.headers,
                method=method,
                body=body,
                decompress_response=False,
            )

    def on_response(self, key, resp):
        if key:
            cache[key] = resp

        self.set_status(resp.code)

        self._headers = tornado.httputil.HTTPHeaders()
        for header, v in resp.headers.get_all():
            self.add_header(header, v)

        self.write(resp.body)
        self.finish()

    def convert_url(self, request):
        return "http://127.0.0.1:%s%s" % (OUTGOING_PORT, request.uri)


if __name__ == "__main__":
    app = tornado.web.Application([
        (r".*", ReverseProxyHandler),
    ])
    app.listen(INCOMING_PORT)
    tornado.ioloop.IOLoop.current().start()
