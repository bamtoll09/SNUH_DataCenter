from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form

router = APIRouter(prefix="/schema")

# -------- Imports --------
import os
import aiofiles
from datetime import datetime
import json

from utils.structure import (
    CohortDetail, SchemaSummary, SchemaDetail, OathFile, CohortInfoTemp, SchemaCertTemp, SchemaDetailTemp, TABLE_NAME, ConnectInfoTemp,
)

# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition, SecUser, SecUserRole,
    CertOath, SchmInfo, SchmCert,
    make_school_model
)
from utils.auth import verify_token

from sqlmodel import Session, select, or_, col, update


# -------- Tool Imports --------
from utils.tools import compare_dates, findout_id, findout_name, findout_role


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- Routes --------
@router.get("/")
async def get_all_schemas(
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> list[dict]:

    user_id = findout_id(session_atlas, user["sub"])
    
    stmt = select(SchmInfo).where(SchmInfo.owner == user_id)
    schm_infos = session_dc.exec(stmt).all()

    stmt = select(SchmCert).where(SchmCert.id.in_([si.id for si in schm_infos]))
    schm_certs = session_dc.exec(stmt).all()

    import random

    results = []

    for si in schm_infos:
        for sc in schm_certs:
            if si.id == sc.id:
                cohort_info_temp = CohortInfoTemp(si.id, si.name, si.description,
                                        random.randint(0, 203040), user["sub"], si.created_at, si.modified_at, si.origin)
                schema_cert_temp = SchemaCertTemp(sc.applied_at, sc.resolved_at, sc.cur_status, sc.review)
                tables = [TABLE_NAME(j+1).name for j, val in enumerate([random.randint(0, 1) if i > 0 else 1 for i in range(random.randint(1, 46))]) if val == 1]
                connect_info_temp = None

                if sc.cur_status == "approved":
                    connect_info_temp = ConnectInfoTemp("data-center-db.hosplital.com", "omop_cdm", "kim_researcher_001", 5432, "cohort_1_kim_researcher_001", "temp_password_123")

                # else:
                #     raise HTTPException(status_code=404, detail="Schm info status not found")
                
                results.append(
                    SchemaDetailTemp(
                        cohort_info_temp,
                        schema_cert_temp,
                        tables,
                        connect_info_temp
                    ).json()
                )

    return results

    # user_role = "public" if findout_role(session_atlas, user["sub"]) else "admin"

    # logger.debug(f"User role is {user_role}")
    
    # if user_role == "admin":
    #     stmt = select(SchmCert).where(SchmCert.cur_status != "before_apply")
    #     schm_certs = session_dc.exec(stmt).all()

    #     stmt = select(SchmInfo).where(SchmInfo.id.in_([sc.id for sc in schm_certs]))
    #     schm_infos = session_dc.exec(stmt).all()

    #     schm_status = {e.id: e.cur_status for e in schm_certs}

    #     stmt = select(SecUser)
    #     users = session_atlas.exec(stmt).all()

    #     user_id_name_mapping = {u.id: u.name for u in users}

    #     all_summary = []

    #     for si in schm_infos:
    #         cohort_summary = SchemaSummary(
    #             id=si.id,
    #             name=si.name,
    #             description=si.description,
    #             status=schm_status[si.id],
    #             owner=user_id_name_mapping[si.owner],
    #             created_at=si.created_at,
    #             last_modified_at=si.last_modified_at
    #         )

    #         all_summary.append(cohort_summary.json())

    #     return all_summary
    
    # elif user_role == "public":
    #     user_id = findout_id(session_atlas, user["sub"])

    #     stmt = select(SchmInfo).where(SchmInfo.owner == user_id)
    #     user_schm_infos = session_dc.exec(stmt).all()

    #     stmt = select(SchmCert).where(
    #         SchmCert.id.in_([c.id for c in user_schm_infos]),
    #         SchmCert.cur_status != "before_apply")
        
    #     user_schm_certs = session_dc.exec(stmt).all()

    #     user_schm_status = {e.id: e.cur_status for e in user_schm_certs}

    #     logger.debug(f"Before length: {len(user_schm_infos)}")

    #     for i in range(len(user_schm_infos)-1, -1, -1):
    #         logger.debug(f"i: {i}")
    #         logger.debug(f"schm_info.id: {user_schm_infos[i].id}, statuses: {user_schm_status.keys()}")
    #         logger.debug(f"schm_info.id is in?: {user_schm_infos[i].id in user_schm_status.keys()}")
    #         if user_schm_infos[i].id not in user_schm_status.keys():
    #             del user_schm_infos[i]

    #     logger.debug(f"After length: {len(user_schm_infos)}")

    #     user_summary = []

    #     for si in user_schm_infos:
    #         cohort_summary = SchemaSummary(
    #             id=si.id,
    #             name=si.name,
    #             description=si.description,
    #             status=user_schm_status[si.id],
    #             owner=user["sub"],
    #             created_at=si.created_at,
    #             last_modified_at=si.last_modified_at
    #         )

    #         user_summary.append(cohort_summary.json())

    #     return user_summary

    # else:
    #     logger.error("User role not found")
    #     raise HTTPException(status_code=404, detail="User role not found")

@router.get("/id/{schema_id}")
async def get_schema_by_id(
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
        owner=owner_name, created_at=schm_info.created_at, last_modified_at=schm_info.modified_at,
        applied_at=schm_cert.applied_at, resolved_at=schm_cert.resolved_at, tables=schm_info.tables,
        files=cert_oath_list, review=schm_cert.review
    )

    return cohort_detail.json()

@router.post("/id/{schema_id}/apply")
async def apply_schema(
    schema_id: int,
    tables: list[str] = [],
    files: list[UploadFile] = File(None),
    remained_files: str = Form(None),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> str:

    # Table upload handling
    stmt = select(SchmInfo).where(SchmInfo.id == schema_id)
    schm_info = session_dc.exec(stmt).first()


    stmt = update(SchmInfo).where(SchmInfo.id == schema_id).values(tables=tables)
    session_dc.exec(stmt)
    session_dc.commit()

    # File handling
    docs_path = os.path.abspath(__file__ + "/../../../documents")
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)

    stmt = select(CertOath).where(CertOath.document_for == schema_id)
    cert_oaths = session_dc.exec(stmt).all()

    remained_files = json.loads(remained_files)

    logger.debug(f"Dumps: {remained_files}")

    if type(remained_files) == dict:
        remained_files = [remained_files]

    logger.debug(f"List: {remained_files}")

    # Need to remove '/documents'
    logger.debug(f"Remained_files: {[file['path'][10:] for file in remained_files]}")

    #  Files removing
    if len(remained_files) > 0:
        for co in cert_oaths:
            if co.path not in [file["path"][10:] for file in remained_files]:
                logger.debug(f"Removing file: {co.name} at {co.path}\n{docs_path} + {co.path}\nTotal path: {os.path.join(docs_path, co.path)}")
                os.remove(f"{docs_path}/{co.path}")
                session_dc.delete(co)

    # Remove all files
    elif cert_oaths is not None:
        for co in cert_oaths:
            logger.debug(f"Removing file: {co.name} at {co.path}\n{docs_path} + {co.path}\nTotal path: {os.path.join(docs_path, co.path)}")
            os.remove(f"{docs_path}/{co.path}")
            session_dc.delete(co)
    
    session_dc.commit()


    # File upload
    # Folder checking and creation
    cert_oath_dir = os.path.join(docs_path, str(schema_id))

    if not os.path.exists(cert_oath_dir):
        os.makedirs(cert_oath_dir)

    if files is not None:
        cert_oath_list = []

        for file in files:
            file_name = file.filename
            file_path = f"/{schema_id}"
            file_type = file.content_type.split("/").pop()
            file_category = "IRB" if "irb" in file_name.lower() else "DRB" if "drb" in file_name.lower() else "ETC"
            
            cert_oath = CertOath(name=file_name, path=file_path, type=file_type, category=file_category, document_for=schema_id)
            cert_oath_list.append(cert_oath)

        session_dc.add_all(cert_oath_list)
        session_dc.commit()


        # Change file_path by id
        stmt = select(CertOath).where(CertOath.document_for == schema_id)
        cert_oaths = session_dc.exec(stmt).all()
        
        for cert_oath in cert_oaths:
            cert_oath.path += f"/{schema_id}_{cert_oath.id}.{cert_oath.type}"

            logger.debug(f"File path: {docs_path} + {cert_oath.path}")

            for file in files:
                if file.filename == cert_oath.name:
                    async with aiofiles.open(os.path.join(docs_path + cert_oath.path), 'wb') as out_file:
                        content = await file.read()
                        await out_file.write(content)

        session_dc.add_all(cert_oaths)
        session_dc.commit()


    # Update SchmCert
    stmt = select(SchmCert).where(SchmCert.id == schema_id)
    schm_cert = session_dc.exec(stmt).first()


    schm_cert.applied_at = datetime.now()
    schm_cert.cur_status = "applied"
    schm_cert.resolved_at = None

    session_dc.add(schm_cert)
    session_dc.commit()

    return "Apply Success"

@router.get("/sync")
async def sync_schemas(
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)):
    
    # Cohort 수정일과 Schema 촤종 수정일을 비교
    # Cohort 수정일은 Schema 최종 수정일보다 같거나 이름.
    # 만일 Cohort 수정일이 Schema 최종 수정일보다 늦으면, Schema를 재승인 받도록 함.

    user_id = findout_id(session_atlas, user["sub"])

    stmt = select(CohortDefinition).where(CohortDefinition.created_by_id == user_id)
    chrt_defs = session_atlas.exec(stmt).all()

    stmt = select(SchmInfo).where(SchmInfo.owner == user_id)
    schm_infos = session_dc.exec(stmt).all()

    synced = False

    for schm_info in schm_infos:
        for chrt_def in chrt_defs:
            if schm_info.ext_id == chrt_def.id:
                if schm_info.modified_at < chrt_def.modified_date:
                    # SchmCert applied_at과 status, resolved_at 수정
                    stmt = select(SchmCert).where(SchmCert.id == schm_info.id)
                    schm_cert = session_dc.exec(stmt).first()
                    schm_cert.applied_at = datetime.now()
                    schm_cert.cur_status = "before_apply"

                    # CertOaths 모두 제거
                    stmt = select(CertOath).where(CertOath.document_for == schm_info.id)
                    cert_oaths = session_dc.exec(stmt).all()
                    for co in cert_oaths:
                        session_dc.delete(co)     

                    # SchmInfo last_modified_at 수정 및 tables 제거
                    schm_info.modified_at = chrt_def.modified_date
                    schm_info.tables = None
                    session_dc.add(schm_info)
                    session_dc.commit()

                    synced = True

    logger.debug("Synchronization Success" if synced else "All are up to date")

    return "Synchronization Success" if synced else "All are up to date"

