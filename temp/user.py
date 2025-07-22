from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form

router = APIRouter(prefix="/user", tags=["temp/user"])

# -------- Imports --------
import os
import aiofiles
from datetime import datetime

from utils.structure import CohortDetail


# -------- Importing Routers --------
from temp.userapi import user_cohort, user_schema

router.include_router(user_cohort.router)
router.include_router(user_schema.router)


# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition, SecUser,
    CertOath, SchmInfo, SchmCert
)
from utils.auth import verify_token

from sqlmodel import Session, select, update


# -------- Tool Imports --------
from utils.tools import findout_id, findout_name


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- Routes --------
@router.get("/")
async def get_user(
    session: Session = Depends(get_atlas_session),
    user = Depends(verify_token)) -> SecUser:
    logger.debug(f"User: {user}")
    data = user["sub"]

    if data is None:
        logger.error("User data not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    else:
        stmt = select(SecUser).where(SecUser.name == data)
        user_data = session.exec(stmt).first()
        if user_data is None:
            logger.error("User not found in database")
            raise HTTPException(status_code=404, detail="User not found in database")
        return user_data

@router.get("/all")
async def get_user(
    session: Session = Depends(get_atlas_session)) -> list[SecUser]:
    stmt = select(SecUser)

    data = session.exec(stmt).all()
    logger.debug(f"User data: {data}")
    return data

@router.get("/verify")
async def verify_user(
    user = Depends(verify_token)) -> bool:

    return True