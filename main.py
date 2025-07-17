from typing import Union

from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# -------- Importing Tabs --------
from tabs import home, search, admin, chrt_list, api_intro


# -------- Importing API Routers --------
from utils import api, documents

# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- Authentication Setup --------
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
import jwt
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from utils.auth import verify_token, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


# -------- Database Connection Setup --------
from utils.dbm import PathwayAnalysisEvents, Security, get_atlas_session
from sqlmodel import Session, select


## ------- FastAPI Application Setup --------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(home.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(chrt_list.router)
app.include_router(api.router)
app.include_router(api_intro.router)

# For protected documents
app.include_router(documents.router)

templates = Jinja2Templates(directory="templates")


# -------- Routes --------
@app.get("/", response_class=HTMLResponse)
async def render_index():
    return templates.TemplateResponse("base.html", {"request": {}})

@app.get("/login")
async def render_login():
    return templates.TemplateResponse("login.html", {"request": {}})

@app.post("/login", response_class=HTMLResponse)
async def login(
    id: str = Form(...),
    pw: str = Form(...),
    session: Session = Depends(get_atlas_session)) -> HTMLResponse:

    logger.debug(f"Attempting login with id={id} and pw")
    logger.debug(f"pw is {pw}")
    stmt = select(Security).where(
        Security.email == id)
    output = session.exec(stmt).first()

    html_content = ("<html><body>"
            f"<h1>Hello, World!</h1>"
            f"</body></html>")

    # login fail
    if output is None or pwd_context.verify(pw, output.password) is False:
        logger.warning(f"Login failed for id={id}")

        html_content = (f"<html><body>"
            f"<h1>Who are you, {id}</h1>"
            f"</body></html>")
        
        return HTMLResponse(content=html_content, status_code=401)
    
    # login success
    else:
        logger.info(f"Login successful for id={id}")

        payload = {"sub": id, "aud": "normal_user",
                   "iat": datetime.now(timezone.utc),
                   "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
        
        access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        html_content = (f"<html><body>"
            f"<h1>Hello, {id}</h1>"
            f"</body></html>")
        
        headers = {"Authorization": f"Bearer {access_token}",
                   "X-Access-Token": access_token}

        return HTMLResponse(content=html_content, headers=headers)

@app.get("/db")
async def read_db(
    session: Session = Depends(get_atlas_session),
    subject_id: int = 1112) -> list[PathwayAnalysisEvents]:
    logger.debug(f"Reading database with subject_id={subject_id}")
    stmt = select(PathwayAnalysisEvents).where(
        PathwayAnalysisEvents.subject_id == subject_id)
    return session.exec(stmt).all()

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}