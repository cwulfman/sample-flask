from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.templating import _TemplateResponse
from schemas import TranslationForm
from SPARQLWrapper import SPARQLWrapper, SPARQLWrapper2, JSON
from rdflib import URIRef, Literal
import urllib.parse
from typing import List, Optional
from pydantic import BaseModel
import rdflib
from kb import Kb, QueryResult
from forms import TranslationForm
from starlette_wtf import StarletteForm


current_file = Path(__file__)
current_file_dir = current_file.parent
# project_root = current_file_dir.parent
project_root = current_file_dir
project_root_absolute = project_root.resolve()
static_root_absolute = project_root_absolute / "static"  # or wherever the static folder actually is
template_root_absolute = project_root_absolute / "templates"  # or wherever the static folder actually is

endpoint = "http://147.182.188.37:7200/repositories/spatrem"

kb = Kb(endpoint)

app: FastAPI = FastAPI()
app.mount("/static",  StaticFiles(directory=str(static_root_absolute)), name="static")
templates: Jinja2Templates = Jinja2Templates(directory=template_root_absolute)

@app.get("/", response_class=HTMLResponse)
def start(request: Request) -> _TemplateResponse:
    return templates.TemplateResponse("index.html", {"request": request})



@app.get("/languages", response_class=HTMLResponse)
async def get_languages(request: Request):
    result: QueryResult = kb.languages()
    return templates.TemplateResponse("languages.html",
                                      { "request": request,
                                        "languages": result.data,
                                        "count": result.count })
    


@app.post("/translations", response_class=HTMLResponse)
async def post_translations(request: Request,
                           page: int = 1,
                           page_size: int = 10,
                           sl: Optional[str] = None,
                           tl: Optional[str] = None,
                           genre: Optional[str] = None,
                           after_date: Optional[int] = None,
                           before_date: Optional[int] = None,
                           magazine: Optional[str] = None):

    # form_data = await request._get_form()
    form_data = await request.form()
    filters = { "sl": form_data.get('sl'),
                "tl": form_data.get('tl'),
                "genre": form_data.get('genre'),
                "after_date": form_data.get('after_date'),
                "before_date":form_data.get('before_date'),
                "magazine": form_data.get('magazine'),
               }
    result: QueryResult = kb.translations(page, page_size, filters)
    form_data = {
        "lang_choices" : [(item['lang'], item['label']) for item in kb.languages().data],
        "magazine_choices": [(item['magazine'], item['label']) for item in kb.magazines().data],
        "date_choices": [(item['date'], item['date']) for item in kb.dates().data],
        "genre_choices" : [(item['genre'], item['genre']) for item in kb.genres().data]
        }

    for _,v in form_data.items():
        v.insert(0, ('any', 'any'))

    form: TranslationForm = await TranslationForm.from_formdata(request)



    form.genre.choices = form_data['genre_choices']
    form.genre.data = filters['genre']

    form.sl.choices = form_data['lang_choices']
    form.sl.data = filters['sl']

    form.tl.choices = form_data['lang_choices']
    form.tl.data = filters['tl']

    form .magazine.choices = form_data['magazine_choices']
    form.magazine.data = filters['magazine']

    form.after_date.choices = form_data['date_choices']
    form.after_date.data = filters['after_date']

    form.before_date.choices = form_data['date_choices']
    form.before_date.data = filters['before_date']

    current_page = page
    prev_page = page - 1
    if prev_page < 0:
        prev_page = None

    if result.count < page_size:
        next_page = None
    else:
        next_page = page + 1
    return templates.TemplateResponse("translations.html",
                                      { "request": request,
                                        "form": form,
                                        "current_page": current_page,
                                        "next_page": next_page,
                                        "prev_page": prev_page,
                                        "page_size": page_size,
                                        "translations" : result.data })





