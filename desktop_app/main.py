# desktop_app/main.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Configura el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main_project.settings')

import django
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from projects.models import Project, Task
from market_analysis.models import JobOffer
from users.models import Skill

# Variable global para almacenar el usuario autenticado
authenticated_user = None

# Función para centrar una ventana
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

# Configurar estilos globales
def setup_styles():
    style = ttk.Style()
    style.theme_use("default")
    
    # Estilo para botones
    style.configure("Custom.TButton", 
                    font=("Arial", 12, "bold"), 
                    padding=15, 
                    foreground="white", 
                    background="#4CAF50")
    style.map("Custom.TButton",
              foreground=[('active', 'white'), ('disabled', 'grey')],
              background=[('active', '#45A049'), ('disabled', '#A9A9A9')])
    
    # Estilo para etiquetas
    style.configure("Custom.TLabel", 
                    font=("Arial", 12), 
                    padding=5)
    
    # Estilo para Treeview
    style.configure("Custom.Treeview", 
                    font=("Arial", 10), 
                    rowheight=25)
    style.configure("Custom.Treeview.Heading", 
                    font=("Arial", 10, "bold"))

# Función para abrir la ventana principal después del inicio de sesión
def open_main_menu():
    main_menu = tk.Toplevel()
    main_menu.title("Menú Principal")
    main_menu.state("zoomed")
    main_menu.configure(bg="#F0F0F0")

    menu_bar = tk.Menu(main_menu, font=("Arial", 12, "italic"))
    main_menu.config(menu=menu_bar)

    file_menu = tk.Menu(menu_bar, tearoff=0, font=("Arial", 12,"italic"))
    file_menu.add_command(label="Cerrar Sesión", command=lambda: logout(main_menu))
    file_menu.add_separator()
    file_menu.add_command(label="Salir", command=main_menu.quit)
    menu_bar.add_cascade(label="Archivo", menu=file_menu, font=("Arial", 12,"italic"))

    management_menu = tk.Menu(menu_bar, tearoff=0, font=("Arial", 12))
    management_menu.add_command(label="Gestión de Proyectos", command=open_project_management_window)
    management_menu.add_command(label="Ofertas de Empleo", command=open_job_offers_window)
    management_menu.add_command(label="Gestión de Usuarios", command=open_user_management_window)
    menu_bar.add_cascade(label="Gestión", menu=management_menu, font=("Arial", 12, "italic"))

    content_frame = tk.Frame(main_menu, bg="#F0F0F0")
    content_frame.pack(expand=True, fill="both", padx=20, pady=20)

    welcome_label = ttk.Label(content_frame, 
                            text=f"Plataforma de Gestión, {authenticated_user.username}!", 
                            style="Custom.TLabel",
                            font=("Arial", 12, "italic"))
    welcome_label.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

    copyright_label = ttk.Label(content_frame, 
                              text="© 2025 Plataforma de Gestión. Todos los derechos reservados.", 
                              style="Custom.TLabel",
                              font=("Arial", 10, "italic"))
    copyright_label.place(relx=0.5, rely=1.0, anchor="s", y=-10)

    btn_frame = tk.Frame(content_frame, bg="#F0F0F0")
    btn_frame.pack(pady=30)

    ttk.Button(btn_frame, text="Gestión de Proyectos", 
               command=open_project_management_window, 
               style="Custom.TButton", 
               width=30).pack(pady=10, fill="x")
    ttk.Button(btn_frame, text="Ofertas de Empleo", 
               command=open_job_offers_window, 
               style="Custom.TButton", 
               width=30).pack(pady=10, fill="x")
    ttk.Button(btn_frame, text="Gestión de Usuarios", 
               command=open_user_management_window, 
               style="Custom.TButton", 
               width=30).pack(pady=10, fill="x")

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
    center_window(login_window, 350, 300)
    login_window.configure(bg="#F0F0F0")
    login_window.resizable(True, True)

    frame = tk.Frame(login_window, bg="#F0F0F0")
    frame.pack(padx=20, pady=20, expand=True, fill="both")

    ttk.Label(frame, text="Usuario:", style="Custom.TLabel").pack(pady=5)
    entry_username = ttk.Entry(frame)
    entry_username.pack(pady=5, fill="x")

    ttk.Label(frame, text="Contraseña:", style="Custom.TLabel").pack(pady=5)
    entry_password = ttk.Entry(frame, show="*")
    entry_password.pack(pady=5, fill="x")

    def login():
        global authenticated_user
        username = entry_username.get()
        password = entry_password.get()
        user = authenticate(username=username, password=password)
        if user is not None:
            authenticated_user = user
            messagebox.showinfo("Inicio de Sesión", f"Bienvenido, {user.username}!")
            login_window.destroy()
            open_main_menu()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas. Inténtalo de nuevo.")

    ttk.Button(frame, text="Iniciar Sesión", 
               command=login, 
               style="Custom.TButton", 
               width=20).pack(pady=15, fill="x")

