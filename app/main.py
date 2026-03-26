from fastapi import FastAPI
from app.db.database import engine
from app.db.models import Base
from app.api import datasets

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(datasets.router)