from typing import Annotated
from fastapi.params import Depends
from sqlmodel import SQLModel, Session, create_engine
from gateway.models import * # Needed for SQLModel to recognize the models defined in gateway.models
from tools.models import * # Needed for SQLModel to recognize the models defined in tools.models
from settings import POSTGRES_URL

# Database one: General purpose, postgresql

postgres_url = POSTGRES_URL

general_engine = create_engine(postgres_url)

async def create_db_and_tables():
    SQLModel.metadata.create_all(general_engine)

async def drop_db_and_tables():
    SQLModel.metadata.drop_all(general_engine)

def get_session():
    with Session(general_engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
