from flexypy.exceptions.web.baseexseptions import BaseWebException


class PathNotFound(BaseWebException):
    def __init__(self, not_found_path, paths: list[str]):
        self.paths = paths
        self.not_found_path = not_found_path
        super().__init__('404 Not found', self.get_html_text())

    def get_html_text(self):
        p = ''
        for path in self.paths:
            p += f"<p>{path}</p>"
        text = f"""
            <h1>Path "{self.not_found_path}" not found</h1>
            <h2>Accept paths:</h2>
            {p}        
        """
        return text
