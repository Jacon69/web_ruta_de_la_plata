# Ficha Técnica - Plataforma Web Colegio Ruta de la Plata

Este repositorio contiene la plataforma web completa para el **Colegio Ruta de la Plata** (Santa Olalla del Cala, Huelva), gestionado por la cooperativa de enseñanza **Ruta De La Plata S C And Scoop**. La plataforma integra un portal público informativo interactivo y un panel de gestión interno (intranet) con control de acceso basado en roles y registro inmutable de auditoría.

---

## 🛠️ Especificaciones Técnicas

### 1. Arquitectura de Software
- **Modelo:** Arquitectura monolítica ligera cliente-servidor.
- **Backend:** Python 3 con **Flask** (Microframework web de alta velocidad).
- **Frontend:** **HTML5 semántico**, **JavaScript clásico (ES6)** y **CSS3 Vanilla** utilizando variables customizadas (CSS Custom Properties) para garantizar una carga veloz y compatibilidad total sin dependencias externas pesadas.
- **Base de Datos:** **SQLite3**, integrada en archivo físico local (`backend/db/school.db`), garantizando máxima portabilidad y cero configuración de servicios.

### 2. Sistema de Seguridad y Roles
- **Cifrado de Contraseñas:** PBKDF2 con hash SHA256 mediante la biblioteca `werkzeug.security`.
- **Manejo de Sesiones:** Cookies de sesión firmadas criptográficamente en el servidor mediante clave secreta única.
- **Control de Acceso Basado en Roles (RBAC):** Endpoints protegidos mediante decoradores que restringen el acceso según los siguientes cuatro perfiles del plan anual:

| Rol | Gestión de Noticias | Gestión de Documentos | Gestión del Menú Comedor | Bandeja de Admisiones | Registros de Auditoría (Logs) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SuperAdmin** | Lectura/Escritura | Lectura/Escritura | Lectura/Escritura | Lectura | Lectura |
| **Dirección** | Lectura/Escritura | Lectura/Escritura | Lectura/Escritura | Lectura | Lectura |
| **Administrativo** | Lectura/Escritura | Lectura/Escritura | Lectura/Escritura | Lectura | 🚫 Sin Acceso |
| **Profesor** | Lectura/Escritura | 🚫 Sin Acceso | 🚫 Sin Acceso | 🚫 Sin Acceso | 🚫 Sin Acceso |

### 3. Registro de Auditoría Inmutable (Activity Logs)
Cumpliendo con los estándares de seguridad administrativa, el sistema implementa una tabla de logs inmutable desde la aplicación:
- **Datos guardados:** Fecha/Hora del evento, ID de usuario, Nombre de usuario, Acción realizada (Ej. `UPDATE_NEWS`), Detalles del cambio y Dirección IP del cliente.
- **Restricción:** No se han expuesto rutas ni endpoints de actualización (`PUT`) o eliminación (`DELETE`) para los logs. La tabla es estrictamente de adición de registros y lectura protegida.

---

## 🎨 Identidad Visual y Diseño (UI/UX)

De acuerdo con el manual de identidad del centro, la interfaz implementa las siguientes directrices visuales:

- **Paleta de Colores Corporativos:**
  - `Verde Oscuro (#41644A)`: Color de marca principal, encabezados, bordes y elementos activos.
  - `Crema Claro (#F1F0E9)`: Color de fondo general, proporcionando un contraste suave y elegante.
  - `Gris Oscuro (#191919)`: Color base para todos los textos legibles.
  - `Blanco (#FFFFFF)`: Fondos de tarjetas y contenedores elevados.
  - `Detalles / Acentos`: Azul (`#4379F2`), Amarillo (`#FFEB00`), Verde Claro (`#6EC207`), Teal (`#1D7A85`), Rojo (`#E21916`) y Forest Green (`#3C6348`).
- **Tipografías:**
  - **Montserrat**: Aplicada a títulos, botones y menús para un impacto visual moderno y limpio.
  - **Alegreya Sans**: Aplicada a textos de cuerpo para asegurar una lectura cómoda y fluida.
- **Diseño Responsive:** Grid y Flexbox adaptados para todo tipo de pantallas (Mobile-friendly, tablets y escritorio).
- **Estética Premium:** Efectos de glassmorphism (desenfoque de fondo en barra de navegación y ventanas modales) con micro-animaciones en hover y transiciones fluidas.

---

## 📂 Estructura de Carpetas

```
school_platform/
├── backend/
│   ├── app.py                # Servidor principal, APIs y enrutamiento
│   ├── database.py           # Conexión SQLite, esquema de tablas y semilla
│   ├── auth.py               # Módulo de autenticación y decoradores RBAC
│   ├── logs.py               # Generación y almacenamiento de logs de auditoría
│   ├── db/
│   │   └── school.db         # Archivo físico de base de datos SQLite
│   └── uploads/              # Carpeta física donde se guardan los PDFs cargados
├── frontend/
│   ├── index.html            # Web pública informativa (6 secciones)
│   ├── admin.html            # Interfaz de gestión e Intranet
│   ├── css/
│   │   └── styles.css        # Hoja de estilos con variables y diseño premium
│   └── js/
│       ├── app.js            # Lógica pública y AJAX del formulario
│       └── admin.js          # Controladores de la Intranet y CRUD
├── venv/                     # Entorno virtual de Python
└── README.md                 # Ficha técnica del proyecto
```

---

## 🚀 Instalación y Despliegue Local

### Requisitos Previos
- Python 3 instalado en el sistema.

### Instrucciones de Configuración
1. **Entrar al directorio del proyecto:**
   ```bash
   cd school_platform
   ```

2. **Crear e iniciar el entorno virtual de Python:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias necesarias (Flask, Requests, Pillow, python-pptx):**
   ```bash
   pip install Flask requests pillow python-pptx
   ```

4. **Inicializar y sembrar la Base de Datos:**
   ```bash
   PYTHONPATH=. python3 backend/database.py
   ```

5. **Lanzar el Servidor en modo desarrollo:**
   ```bash
   PYTHONPATH=. python3 backend/app.py
   ```

El servidor web estará disponible de inmediato en:
- **Sitio Público:** [http://localhost:5000](http://localhost:5000)
- **Panel Administrativo:** [http://localhost:5000/admin.html](http://localhost:5000/admin.html)

### Cuentas Sembradas para Pruebas (Contraseña común: `plata2026`):
- **SuperAdmin:** `admin`
- **Dirección:** `director`
- **Administrativo:** `staff`
- **Profesor:** `profesor`
