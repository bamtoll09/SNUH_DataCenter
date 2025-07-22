from typing import List, Optional

from sqlmodel import SQLModel, Field, create_engine, Session, Column, ARRAY, String

from datetime import datetime


# -------- Importing secret.py --------
from secret import postgres_url, datacenter_url


# -------- DBM Setup --------
atlas_engine = create_engine(postgres_url, echo=True)
dc_engine = create_engine(datacenter_url, echo=True)

def get_atlas_session():
    with Session(atlas_engine) as session:
        yield session

def get_dc_session():
    with Session(dc_engine) as session:
        yield session


# -------- CDM Models --------
class PathwayAnalysisEvents(SQLModel, table=True):
    __tablename__ = "pathway_analysis_events"
    __table_args__ = {"schema": "demo_cdm_results"}
    pathway_analysis_generation_id: int = Field(primary_key=True, default=None)
    target_cohort_id: int = Field(default=None)
    combo_id: int = Field(default=None)
    subject_id: int = Field(default=None)
    ordinal: int | None = Field(default=None)
    cohort_start_date: str = Field(default=None)
    cohort_end_date: str = Field(default=None)
    pathway_analysis_event_id: int = Field(primary_key=True, default=None)


# -------- WebAPI Models --------
class CohortDefinition(SQLModel, table=True):
    __tablename__ = "cohort_definition"
    __table_args__ = {"schema": "webapi"}
    id: int = Field(primary_key=True, default=None)
    name: str = Field(index=True, nullable=False)
    description: str | None = Field(default=None, nullable=True)
    expression_type: str = Field(nullable=False)
    created_date: datetime = Field(default=None, nullable=False)
    modified_date: datetime = Field(default=None, nullable=False)
    created_by_id: int | None = Field(default=None, foreign_key="webapi.sec_user.id", nullable=True)
    modified_by_id: int | None = Field(default=None, foreign_key="webapi.sec_user.id", nullable=True)


class SecUser(SQLModel, table=True):
    __tablename__ = "sec_user"
    __table_args__ = {"schema": "webapi"}
    id: int = Field(primary_key=True, default=None)
    login: str = Field(index=True, nullable=False)
    name: str = Field(nullable=False)
    last_viewed_notifications_time: str | None = Field(default=None, nullable=True)
    origin: str = Field(default=None, nullable=False)


class SecUserRole(SQLModel, table=True):
    __tablename__ = "sec_user_role"
    __table_args__ = {"schema": "webapi"}
    id: int = Field(primary_key=True, default=None)
    user_id: int = Field(default=None, nullable=False, foreign_key="webapi.sec_user.id")
    role_id: int = Field(default=None, nullable=False, foreign_key="webapi.sec_role.id")
    status: str | None = Field(default=None, nullable=True)
    origin: str = Field(default=None, nullable=False)


# -------- WebAPI Security Models --------
class Security(SQLModel, table=True):
    __tablename__ = "security"
    __table_args__ = {"schema": "webapi_security"}
    email: str = Field(primary_key=True, index=True, nullable=False)
    password: str = Field(nullable=False)


# -------- DataCenter Models --------
class SchmCert(SQLModel, table=True):
    __tablename__ = "schm_cert"
    __table_args__ = {"schema": "dc_management"}
    id: int = Field(primary_key=True, default=None, foreign_key="dc_management.schm_info.id")
    applied_at: datetime = Field(default=None, nullable=True)
    cur_status: int = Field(default=None, nullable=True)
    resolved_at: datetime = Field(default=None, nullable=True)
    review: str = Field(default=None, nullable=True)


class SchmInfo(SQLModel, table=True):
    __tablename__ = "schm_info"
    __table_args__ = {"schema": "dc_management"}
    id: Optional[int] = Field(primary_key=True, default=None)
    ext_id: int = Field(default=None, nullable=False)
    owner: int = Field(default=None, nullable=False)
    tables: List[str] | None = Field(sa_column=Column(ARRAY(String(100), dimensions=1), nullable=True))
    origin: str = Field(default=None, nullable=False)
    last_modified_at: datetime = Field(default=None, nullable=False)
    name: str = Field(index=True, nullable=False)
    description: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default=None, nullable=False)


class CertOath(SQLModel, table=True):
    __tablename__ = "cert_oath"
    __table_args__ = {"schema": "dc_management"}
    id: Optional[int] = Field(primary_key=True, default=None)
    name: str = Field(default=None, nullable=True)    
    path: str = Field(default=None, nullable=True)
    type: str = Field(default=None, nullable=True)
    category: str = Field(default=None, nullable=True)
    document_for: int = Field(default=None, nullable=False, foreign_key="dc_management.schm_info.id")


# -------- Custom Schema --------
def make_school_model(schema: str):
    class School(SQLModel, table=True):
        __tablename__ = "school"
        __table_args__ = {"schema": schema}
        id: int = Field(primary_key=True, default=None)
        name: str = Field(default=None, nullable=False)

    return School