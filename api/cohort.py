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

@router.get("/id/{cohort_id}")
async def get_cohort_by_id(
    cohort_id: int | None,
    session_atlas: Session = Depends(get_atlas_session),
    session_dc: Session = Depends(get_dc_session),
    user = Depends(verify_token)) -> dict:

    if cohort_id is None:
        logger.error("Cohort id not found")
        raise HTTPException(status_code=404, detail="Cohort id not found")
    
    stmt = select(ChrtInfo).where(ChrtInfo.id == cohort_id)
    chrt_info = session_dc.exec(stmt).first()

    if chrt_info is None:
        logger.error("Schema id not found on DataCenter")
        raise HTTPException(status_code=404, detail="Schema id not found on DataCenter")

    owner_name = findout_name(session_atlas, chrt_info.owner)
    
    cohort_detail = CohortDetail(
        id=cohort_id, name=chrt_info.name, description=chrt_info.description,
        owner=owner_name, created_at=chrt_info.created_at, modified_at=chrt_info.created_at,
    )

    import random

    stmt = select(ChrtCert).where(ChrtCert.id == cohort_id)
    chrt_cert = session_dc.exec(stmt).first()

    schm_info_temp = None
    file_group_temp = None

    if chrt_cert is not None & chrt_cert.cur_status != "before_apply":
        stmt = select(SchmInfo).where(SchmInfo.id == cohort_id)
        schm_info = session_dc.exec(stmt).first()

        schm_info_temp = SchemaInfoTemp(schm_info.name, schm_info.description)

        stmt = select(CertOath).where(CertOath.document_for == schm_info.id)
        cert_oaths = session_dc.exec(stmt).all()

        irb_drb_temps = []

        for co in cert_oaths:
            docs_path = os.path.abspath(__file__ + "/../../documents")
            
            irb_drb_temps.append(IRBDRBTemp(co.name, co.path, os.path.getsize(docs_path + co.path)))

        file_group_temp = FileGroupTemp(irb_drb_temps)

    results = CohortDetailTemp(
        CohortInfoTemp(
            cohort_id, chrt_info.name, chrt_info.description,
            random.randint(0, 203040), owner_name, chrt_info.created_at, chrt_info.modified_at, "ATLAS"
        ),
        TableInfoTemp([random.randint(0,203040) for r in range(46)], [True if random.randint(0,1) == 1 else False for r in range(46)]),
        schm_info_temp,
        file_group_temp
    ).json()

    return results

@router.post("/id/{cohort_id}/apply")
async def apply_cohort(
    cohort_id: int,
    name: str | None = Form(...),           # for schema
    description: str | None = Form(...),    # for schema
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

    # It should be existed
    stmt = select(ChrtInfo).where(ChrtInfo.id == cohort_id)
    chrt_info = session_dc.exec(stmt).first()

    # It name or description is empty set default
    if name is None:
        name = chrt_info.name
    if description is None:
        description = chrt_info.description


    # Table upload handling
    logger.debug(f"Tables: {tables} \n Files: {[file.filename for file in files]}")
    logger.debug(f"Table dimension: {len(tables)} / {len(tables[0])}")

    stmt = update(ChrtInfo).where(ChrtInfo.id == cohort_id).values(tables=tables)
    session_dc.exec(stmt)
    session_dc.commit()


    # # Get SchmInfo
    # stmt = select(SchmInfo).where(SchmInfo.owner == user_id, SchmInfo.schema_from == cohort_id)
    # schm_info = session_dc.exec(stmt).first()

    # # Create SchmInfo
    # if schm_info is None:
    #     schm_info = SchmInfo(None, name, description, user_id, cohort_id)
    
    # # Already existed
    # else:
    #     schm_info.name = name
    #     schm_info.description = description

    # session_dc.add(schm_info)
    # session_dc.commit()

    # stmt = select(SchmInfo).where(SchmInfo.owner == user_id, SchmInfo.schema_from == cohort_id)
    # schm_info = session_dc.exec(stmt).first()
    
    # # Get SchmConnectInfo
    # stmt = select(SchmConnectInfo).where(SchmConnectInfo.id == schm_info.id)
    # schm_cinfo = session_dc.exec(stmt).first()

    # # Create SchmConnectInfo
    # if schm_cinfo is None:
    #     schm_cinfo = SchmConnectInfo(schm_info.id, "127.0.0.1", 5432, "postgres_userid", "mypass_randint")
        
    #     session_dc.add(schm_cinfo)
    #     session_dc.commit()

    # Get CohortCert
    stmt = select(ChrtCert).where(ChrtCert.id == cohort_id)
    schm_cert = session_dc.exec(stmt).first()
    
    # If cohort is new one
    if schm_cert is None:
        # Initialize(Create) SchmCert
        schm_cert = ChrtCert(id=cohort_id)

    # File handling
    docs_path = os.path.abspath(__file__ + "/../../documents")
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)

    # File removing
    stmt = select(CertOath).where(CertOath.document_for == cohort_id)
    cert_oaths = session_dc.exec(stmt).all()

    if cert_oaths is not None:
        for co in cert_oaths:
            os.remove(f"{docs_path}{co.path}")
            session_dc.delete(co)
        session_dc.commit()

    # File upload
    # Folder checking and creation
    cert_oath_dir = os.path.join(docs_path, str(cohort_id))

    if not os.path.exists(cert_oath_dir):
        logger.debug(f"Folder Created")
        os.makedirs(cert_oath_dir)
    
    cert_oath_list = []

    for file in files:
        file_name = file.filename
        file_path = f"/{cohort_id}"
        file_type = file.content_type.split("/").pop()
        file_category = "IRB" if "irb" in file_name.lower() else "DRB" if "drb" in file_name.lower() else "ETC"
        
        cert_oath = CertOath(name=file_name, path=file_path, type=file_type, category=file_category, document_for=cohort_id)
        cert_oath_list.append(cert_oath)

    session_dc.add_all(cert_oath_list)
    session_dc.commit()


    # Change file_path by id
    stmt = select(CertOath).where(CertOath.document_for == cohort_id)
    cert_oaths = session_dc.exec(stmt).all()

    for cert_oath in cert_oaths:
        cert_oath.path += f"/{cohort_id}_{cert_oath.id}.{cert_oath.type}"

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