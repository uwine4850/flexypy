from flexypy.http.server import WsgiServer


def application(environ, start_response):
    ret = WsgiServer(environ, start_response).start()
    return ret
