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
from projects.models import Project, Task
from market_analysis.models import JobOffer

# Variable global para almacenar el usuario autenticado
authenticated_user = None

# Función para abrir la ventana principal después del inicio de sesión
def open_main_menu():
    main_menu = tk.Toplevel()
    main_menu.title("Menú Principal")
    main_menu.geometry("800x600")

    # Menú de navegación
    menu_bar = tk.Menu(main_menu)

    # Menú "Archivo"
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Cerrar Sesión", command=lambda: logout(main_menu))
    file_menu.add_separator()
    file_menu.add_command(label="Salir", command=main_menu.quit)
    menu_bar.add_cascade(label="Archivo", menu=file_menu)

    # Menú "Gestión"
    management_menu = tk.Menu(menu_bar, tearoff=0)
    management_menu.add_command(label="Gestión de Proyectos", command=open_project_management_window)
    management_menu.add_command(label="Ofertas de Empleo", command=open_job_offers_window)
    management_menu.add_command(label="Gestión de Usuarios", command=open_user_management_window)
    menu_bar.add_cascade(label="Gestión", menu=management_menu)

    # Configurar el menú en la ventana principal
    main_menu.config(menu=menu_bar)

    # Etiqueta de bienvenida
    welcome_label = tk.Label(main_menu, text=f"Bienvenido, {authenticated_user.username}!", font=("Arial", 18))
    welcome_label.pack(pady=20)

    # Botones principales
    tk.Button(main_menu, text="Gestión de Proyectos", command=open_project_management_window, width=20).pack(pady=10)
    tk.Button(main_menu, text="Ofertas de Empleo", command=open_job_offers_window, width=20).pack(pady=10)
    tk.Button(main_menu, text="Gestión de Usuarios", command=open_user_management_window, width=20).pack(pady=10)

# Función para cerrar sesión
def logout(main_menu):
    global authenticated_user
    authenticated_user = None
    main_menu.destroy()
    open_login_window()

# Función para abrir la ventana de inicio de sesión
def open_login_window():
    login_window = tk.Toplevel()
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

        # Autenticar al usuario
        user = authenticate(username=username, password=password)
        if user is not None:
            authenticated_user = user
            messagebox.showinfo("Inicio de Sesión", f"Bienvenido, {user.username}!")
            login_window.destroy()
            open_main_menu()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas. Inténtalo de nuevo.")

    tk.Button(login_window, text="Iniciar Sesión", command=login).pack(pady=10)

# Función para abrir la ventana de gestión de proyectos
def open_project_management_window():
    if authenticated_user is None:
        messagebox.showwarning("Acceso Denegado", "Debes iniciar sesión para acceder a este módulo.")
        return

    project_window = tk.Toplevel()
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
        projects = Project.objects.filter(manager=authenticated_user)
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
            Task.objects.create(title=title, description=description, project=project, status="PENDING")
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

# Función para abrir la ventana de ofertas de empleo
def open_job_offers_window():
    if authenticated_user is None:
        messagebox.showwarning("Acceso Denegado", "Debes iniciar sesión para acceder a este módulo.")
        return

    job_window = tk.Toplevel()
    job_window.title("Ofertas de Empleo")
    job_window.geometry("1200x600")

    # Tabla para mostrar las ofertas de empleo
    tree_jobs = ttk.Treeview(job_window, columns=("Título", "Empresa", "Ubicación", "Fecha", "Fuente"), show="headings", height=20)
    tree_jobs.heading("Título", text="Título")
    tree_jobs.heading("Empresa", text="Empresa")
    tree_jobs.heading("Ubicación", text="Ubicación")
    tree_jobs.heading("Fecha", text="Fecha de Publicación")
    tree_jobs.heading("Fuente", text="Fuente")
    tree_jobs.column("Título", width=300)
    tree_jobs.column("Empresa", width=200)
    tree_jobs.column("Ubicación", width=200)
    tree_jobs.column("Fecha", width=150)
    tree_jobs.column("Fuente", width=150)
    tree_jobs.pack(pady=10, fill=tk.BOTH, expand=True)

    # Función para refrescar las ofertas de empleo
    def refresh_job_offers():
        for row in tree_jobs.get_children():
            tree_jobs.delete(row)
        job_offers = JobOffer.objects.filter(is_active=True).order_by('-publication_date')
        for job in job_offers:
            tree_jobs.insert("", "end", values=(job.title, job.company, job.location, job.publication_date, job.source.name if job.source else "Desconocida"))

    # Botón para refrescar las ofertas
    tk.Button(job_window, text="Refrescar Ofertas", command=refresh_job_offers).pack(pady=10)

    # Cargar las ofertas al abrir la ventana
    refresh_job_offers()