# Función para abrir la ventana de gestión de proyectos
def open_project_management_window():
    if authenticated_user is None:
        messagebox.showwarning("Acceso Denegado", "Debes iniciar sesión para acceder a este módulo.")
        return

    project_window = tk.Toplevel()
    project_window.title("Gestión de Proyectos")
    center_window(project_window, 1200, 700)
    project_window.configure(bg="#F0F0F0")
    project_window.resizable(True, True)

    content_frame = tk.Frame(project_window, bg="#F0F0F0")
    content_frame.pack(expand=True, fill="both", padx=20, pady=20)

    tree_projects = ttk.Treeview(content_frame, 
                                columns=("ID", "Nombre", "Descripción", "Gestor", "Creado"), 
                                show="headings", 
                                style="Custom.Treeview")
    tree_projects.heading("ID", text="ID")
    tree_projects.heading("Nombre", text="Nombre")
    tree_projects.heading("Descripción", text="Descripción")
    tree_projects.heading("Gestor", text="Gestor")
    tree_projects.heading("Creado", text="Creado")
    tree_projects.column("ID", width=50)
    tree_projects.column("Nombre", width=200)
    tree_projects.column("Descripción", width=300)
    tree_projects.column("Gestor", width=150)
    tree_projects.column("Creado", width=150)
    tree_projects.pack(pady=10, fill="both", expand=True)

    tree_tasks = ttk.Treeview(content_frame, 
                             columns=("ID", "Título", "Descripción", "Estado", "Prioridad", "Asignados", "Habilidades", "Fecha Límite", "Vencida"), 
                             show="headings", 
                             style="Custom.Treeview")
    tree_tasks.heading("ID", text="ID")
    tree_tasks.heading("Título", text="Título")
    tree_tasks.heading("Descripción", text="Descripción")
    tree_tasks.heading("Estado", text="Estado")
    tree_tasks.heading("Prioridad", text="Prioridad")
    tree_tasks.heading("Asignados", text="Asignados")
    tree_tasks.heading("Habilidades", text="Habilidades")
    tree_tasks.heading("Fecha Límite", text="Fecha Límite")
    tree_tasks.heading("Vencida", text="Vencida")
    tree_tasks.column("ID", width=50)
    tree_tasks.column("Título", width=200)
    tree_tasks.column("Descripción", width=250)
    tree_tasks.column("Estado", width=100)
    tree_tasks.column("Prioridad", width=80)
    tree_tasks.column("Asignados", width=150)
    tree_tasks.column("Habilidades", width=150)
    tree_tasks.column("Fecha Límite", width=100)
    tree_tasks.column("Vencida", width=80)
    tree_tasks.pack(pady=10, fill="both", expand=True)

    def refresh_projects():
        for row in tree_projects.get_children():
            tree_projects.delete(row)
        projects = Project.objects.filter(manager=authenticated_user)
        for project in projects:
            tree_projects.insert("", "end", values=(
                project.id, 
                project.name, 
                project.description, 
                project.manager.username if project.manager else "Sin gestor", 
                project.created_at.strftime("%Y-%m-%d")
            ))

    def refresh_tasks(project_id):
        for row in tree_tasks.get_children():
            tree_tasks.delete(row)
        tasks = Task.objects.filter(project_id=project_id)
        for task in tasks:
            assigned = ", ".join([user.username for user in task.assigned_to.all()])
            skills = ", ".join([skill.name for skill in task.required_skills.all()])
            tree_tasks.insert("", "end", values=(
                task.id, 
                task.title, 
                task.description, 
                task.get_status_display(), 
                task.get_priority_display(), 
                assigned or "Nadie", 
                skills or "Ninguna", 
                task.deadline.strftime("%Y-%m-%d") if task.deadline else "Sin fecha", 
                "Sí" if task.is_overdue else "No"
            ))

    def on_project_select(event):
        selected_item = tree_projects.selection()
        if selected_item:
            project_id = tree_projects.item(selected_item[0], "values")[0]
            refresh_tasks(project_id)

    tree_projects.bind("<<TreeviewSelect>>", on_project_select)

    def create_project():
        def save_project():
            name = entry_name.get()
            description = entry_description.get("1.0", "end").strip()
            manager_username = combo_manager.get()
            if not name or not description:
                messagebox.showwarning("Advertencia", "Nombre y descripción son obligatorios.")
                return
            manager = User.objects.filter(username=manager_username).first() if manager_username else None
            Project.objects.create(name=name, description=description, manager=manager)
            messagebox.showinfo("Éxito", "Proyecto creado correctamente.")
            refresh_projects()
            create_window.destroy()

        create_window = tk.Toplevel(project_window)
        create_window.title("Crear Proyecto")
        center_window(create_window, 500, 400)
        create_window.configure(bg="#F0F0F0")
        create_window.resizable(True, True)

        frame = tk.Frame(create_window, bg="#F0F0F0")
        frame.pack(padx=20, pady=20, expand=True, fill="both")

        ttk.Label(frame, text="Nombre:", style="Custom.TLabel").pack(pady=5)
        entry_name = ttk.Entry(frame, width=50)
        entry_name.pack(pady=5, fill="x")

        ttk.Label(frame, text="Descripción:", style="Custom.TLabel").pack(pady=5)
        entry_description = tk.Text(frame, width=50, height=5, font=("Arial", 10))
        entry_description.pack(pady=5, fill="x")

        ttk.Label(frame, text="Gestor:", style="Custom.TLabel").pack(pady=5)
        users = User.objects.all()
        combo_manager = ttk.Combobox(frame, values=[""] + [user.username for user in users], state="readonly")
        combo_manager.pack(pady=5, fill="x")

        ttk.Button(frame, text="Guardar", command=save_project, style="Custom.TButton").pack(pady=10, fill="x")

    def edit_project():
        selected_item = tree_projects.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un proyecto para editar.")
            return
        project_id = tree_projects.item(selected_item[0], "values")[0]
        project = Project.objects.get(id=project_id)

        def save_changes():
            project.name = entry_name.get()
            project.description = entry_description.get("1.0", "end").strip()
            manager_username = combo_manager.get()
            if not project.name or not project.description:
                messagebox.showwarning("Advertencia", "Nombre y descripción son obligatorios.")
                return
            project.manager = User.objects.filter(username=manager_username).first() if manager_username else None
            project.save()
            messagebox.showinfo("Éxito", "Proyecto actualizado correctamente.")
            refresh_projects()
            edit_window.destroy()

        edit_window = tk.Toplevel(project_window)
        edit_window.title("Editar Proyecto")
        center_window(edit_window, 500, 400)
        edit_window.configure(bg="#F0F0F0")
        edit_window.resizable(True, True)

        frame = tk.Frame(edit_window, bg="#F0F0F0")
        frame.pack(padx=20, pady=20, expand=True, fill="both")

        ttk.Label(frame, text="Nombre:", style="Custom.TLabel").pack(pady=5)
        entry_name = ttk.Entry(frame, width=50)
        entry_name.insert(0, project.name)
        entry_name.pack(pady=5, fill="x")

        ttk.Label(frame, text="Descripción:", style="Custom.TLabel").pack(pady=5)
        entry_description = tk.Text(frame, width=50, height=5, font=("Arial", 10))
        entry_description.insert("1.0", project.description)
        entry_description.pack(pady=5, fill="x")

        ttk.Label(frame, text="Gestor:", style="Custom.TLabel").pack(pady=5)
        users = User.objects.all()
        combo_manager = ttk.Combobox(frame, values=[""] + [user.username for user in users], state="readonly")
        combo_manager.set(project.manager.username if project.manager else "")
        combo_manager.pack(pady=5, fill="x")

        ttk.Button(frame, text="Guardar Cambios", command=save_changes, style="Custom.TButton").pack(pady=10, fill="x")

    def delete_project():
        selected_item = tree_projects.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona un proyecto para eliminar.")
            return
        project_id = tree_projects.item(selected_item[0], "values")[0]
        project = Project.objects.get(id=project_id)
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas eliminar el proyecto '{project.name}'?"):
            project.delete()
            messagebox.showinfo("Éxito", "Proyecto eliminado correctamente.")
            refresh_projects()
            refresh_tasks(0)

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
            status = combo_status.get()
            priority = int(combo_priority.get().split()[0])
            deadline = entry_deadline.get()
            assigned_usernames = [lb_assigned.get(i) for i in lb_assigned.curselection()]
            skill_names = [lb_skills.get(i) for i in lb_skills.curselection()]

            if not title or not description or not status or not priority:
                messagebox.showwarning("Advertencia", "Título, descripción, estado y prioridad son obligatorios.")
                return
            if deadline:
                try:
                    deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
                except ValueError:
                    messagebox.showwarning("Advertencia", "Formato de fecha inválido. Use AAAA-MM-DD.")
                    return

            task = Task.objects.create(
                title=title,
                description=description,
                project=project,
                status=status,
                priority=priority,
                deadline=deadline
            )
            if assigned_usernames:
                task.assigned_to.set(User.objects.filter(username__in=assigned_usernames))
            if skill_names:
                task.required_skills.set(Skill.objects.filter(name__in=skill_names))
            messagebox.showinfo("Éxito", "Tarea creada correctamente.")
            refresh_tasks(project_id)
            create_task_window.destroy()

        create_task_window = tk.Toplevel(project_window)
        create_task_window.title("Crear Tarea")
        center_window(create_task_window, 600, 700)
        create_task_window.configure(bg="#F0F0F0")
        create_task_window.resizable(True, True)

        frame = tk.Frame(create_task_window, bg="#F0F0F0")
        frame.pack(padx=20, pady=20, expand=True, fill="both")

        ttk.Label(frame, text="Título:", style="Custom.TLabel").pack(pady=5)
        entry_title = ttk.Entry(frame, width=60)
        entry_title.pack(pady=5, fill="x")

        ttk.Label(frame, text="Descripción:", style="Custom.TLabel").pack(pady=5)
        entry_description = tk.Text(frame, width=60, height=5, font=("Arial", 10))
        entry_description.pack(pady=5, fill="x")

        ttk.Label(frame, text="Estado:", style="Custom.TLabel").pack(pady=5)
        combo_status = ttk.Combobox(frame, values=Task.Status.values, state="readonly")
        combo_status.set(Task.Status.PENDING)
        combo_status.pack(pady=5, fill="x")

        ttk.Label(frame, text="Prioridad:", style="Custom.TLabel").pack(pady=5)
        combo_priority = ttk.Combobox(frame, values=[f"{p.value} ({p.label})" for p in Task.Priority], state="readonly")
        combo_priority.set("2 (Media)")
        combo_priority.pack(pady=5, fill="x")

        ttk.Label(frame, text="Asignados:", style="Custom.TLabel").pack(pady=5)
        lb_assigned = tk.Listbox(frame, selectmode="multiple", height=4, exportselection=0, width=60)
        for user in User.objects.all():
            lb_assigned.insert(tk.END, user.username)
        lb_assigned.pack(pady=5, fill="x")

        ttk.Label(frame, text="Habilidades Requeridas:", style="Custom.TLabel").pack(pady=5)
        lb_skills = tk.Listbox(frame, selectmode="multiple", height=4, exportselection=0, width=60)
        for skill in Skill.objects.all():
            lb_skills.insert(tk.END, skill.name)
        lb_skills.pack(pady=5, fill="x")

        ttk.Label(frame, text="Fecha Límite (AAAA-MM-DD, opcional):", style="Custom.TLabel").pack(pady=5)
        entry_deadline = ttk.Entry(frame, width=60)
        entry_deadline.pack(pady=5, fill="x")

        ttk.Button(frame, text="Guardar", command=save_task, style="Custom.TButton").pack(pady=10, fill="x")

    def edit_task():
        selected_item = tree_tasks.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para editar.")
            return
        task_id = tree_tasks.item(selected_item[0], "values")[0]
        task = Task.objects.get(id=task_id)

        def save_changes():
            title = entry_title.get()
            description = entry_description.get("1.0", "end").strip()
            status = combo_status.get()
            priority = int(combo_priority.get().split()[0])
            deadline = entry_deadline.get()
            assigned_usernames = [lb_assigned.get(i) for i in lb_assigned.curselection()]
            skill_names = [lb_skills.get(i) for i in lb_skills.curselection()]

            if not title or not description or not status or not priority:
                messagebox.showwarning("Advertencia", "Título, descripción, estado y prioridad son obligatorios.")
                return
            if deadline:
                try:
                    deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
                except ValueError:
                    messagebox.showwarning("Advertencia", "Formato de fecha inválido. Use AAAA-MM-DD.")
                    return

            task.title = title
            task.description = description
            task.status = status
            task.priority = priority
            task.deadline = deadline
            task.save()
            task.assigned_to.set(User.objects.filter(username__in=assigned_usernames))
            task.required_skills.set(Skill.objects.filter(name__in=skill_names))
            messagebox.showinfo("Éxito", "Tarea actualizada correctamente.")
            refresh_tasks(task.project.id)
            edit_task_window.destroy()

        edit_task_window = tk.Toplevel(project_window)
        edit_task_window.title("Editar Tarea")
        center_window(edit_task_window, 600, 700)
        edit_task_window.configure(bg="#F0F0F0")
        edit_task_window.resizable(True, True)

        frame = tk.Frame(edit_task_window, bg="#F0F0F0")
        frame.pack(padx=20, pady=20, expand=True, fill="both")

        ttk.Label(frame, text="Título:", style="Custom.TLabel").pack(pady=5)
        entry_title = ttk.Entry(frame, width=60)
        entry_title.insert(0, task.title)
        entry_title.pack(pady=5, fill="x")

        ttk.Label(frame, text="Descripción:", style="Custom.TLabel").pack(pady=5)
        entry_description = tk.Text(frame, width=60, height=5, font=("Arial", 10))
        entry_description.insert("1.0", task.description)
        entry_description.pack(pady=5, fill="x")

        ttk.Label(frame, text="Estado:", style="Custom.TLabel").pack(pady=5)
        combo_status = ttk.Combobox(frame, values=Task.Status.values, state="readonly")
        combo_status.set(task.status)
        combo_status.pack(pady=5, fill="x")

        ttk.Label(frame, text="Prioridad:", style="Custom.TLabel").pack(pady=5)
        combo_priority = ttk.Combobox(frame, values=[f"{p.value} ({p.label})" for p in Task.Priority], state="readonly")
        for p in Task.Priority:
            if p.value == task.priority:
                combo_priority.set(f"{p.value} ({p.label})")
        combo_priority.pack(pady=5, fill="x")

        ttk.Label(frame, text="Asignados:", style="Custom.TLabel").pack(pady=5)
        lb_assigned = tk.Listbox(frame, selectmode="multiple", height=4, exportselection=0, width=60)
        assigned_users = [user.username for user in task.assigned_to.all()]
        for user in User.objects.all():
            lb_assigned.insert(tk.END, user.username)
            if user.username in assigned_users:
                lb_assigned.selection_set(tk.END)
        lb_assigned.pack(pady=5, fill="x")

        ttk.Label(frame, text="Habilidades Requeridas:", style="Custom.TLabel").pack(pady=5)
        lb_skills = tk.Listbox(frame, selectmode="multiple", height=4, exportselection=0, width=60)
        selected_skills = [skill.name for skill in task.required_skills.all()]
        for skill in Skill.objects.all():
            lb_skills.insert(tk.END, skill.name)
            if skill.name in selected_skills:
                lb_skills.selection_set(tk.END)
        lb_skills.pack(pady=5, fill="x")

        ttk.Label(frame, text="Fecha Límite (AAAA-MM-DD, opcional):", style="Custom.TLabel").pack(pady=5)
        entry_deadline = ttk.Entry(frame, width=60)
        if task.deadline:
            entry_deadline.insert(0, task.deadline.strftime("%Y-%m-%d"))
        entry_deadline.pack(pady=5, fill="x")

        ttk.Button(frame, text="Guardar Cambios", command=save_changes, style="Custom.TButton").pack(pady=10, fill="x")

    def delete_task():
        selected_item = tree_tasks.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para eliminar.")
            return
        task_id = tree_tasks.item(selected_item[0], "values")[0]
        task = Task.objects.get(id=task_id)
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas eliminar la tarea '{task.title}'?"):
            project_id = task.project.id
            task.delete()
            messagebox.showinfo("Éxito", "Tarea eliminada correctamente.")
            refresh_tasks(project_id)

    btn_frame = tk.Frame(content_frame, bg="#F0F0F0")
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="Crear Proyecto", command=create_project, style="Custom.TButton").grid(row=0, column=0, padx=5)
    ttk.Button(btn_frame, text="Editar Proyecto", command=edit_project, style="Custom.TButton").grid(row=0, column=1, padx=5)
    ttk.Button(btn_frame, text="Eliminar Proyecto", command=delete_project, style="Custom.TButton").grid(row=0, column=2, padx=5)
    ttk.Button(btn_frame, text="Crear Tarea", command=create_task, style="Custom.TButton").grid(row=0, column=3, padx=5)
    ttk.Button(btn_frame, text="Editar Tarea", command=edit_task, style="Custom.TButton").grid(row=0, column=4, padx=5)
    ttk.Button(btn_frame, text="Eliminar Tarea", command=delete_task, style="Custom.TButton").grid(row=0, column=5, padx=5)

    refresh_projects()

