import sqlprobe


def test_package_imports():
    assert sqlprobe is not None


def test_package_exposes_version():
    assert hasattr(sqlprobe, "__version__")
    assert sqlprobe.__version__ == "0.0.1"


def test_cli_app_imports():
    from sqlprobe.cli.main import app

    assert app is not None
