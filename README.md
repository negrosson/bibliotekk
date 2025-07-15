# 📚 Sistema de Biblioteca - Django REST Framework

API REST completa para gestionar una biblioteca digital con múltiples sucursales, sistema de reservas, transferencias y reportes avanzados.

## 🚀 Características Implementadas

### ✅ Fase 1 - Básico (Completado)
- **Modelos básicos**: Usuario, Sucursal, Libro, Ejemplar, Préstamo
- **Autenticación JWT**: Login, registro, tokens de acceso
- **CRUD básico**: Libros y sucursales
- **Sistema de préstamos**: Crear, devolver, validaciones básicas
- **Permisos por rol**: Usuario, bibliotecario, administrador

### ✅ Fase 2 - Sistema de Reservas (Completado)
- **Cola de reservas**: Sistema FIFO automático
- **Gestión de reservas**: Crear, cancelar, procesar automáticamente
- **Posicionamiento**: Cálculo automático de posición en cola
- **Notificaciones**: Procesamiento automático al devolver libros

### ✅ Fase 3 - Transferencias entre Sucursales (Completado)
- **Transferencia de ejemplares**: Entre sucursales
- **Validaciones**: Solo ejemplares disponibles
- **Inventario por sucursal**: Reportes detallados
- **Gestión de ubicaciones**: Control de stock por sucursal

### ✅ Fase 4 - Reportes y Estadísticas (Completado)
- **Libros más populares**: Ranking de préstamos
- **Préstamos vencidos**: Con cálculo de multas
- **Usuarios con multas**: Reporte de deudores
- **Estadísticas generales**: Métricas del sistema
- **Inventarios**: Por sucursal y estado

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repo>
cd bossback
```

2. **Crear entorno virtual**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Aplicar migraciones**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Crear superusuario**
```bash
python manage.py createsuperuser
```

6. **Ejecutar servidor**
```bash
python manage.py runserver
```

## 📋 Endpoints Disponibles

### 🔐 Autenticación
- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/register/` - Registrar usuario

### 📚 Libros
- `GET /api/libros/` - Listar libros
- `POST /api/libros/` - Crear libro (bibliotecario/admin)
- `GET /api/libros/{id}/` - Obtener libro
- `PUT /api/libros/{id}/` - Actualizar libro (bibliotecario/admin)
- `DELETE /api/libros/{id}/` - Eliminar libro (bibliotecario/admin)
- `GET /api/libros/buscar/` - Buscar libros

### 🏢 Sucursales
- `GET /api/sucursales/` - Listar sucursales
- `POST /api/sucursales/` - Crear sucursal (admin)
- `GET /api/sucursales/{id}/` - Obtener sucursal
- `PUT /api/sucursales/{id}/` - Actualizar sucursal (admin)

### 📖 Préstamos
- `GET /api/prestamos/` - Listar préstamos
- `POST /api/prestamos/` - Crear préstamo
- `PATCH /api/prestamos/{id}/devolver/` - Devolver préstamo
- `GET /api/prestamos/activos/` - Préstamos activos
- `GET /api/prestamos/vencidos/` - Préstamos vencidos (admin/bibliotecario)

### 📋 Reservas
- `GET /api/reservas/` - Listar reservas
- `POST /api/reservas/` - Crear reserva
- `DELETE /api/reservas/{id}/cancelar/` - Cancelar reserva
- `GET /api/reservas/cola/{libro_id}/` - Ver cola de reservas

### 📦 Ejemplares
- `GET /api/ejemplares/` - Listar ejemplares
- `POST /api/ejemplares/` - Crear ejemplar (admin/bibliotecario)
- `POST /api/ejemplares/{id}/transferir/` - Transferir ejemplar

### 📊 Reportes
- `GET /api/reportes/` - Reportes generales (admin/bibliotecario)
- `GET /api/sucursales/{id}/inventario/` - Inventario por sucursal

### 👤 Usuario
- `GET /api/usuarios/perfil/` - Ver perfil
- `PUT /api/usuarios/perfil/` - Actualizar perfil
- `GET /api/usuarios/mis-prestamos/` - Mis préstamos
- `GET /api/usuarios/mis-reservas/` - Mis reservas
- `POST /api/usuarios/pagar-multa/` - Pagar multas

## 🔑 Autenticación

Usar JWT tokens en el header:
```
Authorization: Bearer <access_token>
```

## 📊 Roles y Permisos

- **Usuario**: Ver libros, crear préstamos propios, ver perfil
- **Bibliotecario**: Gestionar libros, todos los préstamos
- **Administrador**: Acceso completo

## 💾 Base de Datos

Usando SQLite por defecto. Los modelos incluyen:
- **Usuario**: Extendido con roles y multas
- **Sucursal**: Información básica de sucursales
- **Libro**: Catálogo de libros
- **Ejemplar**: Copias físicas por sucursal
- **Préstamo**: Gestión de préstamos con multas

## 📝 Validaciones Implementadas

- ✅ Máximo 3 préstamos activos por usuario
- ✅ No préstamos si hay multas pendientes
- ✅ Préstamos de 14 días máximo
- ✅ Cálculo automático de multas (1000.00 por día de retraso)
- ✅ Validación de disponibilidad de ejemplares
- ✅ Sistema de cola FIFO para reservas
- ✅ Una reserva activa por libro por usuario
- ✅ Transferencias solo de ejemplares disponibles
- ✅ Eliminación lógica (no física) de registros
- ✅ Validación de ISBN único para libros
- ✅ Validación de código de barras único para ejemplares

## 🔧 Tecnologías

- **Django 4.2.7**
- **Django REST Framework 3.14.0**
- **JWT Authentication** (Simple JWT)
- **MySQL** (configurado para XAMPP)
- **SQLite** (desarrollo local)

## 📊 Base de Datos

### Modelos Implementados
- **Usuario**: Extendido con roles, multas y validaciones
- **Sucursal**: Gestión de múltiples ubicaciones
- **Libro**: Catálogo con ISBN único
- **Ejemplar**: Copias físicas con código de barras único
- **Préstamo**: Gestión completa con multas automáticas
- **Reserva**: Sistema de cola FIFO automático

### Migraciones Incluidas
- `0001_initial.py`: Estructura base de modelos
- `0002_reserva.py`: Sistema de reservas

## 🎯 Estado del Proyecto

**✅ COMPLETADO** - Todas las fases implementadas y funcionales

### Funcionalidades Principales
- 🔐 Autenticación JWT completa
- 📚 Gestión completa de libros y ejemplares
- 🏢 Sistema multi-sucursal
- 📖 Préstamos con validaciones automáticas
- 📋 Reservas con cola FIFO
- 📦 Transferencias entre sucursales
- 📊 Reportes y estadísticas avanzadas
- 💰 Sistema de multas automático
- 👥 Gestión de roles y permisos 