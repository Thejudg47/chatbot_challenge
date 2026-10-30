class Roles:
    __roles_disponibles = [
    "Desarrollador Python Junior",
    "Desarrollador Web Frontend",
    "Integrador de APIs/Bots"
    ]

    @classmethod
    def obtener_roles(cls):
        # Retorna la lista de roles disponibles
        return cls.__roles_disponibles