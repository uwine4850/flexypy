from .baseexceptions import FlexypyBaseException


class TemplateNotFound(FlexypyBaseException):
    def __init__(self, func_name, template_path):
        super().__init__(func_name=func_name, text=f'Template {template_path} not found.')
