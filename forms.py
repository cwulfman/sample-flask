from jinja2 import Template
from wtforms import BooleanField, SelectField, BooleanField
from starlette_wtf import StarletteForm, CSRFProtectMiddleware, csrf_protect
from starlette_wtf import StarletteForm

class TranslationForm(StarletteForm):
    genre = SelectField('Genre', default='any')
    sl = SelectField('Source Language', default='any')
    tl = SelectField('Target Language', default='any')
    magazine = SelectField('Magazine', default='any')
    any_date = BooleanField('any date', default=True)
    after_date = SelectField('After Date', default = 'any')
    before_date = SelectField('Before Date', default = 'any')

