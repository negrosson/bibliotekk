from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Usuario, Sucursal, Libro, Ejemplar, Prestamo, Reserva


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer básico para Usuario"""
    password = serializers.CharField(write_only=True, label='Contraseña')
    
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'rol', 'telefono', 'multas_pendientes', 'suspendido', 'password']
        extra_kwargs = {
            'username': {'label': 'Nombre de Usuario'},
            'email': {'label': 'Correo Electrónico'},
            'first_name': {'label': 'Nombre'},
            'last_name': {'label': 'Apellido'},
            'password': {'write_only': True, 'label': 'Contraseña'},
            'multas_pendientes': {'read_only': True, 'label': 'Multas Pendientes'},
            'suspendido': {'read_only': True, 'label': 'Suspendido'},
        }
    
    def create(self, validated_data):
        """Crear usuario con contraseña encriptada"""
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer básico para login"""
    username = serializers.CharField(label='Nombre de Usuario')
    password = serializers.CharField(label='Contraseña')
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                    return data
                else:
                    raise serializers.ValidationError('Usuario desactivado')
            else:
                raise serializers.ValidationError('Credenciales inválidas')
        else:
            raise serializers.ValidationError('Debe proporcionar username y password')


class SucursalSerializer(serializers.ModelSerializer):
    """Serializer básico para Sucursal"""
    
    class Meta:
        model = Sucursal
        fields = ['id', 'nombre', 'direccion', 'telefono', 'horario_atencion', 'activa']
        extra_kwargs = {
            'nombre': {'label': 'Nombre'},
            'direccion': {'label': 'Dirección'},
            'telefono': {'label': 'Teléfono'},
            'horario_atencion': {'label': 'Horario de Atención'},
            'activa': {'label': 'Activa'},
        }


class LibroSerializer(serializers.ModelSerializer):
    """Serializer básico para Libro"""
    ejemplares_disponibles = serializers.SerializerMethodField(label='Ejemplares Disponibles')
    
    class Meta:
        model = Libro
        fields = ['id', 'titulo', 'autor', 'isbn', 'genero', 'año_publicacion', 
                 'descripcion', 'activo', 'ejemplares_disponibles']
        extra_kwargs = {
            'titulo': {'label': 'Título'},
            'autor': {'label': 'Autor'},
            'isbn': {'label': 'ISBN'},
            'genero': {'label': 'Género'},
            'año_publicacion': {'label': 'Año de Publicación'},
            'descripcion': {'label': 'Descripción'},
            'activo': {'label': 'Activo'},
        }
    
    def get_ejemplares_disponibles(self, obj):
        """Obtener número de ejemplares disponibles"""
        return obj.ejemplares_disponibles()


class EjemplarSerializer(serializers.ModelSerializer):
    """Serializer básico para Ejemplar"""
    libro_titulo = serializers.CharField(source='libro.titulo', read_only=True, label='Título del Libro')
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True, label='Nombre de Sucursal')
    
    class Meta:
        model = Ejemplar
        fields = ['id', 'libro', 'sucursal', 'codigo_barras', 'estado', 
                 'libro_titulo', 'sucursal_nombre']
        extra_kwargs = {
            'libro': {'label': 'Libro'},
            'sucursal': {'label': 'Sucursal'},
            'codigo_barras': {'label': 'Código de Barras'},
            'estado': {'label': 'Estado'},
        }


