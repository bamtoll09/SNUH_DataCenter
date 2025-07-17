from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/list", tags=["list"])

@router.get("/", response_class=HTMLResponse)
async def patients_home(request: Request):
    return templates.TemplateResponse("chrt_list.html", {"request": request})

@router.get("/{cohort_id}", response_class=HTMLResponse)
async def get_cohort(request: Request):
    return templates.TemplateResponse("chrt_detail2.html", {"request": request})