from flexypy.http.request import Request
from dataclasses import dataclass
import mimetypes
from config.apps import PATH_TO_FXP_APPS
from config.dirs import MDDL_LIST_PATH
import importlib
from wsgiref import util
from flexypy.http.routing import UserRoute
from typing import Type
import os
from flexypy.exceptions.web.server import PathNotFound
from urllib import parse
from cgi import FieldStorage
from flexypy.middlewares.mddl import Middleware
import re


@dataclass
class HtmlResponse:
    code: str
    header: list[tuple[str, str]]
    html: bytes


@dataclass
class MddlRedirect:
    from_path: str
    to_path: str


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
        self._get_fxp_apps()
        self.router = Router(self.environ, self.routes, self.full_url)
        self._set_server_cookie()

    def _set_server_cookie(self):
        try:
            if 'HTTP_COOKIE' in self.environ:
                self.request.set_server_cookie(self.environ['HTTP_COOKIE'])
        except Exception as e:
            pass

    def _route(self) -> HtmlResponse:
        path_found = False
        match self.environ['REQUEST_METHOD']:
            case 'GET':
                if self.router.check_url():
                    path_found = True
                    app = self.router.check_url()()

                    # Set request data
                    self.request.GET.set_data(self.router.query_kwargs)
                    self.request.path = self.full_url

                    # Set app request
                    app.request = self.request

                    mddl_app, mddl_redirect = self._run_middlewares(app)
                    if mddl_redirect:
                        if mddl_redirect.from_path and mddl_redirect.to_path:
                            if self.full_url == mddl_redirect.from_path:
                                return self.render.render_redirect(mddl_redirect.to_path)
                    return self._method_get(mddl_app)

                if self.router.check_static_file():
                    return self._method_get_static_files(self.router.check_static_file())

                # If path not found
                if not path_found:
                    t = PathNotFound(self.full_url, [self.server_address + i().get_path() for i in self.routes])
                    return self.render.render_traceback(t.code, t.html)
            case 'POST':
                if self.router.check_url():
                    app = self.router.check_url()()

                    # Set request data
                    self.request.GET.params = self.router.query_kwargs
                    form_data = FieldStorage(fp=self.environ['wsgi.input'], environ=self.environ,
                                             keep_blank_values=True)
                    self.request.POST.set_data(form_data)

                    # Set app request
                    app.request = self.request

                    mddl_app, mddl_redirect = self._run_middlewares(app)
                    if mddl_redirect:
                        if mddl_redirect.from_path and mddl_redirect.to_path:
                            if self.full_url == mddl_redirect.from_path:
                                return self.render.render_redirect(mddl_redirect.to_path)

                    return self._method_post(mddl_app)

    def _method_get(self, app: UserRoute) -> HtmlResponse:
        mime_type = mimetypes.guess_type(app.template_path)[0]
        resp = self.render.render_html('200 OK', [('Content-type', mime_type)], app.get())
        return resp

    def _method_post(self, app: UserRoute):
        resp = self.render.render_redirect(app.post())
        return resp

    def _method_get_static_files(self, filepath) -> HtmlResponse:
        # get static filepath
        if 'HTTP_REFERER' in self.environ:
            current_url: str = self.environ['HTTP_REFERER'].replace(self.server_address, '')
            if current_url.endswith('/'):
                p = filepath.split(current_url)[-1].strip('/')
            elif not current_url:
                p = filepath
            else:
                if current_url.rfind('/') != -1:
                    converted_path = current_url[:current_url.rfind('/')+1:]
                else:
                    converted_path = current_url

                p = filepath

                if filepath.startswith(converted_path):
                    p = filepath.split(converted_path)[-1].strip('/')

                    # If names are duplicated in the path. For example test/test/path/to/file
                    for i in re.finditer(converted_path, filepath):
                        if os.path.exists(filepath[i.end()::]):
                            p = filepath[i.end()::]
                            break

            if os.path.exists(p):
                with open(p, 'rb') as f:
                    mime_type = mimetypes.guess_type(p)[0]
                    resp = self.render.render_html('200 OK', [('Content-type', mime_type)], f.read())
                    return resp

    def _run_middlewares(self, app: UserRoute) -> list[UserRoute, MddlRedirect]:
        mddl = (os.path.join(MDDL_LIST_PATH, 'mddl_list'))
        mddl_app = app
        redirect = None
        if os.path.exists(mddl+'.py'):
            global_t_obj = __import__(mddl.replace('/', '.'), fromlist=['middlewares'])
            mddl_list = getattr(global_t_obj, 'middlewares')

            for mddl in mddl_list:
                m: Middleware = mddl(self.request, app)
                m.start()
                mddl_app = m.app
                redirect = MddlRedirect(m.redirect_from, m.redirect_to)
        return [mddl_app, redirect]

    def _set_cookie(self, header):
        """
        Set the cookies that the user writes to the request.
        After the data is written to the header the field in the request is cleared.
        """
        if self.request.get_user_set_cookie():
            header.extend(("set-cookie", morsel.OutputString())
                          for morsel in self.request.get_user_set_cookie().values())
            # clear request cookies
            self.request.clear_request_cookie()

    def start(self):
        resp = self._route()

        if 'HTTP_COOKIE' in self.environ:
            self.request.set_server_cookie(self.environ['HTTP_COOKIE'])
        if resp:
            # set header cookies
            self._set_cookie(resp.header)

            self.start_response(resp.code, resp.header)
            return [resp.html]
        else:
            mime_type = self.environ['SCRIPT_NAME']
            header = [('Content-type', mime_type)]
            self.start_response('404 Not found', header)
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

    def render_redirect(self, path):
        return HtmlResponse('303 See Other', [('Location', path)], b'')


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
        return par

    def _parse_qs(self, path: str) -> list[str, dict]:
        p = path.split('?')
        return [p[0], parse.parse_qs(self.environ['QUERY_STRING'])]

    def check_static_file(self):
        if self.current_url.rfind('.') != -1:
            return self.current_url
        else:
            return None
