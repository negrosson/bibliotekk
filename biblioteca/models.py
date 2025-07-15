from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta


class Usuario(AbstractUser):
    """Modelo básico de usuario extendido"""
    
    ROLES = [
        ('usuario', 'Usuario Regular'),
        ('bibliotecario', 'Bibliotecario'),
        ('administrador', 'Administrador'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROLES, default='usuario', verbose_name='Rol')
    telefono = models.CharField(max_length=15, blank=True, verbose_name='Teléfono')
    multas_pendientes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Multas Pendientes')
    suspendido = models.BooleanField(default=False, verbose_name='Suspendido')
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
    
    def puede_pedir_prestamo(self):
        """Verifica si el usuario puede solicitar préstamos"""
        if self.suspendido:
            return False
        if self.multas_pendientes > 0:
            return False
        # Verificar que no tenga más de 3 préstamos activos
        prestamos_activos = self.prestamos.filter(estado='activo').count()
        return prestamos_activos < 3

    def puede_hacer_reserva(self):
        """Verifica si el usuario puede hacer reservas"""
        if self.suspendido:
            return False
        if self.multas_pendientes > 0:
            return False
        return True


class Sucursal(models.Model): 
    """Modelo básico para las sucursales de la biblioteca"""
    
    nombre = models.CharField(max_length=100, verbose_name='Nombre') 
    direccion = models.TextField(verbose_name='Dirección') #verbose se usa para que el usuario pueda ver el nombre de la columna en el admin
    telefono = models.CharField(max_length=15, verbose_name='Teléfono')
    horario_atencion = models.CharField(max_length=200, verbose_name='Horario de Atención')
    activa = models.BooleanField(default=True, verbose_name='Activa')
    
    class Meta:
        verbose_name = 'Sucursal' #nombre que se muestra en el admin
        verbose_name_plural = 'Sucursales' #nombre que se muestra en el admin para varias sucursales
    
    def __str__(self):
        return self.nombre


class Libro(models.Model):
    """Modelo básico para los libros del catálogo"""
    
    GENEROS = [
        ('ficcion', 'Ficción'),
        ('no_ficcion', 'No Ficción'),
        ('ciencia', 'Ciencia'),
        ('historia', 'Historia'),
        ('biografia', 'Biografía'),
        ('infantil', 'Infantil'),
        ('juvenil', 'Juvenil'),
        ('otros', 'Otros'),
    ]
    
    titulo = models.CharField(max_length=50, verbose_name='Título') 
    autor = models.CharField(max_length=50, verbose_name='Autor')
    isbn = models.CharField(max_length=13, unique=True, verbose_name='ISBN')
    genero = models.CharField(max_length=20, choices=GENEROS, verbose_name='Género')
    año_publicacion = models.IntegerField(
        validators=[MinValueValidator(1000), MaxValueValidator(datetime.now().year)], #validators es para que el año de publicación sea entre 1000 y el año actual, punto year es para que se tome el año actual
        verbose_name='Año de Publicación'
    )
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True, verbose_name='Activo') #default es para que el campo sea True por defecto
    
    class Meta:
        verbose_name = 'Libro'
        verbose_name_plural = 'Libros'
    
    def __str__(self):
        return f"{self.titulo} - {self.autor}"
    
    def ejemplares_disponibles(self, sucursal=None):
        """Retorna el número de ejemplares disponibles"""
        ejemplares = self.ejemplares.filter(estado='disponible')
        if sucursal:
            ejemplares = ejemplares.filter(sucursal=sucursal) 
        return ejemplares.count() #retorna el número de ejemplares disponibles contando los que estan en la sucursal


class Ejemplar(models.Model):
    """Modelo básico para los ejemplares físicos de los libros"""
    
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('prestado', 'Prestado'),
        ('mantenimiento', 'En Mantenimiento'),
        ('perdido', 'Perdido'),
    ]
    
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name='ejemplares', verbose_name='Libro') #related_name es para que se pueda acceder a los ejemplares desde el libro 
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='ejemplares', verbose_name='Sucursal') # y verbose_name es para que se pueda ver el nombre de la columna en el admin
    codigo_barras = models.CharField(max_length=50, unique=True, verbose_name='Código de Barras')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible', verbose_name='Estado')
    
    class Meta:
        verbose_name = 'Ejemplar'
        verbose_name_plural = 'Ejemplares'
    
    def __str__(self):
        return f"{self.libro.titulo} - {self.codigo_barras} ({self.sucursal.nombre})" #retorna el titulo del libro, el codigo de barras y el nombre de la sucursal
    
    def esta_disponible(self):
        """Verifica si el ejemplar está disponible para préstamo"""
        return self.estado == 'disponible'


