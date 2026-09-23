import contextlib
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import Config
from .radio import make_radio
from .service import HelpPointService


class BrowserSubmission(BaseModel):
    type: str

    # Keep browser payload flexible until shared/codes.json and the final SRS
    # settle the exact UI -> wire-field contract.
    status: Any = None
    people: Any = None
    name: Any = None

    resource: Any = None
    quantity: Any = None
    urgency: Any = None
    notes: Any = None

    severity: Any = None
    condition: Any = None
    condition_code: Any = None
    patient_name: Any = None
    patient_age: Any = None

    conscious: Any = None
    breathing: Any = None
    location: Any = None


def create_app(config: Config | None = None) -> FastAPI:
    config = config or Config()
    radio = make_radio(config.radio)
    service = HelpPointService(config, radio)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            service.close()

    app = FastAPI(title="MeshAid Help Point", lifespan=lifespan)
    app.state.service = service

    @app.get("/api/status")
    def status():
        return service.status()


    @app.get("/api/queue")
    def queue_status():
        return service.queue_status()


    @app.post("/api/messages")
    def submit(body: BrowserSubmission):
        try:
            return service.submit_browser_request(
                body.model_dump(exclude_none=True)
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        
    return app

    
