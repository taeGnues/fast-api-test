from fastapi import FastAPI

import models
from database import engine
from routers import auth, todos, admin, users

app = FastAPI()

# main.py에서 모든 fastapi 객체들을 관리

models.Base.metadata.create_all(bind=engine)  # todos.db가 없을때만 실행됨.

app.include_router(auth.router) # router 를 사용.
app.include_router(todos.router) # router 를 사용.
app.include_router(admin.router) # router 를 사용.
app.include_router(users.router) # router 를 사용.