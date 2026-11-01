from getpass import getpass

from src.auditoria_iam.database.repository import get_resources


user = input("Usuario de MySQL: ")
password = getpass("Contraseña de MySQL: ")

resources = get_resources(user, password)

print("\nIDENTIDADES REGISTRADAS")
print("-" * 40)

for resource in resources:
    print(f"ID: {resource['id']}")
    print(f"Identidad: {resource['display_name']}")
    print(f"Estado: {resource['resource_status']}")
    print(f"Origen: {resource['source_type']}")
    print("-" * 40)

print(f"Total de identidades: {len(resources)}")