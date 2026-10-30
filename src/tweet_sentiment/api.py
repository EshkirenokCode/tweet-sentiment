import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.responses import JSONResponse, RedirectResponse
from threadpoolctl import threadpool_limits

from tweet_sentiment import LABELS, __version__
from tweet_sentiment.artifact import load_artifact
from tweet_sentiment.encoder import TokenLimitError

MAX_BODY_BYTES = 8192


class BodyLimit:
    def __init__(self, app, limit=MAX_BODY_BYTES):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.limit:
                response = JSONResponse({"detail": "Request body exceeds 8192 bytes"}, 413)
                return await response(scope, receive, send)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(
        min_length=1,
        max_length=2000,
        description="English text; at most 2000 characters and 256 model tokens.",
        examples=["The update works really well."],
    )

    @field_validator("text")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Text must not be blank")
        return value


class PredictionResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"label": "positive", "model_version": __version__}]}
    )
    label: Literal["negative", "neutral", "positive"]
    model_version: str


def create_app(artifact_dir=None):
    directory = Path(artifact_dir or os.getenv("MODEL_DIR", "artifacts"))

    @asynccontextmanager
    async def lifespan(app):
        app.state.model = None
        app.state.metadata = None
        with threadpool_limits(limits=1):
            try:
                app.state.model, app.state.metadata = load_artifact(directory)
            except Exception as error:
                logging.getLogger(__name__).error("Model unavailable: %s", type(error).__name__)
            yield

    app = FastAPI(
        title="Tweet sentiment",
        version=__version__,
        lifespan=lifespan,
        description="Three-class sentiment for English text. No calibrated confidence.",
    )
    app.add_middleware(BodyLimit)

    @app.get("/", include_in_schema=False)
    def index():
        return RedirectResponse("/docs")

    @app.get("/health")
    def health():
        return {"status": "alive"}

    @app.get("/ready")
    def ready():
        if app.state.model is None:
            raise HTTPException(503, "Model artifact unavailable or incompatible")
        return {"status": "ready", "model_version": app.state.metadata["model_version"]}

    @app.post(
        "/predict",
        response_model=PredictionResponse,
        responses={
            422: {"description": "Invalid or empty normalized input"},
            503: {"description": "Model unavailable"},
        },
        response_description="Predicted label and evaluated model version",
    )
    def predict(request: PredictionRequest):
        ready()
        if not app.state.model.named_steps["normalize"].transform([request.text])[0]:
            raise HTTPException(422, "Text contains no usable tokens after normalization")
        try:
            label = int(app.state.model.predict([request.text])[0])
        except TokenLimitError as error:
            raise HTTPException(422, str(error)) from error
        return {"label": LABELS[label], "model_version": app.state.metadata["model_version"]}

    return app


app = create_app()
