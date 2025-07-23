from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form

router = APIRouter(prefix="/cohort", tags=["temp/user/cohort"])

# -------- Imports --------
import os
import aiofiles
from datetime import datetime

from utils.structure import CohortDetail, CohortInfoTemp, CohortDetailTemp, TableInfoTemp, SchemaInfoTemp


# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition,
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
async def get_all_cohorts(
    session_atlas: Session = Depends(get_atlas_session),
    user = Depends(verify_token)) -> list[CohortDefinition]:

    user_id = findout_id(session_atlas, user["sub"])

    stmt = select(CohortDefinition).where(CohortDefinition.created_by_id == user_id).order_by(CohortDefinition.modified_date.desc())
    chrt_defs = session_atlas.exec(stmt).all()

    return chrt_defs

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

    return cohort_detail.json()

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
    stmt = select(SchmInfo).where(SchmInfo.ext_id == cohort_id)
    schm_info = session_dc.exec(stmt).first()

    m_date = None if modified_at == "NaN" else datetime.strptime(modified_at, "%Y-%m-%d %H:%M:%S.%f")

    # Create SchemaInfo
    # Table upload handling
    logger.debug(f"Tables: {tables} \n Files: {[file.filename for file in files]}")
    logger.debug(f"Table dimension: {len(tables)} / {len(tables[0])}")

    if schm_info is None:
        c_date = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f")

        schm_info = SchmInfo(ext_id=cohort_id, name=name, description=description, owner=user_id,
                tables=tables, origin="ATLAS", created_at=c_date, modified_at=m_date)

    else:
        schm_info.name = name,
        schm_info.description = description,
        schm_info.owner = user_id,
        schm_info.modified_at = m_date

    session_dc.add(schm_info)
    session_dc.commit()

    stmt = update(SchmInfo).where(SchmInfo.ext_id == cohort_id).values(tables=tables)
    session_dc.exec(stmt)
    session_dc.commit()

    # No it's dead
    # logger.debug(f"If schm_info existed? {schm_info}")

    stmt = select(SchmInfo).where(SchmInfo.ext_id == cohort_id)

    # There'll be existed it's own id
    schm_info = session_dc.exec(stmt).first()

    schema_id = schm_info.id

    stmt = select(SchmCert).where(SchmCert.id == schema_id)
    schm_cert = session_dc.exec(stmt).first()
    
    # Schema is new one
    if schm_cert is None:
        # Initialize(Create) SchmCert
        schm_cert = SchmCert(id=schema_id)

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