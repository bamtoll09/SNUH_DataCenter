from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form

router = APIRouter(prefix="/admin", tags=["api/admin"])

# -------- Imports --------
import os
import aiofiles
from datetime import datetime

from utils.structure import CohortDetail, CohortInfoTemp, CohortCertTemp, CohortDetailTemp, TableInfoTemp, SchemaInfoTemp, IRBDRBTemp, FileGroupTemp, AdminCohortDetailTemp, TABLE_NAME


# -------- Importing Pydantic Models --------
from utils.forms import ReviewBody


# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition,
    CertOath, ChrtInfo, ChrtCert,
    SchmInfo, SchmConnectInfo,
    provision_user, copy_tables_by_cohort_id
)
from utils.auth import verify_token

from sqlmodel import Session, select, update, or_
from sqlalchemy import Table, MetaData, Column, String
from sqlalchemy.schema import CreateSchema, DropSchema


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

    stmt = select(ChrtCert).where(ChrtCert.cur_status != "before_apply")
    chrt_certs = session_dc.exec(stmt).all()

    applied_ids = [cc.id for cc in chrt_certs]

    stmt = select(ChrtInfo).where(ChrtInfo.id.in_(applied_ids))
    chrt_infos = session_dc.exec(stmt).all()

    ids = [ci.owner for ci in chrt_infos]

    id_name_mapping = mapping_id_name(session_atlas, ids)

    import random

    results = []

    if chrt_certs is None:
        return results
    
    for ci in chrt_infos:
        for cr in chrt_certs:
            if ci.id == cr.id:
                tables = [False for i in range(46)] if ci.tables is None else [True if table in ci.tables else False for table in list(TABLE_NAME.__members__.keys())]
                cohort_info_temp = CohortInfoTemp(ci.id, ci.name, ci.description, random.randint(0, 203040),
                                                id_name_mapping[ci.owner], ci.created_at, ci.modified_at, ci.origin)
                cohort_cert_temp = CohortCertTemp(cr.applied_at, cr.resolved_at, cr.cur_status, cr.review)
                table_info_temp = TableInfoTemp([random.randint(0,203040) for r in range(46)], tables)

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
        logger.debug(f"Creating schema connect info")

        # Connect Information
        host = "34.64.249.196" # "127.0.0.1"
        port = 5432
        username = "u" + str(user_id)
        password = "1234"

        schm_cinfo = SchmConnectInfo()
        schm_cinfo.id = schm_info.id
        schm_cinfo.host = host
        schm_cinfo.port = port
        schm_cinfo.username = username
        schm_cinfo.password = password
        
        session_dc.add(schm_cinfo)
        session_dc.commit()

        schema_name = f"schema_{user_id}_{schm_info.id}"

        session_dc.exec(CreateSchema(schema_name, True))
        session_dc.commit()

        provision_user(session_dc, username, password, "datacenter", schema_name)

        copy_tables_by_cohort_id(session_atlas, session_dc, schema_name, cohort_id)

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

@router.get("/clean/document")
async def clean_documents(
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)):

    user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

    if user_role == "public":
        raise HTTPException(status_code=402, detail="User is not an admin")
    
    docs_path = os.path.abspath(__file__ + "/../../documents")

    # 1. documents 내 폴더 이름이 db에 cohort_id로 정의되어 있지 않은 경우,
    #    해당 폴더 삭제
    stmt = select(ChrtInfo)
    chrt_infos = session_dc.exec(stmt).all()

    cids = [ci.id for ci in chrt_infos]

    doc_listdir = os.listdir(docs_path)

    if chrt_infos is None:
        logger.debug(f"Cohort info is empty")
        return True
    
    for dir in doc_listdir: 
        if not int(dir) in cids:
            doc_listfile = os.listdir(docs_path + "/" + dir)

            for file in doc_listfile:
                os.remove(f"{docs_path}/{dir}/{file}")
                # logger.debug(f"File is removed: {dir}/{file}")

            os.removedirs(f"{docs_path}/{dir}")
            logger.debug(f"Folder is removed: {dir}")

    # 2. documents 내 {cohort_id} 폴더 안에 cert oath 테이블에 없는 파일이 존재하는 경우,
    #    해당 파일 삭제
    doc_listdir = os.listdir(docs_path)

    stmt = select(CertOath)
    cert_oaths = session_dc.exec(stmt).all()

    if cert_oaths is None:
        logger.debug(f"Cert oath is empty")
        return True

    cert_oath_paths = [co.path for co in cert_oaths]

    for dir in doc_listdir:
        doc_listfile = os.listdir(docs_path + "/" + dir)

        for file in doc_listfile:
            if not f"/{dir}/{file}" in cert_oath_paths:
                os.remove(f"{docs_path}/{dir}/{file}")
                logger.debug(f"File is removed: {dir}/{file}")
            
    return True

@router.get("/clean/schema")
async def clean_schema(
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)):

    # SchmInfo 존재 여부에 따라 로직이 달라질 예정
    stmt = select(SchmInfo)
    schm_infos = session_dc.exec(stmt).all()

    if schm_infos is None:
        logger.debug("Schema info is empty")
        return True
    

    metadata = MetaData()

    schemata = Table(
        "schemata",
        metadata,
        Column("schema_name", String, primary_key=True),
        schema="information_schema"
    )

    stmt = select(schemata.c.schema_name).where(or_(schemata.c.schema_name.ilike(f"%schema_%")))
    schema_names = session_dc.exec(stmt).all()

    logger.debug(f"Schema List: {schema_names}")

    schema_names_on_db = [f"schema_{si.owner}_{si.id}" for si in schm_infos]

    for schema_name in schema_names:
        if not schema_name in schema_names_on_db:
            session_dc.exec(DropSchema(schema_name, cascade=True, if_exists=True))
            logger.debug(f"Schema is removed: {schema_name}")
    session_dc.commit()

    return True