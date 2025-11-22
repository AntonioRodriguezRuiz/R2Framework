# Initializes the FastAPI application and includes the main entry point.
# It also sets up the database connection and includes the necessary routers.
from fastapi import FastAPI, WebSocket
from scalar_fastapi import get_scalar_api_reference
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


@app.get("/scalar", include_in_schema=False)
async def root():
    return get_scalar_api_reference(
        # Your OpenAPI document
        openapi_url=app.openapi_url,
        # Avoid CORS issues (optional)
        scalar_proxy_url="https://proxy.scalar.com",
    )


@app.websocket("/robot_exception/ws")
async def handle_robot_exception(websocket: WebSocket):
    """
    Passes the exception to the robot exception handler for processing.
    """
    await websocket.accept()
    data = (
        await websocket.receive_json()
    )  # Will only accept one exception per connection
    request = RobotExceptionRequest(**data)
    response = await robot_exception_handler(request, websocket)
    await websocket.send_json({"type": "done", "content": response})
    await websocket.close()
    return
