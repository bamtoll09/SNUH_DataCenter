from datetime import datetime, timedelta

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