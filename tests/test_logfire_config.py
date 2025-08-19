import importlib
import sys
import types


def test_logfire_configured_with_token(monkeypatch):
    stub = types.ModuleType("logfire")
    called = {}

    def configure(**kwargs):
        called["configure"] = kwargs

    def instrument_pydantic_ai():
        called["instrument_ai"] = True

    def instrument_httpx():
        called["instrument_httpx"] = True

    stub.configure = configure
    stub.instrument_pydantic_ai = instrument_pydantic_ai
    stub.instrument_httpx = instrument_httpx

    monkeypatch.setitem(sys.modules, "logfire", stub)
    monkeypatch.setenv("LOGFIRE_TOKEN", "token123")

    import app
    importlib.reload(app)

    assert app.logfire is stub
    assert called["configure"]["token"] == "token123"
    assert called["instrument_ai"]
