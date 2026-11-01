from getpass import getpass

from src.auditoria_iam.database.connection import get_connection
import mysql.connector


user = input("Usuario de MySQL: ")
password = getpass("Contraseña de MySQL: ")

try:
    connection = get_connection(user, password)

    if connection.is_connected():
        print("¡Conexión exitosa con MySQL!")

except mysql.connector.Error as error:
    print(f"Error al conectar con MySQL: {error}")

finally:
    if "connection" in locals() and connection.is_connected():
        connection.close()
        print("Conexión cerrada.")