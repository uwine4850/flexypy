import fire
from flexypy.generate_templates.generator import generate


class Command:
    @staticmethod
    def initproject(dir_path):
        generate(dir_path)


def init_commands():
    fire.Fire(Command())
