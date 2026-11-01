"""
Pruebas unitarias para el módulo de configuración centralizada (settings.py).
Verifica la lectura, validación y manejo de errores sin depender de credenciales reales.
"""
import os
import pytest
from unittest.mock import patch

from src.auditoria_iam.config.settings import DatabaseSettings, get_database_settings


def test_get_database_settings_success():
    """Comprueba la carga exitosa de configuración con variables de entorno válidas."""
    mock_env = {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "3306",
        "DB_NAME": "auditoria_iam_upharven",
        "DB_USER": "test_user",
        "DB_PASSWORD": "mock_password",
        "DB_CONNECT_TIMEOUT": "15"
    }
    with patch.dict(os.environ, mock_env, clear=True):
        settings = get_database_settings()
        assert settings.host == "127.0.0.1"
        assert settings.port == 3306
        assert settings.name == "auditoria_iam_upharven"
        assert settings.user == "test_user"
        assert settings.password == "mock_password"
        assert settings.timeout == 15


def test_get_database_settings_db_name_override():
    """Comprueba que se pueda seleccionar una base de datos alternativa (ej. pruebas)."""
    mock_env = {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "3306",
        "DB_NAME": "auditoria_iam_upharven",
        "DB_USER": "test_user",
        "DB_PASSWORD": "mock_password"
    }
    with patch.dict(os.environ, mock_env, clear=True):
        settings = get_database_settings(db_name_override="auditoria_iam_upharven_pruebas")
        assert settings.name == "auditoria_iam_upharven_pruebas"


@pytest.mark.parametrize("missing_var", ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"])
def test_get_database_settings_missing_required_variables(missing_var):
    """Comprueba que se lance ValueError si falta alguna variable obligatoria."""
    mock_env = {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "3306",
        "DB_NAME": "auditoria_iam_upharven",
        "DB_USER": "test_user",
        "DB_PASSWORD": "mock_password"
    }
    del mock_env[missing_var]
    with patch.dict(os.environ, mock_env, clear=True):
        with pytest.raises(ValueError) as excinfo:
            get_database_settings()
        assert missing_var in str(excinfo.value)
        # Garantizar que no se expongan contraseñas
        assert "mock_password" not in str(excinfo.value)


@pytest.mark.parametrize("invalid_port", ["-1", "0", "70000", "not_a_number"])
def test_get_database_settings_invalid_port(invalid_port):
    """Comprueba que se rechacen puertos fuera del rango 1-65535 o no enteros."""
    mock_env = {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": invalid_port,
        "DB_NAME": "auditoria_iam_upharven",
        "DB_USER": "test_user",
        "DB_PASSWORD": "mock_password"
    }
    with patch.dict(os.environ, mock_env, clear=True):
        with pytest.raises(ValueError) as excinfo:
            get_database_settings()
        assert "DB_PORT" in str(excinfo.value)


@pytest.mark.parametrize("invalid_timeout", ["-5", "0", "abc"])
def test_get_database_settings_invalid_timeout(invalid_timeout):
    """Comprueba que se rechacen timeouts menores o iguales a 0 o no enteros."""
    mock_env = {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "3306",
        "DB_NAME": "auditoria_iam_upharven",
        "DB_USER": "test_user",
        "DB_PASSWORD": "mock_password",
        "DB_CONNECT_TIMEOUT": invalid_timeout
    }
    with patch.dict(os.environ, mock_env, clear=True):
        with pytest.raises(ValueError) as excinfo:
            get_database_settings()
        assert "DB_CONNECT_TIMEOUT" in str(excinfo.value)

