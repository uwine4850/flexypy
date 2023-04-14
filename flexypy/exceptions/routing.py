from .baseexceptions import FlexypyBaseException


class PathParameterAlreadyExists(FlexypyBaseException):
    def __init__(self, func_name, parameter_name):
        super().__init__(func_name=func_name, text=f'Path parameter "{parameter_name}" already exists.')
