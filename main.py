import tornado.ioloop
import tornado.web
import tornado.httputil
from tornado.httpclient import AsyncHTTPClient


http_client = AsyncHTTPClient()
INCOMING_PORT = 8006
OUTGOING_PORT = 8080


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

        http_client.fetch(
            new_url,
            callback=self.on_response,
            headers=self.request.headers,
            method=method,
            body=body,
            decompress_response=False,
        )

    def on_response(self, resp):
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
