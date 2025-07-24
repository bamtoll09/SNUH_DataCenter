from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form

router = APIRouter(prefix="/admin")

# -------- Imports --------
import os
import aiofiles
from datetime import datetime

from utils.structure import CohortDetail, CohortInfoTemp, CohortDetailTemp, TableInfoTemp, SchemaInfoTemp, IRBDRBTemp, FileGroupTemp


# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition,
    CertOath, ChrtInfo, ChrtCert,
    SchmInfo, SchmConnectInfo,
)
from utils.auth import verify_token

from sqlmodel import Session, select, update


# -------- Tool Imports --------
from utils.tools import findout_id, findout_name, mapping_id_name


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- Routes --------
@router.get("/")
async def get_all_cohorts(
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session =  Depends(get_dc_session),
    user = Depends(verify_token)) -> list[dict]:

    stmt = select(ChrtInfo)
    chrt_infos = session_dc.exec(stmt).all()

    ids = list(set([ci.id for ci in chrt_infos]))

    id_name_mapping = mapping_id_name(session_atlas, ids)

    import random

    results = []
    for ci in chrt_infos:
        results.append(
            CohortInfoTemp(ci.id, ci.name, ci.description, random.randint(0, 203040),
                             id_name_mapping[ci.owner], ci.created_at, ci.modified_at, "ATLAS").json())

    return results