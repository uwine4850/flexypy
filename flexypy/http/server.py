from flexypy.http.request import Request
from dataclasses import dataclass
import mimetypes
from config.apps import PATH_TO_FXP_APPS, STATIC_DIR_NAME, STATIC_DIRS
import importlib
from wsgiref import util
from flexypy.http.routing import UserRoute
from typing import Type
import os
from flexypy.exceptions.web.server import PathNotFound
from urllib import parse


@dataclass
class HtmlResponse:
    code: str
    header: list[tuple[str, str]]
    html: bytes


class WsgiServer:
    current_app_path = ''

    def __init__(self, environ: dict, start_response):
        self.environ = environ
        self.start_response = start_response
        self.root_url = util.shift_path_info(self.environ)
        self.full_url = self.root_url + util.request_uri(self.environ).replace(util.application_uri(self.environ), '')
        self.server_address = util.application_uri(self.environ).replace(self.root_url, '')
        self.render: RenderTemplate = RenderTemplate()
        self.routes: list[Type[UserRoute]] = []
        self.router = None
        self.request = Request
        if self.root_url != 'favicon.ico':
            self._get_fxp_apps()
            self.router = Router(self.environ, self.routes, self.full_url)

    def _route(self) -> HtmlResponse:
        path_found = False
        match self.environ['REQUEST_METHOD']:
            case 'GET':
                if self.root_url != 'favicon.ico':
                    if self.router.check_url():
                        path_found = True
                        app = self.router.check_url()()
                        self.request.Get.params = self.router.query_kwargs

                        # SET APP REQUEST
                        app.request = self.request
                        return self._method_get(app)

                    if self.router.check_static_file():
                        path_found = True
                        return self._method_get_static_files(self.router.check_static_file())
                # IF PATH NOT FOUND
                if not path_found:
                    t = PathNotFound(self.full_url, [self.server_address + i().get_path() for i in self.routes])
                    return self.render.render_traceback(t.code, t.html)
            case 'POST':
                pass

    def _method_get(self, app: UserRoute) -> HtmlResponse:
        with open(app.get(), 'rb') as f:
            mime_type = mimetypes.guess_type(app.template_path)[0]
            resp = self.render.render_html('200 OK', [('Content-type', mime_type)], f.read())
            return resp

    def _method_get_static_files(self, filepath) -> HtmlResponse:
        # TODO: TEMP
        p = os.path.join(STATIC_DIR_NAME, filepath.split(STATIC_DIR_NAME)[-1].strip('/'))
        cp = ''
        for i in STATIC_DIRS:
            if os.path.exists(os.path.join(i, p)):
                cp = os.path.join(i, p)
        if not cp:
            raise 'STATIC ROUTE ERROR'

        with open(cp, 'rb') as f:
            mime_type = mimetypes.guess_type(cp)[0]
            resp = self.render.render_html('200 OK', [('Content-type', mime_type)], f.read())
            return resp

    def start(self):
        if self.root_url != 'favicon.ico':
            resp = self._route()
            self.start_response(resp.code, resp.header)
            return [resp.html]
        else:
            return [b'']

    def _get_fxp_apps(self):
        for p in PATH_TO_FXP_APPS:
            import_path = p.replace('/', '.').strip('.') + '.fxp'
            importlib.import_module(import_path)
        self.routes = UserRoute.__subclasses__()


class RenderTemplate:
    def __init__(self):
        pass

    def _text_to_html(self, text: str | bytes) -> bytes:
        if isinstance(text, bytes):
            return bytes(text)
        elif isinstance(text, str):
            return bytes(text, 'utf-8')

    def render_html(self, code, header: list[tuple[str, str]], html: str | bytes) -> HtmlResponse:
        h = self._text_to_html(html)
        return HtmlResponse(code, header, h)

    def render_404(self, html: str | bytes):
        return HtmlResponse('404 Not Found', [('Content-type', 'text/html')], self._text_to_html(html))

    def render_traceback(self, code: str, html: str | bytes):
        return HtmlResponse(code, [('Content-type', 'text/html')], self._text_to_html(html))


class Router:
    def __init__(self, environ,  apps: list[Type[UserRoute]], current_url: str):
        self.environ = environ
        self.apps = apps
        self.current_url = current_url
        self.query_kwargs = {}

    def check_url(self) -> Type[UserRoute] | None:
        url, self.query_kwargs = self._parse_qs(self.current_url)

        for app in self.apps:
            a = app()
            check_path = a.path
            url_params = {}
            # Check slug fields
            if a.slug_data.count != -1:
                url_params = self._get_url_params(a)
                check_path = a.path
                for p in url_params:
                    check_path = check_path.replace(f"[{p}]", url_params[p][0])

            if check_path == url:
                self.query_kwargs.update(url_params)
                return app

        # if url in [app().path for app in self.apps]:
        #     for app in self.apps:
        #         a = app()
        #         if a.path == url:
        #             return app
        return None

    def _get_url_params(self, app) -> dict:
        par = {}
        u = self.current_url
        for sp in app.slug_data.params:
            p = u[app.slug_data.params[sp][0]::]
            if p.find('/') != -1:
                u = app.path[:app.slug_data.params[sp][1]:] + p[p.find('/')::]
                p = p[:p.find('/'):]
            if p:
                par[sp.strip('[').strip(']')] = [p]
            else:
                return par
        # if app.slug_data.count > 0:
        #     u = self.current_url
        #     for sp in app.slug_data.params:
        #         p = u[app.slug_data.params[sp][0]::]
        #         if p.find('/') != -1:
        #             u = app.path[:app.slug_data.params[sp][1]:] + p[p.find('/')::]
        #             p = p[:p.find('/'):]
        #         par.append(p)
        # else:
        #     u = self.current_url
        #     for sp in app.slug_data.params:
        #         p = u[app.slug_data.params[sp][0]::]
        #         par.append(p)
        return par

    def _parse_qs(self, path: str) -> list[str, dict]:
        p = path.split('?')
        return [p[0], parse.parse_qs(self.environ['QUERY_STRING'])]


    def check_static_file(self):
        if self.current_url.rfind('.') != -1:
            return self.current_url
        else:
            return None
