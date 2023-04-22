from cryptography.fernet import Fernet
from config.apps import FERNET_KEY


class Cookie:
    def __init__(self, request):
        self.request = request

    def set_server_cookie(self, header):
        """
        Set the cookies that the user writes to the request.
        After the data is written to the header the field in the request is cleared.
        """
        if self.request.get_user_set_cookie():
            header.extend(("set-cookie", morsel.OutputString())
                          for morsel in self.request.get_user_set_cookie().values())
            # clear request cookies
            self.request.clear_request_cookie()
            return header

    @classmethod
    def encrypt_cookie(cls, value: str):
        key = FERNET_KEY
        fernet = Fernet(key)
        return fernet.encrypt(value.encode())

    @classmethod
    def decrypt_cookie(cls, value: bytes):
        key = FERNET_KEY
        fernet = Fernet(key)
        return fernet.decrypt(value).decode()
