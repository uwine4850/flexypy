class BaseWebException:
    def __init__(self, code: str, html: str | bytes):
        self.code = code
        self.html = html
