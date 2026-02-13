# Leal Café - Sistema de Gestión

Sistema web integral para la administración de ventas, reportes y contabilidad de Leal Café.

## Características

- **Autenticación de Usuarios**: Login y registro con roles (admin/usuario)
- **Gestión de Ventas**: Carga masiva desde Excel, visualización y reportes
- **Reportes Analíticos**: Dashboard de ventas, productos más vendidos
- **Contabilidad**: Registro de gastos y resumen financiero
- **Diseño Moderno**: Interfaz profesional con paleta de colores café/tierra

## Stack Tecnológico

- **Backend**: Flask (Python) con arquitectura modular (Blueprints)
- **Base de Datos**: PostgreSQL para almacenamiento relacional
- **Frontend**: HTML5, CSS3 vanilla, JavaScript vanilla
- **Librerías**: Font Awesome, Google Fonts (Poppins), ExcelJS, SheetJS
- **Deployment**: Render (Web Service + PostgreSQL)

## Paleta de Colores

```css
--primary-color: #6F4E37;        /* Café intenso */
--primary-dark: #5D4029;         /* Café oscuro */
--secondary-color: #3E2723;      /* Marrón oscuro (sidebar) */
--accent-color: #D4A574;         /* Crema dorada */
--success-color: #7CB342;        /* Verde natural */
--warning-color: #F57C00;        /* Naranja cálido */
```

## Estructura del Proyecto

```
leal_cafe/
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   ├── variables.css        # Variables de diseño
│   │   │   ├── components.css       # Componentes reutilizables
│   │   │   ├── dashboard.css        # Estilos del dashboard
│   │   │   └── login.css            # Estilos de autenticación
│   │   ├── js/
│   │   │   └── utils.js             # Funciones JavaScript
│   │   └── images/
│   │       └── logo.png
│   ├── templates/
│   │   ├── base.html                # Plantilla base
│   │   ├── dashboard.html           # Dashboard principal
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── registro.html
│   │   ├── ventas/
│   │   │   ├── index.html
│   │   │   └── cargar.html
│   │   ├── reportes/
│   │   │   ├── index.html
│   │   │   └── productos.html
│   │   └── contabilidad/
│   │       ├── index.html
│   │       └── resumen.html
│   ├── auth/                        # Módulo de autenticación
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── database.py
│   ├── ventas/                      # Módulo de ventas
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── database.py
│   ├── reportes/                    # Módulo de reportes
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── database.py
│   ├── contabilidad/                # Módulo de contabilidad
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── database.py
│   ├── app.py                       # Punto de entrada
│   ├── config.py                    # Configuración
│   └── database.py                  # Funciones de BD globales
├── uploads/                         # Archivos temporales
├── requirements.txt
└── README.md
```

## Instalación

### 1. Requisitos Previos

- Python 3.11+
- PostgreSQL instalado y corriendo
- pip (gestor de paquetes de Python)

### 2. Clonar Repositorio

```bash
git clone <tu-repositorio>
cd leal_cafe
```

### 3. Crear Entorno Virtual (Recomendado)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 4. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar Variables de Entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Edita `.env` con tus configuraciones locales:

```
SECRET_KEY=tu-clave-secreta-aleatoria
FLASK_ENV=development
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu-password
POSTGRES_DATABASE=leal_cafe
```

### 6. Crear Base de Datos

```sql
CREATE DATABASE leal_cafe;
```

### 7. Ejecutar la Aplicación

```bash
python wsgi.py
```

O para desarrollo:

```bash
cd app
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

## Primer Uso

1. **Accede a** `http://localhost:5000`
2. **Registro**: Crea tu cuenta en `/auth/registro`
3. **Login**: Inicia sesión con tus credenciales
4. **Dashboard**: Verás el dashboard principal con accesos rápidos

## Módulos Principales

### 🔐 Autenticación
- Login/Logout
- Registro de usuarios
- Gestión de perfiles
- Control de acceso por roles

