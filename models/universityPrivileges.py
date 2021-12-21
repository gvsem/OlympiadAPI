import json
from pydantic import BaseModel

class Privilege(BaseModel):
    olympiads: list = []
    grades: list[int] = []
    levels: list[int] = []
    profile: str = ''
    subjects: list = []
    ege_subject: str = ''
    diplomas: list[int] = []
    bvi: bool = False

    @staticmethod
    def load(data):
        return Privilege(**data)

class Programme(BaseModel):
    code: str = ''
    name: str = ''
    speciality: str = ''
    privileges: list[Privilege] = []

    @staticmethod
    def load(data):
        return Programme(**data)

class Faculty(BaseModel):
    name: str = ''
    programmes: list[Programme] = []

    @staticmethod
    def load(data):
        return Faculty(**data)


class University(BaseModel):
    name: str = ''
    faculties: list[Faculty] = []

    @staticmethod
    def load(data):
        return University(**data)

