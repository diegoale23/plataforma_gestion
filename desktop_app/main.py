import tkinter as tk
import psycopg2

# Configuración de la base de datos
DB_CONFIG = {
    'dbname': 'plataforma_db',
    'user': 'postgres',
    'password': 'dacp18419361',
    'host': 'localhost',
    'port': '5432',
}

def create_offer():
    # Lógica para crear una oferta en la base de datos
    pass

def read_offers():
    # Lógica para leer ofertas de la base de datos
    pass

def update_offer():
    # Lógica para actualizar una oferta en la base de datos
    pass

def delete_offer():
    # Lógica para eliminar una oferta de la base de datos
    pass

# Interfaz gráfica con Tkinter
root = tk.Tk()
# ... (Crear botones y campos de entrada)
root.mainloop()