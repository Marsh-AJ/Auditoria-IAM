"""
Excepciones controladas para la Fuente de Datos AWS IAM.
Garantiza el manejo seguro de errores sin exponer credenciales ni información confidencial.
"""


class AWSIAMDataSourceError(Exception):
    """Excepción base para errores en la fuente de datos AWS IAM."""
    pass


class AWSIAMAuthenticationError(AWSIAMDataSourceError):
    """Excepción para errores de autenticación o credenciales ausentes/inválidas en AWS."""
    pass


class AWSIAMPermissionError(AWSIAMDataSourceError):
    """Excepción para errores de permisos insuficientes (AccessDenied) en AWS IAM."""
    pass


class AWSIAMConnectionError(AWSIAMDataSourceError):
    """Excepción para fallas de conectividad o resolución de endpoint en AWS."""
    pass

