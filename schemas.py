from os import setgroups
from pydantic import BaseModel
from fastapi import Form

class TranslationForm(BaseModel):
    magazine: str

    @classmethod
    def as_form(
            cls,
            magazine: str = Form(...),
            ):
        return cls(
            magazine=magazine
            )
