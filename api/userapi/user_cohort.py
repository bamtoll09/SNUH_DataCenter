from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form

router = APIRouter(prefix="/cohort")

# -------- Imports --------
import os
import aiofiles
from datetime import datetime

from utils.structure import CohortDetail, CohortInfoTemp, CohortDetailTemp, TableInfoTemp, SchemaInfoTemp, IRBDRBTemp, FileGroupTemp, CohortCertTemp, AppliedCohortDetailTemp, ConnectInfoTemp, TABLE_NAME


# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition,
    CertOath, ChrtInfo, ChrtCert,
    SchmInfo
)
from utils.auth import verify_token

from sqlmodel import Session, select, update


# -------- Tool Imports --------
from utils.tools import findout_id, findout_name, get_syncable


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- Routes --------
@router.get("/")
async def get_my_cohorts(
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> list[dict]:

    user_id = findout_id(session_atlas, user["sub"])
    
    stmt = select(ChrtInfo).where(ChrtInfo.owner == user_id)
    chrt_infos = session_dc.exec(stmt).all()

    stmt = select(ChrtCert).where(ChrtCert.id.in_([ci.id for ci in chrt_infos]))
    chrt_certs = session_dc.exec(stmt).all()

    syncables = get_syncable(session_atlas, session_dc, user["sub"])

    import random

    results = []

    if chrt_certs is None:
        return results

    for ci in chrt_infos:
        for cc in chrt_certs:
            if ci.id == cc.id:
                tables = [False for i in range(46)] if ci.tables is None else [True if table == t else False for t in ci.tables for table in list(TABLE_NAME.__members__.keys())]

                cohort_info_temp = CohortInfoTemp(ci.id, ci.name, ci.description,
                                        random.randint(0, 203040), user["sub"], ci.created_at, ci.modified_at, ci.origin)
                schema_cert_temp = CohortCertTemp(cc.applied_at, cc.resolved_at, cc.cur_status, cc.review)
                table_info_temp = TableInfoTemp([random.randint(0,203040) for r in range(46)], tables)
                # tables = [TABLE_NAME(j+1).name for j, val in enumerate([random.randint(0, 1) if i > 0 else 1 for i in range(random.randint(1, 46))]) if val == 1]
                connect_info_temp = None

                if cc.cur_status == "approved":
                    connect_info_temp = ConnectInfoTemp("data-center-db.hosplital.com", "omop_cdm", "kim_researcher_001", 5432, "cohort_1_kim_researcher_001", "temp_password_123")

                # else:
                #     raise HTTPException(status_code=404, detail="Schm info status not found")
                
                results.append(
                    AppliedCohortDetailTemp(
                        cohort_info_temp,
                        schema_cert_temp,
                        table_info_temp,
                        connect_info_temp,
                        syncables[ci.id]
                    ).json()
                )

    return results

@router.get("/applies")
async def get_my_applied_cohorts(
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> list[dict]:

    user_id = findout_id(session_atlas, user["sub"])
    
    stmt = select(ChrtInfo).where(ChrtInfo.owner == user_id)
    chrt_infos = session_dc.exec(stmt).all()

    stmt = select(ChrtCert).where(ChrtCert.cur_status != "before_apply", ChrtCert.id.in_([ci.id for ci in chrt_infos]))
    chrt_certs = session_dc.exec(stmt).all()

    syncables = get_syncable(session_atlas, session_dc, user["sub"])

    import random

    results = []

    if chrt_certs is None:
        return results

    for ci in chrt_infos:
        for cc in chrt_certs:
            if ci.id == cc.id:
                tables = [False for i in range(46)] if ci.tables is None else [True if table == t else False for t in ci.tables for table in list(TABLE_NAME.__members__.keys())]

                cohort_info_temp = CohortInfoTemp(ci.id, ci.name, ci.description,
                                        random.randint(0, 203040), user["sub"], ci.created_at, ci.modified_at, ci.origin)
                schema_cert_temp = CohortCertTemp(cc.applied_at, cc.resolved_at, cc.cur_status, cc.review)
                table_info_temp = TableInfoTemp([random.randint(0,203040) for r in range(46)], tables)
                # tables = [TABLE_NAME(j+1).name for j, val in enumerate([random.randint(0, 1) if i > 0 else 1 for i in range(random.randint(1, 46))]) if val == 1]
                connect_info_temp = None

                if cc.cur_status == "approved":
                    connect_info_temp = ConnectInfoTemp("data-center-db.hosplital.com", "omop_cdm", "kim_researcher_001", 5432, "cohort_1_kim_researcher_001", "temp_password_123")

                # else:
                #     raise HTTPException(status_code=404, detail="Schm info status not found")
                
                results.append(
                    AppliedCohortDetailTemp(
                        cohort_info_temp,
                        schema_cert_temp,
                        table_info_temp,
                        connect_info_temp,
                        syncables[ci.id]
                    ).json()
                )

    return results

@router.get("/id/{cohort_id}")
async def get_cohort_by_id(
    cohort_id: int | None,
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> dict:

    if cohort_id is None:
        logger.error("Cohort id not found")
        raise HTTPException(status_code=404, detail="Cohort id not found")
    
    stmt = select(CohortDefinition).where(CohortDefinition.id == cohort_id)
    chrt_def = session_atlas.exec(stmt).first()

    if chrt_def is None:
        logger.error("Schema id not found on DataCenter")
        raise HTTPException(status_code=404, detail="Schema id not found on DataCenter")

    owner_name = findout_name(session_atlas, chrt_def.created_by_id)
    
    cohort_detail = CohortDetail(
        id=cohort_id, name=chrt_def.name, description=chrt_def.description,
        owner=owner_name, created_at=chrt_def.created_date, modified_at=chrt_def.modified_date,
    )

    import random

    stmt = select(ChrtInfo).where(ChrtInfo.id == cohort_id)
    chrt_info = session_dc.exec(stmt).first()

    stmt = select(SchmInfo).where(SchmInfo.schema_from == cohort_id)
    schm_info = session_dc.exec(stmt).first()
    
    schm_info_temp = None
    file_group_temp = None

    if schm_info is None:
        schm_info_temp = SchemaInfoTemp(chrt_info.name, chrt_info.description)

    stmt = select(CertOath).where(CertOath.document_for == chrt_info.id)
    cert_oaths = session_dc.exec(stmt).all()

    irb_drb_temps = []

    if cert_oaths is not None:
        for co in cert_oaths:
            docs_path = os.path.abspath(__file__ + "/../../../documents")

        irb_drb_temps.append(IRBDRBTemp(co.name, co.path, os.path.getsize(docs_path + co.path), datetime.now()))

    file_group_temp = FileGroupTemp(irb_drb_temps)

    tables = [False for i in range(46)] if chrt_info.tables is None else [True if table == t else False for t in chrt_info.tables for table in list(TABLE_NAME.__members__.keys())]

    results = CohortDetailTemp(
        CohortInfoTemp(
            cohort_id, chrt_def.name, chrt_def.description,
            random.randint(0, 203040), owner_name, chrt_def.created_date, chrt_def.modified_date, "ATLAS"
        ),
        TableInfoTemp([random.randint(0,203040) for r in range(46)], tables),
        schm_info_temp,
        file_group_temp
    ).json()

    return results

@router.post("/id/{cohort_id}/apply")
async def apply_cohort(
    cohort_id: int,
    name: str = Form(...),
    description: str = Form(...),
    created_at: str = Form(...),
    modified_at: str = Form(...),
    tables: list[str] = Form(...),
    files: list[UploadFile] = File(...),
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> str:

    if cohort_id is None:
        logger.error("Cohort id not found")
        raise HTTPException(status_code=404, detail="Cohort id not found")

    user_id = findout_id(session_atlas, user["sub"])

    if user_id is None:
        logger.error("User id not found")
        raise HTTPException(status_code=404, detail="User id not found")

    # If there is already existed schema
    stmt = select(ChrtInfo).where(ChrtInfo.ext_id == cohort_id)
    schm_info = session_dc.exec(stmt).first()

    m_date = None if modified_at == "NaN" else datetime.strptime(modified_at, "%Y-%m-%d %H:%M:%S.%f")

    # Create SchemaInfo
    # Table upload handling
    logger.debug(f"Tables: {tables} \n Files: {[file.filename for file in files]}")
    logger.debug(f"Table dimension: {len(tables)} / {len(tables[0])}")

    if schm_info is None:
        c_date = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f")

        schm_info = ChrtInfo(ext_id=cohort_id, name=name, description=description, owner=user_id,
                tables=tables, origin="ATLAS", created_at=c_date, modified_at=m_date)

    else:
        schm_info.name = name,
        schm_info.description = description,
        schm_info.owner = user_id,
        schm_info.modified_at = m_date

    session_dc.add(schm_info)
    session_dc.commit()

    stmt = update(ChrtInfo).where(ChrtInfo.ext_id == cohort_id).values(tables=tables)
    session_dc.exec(stmt)
    session_dc.commit()

    # No it's dead
    # logger.debug(f"If schm_info existed? {schm_info}")

    stmt = select(ChrtInfo).where(ChrtInfo.ext_id == cohort_id)

    # There'll be existed it's own id
    schm_info = session_dc.exec(stmt).first()

    schema_id = schm_info.id

    stmt = select(ChrtCert).where(ChrtCert.id == schema_id)
    schm_cert = session_dc.exec(stmt).first()
    
    # Schema is new one
    if schm_cert is None:
        # Initialize(Create) SchmCert
        schm_cert = ChrtCert(id=schema_id)

    # File handling
    docs_path = os.path.abspath(__file__ + "/../../../documents")
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)

    # File removing
    stmt = select(CertOath).where(CertOath.document_for == schema_id)
    cert_oaths = session_dc.exec(stmt).all()

    for co in cert_oaths:
        os.remove(f"{docs_path}/{co.path}")
        session_dc.delete(co)
    session_dc.commit()

    # File upload
    # Folder checking and creation
    cert_oath_dir = os.path.join(docs_path, str(schema_id))

    if not os.path.exists(cert_oath_dir):
        logger.debug(f"Folder Created")
        os.makedirs(cert_oath_dir)
    
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
    schm_cert.applied_at = datetime.now()
    schm_cert.cur_status = "applied"
    schm_cert.resolved_at = None
    schm_cert.review = None

    session_dc.add(schm_cert)
    session_dc.commit()

    return "Apply Success"

@router.get("/sync")
async def sync_cohorts(
    cohort_id: int | None = None,
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)):

    synced = False

    user_id = findout_id(session_atlas, user["sub"])

    if cohort_id is not None:
        stmt = select(ChrtInfo).where(ChrtInfo.id == cohort_id)
        chrt_info = session_dc.exec(stmt).first()

        if chrt_info is None:
            raise HTTPException(404, "Cohort is not found on yours")

        stmt = select(CohortDefinition).where(CohortDefinition.created_by_id == user_id,
                                              CohortDefinition.id == chrt_info.ext_id)
        chrt_def = session_atlas.exec(stmt).first()

        if chrt_def is None:
            raise HTTPException(401, "This cohort is not yours")

        if chrt_info.modified_at < chrt_def.modified_date:
            # ChrtCert applied_at과 status, resolved_at 수정
            stmt = select(ChrtCert).where(ChrtCert.id == chrt_info.id)
            schm_cert = session_dc.exec(stmt).first()

            if schm_cert is not None:
                schm_cert.applied_at = None
                schm_cert.cur_status = "before_apply"
                schm_cert.resolved_at = None
                schm_cert.review = None

            # CertOaths 모두 제거
            stmt = select(CertOath).where(CertOath.document_for == chrt_info.id)
            cert_oaths = session_dc.exec(stmt).all()

            if cert_oaths is not None:
                for co in cert_oaths:
                    session_dc.delete(co)

            # SchmInfo 내용 제거
            # stmt = select(SchmInfo).where()

            # SchmConnectInfo 내용 제거

            # ChrtInfo modified_at 수정 및 tables 제거
            chrt_info.modified_at = chrt_def.modified_date
            chrt_info.tables = None
            session_dc.add(chrt_info)
            session_dc.commit()

            synced = True
    
    else:
    # 외부 Cohort 수정일과 DC Cohort 수정일을 비교
    # 외부 Cohort 수정일은 DC Cohort 수정일보다 같거나 이름.
    # 만일 외부 Cohort 수정일이 DC Cohort 수정일보다 늦으면, Schema를 재승인 받도록 함.

        stmt = select(CohortDefinition).where(CohortDefinition.created_by_id == user_id)
        chrt_defs = session_atlas.exec(stmt).all()

        logger.debug(f"chrt_defs length: {len(chrt_defs)}")

        stmt = select(ChrtInfo).where(ChrtInfo.owner == user_id)
        chrt_infos = session_dc.exec(stmt).all()

        holding_ext_ids = [ci.ext_id for ci in chrt_infos]

        for cd in chrt_defs:
            # New cohort detected
            if cd.id not in holding_ext_ids:
                chrt_info = ChrtInfo()
                chrt_info.id = None
                chrt_info.ext_id = cd.id
                chrt_info.owner = cd.created_by_id
                chrt_info.tables = None
                chrt_info.origin = "ATLAS"
                chrt_info.modified_at = cd.modified_date
                chrt_info.name = cd.name
                chrt_info.description = cd.description
                chrt_info.created_at = cd.created_date
                session_dc.add(chrt_info)
                
                synced = True

            # Existed cohort
            else:
                for ci in chrt_infos:
                    if ci.ext_id == cd.id:
                        if ci.modified_at < cd.modified_date:
                            # ChrtCert applied_at과 status, resolved_at 수정
                            stmt = select(ChrtCert).where(ChrtCert.id == ci.id)
                            schm_cert = session_dc.exec(stmt).first()
                            schm_cert.applied_at = None
                            schm_cert.cur_status = "before_apply"
                            schm_cert.resolved_at = None
                            schm_cert.review = None

                            # CertOaths 모두 제거
                            stmt = select(CertOath).where(CertOath.document_for == ci.id)
                            cert_oaths = session_dc.exec(stmt).all()

                            if cert_oaths is not None:
                                for co in cert_oaths:
                                    session_dc.delete(co)

                            # SchmInfo 내용 제거
                            # stmt = select(SchmInfo).where()

                            # SchmConnectInfo 내용 제거

                            # ChrtInfo modified_at 수정 및 tables 제거
                            ci.modified_at = cd.modified_date
                            ci.tables = None
                            session_dc.add(ci)
                            session_dc.commit()

                            synced = True

    session_dc.commit()

    logger.debug("Synchronization Success" if synced else "All are up to date")

    return "Synchronization Success" if synced else "All are up to date"