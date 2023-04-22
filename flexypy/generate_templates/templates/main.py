try:
    from flexypy.http.server import WsgiServer
except Exception as e:
    pass


def application(environ, start_response):
    ret = WsgiServer(environ, start_response).start()
    return ret