@router.get("/id/{schema_id}/create")
async def create_schema_on_db(
    schema_id: int,
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)
    ):
    
    user_id = findout_id(session_atlas, user["sub"])

    schema_name = f"schema_{user_id}_{schema_id}"

    School = make_school_model(schema_name)
    school = School()

    logger.debug(f"School's schema is {school.__table_args__}")


    from sqlalchemy import text
    session_dc.exec(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    session_dc.exec(text(f"CREATE TABLE IF NOT EXISTS {schema_name}.school (id int PRIMARY KEY, name VARCHAR(1024))"))
    session_dc.commit()

    school.id = 1
    school.name = "HanGang"

    session_dc.add(school)
    session_dc.commit()
    
    return {"result": "success"}

# @router.get("/approved")
# async def get_approved_schemas(
#     session_atlas: Session = Depends(get_atlas_session),
#     session_dc: Session = Depends(get_dc_session),
#     user = Depends(verify_token)) -> list[dict]:

#     user_id = findout_id(session_atlas, user["sub"])

#     stmt = select(SchmInfo).where(SchmInfo.owner == user_id)
#     schm_infos = session_dc.exec(stmt).all()

#     stmt = select(SchmCert).where(
#         SchmCert.id.in_([si.id for si in schm_infos]),
#         SchmCert.cur_status == "approved")
#     schm_certs = session_dc.exec(stmt).all()

#     logger.debug(f"[B] schm_infos length: {len(schm_infos)}, schm_certs length: {len(schm_certs)}")

#     for i in range(len(schm_infos)-1, -1, -1):
#         if schm_infos[i].id not in [sc.id for sc in schm_certs]:
#             del schm_infos[i]

#     logger.debug(f"[A] schm_infos length: {len(schm_infos)}, schm_certs length: {len(schm_certs)}")

#     import random

#     results = []

#     for i in range(len(schm_infos)):
#         results.append(
#             ApprovedSchemaTemp(
#                 CohortInfoTemp(schm_infos[i].id, schm_infos[i].name, schm_infos[i].description,
#                                random.randint(0, 203040), user["sub"], schm_infos[i].created_at, schm_infos[i].last_modified_at),
#                 [TABLE_NAME(j+1).name for j, val in enumerate([random.randint(0, 1) if i > 0 else 1 for i in range(random.randint(1, 46))]) if val == 1],
#                 ConnectInfoTemp("data-center-db.hosplital.com", "omop_cdm", "kim_researcher_001", 5432, "cohort_1_kim_researcher_001", "temp_password_123")
#             ).json()
#         )

#     return results

# @router.get("/rejected")
# async def get_rejected_schemas():
#     pass