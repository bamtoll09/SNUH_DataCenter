from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form

router = APIRouter(prefix="/admin", tags=["api/admin"])

# -------- Imports --------
import os
import aiofiles
from datetime import datetime

from utils.structure import CohortDetail, CohortInfoTemp, CohortCertTemp, CohortDetailTemp, TableInfoTemp, SchemaInfoTemp, IRBDRBTemp, FileGroupTemp, AdminCohortDetailTemp


# -------- Importing Pydantic Models --------
from utils.forms import ReviewBody


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
from utils.tools import findout_id, findout_name, findout_role, mapping_id_name


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- Routes --------
@router.get("/")
async def get_all_cohorts(
    session_atlas: Session = Depends(get_atlas_session),
    user = Depends(verify_token)):

    user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

    if user_role == "public":
        raise HTTPException(status_code=402, detail="User is not an admin")

    return "Allowed"

@router.get("/applies")
async def get_all_applies(
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session =  Depends(get_dc_session),
    user = Depends(verify_token)) -> list[dict]:

    user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

    if user_role == "public":
        raise HTTPException(status_code=402, detail="User is not an admin")

    stmt = select(ChrtCert).where(ChrtCert.cur_status == "applied")
    chrt_certs = session_dc.exec(stmt).all()

    applied_ids = [cc.id for cc in chrt_certs]

    stmt = select(ChrtInfo).where(ChrtInfo.id.in_(applied_ids))
    chrt_infos = session_dc.exec(stmt).all()

    ids = [ci.owner for ci in chrt_infos]

    id_name_mapping = mapping_id_name(session_atlas, ids)

    import random

    results = []

    for ci in chrt_infos:
        for cr in chrt_certs:
            if ci.id == cr.id:
                cohort_info_temp = CohortInfoTemp(ci.id, ci.name, ci.description, random.randint(0, 203040),
                                                id_name_mapping[ci.owner], ci.created_at, ci.modified_at, ci.origin)
                cohort_cert_temp = CohortCertTemp(cr.applied_at, cr.resolved_at, cr.cur_status, cr.review)
                table_info_temp = TableInfoTemp([random.randint(0,203040) for r in range(46)], [True if random.randint(0,1) == 1 else False for r in range(46)])

                stmt = select(CertOath).where(CertOath.document_for == ci.id)
                cert_oaths = session_dc.exec(stmt).all()

                irb_drb_temps = []

                for co in cert_oaths:
                    docs_path = os.path.abspath(__file__ + "/../../documents")

                    irb_drb_temps.append(IRBDRBTemp(co.name, co.path, os.path.getsize(docs_path + co.path)))

                file_group_temp = FileGroupTemp(irb_drb_temps)

                results.append(
                    AdminCohortDetailTemp(
                        cohort_info_temp,
                        cohort_cert_temp,
                        table_info_temp,
                        file_group_temp
                    ).json(table_name_only=True)
                )

    return results

@router.post("/applies/id/{cohort_id}/approve")
async def approve_cohort_by_id(
    cohort_id: int,
    review: ReviewBody | None,
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> dict:

    if cohort_id is None:
        logger.error("Cohort id not found")
        raise HTTPException(status_code=404, detail="Cohort id not found")

    user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

    if user_role == "public":
        raise HTTPException(status_code=402, detail="User is not an admin")
    
    stmt = select(ChrtCert).where(ChrtCert.id == cohort_id)
    chrt_cert = session_dc.exec(stmt).first()

    chrt_cert.cur_status = "approved"
    chrt_cert.resolved_at = datetime.now()
    chrt_cert.review = review.review if review is not None else None
    session_dc.add(chrt_cert)
    session_dc.commit()

    stmt = select(ChrtInfo).where(ChrtInfo.id == cohort_id)
    chrt_info = session_dc.exec(stmt).first()
    
    user_id = chrt_info.owner

    # Get SchmInfo
    stmt = select(SchmInfo).where(SchmInfo.owner == user_id, SchmInfo.schema_from == cohort_id)
    schm_info = session_dc.exec(stmt).first()
    
    # Get SchmConnectInfo
    stmt = select(SchmConnectInfo).where(SchmConnectInfo.id == schm_info.id)
    schm_cinfo = session_dc.exec(stmt).first()

    # Create SchmConnectInfo
    if schm_cinfo is None:
        schm_cinfo = SchmConnectInfo()
        schm_cinfo.id = schm_info.id
        schm_cinfo.host = "127.0.0.1"
        schm_cinfo.port = 5432
        schm_cinfo.username = "postgres_userid"
        schm_cinfo.password = "mypass_randint"
        
        session_dc.add(schm_cinfo)
        session_dc.commit()

    return {"msg": "success"}

@router.post("/applies/id/{cohort_id}/reject")
async def reject_cohort_by_id(
    cohort_id: int,
    review: ReviewBody | None,
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> dict:

    if cohort_id is None:
        logger.error("Cohort id not found")
        raise HTTPException(status_code=404, detail="Cohort id not found")

    user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

    if user_role == "public":
        raise HTTPException(status_code=402, detail="User is not an admin")
    
    stmt = select(ChrtCert).where(ChrtCert.id == cohort_id)
    chrt_cert = session_dc.exec(stmt).first()

    chrt_cert.cur_status = "rejected"
    chrt_cert.resolved_at = datetime.now()
    chrt_cert.review = review.review if review is not None else None
    session_dc.add(chrt_cert)
    session_dc.commit()

    stmt = select(ChrtInfo).where(ChrtInfo.id == cohort_id)
    chrt_info = session_dc.exec(stmt).first()
    
    user_id = chrt_info.owner

    # Get SchmInfo
    stmt = select(SchmInfo).where(SchmInfo.owner == user_id, SchmInfo.schema_from == cohort_id)
    schm_info = session_dc.exec(stmt).first()
    
    # Get SchmConnectInfo
    stmt = select(SchmConnectInfo).where(SchmConnectInfo.id == schm_info.id)
    schm_cinfo = session_dc.exec(stmt).first()

    # Create SchmConnectInfo
    if schm_cinfo is not None:
        session_dc.delete(schm_cinfo)
        session_dc.commit()

    return {"msg": "success"}