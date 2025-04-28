# Plan de Testing: Plataforma Gestión

## Índice

1. [Introducción](#introducción)
2. [Objetivo del Testing](#objetivo-del-testing)
3. [Alcance del Testing](#alcance-del-testing)
   - [Incluido en el Testing](#incluido-en-el-testing)
   - [Excluido del Testing](#excluido-del-testing)
4. [Estrategia de Testing](#estrategia-de-testing)
   - [Enfoque](#enfoque)
   - [Tipos de Testing](#tipos-de-testing)
   - [Herramientas](#herramientas)
5. [Plan de Casos de Prueba](#plan-de-casos-de-prueba)
6. [Criterios de Aceptación](#criterios-de-aceptación)
7. [Observaciones Finales](#observaciones-finales)
   - [Posibles Bugs a Detectar](#posibles-bugs-a-detectar)
   - [Problemas de Usabilidad](#problemas-de-usabilidad)
   - [Sugerencias de Mejora](#sugerencias-de-mejora)

## Introducción

La **Plataforma Gestión** es una aplicación híbrida que combina una aplicación web desarrollada con Django y una aplicación de escritorio basada en Tkinter. Su objetivo principal es facilitar la gestión de proyectos y tareas, analizar el mercado laboral mediante scraping de ofertas de empleo (de plataformas como Tecnoempleo, InfoJobs y LinkedIn), y proporcionar recomendaciones basadas en un motor de IA para asignación de tareas y predicción de tendencias de habilidades. La aplicación incluye módulos para gestión de usuarios, proyectos, análisis de mercado, y un motor de IA, con una base de datos PostgreSQL para almacenar datos.

Este plan de testing tiene como propósito garantizar que las funcionalidades principales de la aplicación (web y escritorio) sean operativas, confiables y usables, verificando que cumplan con los requisitos funcionales y no funcionales descritos en la documentación técnica.

## Objetivo del Testing

El objetivo del testing es verificar que las funcionalidades críticas de la aplicación funcionen correctamente, asegurando que:
- Los usuarios puedan registrarse, iniciar sesión, y gestionar proyectos y tareas sin errores.
- El módulo de scraping recopile datos de ofertas de empleo de forma precisa.
- El motor de IA proporcione recomendaciones de tareas y predicciones de habilidades coherentes.
- La interfaz web (Django) y de escritorio (Tkinter) sean intuitivas y manejen correctamente los flujos de usuario.
- No existan errores críticos que afecten la experiencia del usuario o la integridad de los datos.

## Alcance del Testing

### Incluido en el Testing
- **Aplicación Web (Django)**:
  - Registro e inicio de sesión de usuarios.
  - Gestión de proyectos y tareas (creación, edición, asignación).
  - Visualización y filtrado de ofertas de empleo.
  - Ejecución del scraping de ofertas (Tecnoempleo, InfoJobs, LinkedIn).
  - Visualización de tendencias de mercado y recomendaciones de IA.
  - Gestión de usuarios (solo para administradores).
- **Aplicación de Escritorio (Tkinter)**:
  - Inicio de sesión.
  - Gestión de proyectos y tareas (visualización, creación, edición).
  - Visualización de ofertas de empleo.
  - Gestión de usuarios (solo para administradores).
- **Base de Datos**: Verificación de la integridad de datos en PostgreSQL (por ejemplo, creación de registros, relaciones muchos-a-muchos).

### Excluido del Testing
- Funcionalidades de administración interna avanzada (por ejemplo, configuración de permisos detallados).
- Pruebas de rendimiento bajo cargas altas (>100 usuarios concurrentes).
- Pruebas de seguridad avanzadas (por ejemplo, pruebas de penetración).
- Pruebas de compatibilidad en navegadores poco comunes (por ejemplo, Safari en versiones antiguas).
- Pruebas de la interfaz de escritorio en sistemas operativos no estándar (por ejemplo, Linux sin entorno gráfico).

## Estrategia de Testing

### Enfoque
- **Pruebas Manuales**: Todas las pruebas se realizarán manualmente, ya que no se utilizarán herramientas de automatización en esta fase.
- **Entornos**:
  - **Web**: Pruebas en un navegador moderno (Google Chrome, última versión) en un entorno local (`http://localhost:8000`) o desplegado en la nube (por ejemplo, AWS Elastic Beanstalk).
  - **Escritorio**: Pruebas en un sistema Windows 10/11 con Python 3.10 y Tkinter instalado.
- **Datos de Prueba**: Se usarán datos ficticios para usuarios, proyectos, tareas, y ofertas de empleo. Para el scraping, se probará con credenciales válidas de LinkedIn y 2Captcha.

### Tipos de Testing
1. **Pruebas Funcionales**: Verificar que cada funcionalidad (registro, creación de proyectos, scraping, etc.) cumpla con los requisitos.
2. **Pruebas de Validaciones**: Comprobar que los formularios y entradas manejen correctamente datos válidos e inválidos.
3. **Pruebas de Flujo de Usuario**: Validar que los flujos principales (por ejemplo, registrar usuario → crear proyecto → asignar tarea) sean intuitivos y sin interrupciones.
4. **Pruebas de Interfaz**: Asegurar que las interfaces web y de escritorio sean consistentes, responsivas, y libres de errores visuales.
5. **Pruebas de Integridad de Datos**: Confirmar que los datos se almacenen correctamente en PostgreSQL y que las relaciones (por ejemplo, Task-Skill) sean precisas.

### Herramientas
- **Navegador**: Google Chrome para pruebas web.
- **Entorno Local**: Servidor Django (`python manage.py runserver`) y script Tkinter (`main.py`).
- **Base de Datos**: DBeaver o pgAdmin para inspeccionar datos en PostgreSQL.
- **Logs**: Consola de Django y logs de la aplicación de escritorio para depuración.

## Plan de Casos de Prueba

La siguiente tabla presenta los casos de prueba, incluyendo al menos 10 casos, con 3 casos negativos. Los casos cubren las funcionalidades principales de la aplicación web y de escritorio, con énfasis en los flujos críticos.

| Nº | Caso de Prueba | Pasos | Resultado Esperado | Resultado Real | Estado (OK/Falla) |
|----|----------------|-------|--------------------|----------------|-------------------|
| 1 | Registro de usuario (Web) | 1. Abrir `/users/manage/create/`.<br>2. Completar formulario con datos válidos (username: testuser, email: test@example.com, password: Test1234!).<br>3. Enviar formulario. | Usuario creado; redirige al login con mensaje de éxito. | (Pendiente) | (Pendiente) |
| 2 | Inicio de sesión (Web) | 1. Abrir `/login/`.<br>2. Ingresar credenciales válidas (username: testuser, password: Test1234!).<br>3. Hacer clic en "Iniciar Sesión". | Redirige al dashboard del usuario. | (Pendiente) | (Pendiente) |
| 3 | Creación de proyecto (Web) | 1. Iniciar sesión como Gestor de Proyectos o Administrador.<br>2. Ir a `/projects/`.<br>3. Hacer clic en "Crear Proyecto".<br>4. Completar formulario (nombre: Proyecto1, descripción: Test).<br>5. Enviar. | Proyecto creado; aparece en la lista de proyectos. | (Pendiente) | (Pendiente) |
| 4 | Asignación de tarea (Web) | 1. Iniciar sesión como Gestor de Proyectos.<br>2. Ir a un proyecto.<br>3. Crear tarea (título: Tarea1, descripción: Test, asignar a usuario con habilidades coincidentes).<br>4. Guardar. | Tarea creada y asignada; visible en el proyecto. | (Pendiente) | (Pendiente) |
| 5 | Scraping de ofertas (Web) | 1. Iniciar sesión como Administrador.<br>2. Ir a `/market_analysis/dashboard/`.<br>3. Hacer clic en "Actualizar Ofertas".<br>4. Esperar resultados. | Nuevas ofertas de empleo (Tecnoempleo, InfoJobs, LinkedIn) aparecen en la lista. | (Pendiente) | (Pendiente) |
| 6 | Visualización de tendencias de mercado (Web) | 1. Iniciar sesión como usuario.<br>2. Ir a `/market_analysis/dashboard/`.<br>3. Ver gráfico de tendencias de habilidades. | Gráfico se muestra correctamente con datos coherentes (por ejemplo, Python con alta demanda). | (Pendiente) | (Pendiente) |
| 7 | Inicio de sesión (Escritorio) | 1. Ejecutar `main.py`.<br>2. Ingresar credenciales válidas (username: testuser, password: Test1234!).<br>3. Hacer clic en "Iniciar Sesión". | Se muestra el menú principal con opciones de navegación. | (Pendiente) | (Pendiente) |
| 8 | Gestión de usuarios (Escritorio) | 1. Iniciar sesión como Admin.<br>2. Ir a "Gestión de Usuarios".<br>3. Crear usuario (username: newuser, rol: Collaborator).<br>4. Guardar. | Usuario creado; aparece en la lista de usuarios. | (Pendiente) | (Pendiente) |
| 9 | **Caso Negativo**: Registro con email inválido (Web) | 1. Abrir `/users/manage/create/`.<br>2. Completar formulario con email inválido (username: testuser2, email: invalid, password: Test1234!).<br>3. Enviar formulario. | Mensaje de error: "Email inválido"; registro no se completa. | (Pendiente) | (Pendiente) |
| 10 | **Caso Negativo**: Inicio de sesión con contraseña incorrecta (Web) | 1. Abrir `/login/`.<br>2. Ingresar credenciales inválidas (username: testuser, password: WrongPass).<br>3. Hacer clic en "Iniciar Sesión". | Mensaje de error: "Credenciales inválidas"; no redirige al dashboard. | (Pendiente) | (Pendiente) |
| 11 | **Caso Negativo**: Creación de tarea sin asignados (Web) | 1. Iniciar sesión como Gestor de Proyectos.<br>2. Ir a un proyecto.<br>3. Crear tarea sin asignar usuarios (título: Tarea2, descripción: Test).<br>4. Guardar. | Mensaje de error: "Debe asignar al menos un usuario"; tarea no se crea. | (Pendiente) | (Pendiente) |
| 12 | Visualización de ofertas de empleo (Escritorio) | 1. Iniciar sesión como Colaborador.<br>2. Ir a "Ofertas de Empleo".<br>3. Ver lista de ofertas en Treeview. | Lista de ofertas se muestra correctamente con título, empresa, y ubicación. | (Pendiente) | (Pendiente) |

### Notas sobre los Casos de Prueba
- Los casos cubren las funcionalidades principales descritas en la documentación (registro, login, proyectos, tareas, scraping, tendencias, gestión de usuarios).
- Los casos negativos verifican el manejo de errores en formularios y autenticación, que son críticos para la usabilidad.
- Los casos para la aplicación de escritorio se centran en flujos similares a la web, pero adaptados a la interfaz Tkinter (por ejemplo, Treeview para listas).

## Criterios de Aceptación

La aplicación se considerará aprobada si se cumplen los siguientes criterios:
1. **100% de los casos críticos pasan**: Los casos 1, 2, 3, 4, 5, 7, y 8 (registro, login, creación de proyectos/tareas, scraping, gestión de usuarios) deben tener estado "OK".
2. **Casos negativos manejan errores correctamente**: Los casos 9, 10, y 11 deben mostrar mensajes de error claros y no permitir acciones inválidas.
3. **No se detectan errores críticos**: No deben existir fallos que impidan el uso de funcionalidades principales (por ejemplo, crashes, datos corruptos).
4. **Integridad de datos**: Las operaciones CRUD (crear, leer, actualizar, eliminar) en usuarios, proyectos, tareas, y ofertas deben reflejarse correctamente en PostgreSQL.
5. **Usabilidad básica**: Las interfaces web y de escritorio deben ser navegables sin errores visuales o de interacción evidentes.

If algún caso crítico falla, se reportará como defecto crítico y se corregirá antes de aprobar la aplicación. Los casos no críticos (por ejemplo, visualización de tendencias) que fallen se considerarán defectos menores y se priorizarán para corrección en iteraciones futuras.

## Observaciones Finales

### Posibles Bugs a Detectar
- **Scraping**: El scraping de LinkedIn podría fallar si las credenciales expiran o si la estructura de la página cambia, lo que requiere monitoreo continuo.
- **Interfaz de Escritorio**: La aplicación Tkinter podría tener problemas de responsividad en pantallas de alta resolución o sistemas operativos no probados (por ejemplo, macOS).
- **Validaciones**: Los formularios web podrían no manejar correctamente caracteres especiales o entradas largas, lo que debe probarse exhaustivamente.
- **IA**: Las recomendaciones de tareas podrían ser imprecisas si los datos de habilidades no están bien estructurados, lo que requiere validación de los resultados.

### Problemas de Usabilidad
- **Web**: La interfaz podría beneficiarse de retroalimentación más clara en formularios (por ejemplo, mensajes de error en tiempo real).
- **Escritorio**: La navegación en Tkinter puede ser menos intuitiva que en la web; los botones y Treeview podrían necesitar etiquetas más descriptivas.
- **Consistencia**: Las interfaces web y de escritorio deben usar terminología y estilos visuales consistentes para evitar confusión.

### Sugerencias de Mejora
1. **Pruebas Automáticas**: Implementar pruebas unitarias con `unittest` (Django) para los modelos y vistas, y pruebas de integración para los flujos principales.
2. **Validación Mejorada**: Añadir validaciones en el frontend (JavaScript para la web, validaciones en Tkinter) para reducir errores del usuario antes de enviar formularios.
3. **Monitoreo de Scraping**: Configurar alertas para detectar fallos en el scraping (por ejemplo, usando CloudWatch en AWS o Logging en GCP).
4. **Optimización de IA**: Validar las predicciones de habilidades con datos históricos para mejorar la precisión del motor de IA.
5. **Pruebas de Rendimiento**: Realizar pruebas de carga para verificar el comportamiento con 100 usuarios concurrentes, especialmente en el módulo de scraping.

Este plan de testing proporciona una base sólida para garantizar la calidad de la **Plataforma Gestión**. Se recomienda ejecutar las pruebas en un entorno controlado, documentar los resultados reales, y priorizar la corrección de defectos críticos antes del despliegue final.