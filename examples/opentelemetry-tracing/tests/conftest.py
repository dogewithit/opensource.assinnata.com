"""Configure a global tracer provider with an in-memory span exporter."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXAMPLE_ROOT))

_EXPORTER = InMemorySpanExporter()


@pytest.fixture(scope="session", autouse=True)
def _provider():
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(_EXPORTER))
    trace.set_tracer_provider(provider)  # global, set once per process
    yield


@pytest.fixture
def spans():
    """Finished spans captured during a test; cleared before each."""
    _EXPORTER.clear()
    return _EXPORTER
