from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Sucursal, Libro, Ejemplar, Prestamo


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin básico para Usuario"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'multas_pendientes', 'suspendido')
    list_filter = ('rol', 'suspendido', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Biblioteca', {
            'fields': ('rol', 'telefono', 'multas_pendientes', 'suspendido')
        }),
    )


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    """Admin básico para Sucursal"""
    list_display = ('nombre', 'telefono', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre', 'direccion')


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    """Admin básico para Libro"""
    list_display = ('titulo', 'autor', 'isbn', 'genero', 'año_publicacion', 'activo')
    list_filter = ('genero', 'activo', 'año_publicacion')
    search_fields = ('titulo', 'autor', 'isbn')
    readonly_fields = ('isbn',)


@admin.register(Ejemplar)
class EjemplarAdmin(admin.ModelAdmin):
    """Admin básico para Ejemplar"""
    list_display = ('libro', 'sucursal', 'codigo_barras', 'estado')
    list_filter = ('estado', 'sucursal')
    search_fields = ('libro__titulo', 'codigo_barras')


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    """Admin básico para Prestamo"""
    list_display = ('usuario', 'ejemplar', 'fecha_prestamo', 'fecha_devolucion_esperada', 'estado', 'multa')
    list_filter = ('estado', 'fecha_prestamo')
    search_fields = ('usuario__username', 'ejemplar__libro__titulo')
    readonly_fields = ('fecha_prestamo', 'fecha_devolucion_esperada')
