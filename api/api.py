from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel

# for testing purposes
from fastapi.responses import Response

router = APIRouter(prefix="/api")


# -------- Imports --------
from datetime import datetime
# import numpy as np

from utils.structure import SchemaSummary, SchemaDetail, OathFile


# -------- Router Imports --------
from api import user, cohort, admin

router.include_router(user.router)
router.include_router(cohort.router)
router.include_router(admin.router)


# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition, SecUser, SecUserRole,
    CertOath, ChrtInfo, ChrtCert
)
from utils.auth import verify_token

from sqlmodel import Session, select, or_, col


# -------- Tool Imports --------
from utils.tools import compare_dates, findout_id, findout_name, findout_role


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- Routes --------
@router.get("/")
def api_list():
    data = {
        "message": "Welcome to the API",
        "endpoints": [
            {"path": "/api/patients", "method": "GET", "description": "List all patients"},
            {"path": "/api/patients/{patient_id}", "method": "GET", "description": "Get patient details by ID"},
            {"path": "/api/patients", "method": "POST", "description": "Create a new patient"},
            {"path": "/api/patients/{patient_id}", "method": "PUT", "description": "Update patient details by ID"},
            {"path": "/api/patients/{patient_id}", "method": "DELETE", "description": "Delete patient by ID"},
        ]
    }
    return data

@router.get("/verify")
async def verify_user(
    user = Depends(verify_token)) -> bool:

    return True
    

# 나중에 검색기능 만들자
@router.get("/schema/search")
async def search_schema(
    params: str = "",
    condition: str = "schema",
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)):

    params = params.strip()

    logger.debug(f"Search params: {params}, condition: {condition}")
    
    items = params.split()

    # parameter search is optional, if not provided, return all cohorts
    if len(items) == 0:
        return session_dc.exec(select(ChrtInfo)).all()

    if condition == "schema":
        db_conditions = [
            ChrtInfo.name.ilike(f"%{kw}%")   # 대소문자 무시: ilike
            for kw in items
        ]

        logger.debug(f"{db_conditions}")
        stmt = select(ChrtInfo).where(or_(*db_conditions))

    elif condition == "user":
        db_conditions = [
            SecUser.name.ilike(f"%{kw}%")   # 대소문자 무시: ilike
            for kw in items
        ]

        stmt = select(SecUser).where(or_(*db_conditions))
        users = session_atlas.exec(stmt).all()

        user_id_list = [user.id for user in users]

        stmt = select(ChrtInfo).where(ChrtInfo.owner.in_(user_id_list))

    result = session_dc.exec(stmt).all()

    logger.debug(f"Search result: {result}")

    return result