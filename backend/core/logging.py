"""
Structured logging with Loguru — request correlation IDs and distributed tracing
"""
import os
import sys
import uuid
import contextvars
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


# Context variables for distributed tracing
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")
span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("span_id", default="")
job_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("job_id", default="")


def setup_logging():
    logger.remove()

    # Console — human-readable in dev, JSON-like in prod
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<magenta>trace:{extra[trace_id]}</magenta> | "
        "<magenta>span:{extra[span_id]}</magenta> | "
        "<magenta>job:{extra[job_id]}</magenta> | "
        "<level>{message}</level>"
    )
    logger.add(
        sys.stdout,
        format=log_format,
        level="INFO",
        colorize=True,
        enqueue=True,
    )

    # File — always JSON, rotated
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/app.log",
        rotation="50 MB",
        retention="30 days",
        compression="zip",
        level="INFO",
        serialize=True,  # JSON output
        enqueue=True,    # thread-safe
    )


def get_trace_id() -> str:
    """Get current trace ID from context."""
    return trace_id_var.get("")


def get_span_id() -> str:
    """Get current span ID from context."""
    return span_id_var.get("")


def get_job_id() -> str:
    """Get current job ID from context."""
    return job_id_var.get("")


class TracingContext:
    """Context manager for distributed tracing spans."""

    def __init__(self, span_name: str, job_id: str = ""):
        self.span_name = span_name
        self.job_id = job_id
        self.span_id = str(uuid.uuid4())[:8]
        self.parent_span_id = get_span_id()

    def __enter__(self):
        # Set new span context
        span_id_var.set(self.span_id)
        if self.job_id:
            job_id_var.set(self.job_id)

        # Log with trace context
        logger.bind(
            trace_id=get_trace_id(),
            span_id=self.span_id,
            job_id=self.job_id,
        ).info(f"→ Span: {self.span_name}")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore parent span
        if self.parent_span_id:
            span_id_var.set(self.parent_span_id)

        # Log span completion
        if exc_type:
            logger.bind(
                trace_id=get_trace_id(),
                span_id=self.span_id,
                job_id=self.job_id,
            ).error(f"← Span failed: {self.span_name} - {exc_val}")
        else:
            logger.bind(
                trace_id=get_trace_id(),
                span_id=self.span_id,
                job_id=self.job_id,
            ).info(f"← Span complete: {self.span_name}")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Adds a per-request correlation ID and logs every request/response."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        trace_id = str(uuid.uuid4())[:16]

        # Set trace context
        trace_id_var.set(trace_id)
        span_id_var.set(request_id)

        with logger.contextualize(request_id=request_id, trace_id=trace_id, span_id=request_id):
            logger.info(f"→ {request.method} {request.url.path}")
            try:
                response = await call_next(request)
                logger.info(f"← {response.status_code} {request.url.path}")
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Trace-ID"] = trace_id
                return response
            except Exception as exc:
                logger.exception(f"Unhandled error on {request.url.path}: {exc}")
                raise
