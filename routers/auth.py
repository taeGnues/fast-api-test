from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends  # main에서 router할 수 있게 함.
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import Users
from database import SessionLocal
from passlib.context import CryptContext
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer # OAUTH2 비번
from jose import jwt, JWTError

router = APIRouter(
    prefix='/auth', # 접두사
    tags=['인증관련'] # 타이틀.
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto') # hash 알고리즘
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

# openssl rand -hex 32로 생성함
SECRET_KEY = '72589414265e6e6c5997672c6811264f60f6f3a70cce0b4cec4f842a804d2c72'
ALGORITHM = 'HS256'

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():  # db 정보를 fetch 한다음 close하는 함수.
    db = SessionLocal()
    try:
        yield db  # db를 전달함.
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

# 유저 인증
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password): # 해시값 기반으로 비밀번호 비교
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.utcnow()+ expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# app이 아니라 router로.
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        hashed_password = bcrypt_context.hash(create_user_request.password), # hash
        is_active = True,
        role = create_user_request.role,
    )

    db.add(create_user_model)
    db.commit()

# JWT 확인하고 유저 가져오기
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub') # username과 같음, sub
        user_id: int = payload.get('id') # id
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')

        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')


# OAUTH2 FORM 기반으로 로그인 인증.
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    # 오직 사용자가 입력할 값은 username과 비밀번호가 전부.
    # 사용자 이름 기반으로 유저 가져오기
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return 'Failed Authentication'

    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}
