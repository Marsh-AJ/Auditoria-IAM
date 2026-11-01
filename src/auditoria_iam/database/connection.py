"""
Módulo de Conexión a Base de Datos MySQL Server 9.6.
Proporciona funciones reutilizables y gestores de contexto con cierre defensivo.
"""
from contextlib import contextmanager
from typing import Generator, Optional
import mysql.connector
from mysql.connector.cursor import MySQLCursor
from mysql.connector.connection import MySQLConnection

from src.auditoria_iam.config.settings import DatabaseSettings, get_database_settings


def get_connection(
    user: Optional[str] = None,
    password: Optional[str] = None,
    settings: Optional[DatabaseSettings] = None,
    db_name: Optional[str] = None
) -> MySQLConnection:
    """
    Crea y retorna una nueva conexión a MySQL Server.
    
    Permite el uso de la configuración centralizada (por defecto) o la especificación
    de credenciales manuales para compatibilidad con scripts de prueba interactivos.
    """
    if settings is not None:
        cfg = settings
    elif user is not None and password is not None:
        # Modo interactivo / compatibilidad con scripts originales
        base_cfg = get_database_settings(db_name_override=db_name)
        cfg = DatabaseSettings(
            host=base_cfg.host,
            port=base_cfg.port,
            name=db_name or base_cfg.name,
            user=user,
            password=password,
            timeout=base_cfg.timeout
        )
    else:
        # Modo centralizado estándar desde .env
        cfg = get_database_settings(db_name_override=db_name)

    try:
        connection = mysql.connector.connect(
            host=cfg.host,
            port=cfg.port,
            database=cfg.name,
            user=cfg.user,
            password=cfg.password,
            connection_timeout=cfg.timeout,
            autocommit=False
        )
        return connection
    except mysql.connector.Error:
        # Mensaje controlado que no revela contraseñas, credenciales ni detalles internos del motor
        raise RuntimeError(
            f"Error al conectar con la base de datos MySQL en {cfg.host}:{cfg.port}/{cfg.name}. "
            "Verifique los parámetros de red y autenticación."
        ) from None
    except Exception:
        # Mensaje controlado para errores imprevistos sin divulgar excepciones internas
        raise RuntimeError(
            f"Fallo no esperado al intentar conectar con la base de datos MySQL en {cfg.host}:{cfg.port}/{cfg.name}."
        ) from None


@contextmanager
def get_db_cursor(
    dictionary: bool = True,
    db_name: Optional[str] = None,
    settings: Optional[DatabaseSettings] = None
) -> Generator[MySQLCursor, None, None]:
    """
    Gestor de contexto destinado a consultas de lectura.
    
    Abre una conexión y cursor nuevos, asegurando su cierre defensivo al finalizar.
    No realiza commit automático.
    """
    connection = get_connection(settings=settings, db_name=db_name)
    cursor = None
    try:
        cursor = connection.cursor(dictionary=dictionary)
        yield cursor
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        try:
            connection.close()
        except Exception:
            pass


@contextmanager
def get_db_transaction(
    dictionary: bool = True,
    db_name: Optional[str] = None,
    settings: Optional[DatabaseSettings] = None
) -> Generator[MySQLCursor, None, None]:
    """
    Gestor de contexto para transacciones de escritura.
    
    Ejecuta commit al finalizar el bloque con éxito y rollback obligatorio ante
    cualquier excepción no controlada, garantizando el cierre defensivo de recursos.
    """
    connection = get_connection(settings=settings, db_name=db_name)
    cursor = None
    try:
        cursor = connection.cursor(dictionary=dictionary)
        yield cursor
        connection.commit()
    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        try:
            connection.close()
        except Exception:
            pass
