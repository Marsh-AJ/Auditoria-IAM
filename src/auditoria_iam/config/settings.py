"""
Módulo de Configuración Centralizada del Sistema de Auditoría IAM.
Carga y valida variables de entorno desde el archivo .env sin exponer credenciales.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Localización segura del archivo .env en la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

# Cargar variables de entorno si el archivo existe en disco
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=False)


@dataclass(frozen=True)
class DatabaseSettings:
    """Configuración inmutable para la conexión a MySQL Server."""
    host: str
    port: int
    name: str
    user: str
    password: str
    timeout: int = 10


def get_database_settings(
    db_name_override: Optional[str] = None,
    env_file_path: Optional[Path] = None
) -> DatabaseSettings:
    """
    Obtiene y valida la configuración de base de datos desde las variables de entorno.
    
    Permite especificar un nombre de base de datos alternativo (por ejemplo, la base de pruebas)
    o una ruta de archivo .env personalizada sin modificar permanentemente el código fuente.
    """
    if env_file_path and Path(env_file_path).exists():
        load_dotenv(dotenv_path=env_file_path, override=False)

    host = os.getenv("DB_HOST", "").strip()
    user = os.getenv("DB_USER", "").strip()
    password = os.getenv("DB_PASSWORD", "")
    db_name = (db_name_override or os.getenv("DB_NAME", "")).strip()
    raw_port = os.getenv("DB_PORT", "3306").strip()
    raw_timeout = os.getenv("DB_CONNECT_TIMEOUT", "10").strip()

    # Validaciones de presencia obligatoria sin exponer valores sensibles
    if not host:
        raise ValueError("Configuración inválida: La variable DB_HOST no está definida o está vacía.")
    if not db_name:
        raise ValueError("Configuración inválida: La variable DB_NAME no está definida o está vacía.")
    if not user:
        raise ValueError("Configuración inválida: La variable DB_USER no está definida o está vacía.")
    if not password:
        raise ValueError("Configuración inválida: La variable DB_PASSWORD no está definida o está vacía.")

    # Validación de puerto
    try:
        port = int(raw_port)
        if not (1 <= port <= 65535):
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError(f"Configuración inválida: DB_PORT debe ser un entero entre 1 y 65535 (recibido: '{raw_port}').")

    # Validación de timeout
    try:
        timeout = int(raw_timeout)
        if timeout <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError(f"Configuración inválida: DB_CONNECT_TIMEOUT debe ser un entero mayor a 0 (recibido: '{raw_timeout}').")

    return DatabaseSettings(
        host=host,
        port=port,
        name=db_name,
        user=user,
        password=password,
        timeout=timeout
    )
