from datetime import datetime
from enum import Enum, auto


# -------- Logging Setup --------
import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


class TABLE_NAME(Enum):
    PERSON = auto()
    OBSERVATION_PERIOD = auto()
    SPECIMEN = auto()
    DEATH = auto()
    VISIT_OCCURRENCE = auto()
    VISIT_DETAIL = auto()
    PROCEDURE_OCCURRENCE = auto()
    DRUG_EXPOSURE = auto()
    DEVICE_EXPOSURE = auto()
    CONDITION_OCCURRENCE = auto()
    MEASUREMENT = auto()
    NOTE = auto()
    NOTE_NLP = auto()
    OBSERVATION = auto()
    EPISODE = auto()
    EPISODE_EVENT = auto()
    FACT_RELATIONSHIP = auto()
    BIO_SIGNAL = auto()
    IMAGE_OCCURRENCE = auto()
    IMAGE_FEATURE = auto()
    IMAGING_STUDY = auto()
    IMAGING_SERIES = auto()
    IMAGING_ANNOTATION = auto()
    FILEPATH = auto()
    CONDITION_ERA = auto()
    DRUG_ERA = auto()
    DOSE_ERA = auto()
    COHORT = auto()
    COHORT_DEFINITION = auto()
    LOCATION = auto()
    CARE_SITE = auto()
    PROVIDER = auto()
    CONCEPT = auto()
    VOCABULARY = auto()
    DOMAIN = auto()
    CONCEPT_CLASS = auto()
    CONCEPT_SYNONYM = auto()
    CONCEPT_RELATIONSHIP = auto()
    RELATIONSHIP = auto()
    CONCEPT_ANCESTOR = auto()
    DRUG_STRENGTH = auto()
    SOURCE_TO_CONCEPT_MAP = auto()
    COST = auto()
    PAYER_PLAN_PERIOD = auto()
    CDM_SOURCE = auto()
    METADATA = auto()
TABLE_DESCRIPTION = [
    '환자 정보',
    '환자별 최초 기록 시간, 마지막 기록 시간',
    '검체 정보',
    '사망 정보',
    '방문 정보(입원, 외래, 응급)',
    '방문 상세 정보',
    '오더 (처치, 수술, 검사 처방) 정보',
    '약물 처방 정보',
    '의료장비 및 의료재료 사용 정보',
    '진단 정보',
    '검사 결과 정보',
    '기록지 정보',
    '기록지 추출 내용 정보 (note 테이블 자연어 처리)',
    '관찰 정보 (과거력, 가족력 등)',
    '',
    '',
    '',
    '생체신호 관련 비정형 데이터 메타데이터',
    'DICOM 파일 메타데이터',
    'DICOM 파일 기반 파생 데이터',
    'DICOM 파일 Study 관련 정보',
    'DICOM 파일 Series 관련 정보',
    'DICOM 파일에 대한 AI 등의 annotation 정보',
    'DICOM 파일의 메타 테이블',
    '환자 진단 유지 기간 정보',
    '환자 약물 사용 유지 기간 정보',
    '환자 약물-투여량 사용 유지 기간 정보',
    '코호트 정보',
    '코호트 정의 정보',
    '시군구 정보',
    '병원 정보 (본원, 암병원, 강남센터 등)',
    '직원 정보',
    '표준용어 목록',
    '표준용어 원천 (SNOMED, ICD10 등)',
    '표준용어 사용 테이블',
    '표준용어 원천 하위 분류',
    '표준용어 대체자',
    '표준용어간 관계 (부모-자식 관계 포함)',
    '표준용어간 관계 종류',
    '표준용어간 계층 관계 (부모-자식 관계 제외)',
    '표준용어 중 약물관련 용어 정보',
    '원내코드 - 표준용어 매핑 정보',
    '환자 지불 비용 정보',
    '환자 보험 정보',
    'CDM 구축에 사용된 원천',
    '',
]

def has_person_id(table_name: str):
    return table_name.upper() in ['PERSON', 'OBSERVATION_PERIOD', 'SPECIMEN', 'DEATH', 'VISIT_OCCURRENCE', 'VISIT_DETAIL', 'PROCEDURE_OCCURRENCE', 'DRUG_EXPOSURE', 'DEVICE_EXPOSURE',
                                  'CONDITION_OCCURRENCE', 'MEASUREMENT', 'NOTE', 'OBSERVATION', 'EPISODE', 'BIO_SIGNAL', 'IMAGE_OCCURRENCE', 'IMAGE_FEATURE', 'IMAGING_STUDY',
                                  'IMAGING_SERIES', 'IMAGING_ANNOTATION', 'FILEPATH', 'CONDITION_ERA', 'DRUG_ERA', 'DOSE_ERA', 'PAYER_PLAN_PERIOD']

