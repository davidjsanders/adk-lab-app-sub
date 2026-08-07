import contextlib
import os
from collections.abc import AsyncIterator
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from a2a.server.tasks import InMemoryTaskStore

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


# Initialize standard ADK FastAPI application
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    a2a=True,
    lifespan=lifespan,
)

app.title = "sysman-ops-agent"
app.description = "API endpoint for interacting with the SysMan Operations ADK Agent"
