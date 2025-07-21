from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
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
import jwt, json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from utils.auth import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


# -------- Database Connection Setup --------
from utils.dbm import Security, SecUser, get_atlas_session
from sqlmodel import Session, select


# -------- Tools Setup --------
from utils.tools import findout_role


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

@app.post("/login", response_class=JSONResponse)
async def send_login_post(
    id: str,
    pw: str,
    session_atlas: Session = Depends(get_atlas_session)) -> JSONResponse:

    logger.debug(f"Attempting login with id={id} and pw")
    logger.debug(f"pw is {pw}")

    stmt = select(Security).where(
        Security.email == id)
    output = session_atlas.exec(stmt).first()

    content = dict()

    # login fail
    if output is None or pwd_context.verify(pw, output.password) is False:
        logger.warning(f"Login failed for id={id}")
        
        return JSONResponse(content=json.dumps(content), status_code=401)
    
    # login success
    else:
        logger.info(f"Login successful for id={id}")

        payload = {"sub": id, "aud": "normal_user",
                   "iat": datetime.now(timezone.utc),
                   "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
        
        access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        stmt = select(SecUser).where(SecUser.id == id)
        user = session_atlas.exec(stmt).first()

        isAdmin = False if findout_role(session_atlas, user["sub"]) else True

        content = {"id": user.login, "name": user.name, "token": access_token, "isAdmin": isAdmin}
        
        headers = {"Authorization": f"Bearer {access_token}",
                   "X-Access-Token": access_token}

        return JSONResponse(content=json.dumps(content), headers=headers)