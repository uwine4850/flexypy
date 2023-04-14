from flexypy.http.request import Request
from dataclasses import dataclass
import re


@dataclass
class SlugData:
    count: int
    params: dict


class Route:
    def __init__(self, path, template_path):
        self.path = path
        self.template_path = template_path
        self.method = ''
        self.get_func = None
        self.post_func = None
        self.request: Request = None

    def get_path(self):
        return self.path

    def get(self):
        if self.get_func:
            self.get_func()
        return self.template_path

    def post(self):
        if self.post_func:
            self.post_func()
        return self.template_path

    def set_get(self, func):
        self.get_func = func

    def set_post(self, func):
        self.post_func = func

    def parse_slug(self, path) -> SlugData:
        names = self._get_slug_names(path)
        count = len(names)-1
        params = {}
        for name in names:
            for n in re.finditer(name, path):
                params[f"[{name}]"] = [n.start()-1, n.end()+1]
        return SlugData(count, params)

    def _get_slug_names(self, path):
        names = []
        if path.find('[') != -1 and path.find(']') != -1:
            end = path.find(']')+1
            name = path[path.find('[')+1:path.find(']'):]
            names.append(name)
            p = path[end::]
            if p.find('[') != -1:
                for i in self._get_slug_names(p):
                    names.append(i)
        return names


class UserRoute(Route):
    def __init__(self, path, template_path, parent_route=None):
        self.parent_route = parent_route
        p = self._modify_path(path)
        self.slug_data = self.parse_slug(p)
        super().__init__(p, template_path)

    def _modify_path(self, path) -> str:
        if self.parent_route:
            return self.parent_route().path.strip('/') + '/' + path.strip('/')
        else:
            return path
