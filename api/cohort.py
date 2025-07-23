from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form

router = APIRouter(prefix="/cohort", tags=["api/cohort"])

# -------- Imports --------
import os
import aiofiles
from datetime import datetime

from utils.structure import CohortDetail, CohortInfoTemp, CohortDetailTemp, TableInfoTemp, SchemaInfoTemp, IRBDRBTemp, FileGroupTemp


# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition,
    CertOath, SchmInfo, SchmCert
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
    user = Depends(verify_token)) -> list[dict]:

    user_id = findout_id(session_atlas, user["sub"])

    stmt = select(CohortDefinition).order_by(CohortDefinition.modified_date.desc())
    chrt_defs = session_atlas.exec(stmt).all()

    user_id_list = [cd.created_by_id for cd in chrt_defs]
    user_id_list = list(set(user_id_list))

    user_id_name_mapping = mapping_id_name(session_atlas, user_id_list)

    logger.debug(f"User id list: {user_id_list}, Mapping name: {user_id_name_mapping}")

    import random

    results = []
    for i in range(len(chrt_defs)):
        results.append(
            CohortInfoTemp(chrt_defs[i].id, chrt_defs[i].name, chrt_defs[i].description, random.randint(0, 203040),
                             user_id_name_mapping[chrt_defs[i].created_by_id], chrt_defs[i].created_date, chrt_defs[i].modified_date, "ATLAS").json())

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

    stmt = select(SchmInfo).where(SchmInfo.ext_id == cohort_id)
    schm_info = session_dc.exec(stmt).first()
    
    schm_info_temp = None
    file_group_temp = None

    if schm_info is not None:
        schm_info_temp = SchemaInfoTemp(schm_info.name, schm_info.description)

        stmt = select(CertOath).where(CertOath.document_for == schm_info.id)
        cert_oaths = session_dc.exec(stmt).all()

        irb_drb_temps = []

        for co in cert_oaths:
            docs_path = os.path.abspath(__file__ + "/../../documents")
            
            irb_drb_temps.append(IRBDRBTemp(co.name, co.path, os.path.getsize(docs_path + co.path), datetime.now()))

        file_group_temp = FileGroupTemp(irb_drb_temps)

    results = CohortDetailTemp(
        CohortInfoTemp(
            cohort_id, chrt_def.name, chrt_def.description,
            random.randint(0, 203040), owner_name, chrt_def.created_date, chrt_def.modified_date, "ATLAS"
        ),
        TableInfoTemp([random.randint(0,203040) for r in range(46)], [True if random.randint(0,1) == 1 else False for r in range(46)]),
        schm_info_temp,
        file_group_temp
    ).json()

    return results

@router.post("/id/{cohort_id}/apply")
async def apply_cohort(
    cohort_id: int,
    name: str = Form(...),
    description: str = Form(...),
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

    stmt = select(CohortDefinition).where(CohortDefinition.id == cohort_id)
    chrt_def = session_atlas.exec(stmt).first()

    m_date = chrt_def.modified_date

    # Create SchemaInfo
    # Table upload handling
    logger.debug(f"Tables: {tables} \n Files: {[file.filename for file in files]}")
    logger.debug(f"Table dimension: {len(tables)} / {len(tables[0])}")

    if schm_info is None:
        c_date = chrt_def.created_date

        schm_info = SchmInfo(ext_id=cohort_id, name=name, description=description, owner=user_id,
                tables=tables, origin="ATLAS", created_at=c_date, last_modified_at=m_date)

    else:
        schm_info.name = name,
        schm_info.description = description,
        schm_info.owner = user_id,
        schm_info.last_modified_at = m_date

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
        os.remove(f"{docs_path}{co.path}")
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