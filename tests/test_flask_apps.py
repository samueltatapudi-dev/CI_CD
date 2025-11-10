import importlib.util
from pathlib import Path
import types
from jinja2 import FileSystemLoader
import pytest


BASE_DIR = Path(__file__).resolve().parent.parent


def load_module_from_path(path: Path) -> types.ModuleType:
    # Use a unique module name per path to avoid collisions affecting Flask's import_name
    safe_name = (
        "testapps_" + "_".join(path.parts[-3:]).replace("-", "_").replace(".", "_")
    )
    spec = importlib.util.spec_from_file_location(safe_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


# Define the flask apps to test and their capabilities
APP_SPECS = [
    {
        "name": "ACEest_Fitness",
        "path": BASE_DIR / "flask_apps" / "ACEest_Fitness" / "app.py",
        "form_type": "basic",  # fields: workout, duration
        "requires_positive": False,
        "routes": {"summary": False, "chart": False, "diet": False, "progress": False, "progress_png": False},
    },
    {
        "name": "ACEest_Fitness-V1.1",
        "path": BASE_DIR / "flask_apps" / "ACEest_Fitness-V1.1" / "app.py",
        "form_type": "category",  # fields: category, exercise, duration
        "requires_positive": False,
        "routes": {"summary": True, "chart": False, "diet": False, "progress": False, "progress_png": False},
    },
    {
        "name": "ACEest_Fitness-V1.2",
        "path": BASE_DIR / "flask_apps" / "ACEest_Fitness-V1.2" / "app.py",
        "form_type": "category",
        "requires_positive": False,
        "routes": {"summary": False, "chart": True, "diet": True, "progress": False, "progress_png": False},
    },
    {
        "name": "ACEest_Fitness-V1.2.1",
        "path": BASE_DIR / "flask_apps" / "ACEest_Fitness-V1.2.1" / "app.py",
        "form_type": "category",
        "requires_positive": False,
        "routes": {"summary": False, "chart": False, "diet": False, "progress": True, "progress_png": True},
    },
    {
        "name": "ACEest_Fitness-V1.2.2",
        "path": BASE_DIR / "flask_apps" / "ACEest_Fitness-V1.2.2" / "app.py",
        "form_type": "category",
        "requires_positive": True,
        "routes": {"summary": False, "chart": False, "diet": False, "progress": True, "progress_png": True},
    },
    {
        "name": "ACEest_Fitness-V1.2.3",
        "path": BASE_DIR / "flask_apps" / "ACEest_Fitness-V1.2.3" / "app.py",
        "form_type": "category",
        "requires_positive": True,
        "routes": {"summary": True, "chart": False, "diet": False, "progress": True, "progress_png": True},
    },
]


@pytest.fixture(params=APP_SPECS, ids=[s["name"] for s in APP_SPECS])
def app_env(request):
    spec = request.param
    module = load_module_from_path(Path(spec["path"]))
    app = getattr(module, "app", None)
    if app is None:
        raise AssertionError(f"No Flask app found in {spec['path']}")
    app.config.update(TESTING=True)
    # Ensure templates resolve correctly regardless of import_name root
    templates_dir = Path(spec["path"]).parent / "templates"
    if templates_dir.exists():
        app.jinja_loader = FileSystemLoader(str(templates_dir))
    client = app.test_client()
    # Ensure clean state
    client.post("/clear")
    yield {"client": client, "spec": spec, "module": module}
    # Clean up after each test
    client.post("/clear")


def _add_entry(client, spec, name="Push Ups", duration="15"):
    if spec["form_type"] == "basic":
        return client.post("/add", data={"workout": name, "duration": duration})
    else:
        return client.post(
            "/add",
            data={"category": "Workout", "exercise": name, "duration": duration},
        )


def _index_contains(client, text: str) -> bool:
    r = client.get("/")
    return text in r.get_data(as_text=True)


def test_index_ok(app_env):
    client = app_env["client"]
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("Content-Type", "")


def test_add_get_not_allowed(app_env):
    client = app_env["client"]
    r = client.get("/add")
    assert r.status_code in (405, 404)  # If route is POST-only, 405; some frameworks return 405


def test_add_missing_fields_rejected(app_env):
    client, spec = app_env["client"], app_env["spec"]
    if spec["form_type"] == "basic":
        r = client.post("/add", data={"workout": "TestOnly"})
    else:
        r = client.post("/add", data={"category": "Workout", "exercise": "TestOnly"})
    assert r.status_code in (302, 303)
    assert not _index_contains(client, "TestOnly")


def test_add_invalid_duration_rejected(app_env):
    client, spec = app_env["client"], app_env["spec"]
    r = _add_entry(client, spec, name="InvalidDur", duration="abc")
    assert r.status_code in (302, 303)
    assert not _index_contains(client, "InvalidDur")


def test_add_negative_duration_handling(app_env):
    client, spec = app_env["client"], app_env["spec"]
    r = _add_entry(client, spec, name="NegCase", duration="-5")
    if spec["requires_positive"]:
        assert r.status_code in (302, 303)
        assert not _index_contains(client, "NegCase")
    else:
        # Accepted in older variants; should show up on index
        assert r.status_code in (302, 303)
        assert _index_contains(client, "NegCase")


def test_add_and_clear_flow(app_env):
    client, spec = app_env["client"], app_env["spec"]
    r = _add_entry(client, spec, name="SessionA", duration="10")
    assert r.status_code in (302, 303)
    assert _index_contains(client, "SessionA")
    # Clear and verify removal
    rc = client.post("/clear")
    assert rc.status_code in (302, 303)
    assert not _index_contains(client, "SessionA")


def test_unicode_and_escaping(app_env):
    client, spec = app_env["client"], app_env["spec"]
    # Unicode
    r = _add_entry(client, spec, name="Plank – Core ✅", duration="3")
    assert r.status_code in (302, 303)
    assert _index_contains(client, "Plank – Core ✅")
    # Template injection not executed
    inj = "{{7*7}}"
    r = _add_entry(client, spec, name=inj, duration="2")
    assert r.status_code in (302, 303)
    body = client.get("/").get_data(as_text=True)
    assert "49" not in body


def test_large_input(app_env):
    client, spec = app_env["client"], app_env["spec"]
    long_name = "X" * 200
    r = _add_entry(client, spec, name=long_name, duration="1")
    assert r.status_code in (302, 303)
    assert _index_contains(client, long_name)


def test_optional_routes_exist(app_env):
    client, spec = app_env["client"], app_env["spec"]
    routes = spec["routes"]
    if routes.get("summary"):
        r = client.get("/summary")
        assert r.status_code == 200
    if routes.get("chart"):
        r = client.get("/chart")
        assert r.status_code == 200
    if routes.get("diet"):
        r = client.get("/diet")
        assert r.status_code == 200
    if routes.get("progress"):
        r = client.get("/progress")
        assert r.status_code == 200
    if routes.get("progress_png"):
        r = client.get("/progress.png")
        assert r.status_code == 200
        assert r.headers.get("Content-Type", "").startswith("image/png")
