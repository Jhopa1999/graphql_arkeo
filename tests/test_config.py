"""Pruebas de normalización de paginación y lectura de credenciales."""
import json
from unittest import mock

import config


def test_clamp_page_size_defaults_y_limites():
    assert config.clamp_page_size(None) == config.DEFAULT_PAGE_SIZE
    assert config.clamp_page_size(0) == config.DEFAULT_PAGE_SIZE
    assert config.clamp_page_size(-5) == config.DEFAULT_PAGE_SIZE
    assert config.clamp_page_size(50) == 50
    assert config.clamp_page_size(10_000) == config.MAX_PAGE_SIZE


def test_normalize_page():
    assert config.normalize_page(None) == 1
    assert config.normalize_page(0) == 1
    assert config.normalize_page(-3) == 1
    assert config.normalize_page(7) == 7


def test_get_db_credentials_lee_secret(monkeypatch):
    config.get_db_credentials.cache_clear()
    fake = {
        "host": "10.0.0.1",
        "port": "1433",
        "database": "seven",
        "username": "u",
        "password": "p",
    }
    fake_client = mock.Mock()
    fake_client.get_secret_value.return_value = {"SecretString": json.dumps(fake)}

    with mock.patch("boto3.client", return_value=fake_client):
        creds = config.get_db_credentials()

    assert creds["host"] == "10.0.0.1"
    assert creds["port"] == 1433  # convertido a int
    assert creds["database"] == "seven"
    config.get_db_credentials.cache_clear()


def test_get_db_credentials_falla_si_faltan_claves(monkeypatch):
    config.get_db_credentials.cache_clear()
    fake_client = mock.Mock()
    fake_client.get_secret_value.return_value = {
        "SecretString": json.dumps({"host": "x"})
    }
    with mock.patch("boto3.client", return_value=fake_client):
        try:
            config.get_db_credentials()
            assert False, "debía lanzar RuntimeError"
        except RuntimeError as e:
            assert "requeridas" in str(e)
    config.get_db_credentials.cache_clear()
