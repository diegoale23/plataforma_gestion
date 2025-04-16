# desktop_app/main.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Configura el entorno de Django antes de cualquier importación de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main_project.settings')

import django
django.setup()

# Importaciones de Django después de django.setup()
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from desktop_app.models import Project, Task

# Variable global para almacenar el usuario autenticado
authenticated_user = None

# Función para abrir la ventana de inicio de sesión
def open_login_window():
    login_window = tk.Toplevel(root)
    login_window.title("Iniciar Sesión")
    login_window.geometry("300x200")

    tk.Label(login_window, text="Usuario:").pack(pady=5)
    entry_username = tk.Entry(login_window)
    entry_username.pack(pady=5)

    tk.Label(login_window, text="Contraseña:").pack(pady=5)
    entry_password = tk.Entry(login_window, show="*")
    entry_password.pack(pady=5)

    def login():
        global authenticated_user
        username = entry_username.get()
        password = entry_password.get()

        user = authenticate(username=username, password=password)
        if user is not None:
            authenticated_user = user
            messagebox.showinfo("Inicio de Sesión", f"Bienvenido, {user.username}!")
            login_window.destroy()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas. Inténtalo de nuevo.")

    tk.Button(login_window, text="Iniciar Sesión", command=login).pack(pady=10)

# Función para abrir la ventana de gestión de proyectos
def open_project_management_window():
    if authenticated_user is None:
        messagebox.showwarning("Acceso Denegado", "Debes iniciar sesión para acceder a este módulo.")
        return

    project_window = tk.Toplevel(root)
    project_window.title("Gestión de Proyectos")
    project_window.geometry("1000x600")

    # Tabla para mostrar los proyectos
    tree_projects = ttk.Treeview(project_window, columns=("ID", "Nombre", "Descripción"), show="headings", height=10)
    tree_projects.heading("ID", text="ID")
    tree_projects.heading("Nombre", text="Nombre")
    tree_projects.heading("Descripción", text="Descripción")
    tree_projects.column("ID", width=50)
    tree_projects.column("Nombre", width=200)
    tree_projects.column("Descripción", width=400)
    tree_projects.pack(pady=10)

    # Tabla para mostrar las tareas asociadas al proyecto seleccionado
    tree_tasks = ttk.Treeview(project_window, columns=("ID", "Título", "Descripción", "Estado"), show="headings", height=10)
    tree_tasks.heading("ID", text="ID")
    tree_tasks.heading("Título", text="Título")
    tree_tasks.heading("Descripción", text="Descripción")
    tree_tasks.heading("Estado", text="Estado")
    tree_tasks.column("ID", width=50)
    tree_tasks.column("Título", width=200)
    tree_tasks.column("Descripción", width=300)
    tree_tasks.column("Estado", width=100)
    tree_tasks.pack(pady=10)

    # Función para refrescar la tabla de proyectos
    def refresh_projects():
        for row in tree_projects.get_children():
            tree_projects.delete(row)
        projects = Project.objects.all()
        for project in projects:
            tree_projects.insert("", "end", values=(project.id, project.name, project.description))

    # Función para refrescar las tareas asociadas al proyecto seleccionado
    def refresh_tasks(project_id):
        for row in tree_tasks.get_children():
            tree_tasks.delete(row)
        tasks = Task.objects.filter(project_id=project_id)
        for task in tasks:
            tree_tasks.insert("", "end", values=(task.id, task.title, task.description, task.status))

    # Evento para cargar las tareas al seleccionar un proyecto
    def on_project_select(event):
        selected_item = tree_projects.selection()
        if selected_item:
            project_id = tree_projects.item(selected_item[0], "values")[0]
            refresh_tasks(project_id)

    tree_projects.bind("<<TreeviewSelect>>", on_project_select)

    # Función para crear un nuevo proyecto
    def create_project():
        def save_project():
            name = entry_name.get()
            description = entry_description.get("1.0", "end").strip()
            if not name or not description:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return
            Project.objects.create(name=name, description=description, manager=authenticated_user)
            messagebox.showinfo("Éxito", "Proyecto creado correctamente.")
            refresh_projects()
            create_window.destroy()

        create_window = tk.Toplevel(project_window)
        create_window.title("Crear Proyecto")
        create_window.geometry("400x300")

        tk.Label(create_window, text="Nombre:").pack(pady=5)
        entry_name = tk.Entry(create_window, width=40)
        entry_name.pack(pady=5)

        tk.Label(create_window, text="Descripción:").pack(pady=5)
        entry_description = tk.Text(create_window, width=40, height=5)
        entry_description.pack(pady=5)

        tk.Button(create_window, text="Guardar", command=save_project).pack(pady=10)

    # Función para crear una nueva tarea asociada a un proyecto
    def create_task():
        selected_item = tree_projects.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un proyecto para agregar una tarea.")
            return
        project_id = tree_projects.item(selected_item[0], "values")[0]
        project = Project.objects.get(id=project_id)

        def save_task():
            title = entry_title.get()
            description = entry_description.get("1.0", "end").strip()
            if not title or not description:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return
            Task.objects.create(title=title, description=description, project=project, status="Pending")
            messagebox.showinfo("Éxito", "Tarea creada correctamente.")
            refresh_tasks(project_id)
            create_task_window.destroy()

        create_task_window = tk.Toplevel(project_window)
        create_task_window.title("Crear Tarea")
        create_task_window.geometry("400x300")

        tk.Label(create_task_window, text="Título:").pack(pady=5)
        entry_title = tk.Entry(create_task_window, width=40)
        entry_title.pack(pady=5)

        tk.Label(create_task_window, text="Descripción:").pack(pady=5)
        entry_description = tk.Text(create_task_window, width=40, height=5)
        entry_description.pack(pady=5)

        tk.Button(create_task_window, text="Guardar", command=save_task).pack(pady=10)

    # Botones de acción
    btn_frame = tk.Frame(project_window)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Crear Proyecto", command=create_project).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Crear Tarea", command=create_task).grid(row=0, column=1, padx=5)

    # Cargar los proyectos al iniciar
    refresh_projects()

# Configuración de la ventana principal
root = tk.Tk()
root.title("Aplicación de Escritorio")
root.geometry("800x600")

# Menú de navegación
menu_bar = tk.Menu(root)

# Menú "Archivo"
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Iniciar Sesión", command=open_login_window)
file_menu.add_separator()
file_menu.add_command(label="Salir", command=root.quit)
menu_bar.add_cascade(label="Archivo", menu=file_menu)

# Menú "Gestión"
management_menu = tk.Menu(menu_bar, tearoff=0)
management_menu.add_command(label="Gestión de Proyectos", command=open_project_management_window)
menu_bar.add_cascade(label="Gestión", menu=management_menu)

# Configurar el menú en la ventana principal
root.config(menu=menu_bar)

# Etiqueta de bienvenida
welcome_label = tk.Label(root, text="Bienvenido a la Aplicación de Escritorio", font=("Arial", 18))
welcome_label.pack(pady=20)

# Botones principales
tk.Button(root, text="Iniciar Sesión", command=open_login_window, width=20).pack(pady=10)
tk.Button(root, text="Gestión de Proyectos", command=open_project_management_window, width=20).pack(pady=10)

# Iniciar el bucle principal de la aplicación
root.mainloop()