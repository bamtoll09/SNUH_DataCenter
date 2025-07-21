from datetime import datetime
from enum import Enum, auto


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


class CohortInfoTemp():
    def __init__(self, id: int, name: str, description: str,
                 patient_count: int, author: str, created_date: datetime, modified_date: datetime):
        self.id = id
        self.name = name
        self.description = description
        self.patient_count = patient_count
        self.author = author
        self.created_date = created_date
        self.modified_date = modified_date

    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "patientCount": self.patient_count,
            "author": self.author,
            "createdDate": None if self.created_date is None else self.created_date.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "modifiedDate": None if self.modified_date is None else self.modified_date.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        }
    
class TableInfoTemp():
    def __init__(self, record_counts):
        self.record_counts = record_counts

    def json(self):
        data = []

        for i in range(len(self.record_counts)):
            data.append({"name": TABLE_NAME(i+1).name, "description": "환자의 기본 인구학적 정보", "recordCount": self.record_counts[i]})

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
    
class CohortDetailTemp():
    def __init__(self, cohort_info, table_info, schema_info):
        self.cohort_info = cohort_info
        self.table_info = table_info
        self.schema_info = schema_info

    def json(self):
        return {
            "cohortInfo": self.cohort_info.json(),
            "tableInfo": self.table_info.json(),
            "schemaInfo": self.schema_info.json() if self.schema_info is not None else "{}"
        }

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