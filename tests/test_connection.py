"""
Pruebas unitarias para el módulo de conexión a base de datos (connection.py).
Utiliza mocks para validar la creación de conexiones, manejo de errores y cierre de recursos.
"""
import pytest
from unittest.mock import MagicMock, patch
import mysql.connector

from src.auditoria_iam.config.settings import DatabaseSettings
from src.auditoria_iam.database.connection import (
    get_connection,
    get_db_cursor,
    get_db_transaction
)


@pytest.fixture
def mock_settings():
    return DatabaseSettings(
        host="127.0.0.1",
        port=3306,
        name="auditoria_iam_upharven_pruebas",
        user="test_auditor",
        password="secret_password",
        timeout=10
    )


def test_get_connection_success(mock_settings):
    """Verifica que get_connection llame a mysql.connector.connect con los parámetros configurados."""
    with patch("mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        conn = get_connection(settings=mock_settings)

        assert conn == mock_conn
        mock_connect.assert_called_once_with(
            host="127.0.0.1",
            port=3306,
            database="auditoria_iam_upharven_pruebas",
            user="test_auditor",
            password="secret_password",
            connection_timeout=10,
            autocommit=False
        )


def test_get_connection_error_hides_password(mock_settings):
    """Verifica que los errores de conexión se capturen con mensaje controlado sin divulgar contraseñas ni detalles internos."""
    with patch("mysql.connector.connect") as mock_connect:
        mock_connect.side_effect = mysql.connector.Error(msg="Access denied for user 'test_auditor'@'127.0.0.1'")

        with pytest.raises(RuntimeError) as excinfo:
            get_connection(settings=mock_settings)

        err_msg = str(excinfo.value)
        assert "Error al conectar con la base de datos MySQL en 127.0.0.1:3306/auditoria_iam_upharven_pruebas" in err_msg
        assert "Access denied" not in err_msg
        assert "secret_password" not in err_msg


def test_get_db_cursor_closes_resources_on_success(mock_settings):
    """Verifica que get_db_cursor cierre tanto el cursor como la conexión al concluir con éxito."""
    with patch("src.auditoria_iam.database.connection.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with get_db_cursor(settings=mock_settings) as cursor:
            assert cursor == mock_cursor
            mock_conn.cursor.assert_called_once_with(dictionary=True)

        # Verificar cierres
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        # Verificar que NO se emitió commit (solo lectura)
        mock_conn.commit.assert_not_called()


def test_get_db_cursor_defensive_cleanup_on_cursor_error(mock_settings):
    """Verifica que la conexión se cierre incluso si connection.cursor() falla."""
    with patch("src.auditoria_iam.database.connection.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception("Fallo al crear cursor")
        mock_get_conn.return_value = mock_conn

        with pytest.raises(Exception) as excinfo:
            with get_db_cursor(settings=mock_settings):
                pass

        assert "Fallo al crear cursor" in str(excinfo.value)
        mock_conn.close.assert_called_once()


def test_get_db_transaction_commits_on_success(mock_settings):
    """Verifica que get_db_transaction realice commit y cierre recursos en éxito."""
    with patch("src.auditoria_iam.database.connection.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with get_db_transaction(settings=mock_settings) as cursor:
            assert cursor == mock_cursor

        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


def test_get_db_transaction_rollbacks_on_exception(mock_settings):
    """Verifica que get_db_transaction realice rollback y cierre recursos ante excepciones."""
    with patch("src.auditoria_iam.database.connection.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with pytest.raises(ValueError) as excinfo:
            with get_db_transaction(settings=mock_settings) as cursor:
                raise ValueError("Error durante operación transaccional")

        assert "Error durante operación" in str(excinfo.value)
        mock_conn.commit.assert_not_called()
        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

