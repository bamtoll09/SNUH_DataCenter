from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


# -------- Importing Tabs --------
from tabs import home, search, admin, chrt_list, api_intro


# -------- Setting Router --------
templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/render", tags=["render"])


# --------- Including Routers --------
router.include_router(home.router)
router.include_router(search.router)
router.include_router(admin.router)
router.include_router(chrt_list.router)
router.include_router(api_intro.router)


# -------- Routes --------
@router.get("/", response_class=HTMLResponse)
async def render_base() -> HTMLResponse:
    return templates.TemplateResponse("base.html", {"request": {}})

@router.get("/login")
async def render_login() -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": {}})