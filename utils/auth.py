from fastapi import Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from secret import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

import logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

security = HTTPBearer()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: str = '1234567890'
    aud: str = 'normal_user'
    iat: int = datetime.now(timezone.utc)
    exp: int = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials
    logger.debug(f"Verifying token: {token}")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],
                             audience="normal_user",
                             options={"require": ["exp"]})
        
        if payload["aud"] is None:
            logger.error("User data not found")
            raise HTTPException(status_code=401, detail="User data not found")
        
        return payload
    except jwt.PyJWTError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")