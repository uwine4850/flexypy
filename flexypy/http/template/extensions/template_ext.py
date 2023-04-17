from flexypy.http.template.extensions.base_extension import BaseExtension
from config.dirs import STATICFILES_PATH
import os
from flexypy.exceptions.extension import StaticFileNotFound


class StaticExt(BaseExtension):
    """
    Extensions for outputting files to html template.
    """
    tags = ['static']

    def handler(self, filepath: str):
        for path in STATICFILES_PATH:
            p = os.path.join(path, filepath)
            if os.path.exists(p):
                return p
        raise StaticFileNotFound('StaticExt', filepath)
