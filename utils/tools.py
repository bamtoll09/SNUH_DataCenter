from datetime import datetime

from fastapi import HTTPException
from sqlmodel import select, Session


# -------- DBM Imports --------
from utils.dbm import (
    SecUser, SecUserRole,
)

from sqlmodel import Session, select, or_


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- Functions --------
def compare_dates(date1: datetime, date2: datetime) -> bool:
    return date1 < date2

def findout_id(session_atlas: Session, name: str) -> int:
    stmt = select(SecUser).where(SecUser.name == name)
    user = session_atlas.exec(stmt).first()

    if not user:
        logger.error("User not found in database")
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.debug(f"User id is {user.id}")

    return user.id

def findout_name(session_atlas: Session, id: int) -> str:
    stmt = select(SecUser).where(SecUser.id == id)
    user = session_atlas.exec(stmt).first()

    if not user:
        logger.error("User not found in database")
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.debug(f"User name is {user.name}")

    return user.name

def findout_role(session_atlas: Session, name: str) -> bool:
    user_id = findout_id(session_atlas, name)
    stmt = select(SecUserRole).where(SecUserRole.user_id == user_id).where(
        or_(SecUserRole.role_id==2, SecUserRole.role_id>=1000)
    )
    role = session_atlas.exec(stmt).all()

    if not role:
        return True
    
    return False

def mapping_id_name(session_atlas: Session, ids: list[int]) -> dict:
    stmt = select(SecUser).where(SecUser.id.in_(ids))
    users = session_atlas.exec(stmt).all()

    return {user.id: user.name for user in users}