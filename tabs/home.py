from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/home")


# -------- Routes --------
@router.get("/", response_class=HTMLResponse)
async def patients_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})