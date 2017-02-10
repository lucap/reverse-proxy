import tornado.ioloop
import tornado.web
from tornado.httpclient import AsyncHTTPClient


http_client = AsyncHTTPClient()


class ReverseProxyHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        http_client.fetch(
            self.convert_url(self.request),
            callback=self.on_response,
            headers=self.request.headers
        )

    def on_response(self, resp):
        self.set_status(resp.code)
        for k, v in resp.headers.get_all():
            self.add_header(k, v)
        self.write(resp.body)
        self.finish()

    def convert_url(self, request):
        return 'http://localhost:8000' + request.uri


def make_app():
    return tornado.web.Application([
        (r".*", ReverseProxyHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8001)
    tornado.ioloop.IOLoop.current().start()