def is_on_atlas(table_name: str):
    return table_name.upper() in ['PERSON', 'OBSERVATION_PERIOD', 'SPECIMEN', 'DEATH', 'VISIT_OCCURRENCE', 'VISIT_DETAIL', 'PROCEDURE_OCCURRENCE', 'DRUG_EXPOSURE', 'DEVICE_EXPOSURE',
                                  'CONDITION_OCCURRENCE', 'MEASUREMENT', 'NOTE', 'NOTE_NLP', 'OBSERVATION', 'FACT_RELATIONSHIP',
                                  'CONDITION_ERA', 'DRUG_ERA', 'DOSE_ERA', 'COHORT_DEFINITION', 'LOCATION', 'CARE_SITE', 'PROVIDER', 'CONCEPT', 'VOCABULARY', 'DOMAIN', 'CONCEPT_CLASS',
                                  'CONCEPT_SYNONYM', 'CONCEPT_RELATIONSHIP', 'RELATIONSHIP', 'CONCEPT_ANCESTOR', 'DRUG_STRENGTH', 'SOURCE_TO_CONCEPT_MAP', 'COST', 'PAYER_PLAN_PERIOD',
                                  'CDM_SOURCE', 'METADATA']

tables_pkey = {'PERSON': 'person_id', 'OBSERVATION_PERIOD': 'observation_period_id', 'SPECIMEN': 'specimen_id', 'VISIT_OCCURRENCE': 'visit_occurrence_id', 'VISIT_DETAIL': 'visit_detail_id',
               'PROCEDURE_OCCURRENCE': 'procedure_occurrence_id', 'DEVICE_EXPOSURE': 'device_exposure_id', 'CONDITION_OCCURRENCE': 'condition_occurrence_id', 'NOTE': 'note_id',
               'NOTE_NLP': 'note_nlp_id', 'CONDITION_ERA': 'condition_era_id', 'DRUG_ERA': 'drug_era_id', 'DOSE_ERA': 'dose_era_id', 'LOCATION': 'location_id', 'CARE_SITE': 'care_site_id',
               'PROVIDER': 'provider_id', 'CONCEPT': 'concept_id', 'VOCABULARY': 'vocabulary_id', 'DOMAIN': 'domain_id', 'CONCEPT_CLASS': 'concept_class_id', 'RELATIONSHIP': 'relationship_id',
               'COST': 'cost_id', 'PAYER_PLAN_PERIOD': 'payer_plan_period_id'}


class CohortInfoTemp():
    def __init__(self, id: int, name: str, description: str,
                 patient_count: int, author: str, created_date: datetime, modified_date: datetime, origin: str
                 ):
        self.id = id
        self.name = name
        self.description = description
        self.patient_count = patient_count
        self.author = author
        self.created_date = created_date
        self.modified_date = modified_date
        self.origin = origin

    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "patientCount": self.patient_count,
            "author": self.author,
            "createdDate": None if self.created_date is None else self.created_date.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "modifiedDate": None if self.modified_date is None else self.modified_date.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "origin": self.origin
        }
    
class TableInfoTemp():
    def __init__(self, record_counts, checks):
        self.record_counts = record_counts
        self.checks = checks

    def json(self):
        data = []

        for i in range(len(self.record_counts)):
            data.append({"name": TABLE_NAME(i+1).name, "description": TABLE_DESCRIPTION[i], "recordCount": self.record_counts[i], "checked": self.checks[i]})

        return data
    
    def name_only(self):
        data = [TABLE_NAME(i+1).name for i in range(len(self.record_counts)) if self.checks[i] == 1]

        return data

class SchemaInfoTemp():
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def json(self):
        return {
            "name": self.name,
            "description": self.description
        }
    
class IRBDRBTemp():
    def __init__(self, name: str, path: str, size: int):
        self.name = name
        self.path = path
        self.size = size

    def json(self):
        return {
            "name": self.name,
            "path": self.path,
            "size": f"{self.size / 1024 / 1024:.2}MB"
        }

class FileGroupTemp():
    def __init__(self, file_list: list[IRBDRBTemp]):
        self.file_list = file_list
    
    def json(self):
        return [file.json() for file in self.file_list]
    
class CohortDetailTemp():
    def __init__(self, cohort_info, table_info, schema_info, file_group):
        self.cohort_info = cohort_info
        self.table_info = table_info
        self.schema_info = schema_info
        self.file_group = file_group

    def json(self):
        return {
            "cohortInfo": self.cohort_info.json(),
            "tableInfo": self.table_info.json(),
            "schemaInfo": self.schema_info.json() if self.schema_info is not None else None,
            "irb_drb": self.file_group.json() if self.file_group is not None else None
        }
    
