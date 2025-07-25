from typing import List, Optional

from sqlmodel import SQLModel, Field, create_engine, Session, Column, ARRAY, String
from sqlalchemy import text, select

from datetime import datetime


# -------- Importing secret.py --------
from secret import postgres_url, datacenter_url


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


# -------- DBM Setup --------
atlas_engine = create_engine(postgres_url,
                             pool_pre_ping=True,
                             pool_recycle=900,     # 15 분마다 새로고침
                             pool_size=10,         # 동시 연결 수
                             max_overflow=5)

dc_engine = create_engine(datacenter_url,
                             pool_pre_ping=True,
                             pool_recycle=900,     # 15 분마다 새로고침
                             pool_size=10,         # 동시 연결 수
                             max_overflow=5)

def get_atlas_session():
    with Session(atlas_engine) as session:
        yield session

def get_dc_session():
    with Session(dc_engine) as session:
        yield session


# -------- CDM Results Models --------
class Cohort(SQLModel, table=True):
    __tablename__ = "cohort"
    __table_args__ = {"schema": "demo_cdm_results"}
    cohort_definition_id: int = Field(primary_key=True, default=None)
    subject_id: int = Field(primary_key=True, default=None)
    cohort_start_date: datetime = Field(default=None, nullable=False)
    cohort_end_date: datetime = Field(default=None, nullable=False)

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
class ChrtCert(SQLModel, table=True):
    __tablename__ = "chrt_cert"
    __table_args__ = {"schema": "dc_management"}
    id: int = Field(primary_key=True, default=None, foreign_key="dc_management.chrt_info.id")
    applied_at: datetime = Field(default=None, nullable=True)
    cur_status: int = Field(default=None, nullable=True)
    resolved_at: datetime = Field(default=None, nullable=True)
    review: str = Field(default=None, nullable=True)


class ChrtInfo(SQLModel, table=True):
    __tablename__ = "chrt_info"
    __table_args__ = {"schema": "dc_management"}
    id: Optional[int] = Field(primary_key=True, default=None)
    ext_id: int = Field(default=None, nullable=False)
    owner: int = Field(default=None, nullable=False)
    tables: List[str] | None = Field(sa_column=Column(ARRAY(String(100), dimensions=1), nullable=True))
    origin: str = Field(default=None, nullable=False)
    modified_at: datetime = Field(default=None, nullable=False)
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
    document_for: int = Field(default=None, nullable=False, foreign_key="dc_management.chrt_info.id")

class SchmInfo(SQLModel, table=True):
    __tablename__ = "schm_info"
    __table_args__ = {"schema": "dc_management"}
    id: Optional[int] = Field(primary_key=True, default=None)
    name: str = Field(index=True, nullable=False)
    description: str | None = Field(default=None, nullable=True)
    owner: int = Field(default=None, nullable=False)
    schema_from: int = Field(default=None, nullable=False, foreign_key="dc_management.chrt_info.id")

class SchmConnectInfo(SQLModel, table=True):
    __tablename__ = "schm_connect_info"
    __table_args__ = {"schema": "dc_management"}
    id: int = Field(primary_key=True, default=None, foreign_key="dc_management.schm_info.id")
    host: str = Field(default=None, nullable=False)
    port: int | None = Field(default=None, nullable=True)
    username: str = Field(default=None, nullable=False)
    password: str | None = Field(default=None, nullable=True)



# -------- Custom Schema --------
def make_school_model(schema: str):
    class School(SQLModel, table=True):
        __tablename__ = "school"
        __table_args__ = {"schema": schema}
        id: int = Field(primary_key=True, default=None)
        name: str | None = Field(default=None, sa_column=Column(String(1024), nullable=True))

    return School

def copy_tables_by_cohort_id(
        session_atlas: Session,
        session_dc: Session,
        schema_name: str,
        cohort_id: int,
        tables: list[str]):
    
    stmt = select(ChrtInfo).where(ChrtInfo.id == cohort_id)
    chrt_info = session_dc.exec(stmt).first()

    stmt = select(CohortDefinition).where(CohortDefinition.id == 1) # chrt_info.ext_id)
    chrt_def = session_atlas.exec(stmt).scalars().first()

    logger.debug(f"Cohort def is {type(chrt_def)}")

    stmt = select(Cohort).where(Cohort.cohort_definition_id == chrt_def.id)
    cohorts = session_atlas.exec(stmt).scalars().all()

    subject_ids = [c.subject_id for c in cohorts]
    subject_id_str = "(" + ", ".join(map(str, subject_ids)) + ")"
    
    ddls = [f"CREATE TABLE {schema_name}.{table} AS SELECT * FROM postgres.demo_cdm.{table} \
WHERE person_id IN {subject_id_str}" for table in tables]
    
    # logger.debug(f"Executing: {ddls}")

    for ddl in ddls:
        session_dc.exec(text(ddl))
    session_dc.commit()

# -------- Custom User --------
def provision_user(
    session: Session,
    new_user: str,
    new_pwd: str,
    target_db: str,
    target_schema: str):

    ddl = f"""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{new_user}') THEN
            CREATE ROLE {new_user} LOGIN;
        END IF;
    END$$;

    GRANT CONNECT ON DATABASE {target_db} TO {new_user};
    GRANT USAGE  ON SCHEMA  {target_schema} TO {new_user};
    GRANT SELECT ON ALL TABLES IN SCHEMA {target_schema} TO {new_user};
    ALTER DEFAULT PRIVILEGES IN SCHEMA {target_schema}
        GRANT SELECT ON TABLES TO {new_user};
    """

    session.exec(text(ddl))

    # 패스워드는 bindparam 으로 분리
    session.exec(
        text(f"ALTER ROLE {new_user} WITH PASSWORD :p"),
        params={"p": new_pwd},
    )
    session.commit()