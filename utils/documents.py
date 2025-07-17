from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from utils.auth import verify_token

# 보안 강화
# router = APIRouter(prefix="/documents", dependencies=[Depends(verify_token)], tags=["documents"])
router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/{path:path}")
async def protected_documents(path: str):
    return FileResponse(f"documents/{path}")