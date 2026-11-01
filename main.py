"""
Punto de entrada principal para el Sistema de Auditoría IAM.
Inicia la aplicación de escritorio basada en PySide6.
"""
import sys

from PySide6.QtWidgets import QApplication

from src.auditoria_iam.ui.main_window import MainWindow


def main() -> None:
    """Función de arranque de la aplicación de escritorio."""
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Auditoría IAM")
    app.setOrganizationName("UPHARVEN C.A.")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

