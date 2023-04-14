from cgi import FieldStorage
from abc import abstractmethod


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
    path = ''
    POST = PostFormData
    GET = GetFormData
