"""
Catálogo interactivo de Controles de Seguridad ISO/IEC 27001:2022 y vinculación con reglas IAM.
Proporciona la base de conocimiento estructurada para la consulta detallada de controles,
sus objetivos, aspectos técnicos auditados en AWS IAM, criterios de evaluación y alcance delimitado.
"""
from typing import Any, Dict, List, Optional

# Enlace al documento externo de referencia de la norma alojado en Internet Archive
EXTERNAL_ISO_URL = "https://ia801902.us.archive.org/28/items/iso-iec-27001-2022-standard/ISO%20IEC%2027001%202022%20Standard.pdf"

# Catálogo exhaustivo de los cuatro controles abordados en el prototipo
ISO_CONTROLS_DETAILS: Dict[str, Dict[str, Any]] = {
    "5.15": {
        "code": "5.15",
        "name": "Control de acceso",
        "reference": "ISO/IEC 27001:2022, Anexo A, Control 5.15 (Controles de las personas y organizacionales)",
        "rule_code": "IAM-001",
        "summary": (
            "Orientación sobre el establecimiento, mantenimiento y aplicación de reglas de control de acceso lógico, "
            "asegurando que el acceso a la información y a los recursos de procesamiento se autorice de acuerdo con "
            "los requisitos de seguridad y las funciones asignadas en la organización."
        ),
        "security_objective": (
            "Garantizar que únicamente los usuarios y entidades autorizadas puedan acceder a los recursos del sistema, "
            "evitando accesos no previstos o modificaciones no aprobadas a través de asignaciones incoherentes de perfiles."
        ),
        "technical_aspect": (
            "Inspección automatizada de la correspondencia entre las membresías de grupos asignadas a usuarios IAM y "
            "las relaciones de confianza (AssumeRolePolicyDocument) configuradas en roles IAM, frente a los perfiles "
            "de acceso de referencia formalmente autorizados."
        ),
        "verification_criteria": [
            (
                "C15-01",
                "Verificación de grupos asignados: Compara los grupos reales del usuario frente a los grupos esperados del perfil autorizado."
            ),
            (
                "C15-02",
                "Verificación de confianza en roles: Compara las entidades principales (Principal) de la política de asunción frente a las autorizadas."
            )
        ],
        "status_meanings": {
            "Conforme": "Todos los grupos asignados al usuario o las entidades de confianza del rol coinciden de manera exacta con el perfil de acceso autorizado.",
            "Hallazgo": "Se detectan grupos adicionales, fuera de perfil o relaciones de confianza con entidades no autorizadas en el catálogo de referencia.",
            "No evaluable": "La identidad carece de un perfil de acceso asignado, la entidad no se encuentra registrada o los metadatos de grupos/confianza son incompletos o malformados."
        },
        "scope_notice": (
            "La evaluación se limita estrictamente a la verificación lógica de membresías de grupos IAM y entidades principales de confianza en AWS IAM. "
            "No evalúa procedimientos de autorización fuera de banda ni constituye una certificación de cumplimiento del control organizacional ISO 27001."
        )
    },
    "5.16": {
        "code": "5.16",
        "name": "Gestión de identidades",
        "reference": "ISO/IEC 27001:2022, Anexo A, Control 5.16 (Controles de las personas y organizacionales)",
        "rule_code": "IAM-002",
        "summary": (
            "Pautas sobre la gestión del ciclo de vida de las identidades digitales en los sistemas de información, "
            "incluyendo la asignación, supervisión, modificación oportuna y revocación o desactivación de identidades "
            "que han dejado de operar o que presentan períodos prolongados de inactividad."
        ),
        "security_objective": (
            "Reducir la superficie de ataque previniendo accesos indebidos a través de cuentas huérfanas, credenciales "
            "abandonadas o identidades sin supervisión activa en la infraestructura de nube."
        ),
        "technical_aspect": (
            "Evaluación automatizada en dos vertientes técnicas: 1) Verificación del estado formal de vigencia y activación "
            "('resource_status') para identificar identidades activas o deshabilitadas con deficiencias de desprovisionamiento, "
            "y 2) Análisis de los metadatos normalizados de actividad frente al umbral operativo configurable del prototipo "
            "(90 días continuos por defecto)."
        ),
        "verification_criteria": [
            (
                "C16-01",
                "Estado de vigencia y activación de la identidad: Evalúa el atributo 'resource_status' diferenciando "
                "identidades activas de inactivas o deshabilitadas. Una identidad inactiva no genera automáticamente un Hallazgo: "
                "requiere evidencia explícita de una deficiencia de desprovisionamiento; si no existe evidencia suficiente, el resultado es No evaluable."
            ),
            (
                "C16-02",
                "Actividad reciente de la identidad: Evalúa los metadatos normalizados de actividad disponibles en el recurso admitidos por "
                "el motor ('last_access_days', 'days_since_last_access', 'days_inactive', 'inactivity_days'), comparando los días de inactividad "
                "frente al umbral configurable del prototipo (90 días por defecto)."
            )
        ],
        "status_meanings": {
            "Conforme": (
                "En C16-01: La identidad se encuentra registrada en estado activo o habilitado ('active', 'activo', 'enabled'). "
                "En C16-02: La identidad registra actividad reciente dentro del umbral configurable de inactividad (90 días por defecto)."
            ),
            "Hallazgo": (
                "En C16-01: La identidad se encuentra inactiva o deshabilitada con deficiencia técnica comprobada en el proceso de desprovisionamiento. "
                "En C16-02: La identidad registra una inactividad prolongada que supera el umbral operativo definido para el prototipo (más de 90 días por defecto)."
            ),
            "No evaluable": (
                "En C16-01: El atributo 'resource_status' está ausente o no reconocido, o la identidad está inactiva sin metadatos suficientes "
                "para discernir entre suspensión temporal y deficiencia de desprovisionamiento. "
                "En C16-02: Metadatos de actividad ausentes, inválidos o con tipos de datos no admitidos por el extractor de inactividad."
            )
        },
        "scope_notice": (
            "La evaluación se basa en el estado formal del recurso y los metadatos normalizados de actividad provistos al motor. "
            "No abarca políticas de recursos humanos, procesos de baja laboral fuera de banda ni constituye una certificación de cumplimiento del control organizacional ISO 27001."
        )
    },
    "5.18": {
        "code": "5.18",
        "name": "Derechos de acceso",
        "reference": "ISO/IEC 27001:2022, Anexo A, Control 5.18 (Controles de las personas y organizacionales)",
        "rule_code": "IAM-003",
        "summary": (
            "Directrices para la provisión, ajuste, revisión y revocación periódica de los derechos de acceso lógico, "
            "basándose en el principio de mínimo privilegio y asegurando que las identidades no dispongan de permisos "
            "superfluos o desproporcionados para sus responsabilidades."
        ),
        "security_objective": (
            "Impedir que identidades en la nube operen con privilegios excesivos o irrestrictos, mitigando el impacto "
            "ante eventuales compromisos de credenciales o errores operativos."
        ),
        "technical_aspect": (
            "Análisis sintáctico riguroso de documentos JSON de políticas IAM (administradas e integradas, directas o por grupos), "
            "buscando la coexistencia de comodines globales ('*') en sentencias con efecto 'Allow'."
        ),
        "verification_criteria": [
            (
                "C18-01",
                "Detección de patrones excesivamente amplios: Identifica sentencias con 'Effect: Allow' que contienen simultáneamente 'Action: *' y 'Resource: *'."
            )
        ],
        "status_meanings": {
            "Conforme": "Todas las políticas asignadas delimitan acciones y recursos de forma acotada sin combinar comodines globales simultáneos.",
            "Hallazgo": "Se detecta al menos una política con sentencias permisivas que contienen el patrón de comodines globales ('Action: *' y 'Resource: *').",
            "No evaluable": "Documento JSON de política malformado, sintaxis no normalizable o política asignada cuyo documento no pudo recuperarse del proveedor."
        },
        "scope_notice": (
            "La regla evalúa de forma estrictamente limitada el patrón técnico de comodines globales (Action: *, Resource: *) en políticas JSON de AWS IAM. "
            "No evalúa la gestión de accesos privilegiados (control 8.2), ni roles de emergencia, ni constituye una certificación de cumplimiento ISO 27001."
        )
    },
    "8.5": {
        "code": "8.5",
        "name": "Autenticación segura",
        "reference": "ISO/IEC 27001:2022, Anexo A, Control 8.5 (Controles tecnológicos)",
        "rule_code": "IAM-004",
        "summary": (
            "Requisitos tecnológicos y operativos para garantizar una autenticación robusta y segura de usuarios, "
            "empleando tecnologías acordes con el nivel de riesgo de acceso al sistema, tales como la autenticación multifactor."
        ),
        "security_objective": (
            "Verificar fehacientemente la identidad de los usuarios humanos autorizados para acceder a la consola o servicios de nube, "
            "protegiendo las credenciales frente a ataques de fuerza bruta, phishing o suplantación de identidad."
        ),
        "technical_aspect": (
            "Verificación técnica de la habilitación y activación efectiva de mecanismos de autenticación multifactor (MFA: dispositivos virtuales, hardware o FIDO) "
            "en usuarios interactivos activos de AWS IAM."
        ),
        "verification_criteria": [
            (
                "C85-01",
                "Autenticación multifactor obligatoria: Verifica que los usuarios humanos activos cuenten con el atributo 'mfa_active = True'."
            )
        ],
        "status_meanings": {
            "Conforme": "El usuario activo tiene configurado y habilitado al menos un dispositivo de autenticación multifactor.",
            "Hallazgo": "El usuario activo carece de autenticación multifactor habilitada ('mfa_active = False').",
            "No evaluable": "Metadatos de MFA ausentes, no booleanos o incompletos. (Los roles IAM quedan expresamente excluidos de esta evaluación al ser identidades programáticas temporales sin credenciales de inicio interactivo)."
        },
        "scope_notice": (
            "La verificación se limita exclusivamente al indicador técnico de MFA habilitado en identidades de usuario en AWS IAM. "
            "No evalúa la complejidad de contraseñas, políticas de rotación ni constituye una certificación de cumplimiento ISO 27001."
        )
    }
}


def get_control_detail(code: str) -> Optional[Dict[str, Any]]:
    """Recupera los datos estructurados de un control por su código (ej. '5.15')."""
    return ISO_CONTROLS_DETAILS.get(code)


def get_all_controls() -> List[Dict[str, Any]]:
    """Devuelve la lista ordenada de todos los controles considerados."""
    return list(ISO_CONTROLS_DETAILS.values())