### 💰 Ventas
- **Carga masiva**: Importa ventas desde Excel
- **Visualización**: Tabla con todas las ventas
- **Filtros**: Por fecha, producto
- **Exportación**: Descarga a Excel

### 📊 Reportes
- **Dashboard de ventas**: KPIs principales
- **Productos más vendidos**: Top 50 productos
- **Análisis temporal**: Ventas por día/mes

### 🧮 Contabilidad
- **Registro de gastos**: Por categoría
- **Resumen financiero**: Ingresos, gastos, utilidad
- **Margen de utilidad**: Cálculo automático

## Formato de Excel para Ventas

El archivo Excel debe tener las siguientes columnas:

| Fecha | Producto | Cantidad | Precio Unitario | Total (opcional) |
|-------|----------|----------|-----------------|------------------|
| 2024-01-15 | Café Americano | 2 | 45.00 | 90.00 |
| 2024-01-15 | Cappuccino | 1 | 55.00 | 55.00 |

- **Fecha**: Formato YYYY-MM-DD o DD/MM/YYYY
- **Producto**: Nombre del producto
- **Cantidad**: Número de unidades
- **Precio Unitario**: Precio por unidad
- **Total**: Se calcula automáticamente si no se proporciona

## Base de Datos

### Tablas Principales

**usuarios**
- id, nombre, apellido, email, password, rol, activo, fecha_creacion

**ventas**
- id, fecha, producto, cantidad, precio_unitario, total, usuario_id, fecha_carga

**productos**
- id, nombre, categoria, precio, activo, fecha_creacion

**gastos**
- id, fecha, concepto, categoria, monto, comprobante, usuario_id, fecha_registro

## Tecnologías de Frontend

- **Google Fonts**: Poppins (300, 400, 500, 600, 700)
- **Font Awesome**: v6.4.0 para iconos
- **ExcelJS**: v4.3.0 para exportar a Excel
- **SheetJS (XLSX)**: v0.18.5 para leer Excel

## Seguridad

- Contraseñas hasheadas con Werkzeug
- Sesiones seguras con Flask
- Validación de inputs en frontend y backend
- Protección contra inyección SQL con queries parametrizadas

## Variables de Entorno

Archivo `.env` para desarrollo local:

```
SECRET_KEY=tu-clave-secreta-aqui
FLASK_ENV=development
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu-password
POSTGRES_DATABASE=leal_cafe
```

Para producción en Render, usa `DATABASE_URL`:

```
SECRET_KEY=<generada-por-render>
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:port/db
```

## Deployment en Render

Para deployar esta aplicación en Render, consulta la guía completa en [DEPLOYMENT.md](DEPLOYMENT.md).

**Resumen rápido:**
1. Crea una base de datos PostgreSQL en Render
2. Crea un Web Service conectado a tu repositorio GitHub
3. Configura las variables de entorno
4. Render automáticamente desplegará tu app

**Archivos importantes para deployment:**
- `wsgi.py` - Punto de entrada WSGI
- `Procfile` - Comando de inicio para Gunicorn
- `render.yaml` - Configuración de Render (opcional)
- `requirements.txt` - Dependencias Python

## Desarrollo

### Agregar Nuevo Módulo

1. Crear carpeta en `app/nombre_modulo/`
2. Crear `__init__.py`, `routes.py`, `database.py`
3. Registrar Blueprint en `app.py`
4. Crear templates en `templates/nombre_modulo/`

### Componentes CSS Reutilizables

Consulta `static/css/components.css` para:
- Botones (.btn-primary, .btn-secondary, etc.)
- Formularios (.form-group, .form-control)
- Tablas (.data-table)
- Cards (.card, .section-box)
- Alertas (.alert-success, .alert-danger, etc.)
- Badges (.badge-primary, .badge-success, etc.)

## Soporte

Para reportar problemas o sugerencias, contacta al equipo de desarrollo.

## Licencia

Proyecto propietario de Leal Café © 2024
