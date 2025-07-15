# URLs PARA VISTAS - SISTEMA DE BIBLIOTECA CON MIXINS DRF

from django.urls import path
from . import views as v

urlpatterns = [
    # ============================================================================
    # AUTENTICACIÓN - LOGIN, REGISTER, REFRESH TOKEN
    # ============================================================================
    path('login/', v.LoginAPI.as_view(), name='login-api'),
    path('register/', v.RegistroAPI.as_view(), name='register-api'),
    path('refresh/', v.RefreshTokenAPI.as_view(), name='refresh-token-api'),
    
    # ============================================================================
    # GESTIÓN DE LIBROS - CRUD CON MIXINS DRF
    # ============================================================================
    path('libros/', v.LibroAPI.as_view(), name='libro-api'), #sirve para obtener la lista de libros, libro-api esta definido en views.py
    path('libros/<int:pk>/', v.LibroDetailAPI.as_view(), name='libro-detail-api'),# en especifico
    path('libros/<int:libro_id>/disponibilidad/', v.disponibilidad_libro_api, name='disponibilidad-libro-api'),#sirve para obtener la disponibilidad de un libro en todas las sucursales
    path('libros/buscar/', v.buscar_libros_api, name='buscar-libros-api'),#sirve para buscar libros por titulo, autor, género o disponibilidad
    
    # ============================================================================
    # GESTIÓN DE USUARIOS - PERFIL, ACTUALIZACIÓN, HISTORIAL
    # ============================================================================
    path('usuarios/perfil/', v.perfil_usuario_api, name='perfil-usuario-api'),#sirve para obtener el perfil del usuario
    path('usuarios/perfil/actualizar/', v.actualizar_perfil_api, name='actualizar-perfil-api'),
    path('usuarios/historial-prestamos/', v.historial_prestamos_api, name='historial-prestamos-api'),
    path('usuarios/mis-reservas/', v.mis_reservas_api, name='mis-reservas-api'),
    path('usuarios/pagar-multa/', v.pagar_multa_api, name='pagar-multa-api'),
    
    # ============================================================================
    # GESTIÓN DE SUCURSALES - CRUD CON MIXINS DRF
    # ============================================================================
    path('sucursales/', v.SucursalAPI.as_view(), name='sucursal-api'), #sirve para obtener la lista de sucursales
    path('sucursales/<int:pk>/', v.SucursalDetailAPI.as_view(), name='sucursal-detail-api'),#en especifico
    path('sucursales/<int:sucursal_id>/inventario/', v.inventario_sucursal_api, name='inventario-sucursal-api'),#sirve para obtener el inventario de una sucursal
    
    # ============================================================================
    # GESTIÓN DE EJEMPLARES - CRUD CON MIXINS DRF
    # ============================================================================
    path('ejemplares/', v.EjemplarAPI.as_view(), name='ejemplar-api'),
    path('ejemplares/<int:pk>/', v.EjemplarDetailAPI.as_view(), name='ejemplar-detail-api'),
    path('ejemplares/<int:ejemplar_id>/transferir/', v.transferir_ejemplar_api, name='transferir-ejemplar-api'),
    
    # ============================================================================
    # GESTIÓN DE PRÉSTAMOS - CRUD CON MIXINS DRF
    # ============================================================================
    path('prestamos/', v.PrestamoAPI.as_view(), name='prestamo-api'),
    path('prestamos/<int:pk>/', v.PrestamoDetailAPI.as_view(), name='prestamo-detail-api'),
    path('prestamos/<int:prestamo_id>/devolver/', v.devolver_prestamo_api, name='devolver-prestamo-api'),
    path('prestamos/activos/', v.prestamos_activos_api, name='prestamos-activos-api'),
    path('prestamos/vencidos/', v.prestamos_vencidos_api, name='prestamos-vencidos-api'),
    
    # ============================================================================
    # SISTEMA DE RESERVAS - CRUD CON MIXINS DRF
    # ============================================================================
    path('reservas/', v.ReservaAPI.as_view(), name='reserva-api'),
    path('reservas/<int:reserva_id>/cancelar/', v.cancelar_reserva_api, name='cancelar-reserva-api'),
    path('reservas/cola/<int:libro_id>/', v.cola_reservas_api, name='cola-reservas-api'),
    
    # ============================================================================
    # REPORTES - CON MIXINS DRF
    # ============================================================================
    path('reportes/', v.ReportesAPI.as_view(), name='reportes-api'),
] 