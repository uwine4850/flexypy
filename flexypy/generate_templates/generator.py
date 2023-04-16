from flexypy.generate_templates.templates.config import dirs, apps
from flexypy.generate_templates.templates import main
import os


files = [
    {'dir': 'config', 'name': 'dirs.py', 'path': dirs.__file__},
    {'dir': 'config', 'name': 'apps.py', 'path': apps.__file__},
    {'dir': '', 'name': 'main.py', 'path': main.__file__},
]


def generate(generate_dir):

    if generate_dir == '.':
        gd = os.getcwd()
    elif generate_dir == '':
        raise 'ERR'
    else:
        gd = generate_dir

    for file in files:
        dir_path = os.path.join(gd, file['dir'])
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        if os.path.exists(dir_path):
            if not os.path.exists(os.path.join(dir_path, file['name'])) and file['name']:
                with open(os.path.join(dir_path, file['name']), 'w+') as wf:
                    with open(file['path'], 'r') as rf:
                        wf.write(rf.read())


if __name__ == '__main__':
    generate('/home/uwine/Documents/python/flexypy/')
