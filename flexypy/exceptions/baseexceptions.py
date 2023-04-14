class FlexypyBaseException(Exception):
    def __init__(self, func_name: str, text: str):
        self.text = text
        self.func_name = func_name

    def __str__(self):
        return f'{self.func_name}: {self.text}'