# Función para abrir la ventana de ofertas de empleo
def open_job_offers_window():
    if authenticated_user is None:
        messagebox.showwarning("Acceso Denegado", "Debes iniciar sesión para acceder a este módulo.")
        return

    job_window = tk.Toplevel()
    job_window.title("Ofertas de Empleo")
    center_window(job_window, 1200, 600)
    job_window.configure(bg="#F0F0F0")
    job_window.resizable(True, True)

    content_frame = tk.Frame(job_window, bg="#F0F0F0")
    content_frame.pack(expand=True, fill="both", padx=20, pady=20)

    tree_jobs = ttk.Treeview(content_frame, 
                            columns=("ID", "Título", "Empresa", "Ubicación", "Fecha", "Fuente", "Activo"), 
                            show="headings", 
                            style="Custom.Treeview")
    tree_jobs.heading("ID", text="ID")
    tree_jobs.heading("Título", text="Título")
    tree_jobs.heading("Empresa", text="Empresa")
    tree_jobs.heading("Ubicación", text="Ubicación")
    tree_jobs.heading("Fecha", text="Fecha de Publicación")
    tree_jobs.heading("Fuente", text="Fuente")
    tree_jobs.heading("Activo", text="Activo")
    tree_jobs.column("ID", width=50)
    tree_jobs.column("Título", width=300)
    tree_jobs.column("Empresa", width=200)
    tree_jobs.column("Ubicación", width=150)
    tree_jobs.column("Fecha", width=150)
    tree_jobs.column("Fuente", width=100)
    tree_jobs.column("Activo", width=80)
    tree_jobs.pack(pady=10, fill="both", expand=True)

    def refresh_job_offers():
        for row in tree_jobs.get_children():
            tree_jobs.delete(row)
        job_offers = JobOffer.objects.all().order_by('-publication_date')
        for job in job_offers:
            tree_jobs.insert("", "end", values=(
                job.id, 
                job.title, 
                job.company, 
                job.location, 
                job.publication_date, 
                job.source.name if job.source else "Desconocida", 
                "Sí" if job.is_active else "No"
            ))

    def create_job_offer():
        def save_job_offer():
            title = entry_title.get()
            company = entry_company.get()
            location = entry_location.get()
            publication_date = entry_date.get()
            source = entry_source.get()
            is_active = var_is_active.get()

            if not all([title, company, location, publication_date]):
                messagebox.showwarning("Advertencia", "Los campos obligatorios deben estar completos.")
                return
            
            try:
                publication_date = datetime.strptime(publication_date, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("Advertencia", "Formato de fecha inválido. Use AAAA-MM-DD.")
                return

            JobOffer.objects.create(
                title=title,
                company=company,
                location=location,
                publication_date=publication_date,
                source=source or None,
                is_active=is_active
            )
            messagebox.showinfo("Éxito", "Oferta de empleo creada correctamente.")
            refresh_job_offers()
            create_window.destroy()

        create_window = tk.Toplevel(job_window)
        create_window.title("Crear Oferta de Empleo")
        center_window(create_window, 500, 500)
        create_window.configure(bg="#F0F0F0")
        create_window.resizable(True, True)

        frame = tk.Frame(create_window, bg="#F0F0F0")
        frame.pack(padx=20, pady=20, expand=True, fill="both")

        ttk.Label(frame, text="Título:", style="Custom.TLabel").pack(pady=5)
        entry_title = ttk.Entry(frame, width=50)
        entry_title.pack(pady=5, fill="x")

        ttk.Label(frame, text="Empresa:", style="Custom.TLabel").pack(pady=5)
        entry_company = ttk.Entry(frame, width=50)
        entry_company.pack(pady=5, fill="x")

        ttk.Label(frame, text="Ubicación:", style="Custom.TLabel").pack(pady=5)
        entry_location = ttk.Entry(frame, width=50)
        entry_location.pack(pady=5, fill="x")

        ttk.Label(frame, text="Fecha de Publicación (AAAA-MM-DD):", style="Custom.TLabel").pack(pady=5)
        entry_date = ttk.Entry(frame, width=50)
        entry_date.pack(pady=5, fill="x")

        ttk.Label(frame, text="Fuente (opcional):", style="Custom.TLabel").pack(pady=5)
        entry_source = ttk.Entry(frame, width=50)
        entry_source.pack(pady=5, fill="x")

        var_is_active = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Activo", variable=var_is_active).pack(pady=5)

        ttk.Button(frame, text="Guardar", command=save_job_offer, style="Custom.TButton").pack(pady=10, fill="x")

    def edit_job_offer():
        selected_item = tree_jobs.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona una oferta para editar.")
            return
        job_id = tree_jobs.item(selected_item[0], "values")[0]
        job = JobOffer.objects.get(id=job_id)

        def save_changes():
            job.title = entry_title.get()
            job.company = entry_company.get()
            job.location = entry_location.get()
            publication_date = entry_date.get()
            job.source = entry_source.get() or None
            job.is_active = var_is_active.get()

            if not all([job.title, job.company, job.location, publication_date]):
                messagebox.showwarning("Advertencia", "Los campos obligatorios deben estar completos.")
                return

            try:
                job.publication_date = datetime.strptime(publication_date, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("Advertencia", "Formato de fecha inválido. Use AAAA-MM-DD.")
                return

            job.save()
            messagebox.showinfo("Éxito", "Oferta de empleo actualizada correctamente.")
            refresh_job_offers()
            edit_window.destroy()

        edit_window = tk.Toplevel(job_window)
        edit_window.title("Editar Oferta de Empleo")
        center_window(edit_window, 500, 500)
        edit_window.configure(bg="#F0F0F0")
        edit_window.resizable(True, True)

        frame = tk.Frame(edit_window, bg="#F0F0F0")
        frame.pack(padx=20, pady=20, expand=True, fill="both")

        ttk.Label(frame, text="Título:", style="Custom.TLabel").pack(pady=5)
        entry_title = ttk.Entry(frame, width=50)
        entry_title.insert(0, job.title)
        entry_title.pack(pady=5, fill="x")

        ttk.Label(frame, text="Empresa:", style="Custom.TLabel").pack(pady=5)
        entry_company = ttk.Entry(frame, width=50)
        entry_company.insert(0, job.company)
        entry_company.pack(pady=5, fill="x")

        ttk.Label(frame, text="Ubicación:", style="Custom.TLabel").pack(pady=5)
        entry_location = ttk.Entry(frame, width=50)
        entry_location.insert(0, job.location)
        entry_location.pack(pady=5, fill="x")

        ttk.Label(frame, text="Fecha de Publicación (AAAA-MM-DD):", style="Custom.TLabel").pack(pady=5)
        entry_date = ttk.Entry(frame, width=50)
        entry_date.insert(0, job.publication_date.strftime("%Y-%m-%d"))
        entry_date.pack(pady=5, fill="x")

        ttk.Label(frame, text="Fuente (opcional):", style="Custom.TLabel").pack(pady=5)
        entry_source = ttk.Entry(frame, width=50)
        entry_source.insert(0, job.source.name if job.source else "")
        entry_source.pack(pady=5, fill="x")

        var_is_active = tk.BooleanVar(value=job.is_active)
        ttk.Checkbutton(frame, text="Activo", variable=var_is_active).pack(pady=5)

        ttk.Button(frame, text="Guardar Cambios", command=save_changes, style="Custom.TButton").pack(pady=10, fill="x")

    def delete_job_offer():
        selected_item = tree_jobs.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Selecciona una oferta para eliminar.")
            return
        job_id = tree_jobs.item(selected_item[0], "values")[0]
        job = JobOffer.objects.get(id=job_id)
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas eliminar la oferta '{job.title}'?"):
            job.delete()
            messagebox.showinfo("Éxito", "Oferta de empleo eliminada correctamente.")
            refresh_job_offers()

    btn_frame = tk.Frame(content_frame, bg="#F0F0F0")
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="Crear Oferta", command=create_job_offer, style="Custom.TButton").grid(row=0, column=0, padx=5)
    ttk.Button(btn_frame, text="Editar Oferta", command=edit_job_offer, style="Custom.TButton").grid(row=0, column=1, padx=5)
    ttk.Button(btn_frame, text="Eliminar Oferta", command=delete_job_offer, style="Custom.TButton").grid(row=0, column=2, padx=5)
    ttk.Button(btn_frame, text="Refrescar Ofertas", command=refresh_job_offers, style="Custom.TButton").grid(row=0, column=3, padx=5)

    refresh_job_offers()

# Función para abrir la ventana de gestión de usuarios
def open_user_management_window():
    if authenticated_user is None:
        messagebox.showwarning("Acceso Denegado", "Debes iniciar sesión para acceder a este módulo.")
        return

    user_window = tk.Toplevel()
    user_window.title("Gestión de Usuarios")
    center_window(user_window, 1000, 600)
    user_window.configure(bg="#F0F0F0")
    user_window.resizable(True, True)

    content_frame = tk.Frame(user_window, bg="#F0F0F0")
    content_frame.pack(expand=True, fill="both", padx=20, pady=20)

    tree_users = ttk.Treeview(content_frame, 
                             columns=("ID", "Usuario", "Email", "Activo"), 
                             show="headings", 
                             style="Custom.Treeview")
    tree_users.heading("ID", text="ID")
    tree_users.heading("Usuario", text="Usuario")
    tree_users.heading("Email", text="Email")
    tree_users.heading("Activo", text="Activo")
    tree_users.column("ID", width=50)
    tree_users.column("Usuario", width=200)
    tree_users.column("Email", width=300)
    tree_users.column("Activo", width=100)
    tree_users.pack(pady=10, fill="both", expand=True)

    def refresh_users():
        for row in tree_users.get_children():
            tree_users.delete(row)
        users = User.objects.all()
        for user in users:
            tree_users.insert("", "end", values=(user.id, user.username, user.email, "Sí" if user.is_active else "No"))

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
        center_window(create_window, 500, 400)
        create_window.configure(bg="#F0F0F0")
        create_window.resizable(True, True)

        frame = tk.Frame(create_window, bg="#F0F0F0")
        frame.pack(padx=20, pady=20, expand=True, fill="both")

        ttk.Label(frame, text="Usuario:", style="Custom.TLabel").pack(pady=5)
        entry_username = ttk.Entry(frame, width=50)
        entry_username.pack(pady=5, fill="x")

        ttk.Label(frame, text="Email:", style="Custom.TLabel").pack(pady=5)
        entry_email = ttk.Entry(frame, width=50)
        entry_email.pack(pady=5, fill="x")

        ttk.Label(frame, text="Contraseña:", style="Custom.TLabel").pack(pady=5)
        entry_password = ttk.Entry(frame, show="*", width=50)
        entry_password.pack(pady=5, fill="x")

        ttk.Button(frame, text="Guardar", command=save_user, style="Custom.TButton").pack(pady=10, fill="x")

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
        center_window(edit_window, 500, 400)
        edit_window.configure(bg="#F0F0F0")
        edit_window.resizable(True, True)

        frame = tk.Frame(edit_window, bg="#F0F0F0")
        frame.pack(padx=20, pady=20, expand=True, fill="both")

        ttk.Label(frame, text="Usuario:", style="Custom.TLabel").pack(pady=5)
        entry_username = ttk.Entry(frame, width=50)
        entry_username.insert(0, user.username)
        entry_username.pack(pady=5, fill="x")

        ttk.Label(frame, text="Email:", style="Custom.TLabel").pack(pady=5)
        entry_email = ttk.Entry(frame, width=50)
        entry_email.insert(0, user.email)
        entry_email.pack(pady=5, fill="x")

        var_is_active = tk.BooleanVar(value=user.is_active)
        ttk.Checkbutton(frame, text="Activo", variable=var_is_active).pack(pady=5)

        ttk.Button(frame, text="Guardar Cambios", command=save_changes, style="Custom.TButton").pack(pady=10, fill="x")

    btn_frame = tk.Frame(content_frame, bg="#F0F0F0")
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="Crear Usuario", command=create_user, style="Custom.TButton").grid(row=0, column=0, padx=5)
    ttk.Button(btn_frame, text="Editar Usuario", command=edit_user, style="Custom.TButton").grid(row=0, column=1, padx=5)
    ttk.Button(btn_frame, text="Eliminar Usuario", command=delete_user, style="Custom.TButton").grid(row=0, column=2, padx=5)

    refresh_users()

# Iniciar la aplicación
root = tk.Tk()
root.withdraw()
setup_styles()
open_login_window()
root.mainloop()