from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

from models import Todos
from database import SessionLocal

from routers.auth import get_current_user

router = APIRouter(
    prefix='/admin', # 접두사
    tags=['어드민'] # 타이틀.
)

def get_db():  # db 정보를 fetch 한다음 close하는 함수.
    db = SessionLocal()
    try:
        yield db  # db를 전달함.
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return db.query(Todos).all()