from pathlib import Path
from os import name
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import starlette
from starlette.templating import _TemplateResponse

from pathlib import Path

current_file = Path(__file__)
current_file_dir = current_file.parent
# project_root = current_file_dir.parent
project_root = current_file_dir
project_root_absolute = project_root.resolve()
static_root_absolute = project_root_absolute / "static"  # or wherever the static folder actually is
template_root_absolute = project_root_absolute / "templates"  # or wherever the static folder actually is

app: FastAPI = FastAPI()
app.mount("/static",  StaticFiles(directory=str(static_root_absolute)), name="static")
templates: Jinja2Templates = Jinja2Templates(directory=template_root_absolute)

@app.get("/", response_class=HTMLResponse)
def start(request: Request) -> _TemplateResponse:
    return templates.TemplateResponse("index.html", {"request": request})
