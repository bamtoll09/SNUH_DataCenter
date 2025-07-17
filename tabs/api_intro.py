from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/api_intro", tags=["api_intro"])

@router.get("/", response_class=HTMLResponse)
async def patients_home(request: Request):
    return templates.TemplateResponse("api_intro.html", {"request": request})