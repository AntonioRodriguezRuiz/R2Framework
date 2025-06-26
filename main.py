# Initializes the FastAPI application and includes the main entry point.
# It also sets up the database connection and includes the necessary routers.
from fastapi import FastAPI
from contextlib import asynccontextmanager
import database.general as database
from gateway.agent import robot_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to initialize and clean up the database connection.
    """
    await database.create_db_and_tables()
    yield
    await database.drop_db_and_tables()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI application!"}


@app.post("/robot_exception")
async def handle_robot_exception(details: str):
    """
    Passes the exception to the robot exception handler for processing.
    """
    response = robot_exception_handler(details)
    return response
