from cgi import FieldStorage
from abc import abstractmethod
from http import cookies
from flexypy.http.cookie import Cookie
import datetime


class FormData:
    @abstractmethod
    def get(cls, key) -> list:
        pass

    @abstractmethod
    def keys(cls) -> list:
        pass

    @abstractmethod
    def get_data(cls) -> FieldStorage:
        pass


class PostFormData(FormData):
    _form_data: FieldStorage

    @classmethod
    def get(cls, key) -> list:
        return cls._form_data.getlist(key)

    @classmethod
    def keys(cls) -> list:
        return cls._form_data.keys()

    @classmethod
    def get_data(cls) -> FieldStorage:
        return cls._form_data

    @classmethod
    def set_data(cls, form_data: FieldStorage):
        cls._form_data = form_data


class GetFormData(FormData):
    _form_data: dict

    @classmethod
    def get(cls, key):
        return cls._form_data.get(key)

    @classmethod
    def keys(cls) -> list:
        return list(cls._form_data.keys())

    @classmethod
    def get_data(cls) -> dict:
        return cls._form_data

    @classmethod
    def set_data(cls, form_data: dict):
        cls._form_data = form_data


class Request:
    _set_cookie: cookies.SimpleCookie = {}
    _server_cookie: cookies.SimpleCookie = None
    path = ''
    POST = PostFormData
    GET = GetFormData

    @classmethod
    def get_user_set_cookie(cls):
        return cls._set_cookie

    @classmethod
    def clear_request_cookie(cls):
        cls._set_cookie = {}

    @classmethod
    def set_cookie(cls, name, value, expires=None, max_age=None):
        c = cookies.SimpleCookie()
        c[name] = Cookie.encrypt_cookie(value).decode()
        c[name]['expires'] = (datetime.datetime.now() + datetime.timedelta(days=365)). \
            strftime('%a, %d-%b-%Y %H:%M:%S GMT')
        c[name]['secure'] = True
        c[name]['path'] = '/'
        if max_age is not None:
            c[name]['max-age'] = max_age
        if expires:
            c[name]['expires'] = expires
        cls._set_cookie.update(c)

    @classmethod
    def set_server_cookie(cls, cookie):
        c = cookies.SimpleCookie()
        if cookie:
            c.load(cookie)
        cls._server_cookie = c

    @classmethod
    def get_server_cookie(cls, name):
        try:
            return Cookie.decrypt_cookie(cls._server_cookie.get(name).value.encode())
        except:
            return None

    @classmethod
    def delete_cookie(cls, name):
        cls.set_cookie(name, '', expires='Thu, 01, Jan 1970 00:00:00 GMT', max_age=0)
