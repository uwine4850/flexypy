import jinja2
from config.dirs import TEMPLATES_PATH, EXTENSIONS_PATH, GLOBAL_TEMPLATE_OBJECTS_PATH, GLOBAL_TEMPLATE_FUNCTIONS_PATH
import os
from typing import Callable, Type
from flexypy.http.template.extensions.base_extension import BaseExtension
import importlib
from flexypy.exceptions.render import TemplateNotFound


class RenderTemplate:
    def __init__(self, template_path):
        self.template_path = template_path
        self._template_source: str = ''
        self._methods = []

    def set_template_methods(self, functions: list[Callable]):
        for fun in functions:
            self._methods.append(fun)
        return self

    def render(self, **kwargs) -> str:
        try:
            for templ in TEMPLATES_PATH:
                filepath = os.path.join(templ, self.template_path)
                if os.path.exists(filepath):
                    return _JinjaInit(filepath).template_methods(self._methods).jinit(**kwargs)
            raise TemplateNotFound('render', self.template_path)
        except Exception as e:
            raise e


class _JinjaInit:
    def __init__(self, filepath: str):
        self._path = filepath.split('templates')[-1]
        self._env = jinja2.Environment(loader=self._get_loader(), extensions=self._get_extensons())
        self._template = self._env.get_template(self._path)
        self._template_obj = []

    def template_methods(self, methods: list[callable]):
        """
        Adding Python methods to all templates.
        """
        for meth in methods:
            methname = meth.__name__
            self._env.globals[methname] = meth
        return self

    def _get_loader(self) -> jinja2.ChoiceLoader:
        """
        Creates loaders for html templates.
        """
        try:
            fsl = []
            for template in TEMPLATES_PATH:
                fsl.append(jinja2.FileSystemLoader(template))
            loader = jinja2.ChoiceLoader(fsl)
            return loader
        except Exception as e:
            raise e

    def _get_extensons(self) -> list[Type[BaseExtension]]:
        """
        Collects all template extensions (Classes) inherited from BaseExtension.
        """

        # dafault extensions path
        EXTENSIONS_PATH.append('flexypy/http/template/extensions/')

        for path in EXTENSIONS_PATH:
            p = path.replace('/', '.')
            importlib.import_module(f'{p}template_ext')
        return BaseExtension.__subclasses__()

    def jinit(self, **kwargs):
        objects = kwargs

        # set global methods
        global_objects = (os.path.join(GLOBAL_TEMPLATE_OBJECTS_PATH, 'global_objects'))
        if os.path.exists(global_objects+'.py'):
            global_t_obj = __import__(global_objects.replace('/', '.'), fromlist=['objects'])
            objects = getattr(global_t_obj, 'objects')
            objects.update(kwargs)

        # set global functions
        global_functions = os.path.join(GLOBAL_TEMPLATE_FUNCTIONS_PATH, 'global_functions')
        if os.path.exists(global_functions+'.py'):
            global_t_obj = __import__(global_functions.replace('/', '.'), fromlist=['objects'])
            self.template_methods(getattr(global_t_obj, 'objects'))

        for obj in self._template_obj:
            kwargs[obj] = self._template_obj[obj]
        render = self._template.render(objects)
        return render
