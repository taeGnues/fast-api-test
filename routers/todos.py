from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

from models import Todos
from database import SessionLocal

from routers.auth import get_current_user

router = APIRouter()

def get_db():  # db 정보를 fetch 한다음 close하는 함수.
    db = SessionLocal()
    try:
        yield db  # db를 전달함.
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class TodoRequest(BaseModel):  # DTO.
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):  # db가 열리는 것에 의존함.
    if user is None: # user id를 가짐.
        raise HTTPException(status_code=401, detail='Authentication Error')

    return db.query(Todos).filter(Todos.owner_id==user.get('id')).all()

@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):  # 0이하는 입력 불가
    if user is None: # user id를 가짐.
        raise HTTPException(status_code=401, detail='Authentication Error')

    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id==user.get('id')).first()

    if todo_model is not None:  # 비어있는지 확인
        return todo_model
    raise HTTPException(status_code=404, detail='Todo not found')  # fastapi.httpexception으로 가져오기


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None: # user id를 가짐.
        raise HTTPException(status_code=401, detail='Authentication Error')
    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get('id'))

    db.add(todo_model)
    db.commit()


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency,
                      db: db_dependency,
                      todo_request: TodoRequest, # 순서 신경써서 써야함.
                      todo_id: int = Path(gt=0)
                      ):
    if user is None: # user id를 가짐.
        raise HTTPException(status_code=401, detail='Authentication Error')

    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id==user.get('id')).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)  # 바뀐거 알아서 인식.
    db.commit()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None: # user id를 가짐.
        raise HTTPException(status_code=401, detail='Authentication Error') # 인증기반.

    todo_model = db.query(Todos).filter(Todos.id==todo_id).filter(Todos.owner_id==user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found')
    db.query(Todos).filter(Todos.id==todo_id).filter(Todos.owner_id==user.get('id')).delete()
    db.commit()