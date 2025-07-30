from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form

router = APIRouter(prefix="/schema")

# -------- Imports --------
import os
import aiofiles
from datetime import datetime
import json

from utils.structure import (
    CohortDetail, SchemaSummary, SchemaDetail, OathFile, CohortInfoTemp, CohortCertTemp, AppliedCohortDetailTemp, TABLE_NAME, ConnectInfoTemp, TableInfoTemp
)

# -------- DBM Imports --------
from utils.dbm import (
    get_atlas_session, get_dc_session,
    CohortDefinition, SecUser, SecUserRole,
    CertOath, ChrtInfo, ChrtCert,
    make_school_model, provision_user, copy_tables_by_cohort_id
)
from utils.auth import verify_token

from sqlmodel import Session, select, or_, col, update


# -------- Tool Imports --------
from utils.tools import compare_dates, findout_id, findout_name, findout_role


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

# @router.get("/id/{schema_id}/create")
# async def create_schema_on_db(
#     schema_id: int,
#     session_atlas: Session = Depends(get_atlas_session),
#     session_dc: Session = Depends(get_dc_session),
#     user = Depends(verify_token)
#     ):
    
#     user_id = findout_id(session_atlas, user["sub"])

#     schema_name = f"schema_{user_id}_{schema_id}"

#     # School = make_school_model(schema_name)
#     # school = School()

#     # logger.debug(f"School's schema is {school.__table_args__}")
    

#     # from sqlalchemy.schema import CreateSchema, CreateTable

#     # session_dc.exec(CreateSchema(schema_name, if_not_exists=True))
#     # session_dc.exec(CreateTable(school.__table__, if_not_exists=True))
#     # session_dc.exec(text(f"CREATE SCHEMA IF NOT EXISTS :schema_name").bindparams(schema_name=schema_name))
#     # session_dc.exec(text(f"CREATE TABLE IF NOT EXISTS :schema_name.school (id int PRIMARY KEY, name VARCHAR(1024))").bindparams(schema_name=schema_name))
#     # session_dc.commit()

#     # school.id = 1
#     # school.name = "HanGang"

#     # schools = session_dc.exec(select(School)).all()
#     # if len(schools) > 0:
#     #     for s in schools:
#     #         session_dc.delete(s)
#     #     session_dc.commit()

#     # session_dc.add(school)
#     # session_dc.commit()

#     provision_user(session_dc, "u" + str(user_id), "1234", "datacenter", schema_name)

#     copy_tables_by_cohort_id(session_atlas, session_dc, schema_name, schema_id)
    
#     return {"result": "success"}