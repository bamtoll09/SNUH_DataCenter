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
from api import user, cohort, schema

router.include_router(user.router)
router.include_router(cohort.router)
router.include_router(schema.router)


# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition, SecUser, SecUserRole,
    CertOath, SchmInfo, SchmCert
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


# -------- User API --------
@router.get("/user")
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

@router.get("/user_all")
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
    

# -------- Account API --------
@router.get("/account/role")
async def get_role(
    session: Session = Depends(get_atlas_session),
    user = Depends(verify_token)) -> str:
    logger.debug(f"User: {user}")
    
    # Get user ID from database
    user_info = session.exec(select(SecUser).where(
        SecUser.name == user["sub"]
    )).first()

    if not user_info:
        logger.error("User not found in database")
        raise HTTPException(status_code=404, detail="User not found")

    return "public" if findout_role(session, user_info.name) else "admin"

# -------- Cohort API --------
# @router.get("/cohort")
# async def get_cohort(
#     session_atlas: Session = Depends(get_atlas_session),
#     session_dc: Session = Depends(get_dc_session),
#     user = Depends(verify_token)) -> list[dict]:

#     user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

#     logger.debug(f"User role is {user_role}")
    
#     if user_role == "admin":
#         stmt = select(SchmInfo)
#         schm = session_dc.exec(stmt).all()

#         stmt = select(SchmCert)
#         schm_cert = session_dc.exec(stmt).all()

#         schm_status = {e.id: e.cur_status for e in schm_cert}

#         stmt = select(SecUser)
#         users = session_atlas.exec(stmt).all()

#         user_id_name_mapping = {u.id: u.name for u in users}

#         all_summary = []

#         for s in schm:
#             cohort_summary = SchemaSummary(
#                 id=s.id,
#                 name=s.name,
#                 description=s.description,
#                 status=schm_status[s.id],
#                 owner=user_id_name_mapping[s.owner],
#                 created_at=s.created_at,
#                 last_modified_at=s.last_modified_at
#             )

#             all_summary.append(cohort_summary.json())

#         return all_summary
#     elif user_role == "public":
#         user_id = findout_id(session_atlas, user["sub"])

#         stmt = select(SchmInfo).where(SchmInfo.owner == user_id)
#         user_schm = session_dc.exec(stmt).all()

#         stmt = select(SchmCert).where(SchmCert.id.in_([c.id for c in user_schm]))
#         user_schm_cert = session_dc.exec(stmt).all()

#         user_schm_status = {e.id: e.cur_status for e in user_schm_cert}

#         user_summary = []

#         for s in user_schm:
#             cohort_summary = SchemaSummary(
#                 id=s.id,
#                 name=s.name,
#                 description=s.description,
#                 status=user_schm_status[s.id],
#                 owner=user["sub"],
#                 created_at=s.created_at,
#                 last_modified_at=s.last_modified_at
#             )

#             user_summary.append(cohort_summary.json())

#         return user_summary
#     else:
#         logger.error("User role not found")
#         raise HTTPException(status_code=404, detail="User role not found")
    
# @router.get("/cohort/sync")
# async def sync_cohort(
#     session_atlas: Session = Depends(get_atlas_session),
#     session_dc: Session = Depends(get_dc_session),
#     user = Depends(verify_token)) -> Response:

#     logger.debug("Passed")

#     # Get user ID from database
#     user_info = session_atlas.exec(select(SecUser).where(
#         SecUser.name == user["sub"]
#     )).first()

#     user_id = user_info.id

#     # Get ATLAS cohorts by the user ID
#     atlas_chrts = session_atlas.exec(select(CohortDefinition).where(
#         CohortDefinition.created_by_id == user_id,
#     )).all()

#     # Get DataCenter cohorts by the user ID
#     dc_chrts = session_dc.exec(select(SchmInfo).where(
#         SchmInfo.owner == user_id
#     )).all()

#     # Check difference in length to find out there are new cohorts
#     logger.debug(f"Length Difference: {len(atlas_chrts)- len(dc_chrts)}")
    
#     atlas_chrts_ids = [c.id for c in atlas_chrts]

#     need_to_add = [c for c in atlas_chrts if c.id not in [d.ext_id for d in dc_chrts]]

#     logger.debug(f"Need to add: {len(need_to_add)} cohorts")

#     if len(need_to_add) > 0:
#         schm_info_list = [SchmInfo(ext_id=c.id, name=c.name, description=c.description, owner=user_id, tables=None, origin="ATLAS", created_at=c.created_date, last_modified_at=c.modified_date) for c in need_to_add]

#         session_dc.add_all(schm_info_list)
#         session_dc.commit()

#         # Add to schm_cert too
#         ext_ids = [c.id for c in need_to_add]

#         logger.debug(f"Externel ids {ext_ids}")

#         stmt = select(SchmInfo).where(SchmInfo.ext_id.in_(ext_ids))

#         new_schm_infos = session_dc.exec(stmt).all()

#         logger.debug(f"New schm_infos {new_schm_infos}")
        
#         schm_cert_list = [SchmCert(id=d.id) for d in new_schm_infos]

#         session_dc.add_all(schm_cert_list)
#         session_dc.commit()

#         # For now, just return a success message
#         return "Adding Cohorts to DataCenter is Completed"
    
#     # Check modified time of cohorts
#     need_to_update = [{"ext_id": c.id, "name": c.name, "description": c.description, "tables": None, "last_modified_at": c.modified_date} for c in atlas_chrts if compare_dates([d for d in dc_chrts if c.id == d.ext_id][0].last_modified_at, c.modified_date)]