class PrestamoSerializer(serializers.ModelSerializer):
    """Serializer básico para Prestamo"""
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, label='Usuario')
    libro_titulo = serializers.CharField(source='ejemplar.libro.titulo', read_only=True, label='Libro')
    sucursal_nombre = serializers.CharField(source='ejemplar.sucursal.nombre', read_only=True, label='Sucursal')
    
    class Meta:
        model = Prestamo
        fields = ['id', 'usuario', 'ejemplar', 'fecha_prestamo', 
                 'fecha_devolucion_esperada', 'fecha_devolucion_real', 
                 'estado', 'multa', 'usuario_username', 'libro_titulo', 
                 'sucursal_nombre']
        read_only_fields = ['fecha_prestamo', 'fecha_devolucion_esperada', 
                           'fecha_devolucion_real', 'multa']
        extra_kwargs = {
            'usuario': {'label': 'Usuario'},
            'ejemplar': {'label': 'Ejemplar'},
            'estado': {'label': 'Estado'},
            'multa': {'label': 'Multa'},
        }
    
    def validate(self, data):
        """Validaciones básicas para crear préstamo"""
        usuario = data.get('usuario')
        ejemplar = data.get('ejemplar')
        
        # Verificar que el usuario puede pedir préstamos
        if not usuario.puede_pedir_prestamo():
            raise serializers.ValidationError(
                'El usuario no puede solicitar préstamos (suspendido, multas pendientes o límite alcanzado)'
            )
        
        # Verificar que el ejemplar está disponible
        if not ejemplar.esta_disponible():
            raise serializers.ValidationError('El ejemplar no está disponible')
        
        return data
    
    def create(self, validated_data):
        """Crear préstamo y actualizar estado del ejemplar"""
        prestamo = super().create(validated_data)
        # Cambiar estado del ejemplar a prestado
        prestamo.ejemplar.estado = 'prestado'
        prestamo.ejemplar.save()
        return prestamo


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Serializer básico para el perfil del usuario"""
    prestamos_activos = serializers.SerializerMethodField(label='Préstamos Activos')
    
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'telefono', 'multas_pendientes', 'prestamos_activos']
        read_only_fields = ['username', 'multas_pendientes']
        extra_kwargs = {
            'username': {'label': 'Nombre de Usuario'},
            'email': {'label': 'Correo Electrónico'},
            'first_name': {'label': 'Nombre'},
            'last_name': {'label': 'Apellido'},
            'telefono': {'label': 'Teléfono'},
        }
    
    def get_prestamos_activos(self, obj):
        """Obtener número de préstamos activos"""
        return obj.prestamos.filter(estado='activo').count()


class ReservaSerializer(serializers.ModelSerializer):
    """Serializer básico para Reserva"""
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, label='Usuario')
    libro_titulo = serializers.CharField(source='libro.titulo', read_only=True, label='Libro')
    libro_autor = serializers.CharField(source='libro.autor', read_only=True, label='Autor')
    
    class Meta:
        model = Reserva
        fields = ['id', 'usuario', 'libro', 'fecha_reserva', 'fecha_expiracion', 
                 'estado', 'posicion_cola', 'usuario_username', 'libro_titulo', 'libro_autor']
        read_only_fields = ['fecha_reserva', 'fecha_expiracion', 'posicion_cola']
        extra_kwargs = {
            'usuario': {'label': 'Usuario'},
            'libro': {'label': 'Libro'},
            'estado': {'label': 'Estado'},
        }
    
    def validate(self, data):
        """Validaciones para crear reserva"""
        usuario = data.get('usuario')
        libro = data.get('libro')
        
        # Verificar que el usuario puede hacer reservas
        if not usuario.puede_hacer_reserva():
            raise serializers.ValidationError(
                'El usuario no puede hacer reservas (suspendido o multas pendientes)'
            )
        
        # Verificar que no tenga ya una reserva activa del mismo libro
        if Reserva.objects.filter(usuario=usuario, libro=libro, estado='activa').exists():
            raise serializers.ValidationError('Ya tienes una reserva activa para este libro')
        
        return data
    
    def create(self, validated_data):
        """Crear reserva y asignar posición en cola"""
        libro = validated_data['libro']
        
        # Calcular posición en cola
        ultima_posicion = Reserva.objects.filter(
            libro=libro, 
            estado='activa'
        ).count()
        
        validated_data['posicion_cola'] = ultima_posicion + 1
        
        return super().create(validated_data) 