class ConnectInfoTemp():
    def __init__(self, host, database, username, port, schema, password):
        self.host = host
        self.database = database
        self.username = username
        self.port = port
        self.schema = schema
        self.password = password

    def json(self):
        return {
            "host": self.host,
            "database": self.database,
            "username": self.username,
            "port": self.port,
            "schema": self.schema,
            "password": self.password
        }
    
class CohortCertTemp():
    def __init__(self, applied_date: datetime, resolved_date: datetime, status: str, review: str):
        self.applied_date = applied_date
        self.resolved_date = resolved_date
        self.status = status
        self.review = review

    def json(self):
        return {
            "appliedDate": None if self.applied_date is None else self.applied_date.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "resolvedDate": None if self.resolved_date is None else self.resolved_date.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "status": self.status,
            "review": self.review
        }

class AppliedCohortDetailTemp():
    def __init__(self, cohort_info: CohortInfoTemp, cohort_cert: CohortCertTemp, table_info: TableInfoTemp, file_group: FileGroupTemp, connect_info: ConnectInfoTemp, is_synced: bool):
        self.cohort_info = cohort_info
        self.schema_cert = cohort_cert
        self.table_info = table_info
        self.file_group = file_group
        self.connect_info = connect_info
        self.is_synced = is_synced

    def json(self, table_name_only = False):
        data = self.cohort_info.json()
        data.update(self.schema_cert.json())
        data.update({"isSynced": self.is_synced})
        data.update({"tables": self.table_info.name_only() if table_name_only else self.table_info.json(), "irb_drb": self.file_group.json(), "connectInfo": self.connect_info.json() if self.connect_info is not None else None })
        return data
    
class AdminCohortDetailTemp():
    def __init__(self, cohort_info: CohortInfoTemp, cohort_cert: CohortCertTemp, table_info: TableInfoTemp, file_group: FileGroupTemp):
        self.cohort_info = cohort_info
        self.schema_cert = cohort_cert
        self.table_info = table_info
        self.file_group = file_group

    def json(self, table_name_only = False):
        data = self.cohort_info.json()
        data.update(self.schema_cert.json())
        data.update({"tables": self.table_info.name_only() if table_name_only else self.table_info.json(), "irb_drb": self.file_group.json()})
        return data


# -------- --------
class CohortDetail():
    def __init__(self, id: int, name: str, description: str,
                 owner: str, created_at: datetime, modified_at: datetime):
        self.id = id
        self.name = name
        self.description = description
        self.owner = owner
        self.created_at = created_at
        self.modified_at = modified_at

    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "created_at": None if self.created_at is None else self.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "modified_at": None if self.modified_at is None else self.modified_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        }

class SchemaSummary():
    def __init__(self, id: int, name: str, description: str, status: int,
                 owner: str, created_at: datetime, last_modified_at: datetime):
        self.id = id
        self.name = name
        self.desccription = description
        self.status = status
        self.owner = owner
        self.created_at = created_at
        self.last_modified_at = last_modified_at

    def json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.desccription,
            "status": self.status,
            "owner": self.owner,
            "created_at": None if self.created_at is None else self.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "last_modified_at": None if self.last_modified_at is None else self.last_modified_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        }
    
class OathFile():
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    def json(self) -> dict:
        return {
            "name": self.name,
            "path": self.path
        }

class SchemaDetail():
    def __init__(self, id: int, name: str, description: str, status: int,
                 owner: str, created_at: datetime, last_modified_at: datetime,
                 applied_at: datetime, resolved_at: str, tables: list[str],
                 files: list[OathFile], review: str):
        self.id = id
        self.name = name
        self.description = description
        self.status = status
        self.owner = owner
        self.created_at = created_at
        self.last_modified_at = last_modified_at
        self.applied_at = applied_at
        self.resolved_at = resolved_at
        self.tables = tables
        self.files = files
        self.review = review

    def json(self) -> dict:
        created_at = None if self.created_at is None else self.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        last_modified_at = None if self.last_modified_at is None else self.last_modified_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        applied_at = None if self.applied_at is None else self.applied_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        resolved_at = None if self.resolved_at is None else self.resolved_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "owner": self.owner,
            "created_at": created_at,
            "last_modified_at": last_modified_at,
            "applied_at": applied_at,
            "resolved_at": resolved_at,
            "tables": self.tables,
            "files": [file.json() for file in self.files],
            "review": self.review
        }