from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# -------- Importing Pydantic Models --------
from utils.forms import LoginForm


# -------- Importing API Routers --------
from utils import api, documents


# -------- Importing Rendering Routes --------
from utils import render


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- Authentication Setup --------
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from utils.auth import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


# -------- Database Connection Setup --------
from utils.dbm import PathwayAnalysisEvents, Security, get_atlas_session
from sqlmodel import Session, select


## ------- FastAPI Application Setup --------
app = FastAPI()

origins = [
    "http://localhost",
    "https://localhost",
    "http://localhost:8000",
    "https://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(api.router)

# For protected documents
app.include_router(documents.router)
app.include_router(render.router)

templates = Jinja2Templates(directory="templates")


# -------- Routes --------
@app.get("/", response_class=HTMLResponse)
async def render_base() -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": {}})

@app.post("/login", response_class=HTMLResponse)
async def send_login_post(
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