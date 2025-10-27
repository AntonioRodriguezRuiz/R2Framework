# Initializes the FastAPI application and includes the main entry point.
# It also sets up the database connection and includes the necessary routers.
from fastapi import FastAPI
from contextlib import asynccontextmanager
import database.general as database
from gateway.agent import robot_exception_handler
from gateway.models import RobotExceptionRequest
from strands.telemetry import StrandsTelemetry
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to initialize and clean up the database connection.
    """
    strands_telemetry = StrandsTelemetry()
    strands_telemetry.setup_otlp_exporter()  # Send traces to OTLP endpoint
    strands_telemetry.setup_meter(
        enable_console_exporter=False, enable_otlp_exporter=True
    )  # Setup new meter provider and sets it as global

    logging.getLogger("strands").setLevel(logging.DEBUG)
    logging.basicConfig(
        format="%(levelname)s | %(name)s | %(message)s",
        filename="strands.log",
        filemode="a",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    await database.create_db_and_tables()
    yield
    await database.drop_db_and_tables()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI application!"}


@app.post("/robot_exception")
async def handle_robot_exception(request: RobotExceptionRequest):
    """
    Passes the exception to the robot exception handler for processing.
    """
    response = robot_exception_handler(request)
    return response
