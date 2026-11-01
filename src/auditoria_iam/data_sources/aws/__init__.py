"""
Paquete Fuente de Datos AWS IAM mediante Boto3 para Auditoría ISO/IEC 27001.
"""
from src.auditoria_iam.data_sources.aws.adapter import (
    AWSIAMDataSource,
    READ_ONLY_OPERATIONS,
)
from src.auditoria_iam.data_sources.aws.exceptions import (
    AWSIAMAuthenticationError,
    AWSIAMConnectionError,
    AWSIAMDataSourceError,
    AWSIAMPermissionError,
)

__all__ = [
    "AWSIAMDataSource",
    "AWSIAMDataSourceError",
    "AWSIAMAuthenticationError",
    "AWSIAMPermissionError",
    "AWSIAMConnectionError",
    "READ_ONLY_OPERATIONS",
]