class Prestamo(models.Model):
    """Modelo básico para los préstamos de libros"""
    
    ESTADOS = [
        ('activo', 'Activo'),
        ('devuelto', 'Devuelto'),
        ('vencido', 'Vencido'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='prestamos', verbose_name='Usuario')
    ejemplar = models.ForeignKey(Ejemplar, on_delete=models.CASCADE, related_name='prestamos', verbose_name='Ejemplar')
    fecha_prestamo = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Préstamo')
    fecha_devolucion_esperada = models.DateTimeField(verbose_name='Fecha de Devolución Esperada')
    fecha_devolucion_real = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Devolución Real')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo', verbose_name='Estado')
    multa = models.DecimalField(max_digits=7, decimal_places=2, default=0.00, verbose_name='Multa')
    
    class Meta:
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'
    
    def save(self, *args, **kwargs):
        # Establecer fecha de devolución esperada (14 días)
        if not self.fecha_devolucion_esperada:
            self.fecha_devolucion_esperada = datetime.now() + timedelta(days=14)
        super().save(*args, **kwargs)   #args y kwargs son para que se pueda guardar el préstamo con los argumentos que se le pasan
        #por ejemplo, si se guarda un préstamo con fecha_devolucion_esperada = None, se establece la fecha de devolución esperada a 14 días desde la fecha actual
    
    def __str__(self):
        return f"{self.usuario.username} - {self.ejemplar.libro.titulo}"
    
    def esta_vencido(self):
        """Verifica si el préstamo está vencido"""
        if self.estado == 'devuelto': #si el préstamo está devuelto, no está vencido
            return False #retorna False porque el préstamo no está vencido
        return datetime.now() > self.fecha_devolucion_esperada #retorna True si el préstamo está vencido
    
    def calcular_multa(self): 
        """Calcula la multa por días de retraso"""
        if not self.esta_vencido(): #si el préstamo no está vencido, no hay multa
            return 0 #retorna 0 porque no hay multa
        
        dias_retraso = (datetime.now() - self.fecha_devolucion_esperada).days #calcula los días de retraso
        multa_por_dia = 1000.00  # $1000.00 por día
        return dias_retraso * multa_por_dia
    
    def devolver(self):
        """Marca el préstamo como devuelto"""
        self.fecha_devolucion_real = datetime.now()
        self.estado = 'devuelto'
        self.ejemplar.estado = 'disponible'
        
        # Calcular multa si hay retraso
        if self.esta_vencido():
            self.multa = self.calcular_multa()
            self.usuario.multas_pendientes += self.multa #suma la multa al total de multas pendientes
            self.usuario.save() #guarda el total de multas pendientes
        
        self.ejemplar.save() #guarda el estado del ejemplar
        self.save()


class Reserva(models.Model): 
    """Modelo para el sistema de reservas con cola de espera"""
    
    ESTADOS = [
        ('activa', 'Activa'),
        ('cumplida', 'Cumplida'),
        ('cancelada', 'Cancelada'),
        ('expirada', 'Expirada'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas', verbose_name='Usuario')
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name='reservas', verbose_name='Libro')
    fecha_reserva = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Reserva')
    fecha_expiracion = models.DateTimeField(verbose_name='Fecha de Expiración')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activa', verbose_name='Estado')
    posicion_cola = models.IntegerField(default=1, verbose_name='Posición en Cola')
    
    class Meta: #meta es para definir propiedades del modelo
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        # Un usuario no puede tener múltiples reservas activas del mismo libro
        unique_together = [['usuario', 'libro', 'estado']] #unique_together es para que no se pueda tener múltiples reservas activas del mismo libro
        ordering = ['fecha_reserva'] 
    
    def save(self, *args, **kwargs): 
        
        if not self.fecha_expiracion: 
            self.fecha_expiracion = datetime.now() + timedelta(days=2) #si no se ha establecido la fecha de expiración, se establece a 2 días desde la fecha actual
        super().save(*args, **kwargs) #args y kwargs son para que se pueda guardar la reserva con los argumentos que se le pasan
        #por ejemplo, si se guarda una reserva con fecha_expiracion = None, se establece la fecha de expiración a 2 días desde la fecha actual
    
    def __str__(self): # __str__ es para que se pueda ver el nombre de la reserva en el admin
        return f"{self.usuario.username} - {self.libro.titulo} (Posición: {self.posicion_cola})" #retorna el nombre del usuario, el titulo del libro y la posición en la cola
    
    def esta_expirada(self):
        """Verifica si la reserva está expirada"""
        return datetime.now() > self.fecha_expiracion and self.estado == 'activa' #retorna True si la reserva está expirada y activa
    
    def cancelar(self):
        """Cancela la reserva y reorganiza la cola"""
        self.estado = 'cancelada'
        self.save()
        
        # Reorganizar posiciones en la cola
        reservas_posteriores = Reserva.objects.filter(
            libro=self.libro,
            estado='activa',
            posicion_cola__gt=self.posicion_cola #posterior a la posición de la reserva actual
        )
        
        for reserva in reservas_posteriores: 
            reserva.posicion_cola -= 1 #resta 1 a la posición de la reserva actual
            reserva.save()
    
    def obtener_posicion_en_cola(self):
        """Obtiene la posición actual en la cola"""
        return Reserva.objects.filter(
            libro=self.libro, #self.libro es el libro de la reserva actual
            estado='activa', 
            fecha_reserva__lt=self.fecha_reserva #porque lt, es para indicar que la fecha de reserva es menor a la fecha de la reserva actual
        ).count() + 1 # cuenta las reservas activas del mismo libro y las que tienen una fecha de reserva menor a la fecha de la reserva actual