@app.get("/translations", response_class=HTMLResponse)
async def get_translations(request: Request,
                           page: int = 1,
                           page_size: int = 10,
                           sl: Optional[str] = None,
                           tl: Optional[str] = None,
                           genre: Optional[str] = None,
                           after_date: Optional[int] = None,
                           before_date: Optional[int] = None,
                           magazine: Optional[str] = None):

    filters = { "sl": sl,
                "tl": tl,
                "genre": genre,
                "after_date": after_date,
                "before_date": before_date,
                "magazine": magazine,
               }

    result: QueryResult = kb.translations(page, page_size, filters)

    form_data = {
        "lang_choices" : [(item['lang'], item['label']) for item in kb.languages().data],
        "magazine_choices": [(item['magazine'], item['label']) for item in kb.magazines().data],
        "date_choices": [(item['date'], item['date']) for item in kb.dates().data],
        "genre_choices" : [(item['genre'], item['genre']) for item in kb.genres().data]
        }

    for _,v in form_data.items():
        v.insert(0, ('any', 'any'))

    print("in get_translations")
    form = TranslationForm(request)
    # form = await TranslationForm.from_formdata(request)
    form.genre.choices = form_data['genre_choices']
    form.sl.choices = form_data['lang_choices']
    form.tl.choices = form_data['lang_choices']
    form .magazine.choices = form_data['magazine_choices']
    form.after_date.choices = form_data['date_choices']
    form.before_date.choices = form_data['date_choices']

    current_page = page
    prev_page = page - 1
    if prev_page < 0:
        prev_page = None

    if result.count < page_size:
        next_page = None
    else:
        next_page = page + 1
    data = result.data
    return templates.TemplateResponse("translations.html",
                                      { "request": request,
                                        "form": form,
                                        "current_page": current_page,
                                        "next_page": next_page,
                                        "prev_page": prev_page,
                                        "page_size": page_size,
                                        "translations" : result.data })


@app.get("/translators", response_class=HTMLResponse)
async def get_translators(request: Request):
    result: QueryResult = kb.translators()
    return templates.TemplateResponse("translators.html",
                                      { "request": request,
                                        "translators": result.data })

@app.get("/translators/{id}", response_class=HTMLResponse)
def get_translator(request: Request, id:str):

    result = kb.translator(id)
    return templates.TemplateResponse("translator.html",
                                      { "request": request,
                                        "names": result['names'],
                                        "works": result['works'],
                                        "info": result['info'],
                                       })



@app.get("/magazines", response_class=HTMLResponse)
async def get_magazines(request: Request):
    result: QueryResult = kb.magazines()
    return templates.TemplateResponse("magazines.html",
                                      { "request": request,
                                        "magazines": result.data })

@app.get("/magazines/{key}", response_class=HTMLResponse)
async def get_magazine_by_key(request: Request, key:str):
    result: dict = kb.magazine(key)
    return templates.TemplateResponse("magazine.html",
                                      {
                                          "request": request,
                                          "info": result['info'],
                                          "issues": result['issues']
                                      })

@app.get("/issues/{key}", response_class=HTMLResponse)
async def get_issue_by_key(request: Request, key):
         result = kb.issue(key)
         return templates.TemplateResponse("issue.html", { "request": request,
                                                           "info": result['info'],
                                                           "constituents": result['constituents']})
@app.get("/authors/{key}", response_class=HTMLResponse)
async def get_author_by_key(request: Request, key):
    result = kb.author(key)
    return templates.TemplateResponse("author.html", { "request": request,
                                                           "data" :result.data})


@app.get("/api") 
async def get_api():
    return "<p>this is the api<p>"

@app.get("/api/languages")
async def api_get_languages():
    return kb.languages()

@app.get("/api/pubDates")
async def api_get_pubDates():
    return kb.dates()

@app.get("/api/magazines")
async def api_get_magazines():
    return kb.magazines()

@app.get("/api/magazines/{key}")
async def api_get_magazine(key):
    return kb.magazine(key)

@app.get("/api/issues/{magkey}")
async def api_get_issues(magkey):
    return kb.issues(magkey)

@app.get("/api/constituents/{issuekey}")
async def api_get_constituents(issuekey):
    return kb.constituents(issuekey)

@app.get("/api/constituent/{conkey}")
async def api_get_constituent(conkey):
    return kb.constituent(conkey)

@app.head("/api/translations")
async def api_get_translations_count():
    translations: QueryResult  = kb.translations(page=0, page_size=0)
    content = {"count": translations.count}
    headers = {"X-result-count": str(translations.count), "Content-Language": "en-US"}
    return JSONResponse(content=content, headers=headers)

@app.get("/api/translations")
async def api_get_translations() -> QueryResult:
    return kb.translations(page=0, page_size=20)

@app.get("/api/authors/{key}")
async def api_get_author_by_key(key):
    return kb.author(key)
