# Documentación Técnica: Plataforma Gestión

## Índice

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
   - [Descripción General](#descripción-general)
   - [Arquitectura de la Aplicación Web](#arquitectura-de-la-aplicación-web)
   - [Arquitectura de la Aplicación de Escritorio](#arquitectura-de-la-aplicación-de-escritorio)
   - [Componentes Compartidos](#componentes-compartidos)
   - [Flujo de Interacción](#flujo-de-interacción)
2. [Diagrama Entidad-Relación (ER)](#diagrama-entidad-relación-er)
   - [Entidades y Atributos](#entidades-y-atributos)
   - [Relaciones](#relaciones)
   - [Diagrama ER (Textual)](#diagrama-er-textual)
3. [Componentes Modulares e Interacciones](#componentes-modulares-e-interacciones)
   - [Módulos](#módulos)
   - [Interacciones entre Componentes](#interacciones-entre-componentes)
4. [Modelo de IA e Implementación](#modelo-de-ia-e-implementación)
   - [Descripción del Modelo de IA](#descripción-del-modelo-de-ia)
   - [Detalles de Implementación](#detalles-de-implementación)
   - [Integración](#integración)
5. [Instrucciones de Instalación y Configuración](#instrucciones-de-instalación-y-configuración)
   - [Prerrequisitos](#prerrequisitos)
   - [Configuración de la Aplicación Web](#configuración-de-la-aplicación-web)
   - [Configuración de la Aplicación de Escritorio](#configuración-de-la-aplicación-de-escritorio)
   - [Solución de Problemas](#solución-de-problemas)
6. [Estructura del Proyecto](#estructura-del-proyecto)
   - [Descripción](#descripción)
7. [Descripción de la Funcionalidad](#descripción-de-la-funcionalidad)
   - [Funcionalidades Principales](#funcionalidades-principales)
   - [Web vs. Escritorio](#web-vs-escritorio)
8. [Manual de Usuario](#manual-de-usuario)
   - [Aplicación Web](#aplicación-web)
   - [Aplicación de Escritorio](#aplicación-de-escritorio)
9. [Análisis de Requisitos](#análisis-de-requisitos)
   - [Requisitos Funcionales](#requisitos-funcionales)
   - [Requisitos No Funcionales](#requisitos-no-funcionales)
   - [Restricciones](#restricciones)

## Arquitectura del Sistema

### Descripción General

El sistema es una plataforma híbrida que incluye una **aplicación web** desarrollada con Django y una **aplicación de escritorio** construida con Tkinter. Ambos componentes comparten la misma lógica de backend y base de datos, garantizando consistencia en la gestión de datos y reglas de negocio. La arquitectura sigue un enfoque modular y en capas para facilitar la escalabilidad y el mantenimiento.

### Arquitectura de la Aplicación Web

- **Framework**: Django 4.x (framework web basado en Python).
- **Componentes**:
  - **Frontend**: Plantillas HTML con Bootstrap para diseño responsivo, mejoradas con JavaScript para interacciones dinámicas.
  - **Backend**: Vistas, modelos y formularios de Django gestionan la lógica de negocio, el procesamiento de datos y la autenticación de usuarios.
  - **Base de Datos**: PostgreSQL (o SQLite para desarrollo) almacena todos los datos, incluyendo proyectos, tareas, ofertas de empleo y perfiles de usuario.
  - **Módulo de Scraping**: Scrapers basados en Selenium para ofertas de empleo de Tecnoempleo, InfoJobs y LinkedIn, integrados en la app `market_analysis`.
  - **Motor de IA**: Proporciona predicciones de tendencias de habilidades y recomendaciones de tareas, implementado en la app `ai_engine`.
- **Despliegue**: Normalmente desplegado en un servidor WSGI (por ejemplo, Gunicorn) con Nginx como proxy inverso.

### Arquitectura de la Aplicación de Escritorio

- **Framework**: Tkinter (biblioteca estándar de GUI de Python).
- **Componentes**:
  - **Interfaz Gráfica**: Interfaz basada en Tkinter con estilos personalizados para botones, etiquetas y widgets Treeview.
  - **Integración con Backend**: Comparte los mismos modelos de Django y base de datos que la aplicación web, accedidos a través del ORM de Django.
  - **Funcionalidad**: Replica las funciones principales de la aplicación web (gestión de proyectos, ofertas de empleo, usuarios), optimizada para uso en escritorio.
- **Ejecución**: Se ejecuta como un script Python independiente (`main.py`) con la configuración de Django para acceso a la base de datos.

### Componentes Compartidos

- **Base de Datos**: Una única base de datos PostgreSQL sirve a ambas aplicaciones, asegurando consistencia de datos.
- **Autenticación**: El sistema de autenticación de Django se utiliza para ambas aplicaciones, con control de acceso basado en roles.
- **Lógica de Negocio**: Encapsulada en modelos y vistas de Django, reutilizable en ambas aplicaciones.

### Flujo de Interacción

1. **Interacción del Usuario**:
   - Web: Los usuarios interactúan a través del navegador, enviando solicitudes HTTP a las vistas de Django.
   - Escritorio: Los usuarios interactúan a través de la interfaz Tkinter, activando llamadas al backend mediante modelos de Django.
2. **Procesamiento en Backend**:
   - Django procesa las solicitudes, interactúa con la base de datos y devuelve respuestas.
   - Las tareas de scraping se activan mediante vistas web o trabajos programados, almacenando resultados en la base de datos.
3. **Integración de IA**:
   - El motor de IA procesa datos de ofertas de empleo para generar tendencias de habilidades y recomendaciones de tareas, accesibles desde ambas interfaces.

## Diagrama Entidad-Relación (ER)

A continuación, se presenta una representación textual del diagrama ER de la base de datos, describiendo entidades, atributos y relaciones. Un diagrama visual puede crearse con herramientas como DBeaver o Lucidchart basado en esta descripción.

### Entidades y Atributos

- **Usuario** (Django `auth_user`):
  - `id` (PK), `username`, `email`, `password`, `is_active`
- **PerfilUsuario**:
  - `id` (PK), `user` (FK a Usuario), `role` (FK a Rol), `bio`, `location`
  - M2M: `skills` (a Habilidad)
- **Rol**:
  - `id` (PK), `name`
  - M2M: `permissions` (a Permiso)
- **Habilidad**:
  - `id` (PK), `name`
- **Proyecto**:
  - `id` (PK), `name`, `description`, `manager` (FK a Usuario), `created_at`, `updated_at`
- **Tarea**:
  - `id` (PK), `project` (FK a Proyecto), `title`, `description`, `status`, `priority`, `deadline`, `created_at`, `updated_at`
  - M2M: `assigned_to` (a Usuario), `required_skills` (a Habilidad)
- **FuenteEmpleo**:
  - `id` (PK), `name`, `url`, `last_scraped`
- **OfertaEmpleo**:
  - `id` (PK), `title`, `company`, `location`, `description`, `salary_range`, `publication_date`, `url`, `source` (FK a FuenteEmpleo), `applicants_count`, `industry`, `raw_data`, `scraped_at`, `updated_at`, `is_active`
  - M2M: `required_skills` (a Habilidad)
- **TendenciaMercado**:
  - `id` (PK), `analysis_date`, `period`, `region`, `industry`, `skill_trends` (JSON), `source_description`, `created_at`

### Relaciones

- **Usuario ↔ PerfilUsuario**: Uno a Uno (cada usuario tiene un perfil).
- **PerfilUsuario ↔ Rol**: Muchos a Uno (varios perfiles pueden tener el mismo rol).
- **PerfilUsuario ↔ Habilidad**: Muchos a Muchos (los usuarios pueden tener múltiples habilidades).
- **Rol ↔ Permiso**: Muchos a Muchos (los roles pueden tener múltiples permisos).
- **Proyecto ↔ Usuario**: Muchos a Uno (varios proyectos pueden tener el mismo gerente).
- **Tarea ↔ Proyecto**: Muchos a Uno (varias tareas pertenecen a un proyecto).
- **Tarea ↔ Usuario**: Muchos a Muchos (las tareas pueden asignarse a varios usuarios).
- **Tarea ↔ Habilidad**: Muchos a Muchos (las tareas pueden requerir múltiples habilidades).
- **OfertaEmpleo ↔ FuenteEmpleo**: Muchos a Uno (varias ofertas provienen de una fuente).
- **OfertaEmpleo ↔ Habilidad**: Muchos a Muchos (las ofertas pueden requerir múltiples habilidades).
- **TendenciaMercado**: Sin relaciones directas (almacena datos agregados).

### Diagrama ER (Textual)

```
[Usuario] --1:1--> [PerfilUsuario] --M:1--> [Rol] --M:M--> [Permiso]
[PerfilUsuario] --M:M--> [Habilidad]
[Proyecto] --M:1--> [Usuario] (gerente)
[Tarea] --M:1--> [Proyecto]
[Tarea] --M:M--> [Usuario] (assigned_to)
[Tarea] --M:M--> [Habilidad] (required_skills)
[OfertaEmpleo] --M:1--> [FuenteEmpleo]
[OfertaEmpleo] --M:M--> [Habilidad] (required_skills)
[TendenciaMercado]
```

## Componentes Modulares e Interacciones

### Módulos

1. **App de Usuarios**:
   - **Propósito**: Gestiona autenticación, perfiles, roles y habilidades de usuarios.
   - **Componentes**:
     - Modelos: `PerfilUsuario`, `Rol`, `Habilidad`
     - Vistas: Registro, panel de control, gestión de usuarios (solo admin)
     - Formularios: `SignUpForm` para creación de usuarios
   - **Interacciones**: Proporciona autenticación y control de acceso basado en roles para otros módulos.

2. **App de Proyectos**:
   - **Propósito**: Gestiona proyectos y tareas.
   - **Componentes**:
     - Modelos: `Proyecto`, `Tarea`
     - Vistas: Operaciones CRUD para proyectos y tareas, acceso basado en roles
     - Formularios: `ProjectForm`, `TaskForm`
   - **Interacciones**: Se integra con la app de Usuarios para asignaciones de tareas y requisitos de habilidades.

3. **App de Análisis de Mercado**:
   - **Propósito**: Realiza scraping de ofertas de empleo y analiza tendencias de mercado.
   - **Componentes**:
     - Modelos: `FuenteEmpleo`, `OfertaEmpleo`, `TendenciaMercado`
     - Vistas: Panel de control, lista de ofertas, activación de scraping, informe de habilidades
     - Scrapers: `TecnoempleoScraper`, `InfojobsScraper`, `LinkedinScraper`
   - **Interacciones**: Utiliza habilidades de la app de Usuarios para etiquetar ofertas, alimenta datos al motor de IA.

4. **App de Motor de IA**:
   - **Propósito**: Proporciona predicciones de tendencias de habilidades y recomendaciones de tareas.
   - **Componentes**:
     - Lógica: `predictions.py` (tendencias de habilidades), `recommendations.py` (asignaciones de tareas)
   - **Interacciones**: Consume datos de OfertaEmpleo y Habilidad, proporciona recomendaciones a las apps de Usuarios y Proyectos.

5. **App de Escritorio**:
   - **Propósito**: Proporciona una interfaz basada en Tkinter para las mismas funcionalidades que la app web.
   - **Componentes**:
     - `main.py`: Script principal con interfaz Tkinter
     - Funciones: Inicio de sesión, gestión de proyectos, ofertas de empleo, gestión de usuarios
   - **Interacciones**: Usa modelos de Django directamente, compartiendo la misma base de datos que la app web.

### Interacciones entre Componentes

- **Autenticación**: La app de Usuarios autentica a los usuarios para ambas aplicaciones, almacenando datos de sesión en la base de datos.
- **Flujo de Datos**:
  - Web: Solicitudes HTTP → Vistas de Django → Modelos → Base de Datos.
  - Escritorio: Eventos de Tkinter → Modelos de Django → Base de Datos.
- **Scraping**:
  - Activado mediante vista web (`run_scraping`), almacena OfertasEmpleo en la base de datos.
  - La app de escritorio muestra OfertasEmpleo mediante Treeview de Tkinter.
- **Recomendaciones de IA**:
  - El motor de IA procesa datos de OfertaEmpleo, almacena tendencias en TendenciaMercado.
  - Las recomendaciones se muestran en el panel de usuario (web) o menú principal (escritorio).

## Modelo de IA e Implementación

### Descripción del Modelo de IA

El motor de IA proporciona dos funcionalidades principales:

1. **Predicciones de Tendencias de Habilidades** (`get_future_skills_predictions`):
   - Predice la demanda futura de habilidades basada en datos de ofertas de empleo.
   - Implementado en `ai_engine/logic/predictions.py`.
2. **Recomendaciones de Tareas** (`get_task_recommendations`):
   - Recomienda tareas a usuarios según sus habilidades y los requisitos de las tareas.
   - Implementado en `ai_engine/logic/recommendations.py`.

### Detalles de Implementación

- **Predicciones de Tendencias de Habilidades**:
  - **Fuente de Datos**: Agrega `OfertaEmpleo.required_skills` y `TendenciaMercado.skill_trends`.
  - **Algoritmo**: Análisis estadístico simple (por ejemplo, frecuencia de habilidades en ofertas recientes) con un mecanismo de puntuación.
  - **Salida**: Diccionario de habilidades con puntajes predichos (por ejemplo, `{'python': {'predicted_score': 0.85}}`).
  - **Uso**: Mostrado en el panel de mercado y usado para autocompletado en búsquedas de habilidades.
- **Recomendaciones de Tareas**:
  - **Fuente de Datos**: Compara `PerfilUsuario.skills` con `Tarea.required_skills`.
  - **Algoritmo**: Similitud de coseno o coincidencia basada en reglas para clasificar tareas por superposición de habilidades.
  - **Salida**: Lista de tareas recomendadas para un usuario.
  - **Uso**: Mostrado en el panel de usuario para colaboradores.

### Integración

- **Web**: Las salidas de IA se renderizan en plantillas (`market_analysis/dashboard.html`, `users/dashboard.html`).
- **Escritorio**: Las salidas de IA no están integradas directamente, pero pueden accederse mediante consultas a la base de datos en `main.py`.
- **Escalabilidad**: El modelo de IA es ligero, pero puede extenderse con bibliotecas de aprendizaje automático (por ejemplo, scikit-learn) para predicciones más complejas.

## Instrucciones de Instalación y Configuración

### Prerrequisitos

- Python 3.8+
- PostgreSQL (o SQLite para desarrollo)
- Navegador Chrome (para scrapers de Selenium)
- Clave de API de 2Captcha (para scraping de InfoJobs)
- Credenciales de LinkedIn (para scraping de LinkedIn)

### Configuración de la Aplicación Web

1. **Clonar el Repositorio**:
   ```bash
   git clone <url_repositorio>
   cd main_project
   ```

2. **Crear un Entorno Virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
   Ejemplo de `requirements.txt`:
   ```
   django>=4.0
   psycopg2-binary
   selenium
   beautifulsoup4
   requests
   twocaptcha
   webdriver-manager
   matplotlib
   ```

4. **Configurar Variables de Entorno**:
   Crear un archivo `.env` en la raíz del proyecto:
   ```plaintext
   SECRET_KEY=tu_clave_secreta_django
   DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/nombre_db
   TWOCAPTCHA_API_KEY=tu_clave_2captcha
   LINKEDIN_USERNAME=tu_email_linkedin
   LINKEDIN_PASSWORD=tu_contraseña_linkedin
   ```

5. **Configurar la Base de Datos**:
   ```bash
   python manage.py migrate
   ```

6. **Crear un Superusuario**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Ejecutar el Servidor de Desarrollo**:
   ```bash
   python manage.py runserver
   ```
   Acceder en `http://localhost:8000`.

### Configuración de la Aplicación de Escritorio

1. **Asegurar Dependencias de la App Web**:
   Seguir los pasos de configuración de la aplicación web para instalar dependencias y configurar la base de datos.

2. **Ejecutar la App de Escritorio**:
   ```bash
   python desktop_app/main.py
   ```

3. **Notas**:
   - La app de escritorio usa la misma base de datos que la app web.
   - Asegurarse de que el módulo de configuración de Django esté correctamente establecido en `main.py` (`DJANGO_SETTINGS_MODULE=main_project.settings`).

### Solución de Problemas

- **Errores de Selenium**: Asegurarse de que Chrome y ChromeDriver estén instalados y sean compatibles.
- **Problemas de Base de Datos**: Verificar que PostgreSQL esté en ejecución y que las credenciales sean correctas.
- **Fallos de Scraping**: Comprobar el saldo de 2Captcha y las credenciales de LinkedIn.

## Estructura del Proyecto

```
main_project/
├── ai_engine/
│   └── logic/
│       ├── predictions.py
│       └── recommendations.py
├── desktop_app/
│   └── main.py
├── market_analysis/
│   ├── migrations/
│   ├── scraping/
│   │   ├── base_scraper.py
│   │   ├── infojobs_scraper.py
│   │   ├── linkedin_scraper.py
│   │   └── tecnoempleo_scraper.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── projects/
│   ├── migrations/
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── users/
│   ├── migrations/
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── main_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── .env
```

### Descripción

- **ai_engine/**: Contiene la lógica de IA para predicciones y recomendaciones.
- **desktop_app/**: Aplicación de escritorio basada en Tkinter.
- **market_analysis/**: Gestiona el scraping de ofertas de empleo y el análisis de tendencias de mercado.
- **projects/**: Gestiona proyectos y tareas.
- **users/**: Gestiona autenticación y perfiles de usuarios.
- **main_project/**: Configuraciones y URLs del proyecto Django.

## Descripción de la Funcionalidad

### Funcionalidades Principales

1. **Gestión de Usuarios**:
   - Registro, inicio de sesión y acceso basado en roles (Admin, Gerente, Colaborador).
   - Operaciones CRUD para usuarios (solo admin).
2. **Gestión de Proyectos**:
   - Crear, actualizar, eliminar proyectos y tareas.
   - Asignar tareas a usuarios con habilidades coincidentes.
3. **Gestión de Ofertas de Empleo**:
   - Scraping de ofertas de empleo de Tecnoempleo, InfoJobs y LinkedIn.
   - Mostrar y filtrar ofertas, exportar informes de habilidades.
4. **Análisis de Mercado**:
   - Analizar tendencias de habilidades basadas en datos de ofertas.
   - Proporcionar autocompletado para búsquedas de habilidades.
5. **Recomendaciones de IA**:
   - Recomendar tareas a usuarios según habilidades.
   - Predecir la demanda futura de habilidades.

### Web vs. Escritorio

- **Web**: Basada en navegador, responsiva, ideal para acceso remoto.
- **Escritorio**: Independiente, optimizada para uso local, replica la funcionalidad web.

## Manual de Usuario

### Aplicación Web

1. **Inicio de Sesión**:
   - Navegar a `http://localhost:8000`.
   - Ingresar nombre de usuario y contraseña.
   - Hacer clic en "Iniciar Sesión".

   ![alt text](image.png)

2. **Panel de Control**:
   - Ver contenido específico según el rol (por ejemplo, recomendaciones de tareas para Colaboradores).
   - Navegar a Proyectos, Ofertas de Empleo o Gestión de Usuarios (según rol).

   ![alt text](image-1.png)

3. **Gestión de Proyectos**:
   - Ir a `/projects/`.
   - Hacer clic en "Crear Proyecto" para agregar un nuevo proyecto.
   - Seleccionar un proyecto para ver tareas, agregar/editar tareas o asignar usuarios.

   ![alt text](image-2.png)

   ![alt text](image-4.png)

   ![alt text](image-3.png)

   ![alt text](image-5.png)
   ![alt text](image-6.png)

4. **Gestión de Ofertas de Empleo**:
   - Ir a `/market/offers/`.
   - Buscar ofertas por palabra clave.
   - Hacer clic en "Ejecutar Scraping" para obtener nuevas ofertas (solo admin).
   - Exportar informe de habilidades como PNG.

   ![alt text](image-7.png)
   ![alt text](image-8.png)
   ![alt text](image-9.png)


5. **Gestión de Usuarios** (Solo Admin):
   - Ir a `/users/manage/`.
   - Crear, actualizar o eliminar usuarios.
   - Asignar roles a usuarios.

   ![alt text](image-10.png)

   ![alt text](image-11.png)
   ![alt text](image-12.png)
   ![alt text](image-13.png)

### Aplicación de Escritorio

1. **Iniciar**:
   - Ejecutar `python desktop_app/main.py`.
2. **Inicio de Sesión**:
   - Ingresar nombre de usuario y contraseña en la ventana de inicio de sesión.
   - Hacer clic en "Iniciar Sesión".
3. **Menú Principal**:
   - Ver mensaje de bienvenida y botones de navegación.
   - Hacer clic en "Gestión de Proyectos", "Ofertas de Empleo" o "Gestión de Usuarios".
4. **Gestión de Proyectos**:
   - Ver proyectos en un Treeview.
   - Seleccionar un proyecto para ver tareas.
   - Usar botones para crear/editar/eliminar proyectos o tareas.
5. **Gestión de Ofertas de Empleo**:
   - Ver ofertas de empleo en un Treeview.
   - Crear/editar/eliminar ofertas manualmente.
6. **Gestión de Usuarios**:
   - Ver usuarios en un Treeview.
   - Crear/editar/eliminar usuarios.

## Análisis de Requisitos

### Requisitos Funcionales

- **Gestión de Usuarios**:
  - Los usuarios pueden registrarse, iniciar sesión y gestionar perfiles.
  - Los administradores pueden gestionar todos los usuarios y asignar roles.
- **Gestión de Proyectos**:
  - Los usuarios pueden crear y gestionar proyectos y tareas.
  - Las tareas pueden asignarse según habilidades y tienen fechas límite.
- **Gestión de Ofertas de Empleo**:
  - El sistema realiza scraping de ofertas de empleo de múltiples fuentes.
  - Los usuarios pueden filtrar y analizar ofertas.
- **Análisis de Mercado**:
  - El sistema proporciona análisis de tendencias de habilidades y visualizaciones.
- **Recomendaciones de IA**:
  - El sistema recomienda tareas y predice la demanda de habilidades.

### Requisitos No Funcionales

- **Rendimiento**: Soportar hasta 100 usuarios concurrentes; el scraping se completa en 5 minutos para 50 ofertas.
- **Escalabilidad**: Soportar fuentes de empleo adicionales y modelos de IA.
- **Seguridad**: Control de acceso basado en roles, autenticación segura.
- **Usabilidad**: Interfaz intuitiva para web y escritorio.
- **Fiabilidad**: Gestionar errores de scraping con gracia, garantizar consistencia de datos.

### Restricciones

- **Scraping**: Limitado por restricciones de los sitios web y desafíos CAPTCHA.
- **LinkedIn**: Requiere credenciales válidas y riesgo de bloqueo de cuenta.
- **Hardware**: La app de escritorio requiere instalación local de Python.