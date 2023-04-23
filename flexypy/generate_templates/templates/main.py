try:
    from flexypy.http.server import WsgiServer
except Exception as e:
    print(e)


def application(environ, start_response):
    ret = WsgiServer(environ, start_response).start()
    return ret
