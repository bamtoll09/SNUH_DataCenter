from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/search", tags=["search"])

@router.get("/", response_class=HTMLResponse)
async def patients_home(request: Request):
    # return templates.TemplateResponse("search.html", {"request": request})

    return templates.TemplateResponse("search.html", {"request": request})

@router.get("/{schema_id}", response_class=HTMLResponse)
async def detail(request: Request, schema_id: int):

    schema = {"title": "Cohort Title", "description": "Cohort Description", "status": "approved",
          "created_at": "20xx.xx.xx xx:xx:xx.xxx", "updated_at": "20xx.xx.xx xx:xx:xx.xxx",
          "request_date": "20xx.xx.xx xx:xx:xx.xxx", "approval_date": "20xx.xx.xx xx:xx:xx.xxx"}

    return templates.TemplateResponse("schm_detail.html", {"request": request, "schema": schema})