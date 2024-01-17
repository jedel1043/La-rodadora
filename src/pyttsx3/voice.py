from typing import List


class Voice(object):
    def __init__(
        self,
        id: str,
        name: str = "unknown",
        languages: List[str] = [],
        gender: str = "unknown",
        age: str = "unknown",
    ):
        self.id = id
        self.name: str = name
        self.languages: List[str] = languages
        self.gender: str = gender
        self.age: str = age

    def __str__(self):
        return (
            """<Voice id=%(id)s
          name=%(name)s
          languages=%(languages)s
          gender=%(gender)s
          age=%(age)s>"""
            % self.__dict__
        )