# Función para abrir la ventana de gestión de usuarios
def open_user_management_window():
    if authenticated_user is None:
        messagebox.showwarning("Acceso Denegado", "Debes iniciar sesión para acceder a este módulo.")
        return

    user_window = tk.Toplevel()
    user_window.title("Gestión de Usuarios")
    user_window.geometry("1000x600")

    # Tabla para mostrar los usuarios
    tree_users = ttk.Treeview(user_window, columns=("ID", "Usuario", "Email", "Activo"), show="headings", height=15)
    tree_users.heading("ID", text="ID")
    tree_users.heading("Usuario", text="Usuario")
    tree_users.heading("Email", text="Email")
    tree_users.heading("Activo", text="Activo")
    tree_users.column("ID", width=50)
    tree_users.column("Usuario", width=200)
    tree_users.column("Email", width=300)
    tree_users.column("Activo", width=100)
    tree_users.pack(pady=10)

    # Función para refrescar la tabla de usuarios
    def refresh_users():
        for row in tree_users.get_children():
            tree_users.delete(row)
        users = User.objects.all()
        for user in users:
            tree_users.insert("", "end", values=(user.id, user.username, user.email, "Sí" if user.is_active else "No"))

    # Función para crear un nuevo usuario
    def create_user():
        def save_user():
            username = entry_username.get()
            email = entry_email.get()
            password = entry_password.get()
            if not username or not email or not password:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return
            User.objects.create_user(username=username, email=email, password=password)
            messagebox.showinfo("Éxito", "Usuario creado correctamente.")
            refresh_users()
            create_window.destroy()

        create_window = tk.Toplevel(user_window)
        create_window.title("Crear Usuario")
        create_window.geometry("400x300")

        tk.Label(create_window, text="Usuario:").pack(pady=5)
        entry_username = tk.Entry(create_window, width=40)
        entry_username.pack(pady=5)

        tk.Label(create_window, text="Email:").pack(pady=5)
        entry_email = tk.Entry(create_window, width=40)
        entry_email.pack(pady=5)

        tk.Label(create_window, text="Contraseña:").pack(pady=5)
        entry_password = tk.Entry(create_window, show="*", width=40)
        entry_password.pack(pady=5)

        tk.Button(create_window, text="Guardar", command=save_user).pack(pady=10)

    # Función para eliminar un usuario
    def delete_user():
        selected_item = tree_users.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para eliminar.")
            return
        user_id = tree_users.item(selected_item[0], "values")[0]
        user = User.objects.get(id=user_id)
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas eliminar al usuario '{user.username}'?"):
            user.delete()
            messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
            refresh_users()

    # Función para editar un usuario
    def edit_user():
        selected_item = tree_users.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para editar.")
            return
        user_id = tree_users.item(selected_item[0], "values")[0]
        user = User.objects.get(id=user_id)

        def save_changes():
            user.username = entry_username.get()
            user.email = entry_email.get()
            user.is_active = var_is_active.get()
            user.save()
            messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
            refresh_users()
            edit_window.destroy()

        edit_window = tk.Toplevel(user_window)
        edit_window.title("Editar Usuario")
        edit_window.geometry("400x300")

        tk.Label(edit_window, text="Usuario:").pack(pady=5)
        entry_username = tk.Entry(edit_window, width=40)
        entry_username.insert(0, user.username)
        entry_username.pack(pady=5)

        tk.Label(edit_window, text="Email:").pack(pady=5)
        entry_email = tk.Entry(edit_window, width=40)
        entry_email.insert(0, user.email)
        entry_email.pack(pady=5)

        var_is_active = tk.BooleanVar(value=user.is_active)
        tk.Checkbutton(edit_window, text="Activo", variable=var_is_active).pack(pady=5)

        tk.Button(edit_window, text="Guardar Cambios", command=save_changes).pack(pady=10)

    # Botones de acción
    btn_frame = tk.Frame(user_window)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Crear Usuario", command=create_user).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Editar Usuario", command=edit_user).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Eliminar Usuario", command=delete_user).grid(row=0, column=2, padx=5)

    # Cargar los usuarios al iniciar
    refresh_users()

# Iniciar la aplicación con la ventana de inicio de sesión
root = tk.Tk()
root.withdraw()  # Oculta la ventana principal de Tkinter
open_login_window()
root.mainloop()