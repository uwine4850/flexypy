from .baseexceptions import FlexypyBaseException


class StaticFileNotFound(FlexypyBaseException):
    def __init__(self, func_name, static_file_name):
        super().__init__(func_name=func_name, text=f'Static file "{static_file_name}" not found.')