#     if len(need_to_update) > 0:
#         for update in need_to_update:
#             stmt = select(SchmInfo).where(SchmInfo.ext_id == update["ext_id"], SchmInfo.owner == user_id)
#             schm_info = session_dc.exec(stmt).first()
#             if schm_info:
#                 schm_info.last_modified_at = update["last_modified_at"]
#                 schm_info.tables = update["tables"]
#                 session_dc.add(schm_info)
        
#         session_dc.commit()
#         logger.debug(f"Updated {len(need_to_update)} cohorts in DataCenter")

#         return "Cohorts in DataCenter are updated successfully"

#     return f"No new cohorts to add to DataCenter"

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
        return session_dc.exec(select(SchmInfo)).all()

    if condition == "schema":
        db_conditions = [
            SchmInfo.name.ilike(f"%{kw}%")   # 대소문자 무시: ilike
            for kw in items
        ]

        logger.debug(f"{db_conditions}")
        stmt = select(SchmInfo).where(or_(*db_conditions))

    elif condition == "user":
        db_conditions = [
            SecUser.name.ilike(f"%{kw}%")   # 대소문자 무시: ilike
            for kw in items
        ]

        stmt = select(SecUser).where(or_(*db_conditions))
        users = session_atlas.exec(stmt).all()

        user_id_list = [user.id for user in users]

        stmt = select(SchmInfo).where(SchmInfo.owner.in_(user_id_list))

    result = session_dc.exec(stmt).all()

    logger.debug(f"Search result: {result}")

    return result

# async def get_user(
#     session: Session = Depends(get_session),
#     user = Depends(verify_token)) -> list[SecUser]:
#     stmt = select(SecUser).where(
#         SecUser.id == user["sub"])
#     return session.exec(stmt).all()

# def convert_date(date_str: str) -> datetime:
#     return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")


# -------- Admin API --------
@router.get("/admin/applies")
async def get_applies(
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> list[SchmInfo]:

    user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

    if user_role != "admin":
        logger.error("User is not an admin")
        raise HTTPException(status_code=403, detail="User is not an admin")
    
    stmt = select(SchmInfo)
    schm_infos = session_dc.exec(stmt).all()

    return schm_infos

@router.get("/admin/applies/id/{schema_id}")
async def get_applied_schema_by_id(
    schema_id: int | None,
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)):
    # 코호트 제목, 설명, 소유자, 생성일자, 최종 수정일자, 신청날짜, 승인날짜, 승인상태
    # 테이블 목록, IRB/DRB 파일정보, 승인여부
    # 검토의견

    # ATLAS DB에서 가져올 것
    # 코호트 제목, 설명, 생성일자
    
    # DC DB에서 가져올 것
    # 최종 수정일자, 신청날짜, 승인날짜, 테이블 목록, 승인여부, IRB/DRB 파일정보, 검토의견, 승인상태

    # user_id = findout_id(session_atlas, user["sub"])

    if schema_id is None:
        logger.error("Schema id not found")
        raise HTTPException(status_code=404, detail="Schema id not found")
    
    stmt = select(SchmInfo).where(SchmInfo.id == schema_id)
    schm_info = session_dc.exec(stmt).first()

    if schm_info is None:
        logger.error("Schema info not found")
        raise HTTPException(status_code=404, detail="Schema info not found")
    
    
    stmt = select(SchmCert).where(SchmCert.id == schema_id)
    schm_cert = session_dc.exec(stmt).first()

    if schm_cert is None:
        logger.error("Schema cert not found on DataCenter")
        raise HTTPException(status_code=404, detail="Schema cert not found on DataCenter")
    
    stmt = select(CertOath).where(CertOath.document_for == schema_id)
    cert_oaths = session_dc.exec(stmt).all()

    cert_oath_list = []

    if cert_oaths is not None:
        cert_oath_list = [OathFile(name=c.name, path=c.path) for c in cert_oaths]

    owner_name = findout_name(session_atlas, schm_info.owner)
    
    cohort_detail = SchemaDetail(
        id=schema_id, name=schm_info.name, description=schm_info.description, status=schm_cert.cur_status,
        owner=owner_name, created_at=schm_info.created_at, last_modified_at=schm_info.last_modified_at,
        applied_at=schm_cert.applied_at, resolved_at=schm_cert.resolved_at, tables=schm_info.tables,
        files=cert_oath_list, review=schm_cert.review
    )

    return cohort_detail.json()


class CohortReview(BaseModel):
    review: str = ""

@router.post("/admin/applies/id/{cohort_id}/approve")
async def approve_cohort(
    cohort_id: int,
    cohort_review: CohortReview,
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)):

    user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

    if user_role != "admin":
        logger.error("User is not an admin")
        raise HTTPException(status_code=403, detail="User is not an admin")
    
    stmt = select(SchmCert).where(SchmCert.id == cohort_id)
    schm_cert = session_dc.exec(stmt).first()

    schm_cert.cur_status = "approved"
    schm_cert.resolved_at = datetime.now()
    schm_cert.review = cohort_review.review

    session_dc.add(schm_cert)
    session_dc.commit()

    return "Cohort approved"
    

@router.post("/admin/applies/id/{cohort_id}/reject")
async def approve_cohort(
    cohort_id: int,
    cohort_review: CohortReview,
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)):

    user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

    if user_role != "admin":
        logger.error("User is not an admin")
        raise HTTPException(status_code=403, detail="User is not an admin")
    
    stmt = select(SchmCert).where(SchmCert.id == cohort_id)
    schm_cert = session_dc.exec(stmt).first()
    
    schm_cert.cur_status = "rejected"
    schm_cert.resolved_at = datetime.now()
    schm_cert.review = cohort_review.review

    session_dc.add(schm_cert)
    session_dc.commit()

    return "Cohort rejected"