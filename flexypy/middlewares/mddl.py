
class Middleware:
    def __init__(self, request, app):
        self.request = request
        self.app = app
        self.redirect_from = ''
        self.redirect_to = ''
        self.template_kwargs = {}

    def start(self):
        pass

    def redirect(self, from_path, to_path):
        self.redirect_from = from_path
        self.redirect_to = to_path

    def set_template_kwargs(self, **kwargs):
        self.template_kwargs = kwargs
