# VISTAS DE LA API - SISTEMA DE BIBLIOTECA CON MIXINS DRF

# Importaciones de Django REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, mixins, generics #status es para el estado de la respuesta, mixins es para las vistas, generics es para las vistas genéricas
from rest_framework.permissions import IsAuthenticated, AllowAny #IsAuthenticated es para verificar si el usuario está autenticado, AllowAny es para permitir el acceso a todos los usuarios
from rest_framework.decorators import api_view, permission_classes #api_view es para definir una vista, permission_classes es para definir las clases de permisos

# Importaciones de Django
from django.contrib.auth import authenticate #authenticate es para autenticar al usuario
from django.db.models import Count #Count es para contar los elementos de un modelo
from django.utils import timezone #timezone es para manejar las fechas y horas
from datetime import timedelta #timedelta es para manejar los intervalos de tiempo

# Importaciones de JWT
from rest_framework_simplejwt.tokens import RefreshToken

# Importaciones locales
from .models import Usuario, Sucursal, Libro, Ejemplar, Prestamo, Reserva
from .serializers import (
    UsuarioSerializer, SucursalSerializer, LibroSerializer, 
    EjemplarSerializer, PrestamoSerializer, ReservaSerializer
)

# ============================================================================
# VISTAS DE LIBROS CON MIXINS DRF # drf es para django rest framework
# ============================================================================

class LibroAPI(mixins.ListModelMixin, #mixins es para las vistas, ListModelMixin es para listar los modelos
               mixins.CreateModelMixin, #CreateModelMixin es para crear los modelos
               generics.GenericAPIView): #generics es para las vistas genéricas
    """Vista para gestión de libros usando mixins DRF"""
    queryset = Libro.objects.filter(activo=True) #queryset es para filtrar los libros por activos
    serializer_class = LibroSerializer 
    permission_classes = [IsAuthenticated] #solo autenticados acceden a permisos
    
    def get(self, request, *args, **kwargs): #get es para obtener los datos
        """Obtener todos los libros activos"""
        return self.list(request, *args, **kwargs) #retorna una lista
    
    def post(self, request, *args, **kwargs):
        """Crear nuevo libro (solo bibliotecarios y administradores)"""
        if request.user.rol not in ['bibliotecario', 'administrador']:
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        # Validar ISBN único antes de crear
        
        isbn = request.data.get('isbn')
        if isbn and Libro.objects.filter(isbn=isbn).exists():
            return Response("ISBN ya existe", status=status.HTTP_400_BAD_REQUEST)
        
        return self.create(request, *args, **kwargs)






class LibroDetailAPI(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     generics.GenericAPIView):
    """Vista para operaciones específicas de libros"""
    queryset = Libro.objects.filter(activo=True)
    serializer_class = LibroSerializer 
    permission_classes = [IsAuthenticated] 
    
    def get(self, request, *args, **kwargs):
        """Obtener libro específico"""
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        """Actualizar libro (solo bibliotecarios y administradores)"""
        if request.user.rol not in ['bibliotecario', 'administrador']:
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        # Validar ISBN único en actualizaciones
        isbn = request.data.get('isbn')
        if isbn:
            libro_actual = self.get_object()
            if Libro.objects.filter(isbn=isbn).exclude(id=libro_actual.id).exists():
                return Response("ISBN ya existe", status=status.HTTP_400_BAD_REQUEST)
            
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Eliminar libro (solo administradores)"""
        if request.user.rol != 'administrador':
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        libro = self.get_object()
        # Verificar que no tenga préstamos activos
        if Prestamo.objects.filter(ejemplar__libro=libro, estado='activo').exists():
            return Response("No se puede eliminar: libro tiene préstamos activos", 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Eliminación lógica
        libro.activo = False
        libro.save()
        return Response("Libro eliminado exitosamente", status=status.HTTP_200_OK)


#Obtiene la disponibilidad de un libro específico en todas las sucursales donde hay ejemplares disponibles

@api_view(['GET']) #solo acepta peticiones get
@permission_classes([IsAuthenticated]) #requiere autenticacion
def disponibilidad_libro_api(request, libro_id):  #recibe id del libro
    """Obtener disponibilidad de un libro por sucursal"""
    try:
        libro = Libro.objects.get(id=libro_id, activo=True) #Busca el libro con el ID especificado, pero solo si está activo
        
        ejemplares_por_sucursal = Ejemplar.objects.filter(  #Filtra ejemplares del libro específico
            libro=libro, 
            estado='disponible' #Solo ejemplares disponibles (no prestados)
        ).values('sucursal__nombre', 'sucursal__id').annotate( #Obtiene nombre e ID de la sucursal, values=obtener los valores de la sucursal
            cantidad_disponible=Count('id') #Cuenta cuántos ejemplares hay por sucursal
        )
        
        disponibilidad = [] #Lista para almacenar la disponibilidad de cada sucursal
        for item in ejemplares_por_sucursal: #Recorre cada sucursal
            disponibilidad.append({ #Agrega la disponibilidad de la sucursal a la lista
                'sucursal_id': item['sucursal__id'], 
                'sucursal_nombre': item['sucursal__nombre'], 
                'cantidad_disponible': item['cantidad_disponible'] 
            })
        
        response_data = { #Crea un diccionario con la información de la disponibilidad del libro
        #Crea la respuesta con información del libro, disponibilidad por sucursal y total general
            'libro': {
                'id': libro.id,
                'titulo': libro.titulo,
                'autor': libro.autor
            },
            'disponibilidad_por_sucursal': disponibilidad,
            'total_disponible': sum(item['cantidad_disponible'] for item in disponibilidad)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Libro.DoesNotExist:
        return Response("Libro no encontrado", status=status.HTTP_404_NOT_FOUND)
    except:
        return Response("ERROR al obtener disponibilidad", status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_libros_api(request):
    """Búsqueda avanzada de libros con múltiples filtros"""
    try:
       
        query = request.GET.get('q', '') #Obtén el parámetro 'q' de la URL, si no existe usa cadena vacía
        genero = request.GET.get('genero', '') #Obtén el parámetro 'genero' de la URL, si no existe usa cadena vacía
        autor = request.GET.get('autor', '')
        disponible = request.GET.get('disponible', '')
        sucursal = request.GET.get('sucursal', '')
        
       
        libros = Libro.objects.filter(activo=True)#Empieza con todos los libros que estén activos (no eliminados)
        
        if query:
            libros = libros.filter(titulo__icontains=query) #Si se proporcionó un término de búsqueda, filtra los libros que contengan ese término en el título
        
        if genero:
            libros = libros.filter(genero__icontains=genero) #Si se especificó un género, filtra los libros que contengan ese género
        
        if autor:
            libros = libros.filter(autor__icontains=autor) #Si se especificó un género, filtra los libros que contengan ese género
        
        
        if disponible and disponible.lower() == 'true': #Si se especificó disponibilidad y es 'true
            libros = libros.filter(ejemplares__estado='disponible').distinct()#Filtra solo libros que tengan ejemplares disponibles
        
        if sucursal:
            try:
                sucursal_id = int(sucursal) #i se especificó una sucursal
                libros = libros.filter(ejemplares__sucursal__id=sucursal_id).distinct() #Intenta convertir la sucursal a número ID
            except ValueError:
                libros = libros.filter(ejemplares__sucursal__nombre__icontains=sucursal).distinct() #Si no se puede convertir a número, filtra por nombre
        
        datosSerializados = LibroSerializer(libros, many=True)
        
        response_data = { #Crea un diccionario con la información de la búsqueda
            'total_resultados': libros.count(),#Incluye el total de libros encontrados
            'filtros_aplicados': { #Incluye los filtros que se aplicaron
                'busqueda_general': query,
                'genero': genero,
                'autor': autor,
                'disponible': disponible,
                'sucursal': sucursal
            },
            'libros': datosSerializados.data #Incluye la lista de libros en formato JSON
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except:
        return Response("ERROR en búsqueda", status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# VISTAS DE SUCURSALES CON MIXINS DRF
# ============================================================================

class SucursalAPI(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
    """Vista para gestión de sucursales usando mixins DRF"""
    queryset = Sucursal.objects.filter(activa=True) #se esta filtrando las sucursales por activas.
    serializer_class = SucursalSerializer #se esta serializando los datos de las sucursales
    permission_classes = [IsAuthenticated] #SOLO AUTENTICADOS
    
    def get(self, request, *args, **kwargs): #se esta definiendo una vista que se llama get, se encarga de obtener todas las sucursales activas
        """Obtener todas las sucursales activas"""
        return self.list(request, *args, **kwargs) #retorna la lista de sucursales activas
    
    def post(self, request, *args, **kwargs): 
        """Crear nueva sucursal (solo administradores)"""
        if request.user.rol != 'administrador':
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        return self.create(request, *args, **kwargs)

class SucursalDetailAPI(mixins.RetrieveModelMixin,#RetrieveModelMixin es para obtener una sucursal específica
                        mixins.UpdateModelMixin,#UpdateModelMixin es para actualizar una sucursal
                        mixins.DestroyModelMixin,#DestroyModelMixin es para eliminar una sucursal
                        generics.GenericAPIView):#GenericAPIView es para las vistas genéricas
    """Vista para operaciones específicas de sucursales"""
    queryset = Sucursal.objects.filter(activa=True)
    serializer_class = SucursalSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Obtener sucursal específica"""
        return self.retrieve(request, *args, **kwargs) #retorna la sucursal especifica
    
    def put(self, request, *args, **kwargs):
        """Actualizar sucursal (solo administradores)"""
        if request.user.rol != 'administrador':
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Eliminar sucursal (eliminación lógica - solo administradores)"""
        if request.user.rol != 'administrador':
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        sucursal = self.get_object()
        
        # Verificar que no tenga ejemplares activos
        ejemplares_activos = Ejemplar.objects.filter(sucursal=sucursal).count()
        if ejemplares_activos > 0:
            return Response(
                f"No se puede eliminar: la sucursal tiene {ejemplares_activos} ejemplares. "
                "Transfiera los ejemplares a otra sucursal primero.",
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Eliminación lógica: cambiar activa a False
        sucursal.activa = False
        sucursal.save()
        
        return Response(
            f"Sucursal '{sucursal.nombre}' eliminada exitosamente",
            status=status.HTTP_200_OK
        )

@api_view(['GET']) #solo get porque se esta obteniendo un inventario y solo get es para obtener datos
@permission_classes([IsAuthenticated]) #SOLO AUTENTICADOS
def inventario_sucursal_api(request, sucursal_id): #se esta definiendo una vista que se llama inventario_sucursal_api, que es una vista que se encarga de obtener el inventario de una sucursal
    """Obtener inventario completo de una sucursal"""
    try:
        sucursal = Sucursal.objects.get(id=sucursal_id, activa=True)
        
        # Obtener ejemplares de la sucursal agrupados por libro
        ejemplares = Ejemplar.objects.filter(sucursal=sucursal).select_related('libro') #select_related es para obtener los datos de los libros relacionados con los ejemplares
        # tambien se conoce como prefetch_related, que es para obtener los datos de los libros relacionados con los ejemplares
        
        # Agrupar por libro y estado
        inventario = {} 
        for ejemplar in ejemplares:  
            libro_id = ejemplar.libro.id #se obtiene el id del libro
            if libro_id not in inventario: #si el libro_id no esta en el inventario, se crea un nuevo inventario
                inventario[libro_id] = { #se crea un nuevo inventario
                    'libro': {
                        'id': ejemplar.libro.id,
                        'titulo': ejemplar.libro.titulo,
                        'autor': ejemplar.libro.autor,
                        'isbn': ejemplar.libro.isbn,
                        'genero': ejemplar.libro.genero
                    },
                    'ejemplares': { 
                        'disponible': 0, 
                        'prestado': 0,
                        'en_mantenimiento': 0,
                        'total': 0
                    }
                }
            
            # Contar ejemplares por estado
            inventario[libro_id]['ejemplares'][ejemplar.estado] += 1 #se obtiene el estado del ejemplar y se le suma 1 al inventario, y porque 1? porque se esta contando los ejemplares por estado
            inventario[libro_id]['ejemplares']['total'] += 1 #se obtiene el total de ejemplares 
        
        # Convertir a lista
        inventario_lista = list(inventario.values()) #se convierte el inventario a una lista, values = valores, al poner list fuera de () se convierte el inventario a una lista
        #inventario.values() es para obtener los valores del inventario, 
        
        # Estadísticas generales, aparecen en el inventario
        estadisticas = {
            'total_libros_diferentes': len(inventario_lista), #len es para obtener la longitud de la lista, y porque len? porque se esta contando los libros diferentes
            'total_ejemplares': ejemplares.count(), #count es para obtener el total de ejemplares, y porque count? porque se esta contando los ejemplares
            'ejemplares_disponibles': ejemplares.filter(estado='disponible').count(), #filter es para filtrar los ejemplares por estado, y porque count? porque se esta contando los ejemplares por estado
            'ejemplares_prestados': ejemplares.filter(estado='prestado').count(), #filter es para filtrar los ejemplares por estado, y se cuenta los ejemplares prestados
            'ejemplares_en_mantenimiento': ejemplares.filter(estado='en_mantenimiento').count() #filter es para filtrar los ejemplares por estado, y porque filter? porque se esta filtrando los ejemplares por estado
        }
        #despues de esto se crea un diccionario que se llama response_data, que contiene la sucursal, las estadisticas y el inventario
        # en la vista del usuario se mostrara el inventario de la sucursal, las estadisticas y el inventario
        response_data = { #se crea un diccionario que se llama response_data, que contiene la sucursal, las estadisticas y el inventario
            'sucursal': {
                'id': sucursal.id, #cada ves que se pone un . se esta accediendo a un atributo de la sucursal ( ubicada en models.py)
                'nombre': sucursal.nombre, #nombre es el nombre de la sucursal
                'direccion': sucursal.direccion #direccion es la direccion de la sucursal
            },
            'estadisticas': estadisticas,
            'inventario': inventario_lista
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Sucursal.DoesNotExist:
        return Response("Sucursal no encontrada", status=status.HTTP_404_NOT_FOUND)
    except:
        return Response("ERROR al obtener inventario", status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# VISTAS DE EJEMPLARES CON MIXINS DRF
# ============================================================================

class EjemplarAPI(mixins.ListModelMixin, #se le pone API para que se pueda acceder a la vista desde la URL
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
    """Vista para gestión de ejemplares usando mixins DRF"""
    queryset = Ejemplar.objects.all()
    serializer_class = EjemplarSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar ejemplares según parámetros"""
        queryset = super().get_queryset()
        
        libro_id = self.request.GET.get('libro_id')#se obtiene el id del libro
        sucursal_id = self.request.GET.get('sucursal_id')#se obtiene el id de la sucursal
        estado = self.request.GET.get('estado')#se obtiene el estado del ejemplar
        
        if libro_id:
            queryset = queryset.filter(libro_id=libro_id)#se filtra el ejemplar por el id del libro
        if sucursal_id:
            queryset = queryset.filter(sucursal_id=sucursal_id)#se filtra el ejemplar por el id de la sucursal
        if estado:
            queryset = queryset.filter(estado=estado)#se filtra el ejemplar por el estado
        
        return queryset#se retorna el queryset
    
    def get(self, request, *args, **kwargs):
        """Obtener ejemplares con filtros opcionales"""
        return self.list(request, *args, **kwargs) #se retorna la lista de ejemplares
    
    def post(self, request, *args, **kwargs):
        if request.user.rol not in ['bibliotecario', 'administrador']:
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        # Validar código de barras único
        codigo_barras = request.data.get('codigo_barras')
        if codigo_barras and Ejemplar.objects.filter(codigo_barras=codigo_barras).exists():
            return Response("Código de barras ya existe", status=status.HTTP_400_BAD_REQUEST)
        
        return self.create(request, *args, **kwargs) #retorna la creacion de un nuevo ejemplar

class EjemplarDetailAPI(mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    """Vista para operaciones específicas de ejemplares"""
    queryset = Ejemplar.objects.all() 
    serializer_class = EjemplarSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Obtener ejemplar específico"""
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        """Actualizar ejemplar (solo bibliotecarios y administradores)"""
        if request.user.rol not in ['bibliotecario', 'administrador']:
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        # Validar código de barras único en actualizaciones
        codigo_barras = request.data.get('codigo_barras')
        if codigo_barras:
            ejemplar_actual = self.get_object()
            if Ejemplar.objects.filter(codigo_barras=codigo_barras).exclude(id=ejemplar_actual.id).exists():
                return Response("Código de barras ya existe", status=status.HTTP_400_BAD_REQUEST)
        
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Eliminar ejemplar (solo administradores)"""
        if request.user.rol != 'administrador':
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        ejemplar = self.get_object()
        # Verificar que no tenga préstamos activos
        if Prestamo.objects.filter(ejemplar=ejemplar, estado='activo').exists():
            return Response("No se puede eliminar: ejemplar tiene préstamos activos", 
                          status=status.HTTP_400_BAD_REQUEST)
        
        return self.destroy(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transferir_ejemplar_api(request, ejemplar_id):
    """Transferir ejemplar entre sucursales"""
    if request.user.rol not in ['bibliotecario', 'administrador']:
        return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
    
    try:
        ejemplar = Ejemplar.objects.get(id=ejemplar_id)
        sucursal_destino_id = request.data.get("sucursal_destino_id")
        
        if ejemplar.estado != 'disponible':
            return Response("Solo se pueden transferir ejemplares disponibles", 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sucursal_destino = Sucursal.objects.get(id=sucursal_destino_id)
        except Sucursal.DoesNotExist:
            return Response("Sucursal destino no encontrada", status=status.HTTP_404_NOT_FOUND)
        
        if ejemplar.sucursal.id == sucursal_destino.id:
            return Response("El ejemplar ya está en esa sucursal", status=status.HTTP_400_BAD_REQUEST)
        
        sucursal_origen = ejemplar.sucursal.nombre
        ejemplar.sucursal = sucursal_destino
        ejemplar.save()
        
        return Response(f"Ejemplar transferido exitosamente de {sucursal_origen} a {sucursal_destino.nombre}", 
                       status=status.HTTP_200_OK)
    except Ejemplar.DoesNotExist:
        return Response("Ejemplar no encontrado", status=status.HTTP_404_NOT_FOUND)
    except:
        return Response("ERROR al transferir ejemplar", status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# VISTAS DE PRÉSTAMOS CON MIXINS DRF
# ============================================================================

class PrestamoAPI(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
    """Vista para gestión de préstamos usando mixins DRF"""
    serializer_class = PrestamoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar préstamos según el rol del usuario"""
        if self.request.user.rol == 'usuario':
            return Prestamo.objects.filter(usuario=self.request.user)
        else:
            return Prestamo.objects.all()
    
    def get(self, request, *args, **kwargs):
        """Obtener préstamos (usuarios ven solo los suyos)"""
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Crear nuevo préstamo"""
        # Determinar usuario del préstamo
        if request.user.rol == 'usuario':
            usuario = request.user
        else:
            usuario_id = request.data.get("usuario_id", request.user.id)
            try:
                usuario = Usuario.objects.get(id=usuario_id)
            except Usuario.DoesNotExist:
                return Response("Usuario no encontrado", status=status.HTTP_404_NOT_FOUND)
        
        # Validar que el usuario puede pedir préstamos
        if not usuario.puede_pedir_prestamo():
            return Response("Usuario no puede pedir préstamos", status=status.HTTP_400_BAD_REQUEST)
            
        # Validar que el ejemplar existe y está disponible
        ejemplar_id = request.data.get("ejemplar_id")
        try:
            ejemplar = Ejemplar.objects.get(id=ejemplar_id)
            if not ejemplar.esta_disponible():
                return Response("Ejemplar no disponible", status=status.HTTP_400_BAD_REQUEST)
        except Ejemplar.DoesNotExist:
            return Response("Ejemplar no existe", status=status.HTTP_404_NOT_FOUND)
            
        # Crear préstamo
        prestamo = Prestamo.objects.create(
            usuario=usuario,
            ejemplar=ejemplar,
            fecha_devolucion_esperada=timezone.now() + timedelta(days=14)
        )
        
        # Cambiar estado del ejemplar
        ejemplar.estado = 'prestado'
        ejemplar.save()
        
        return Response("Préstamo creado exitosamente", status=status.HTTP_201_CREATED)

class PrestamoDetailAPI(mixins.RetrieveModelMixin,
                        generics.GenericAPIView):
    """Vista para operaciones específicas de préstamos"""
    serializer_class = PrestamoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar préstamos según el rol del usuario"""
        if self.request.user.rol == 'usuario':
            return Prestamo.objects.filter(usuario=self.request.user)
        else:
            return Prestamo.objects.all()
    
    def get(self, request, *args, **kwargs):
        """Obtener préstamo específico"""
        return self.retrieve(request, *args, **kwargs)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def devolver_prestamo_api(request, prestamo_id): #se esta definiendo una vista que se llama devolver_prestamo_api, que es una vista que se encarga de procesar la devolucion de un prestamo
    """Procesar devolución de préstamo"""
    if request.user.rol not in ['bibliotecario', 'administrador']:
        return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
    
    try:
        prestamo = Prestamo.objects.get(id=prestamo_id)
        
        if prestamo.estado != 'activo':
            return Response("Préstamo no está activo", status=status.HTTP_400_BAD_REQUEST)
        
        # Procesar devolución
        prestamo.fecha_devolucion_real = timezone.now() #se le asigna la fecha actual a la fecha de devolucion real
        prestamo.estado = 'devuelto' #se cambia el estado del prestamo a devuelto
        
        # Calcular multa si hay retraso
        if prestamo.fecha_devolucion_real > prestamo.fecha_devolucion_esperada:
            dias_retraso = (prestamo.fecha_devolucion_real - prestamo.fecha_devolucion_esperada).days #.days es para obtener los dias de retraso
            multa = dias_retraso * 1000.00
            prestamo.multa = multa 
            
            # Agregar multa al usuario
            prestamo.usuario.multas_pendientes += multa # SE USa punto para acceder a los atributos del usuario. em esdte caso se esta accediendo a la multa pendiente del usuario
            prestamo.usuario.save() #se guarda el usuario con la multa pendiente
        
        prestamo.save() #se guarda el prestamo
        
        # Cambiar estado del ejemplar
        prestamo.ejemplar.estado = 'disponible'
        prestamo.ejemplar.save()
        
        # Procesar cola de reservas
        procesar_cola_reservas(prestamo.ejemplar.libro) # se lee como procesar la cola de reservas, y se le pasa el libro como parametro
        # en la practica seria procesar la cola de reservas del libro que se devolvio, se agrega el libro a la cola de reservas
        
        return Response("Préstamo devuelto exitosamente", status=status.HTTP_200_OK)
    except Prestamo.DoesNotExist:
        return Response("Préstamo no encontrado", status=status.HTTP_404_NOT_FOUND)
    except:
        return Response("ERROR al devolver préstamo", status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prestamos_activos_api(request): 
    """Obtener solo préstamos activos"""
    try:
        if request.user.rol == 'usuario':
            prestamos = Prestamo.objects.filter(usuario=request.user, estado='activo')
        else:
            prestamos = Prestamo.objects.filter(estado='activo')
        
        datosSerializados = PrestamoSerializer(prestamos, many=True)
        
        estadisticas = {
            'total_prestamos_activos': prestamos.count(),
            'proximos_a_vencer': prestamos.filter( # se esta filtrando los prestamos que estan activos y que la fecha de devolucion esperada es menor a la fecha actual + 3 dias
                fecha_devolucion_esperada__lte=timezone.now() + timedelta(days=3)
            ).count()
        }
        
        response_data = { # se esta creando un diccionario que se llama response_data, que contiene el estadisticas y los prestamos activos
            'estadisticas': estadisticas, 
            'prestamos_activos': datosSerializados.data # se esta serializando los prestamos activos, el porque es para que se pueda enviar en formato json
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except:
        return Response("ERROR al obtener préstamos activos", status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prestamos_vencidos_api(request):
    """Obtener solo préstamos vencidos"""
    if request.user.rol not in ['bibliotecario', 'administrador']:
        return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
    try:
        # Obtener préstamos vencidos ordenados por fecha de devolución esperada
        prestamos_vencidos = Prestamo.objects.filter(
            estado='activo',
            fecha_devolucion_esperada__lt=timezone.now()
        ).order_by('fecha_devolucion_esperada')
        
        # Serializar los préstamos vencidos
        datosSerializados = PrestamoSerializer(prestamos_vencidos, many=True)
        
        
        # Calcular estadísticas de préstamos vencidos de forma ordenada y clara
        total_prestamos_vencidos = prestamos_vencidos.count() #aqui se esta contando los prestamos vencidos
        multas_estimadas = sum( #aqui se esta sumando las multas estimadas de los prestamos vencidos
            (timezone.now() - p.fecha_devolucion_esperada).days * 1000.00 #aqui se esta calculando la multa estimada multiplicando los dias de retraso por 1000.00
            for p in prestamos_vencidos #aqui se esta iterando sobre los prestamos vencidos
        )
        estadisticas = { 
            'total_prestamos_vencidos': total_prestamos_vencidos,  #aqui aun no estan en json, sino mas abajo se serializa
            'multas_estimadas': multas_estimadas
        }
        
        response_data = { # se esta creando un diccionario que se llama response_data, que contiene el estadisticas y los prestamos vencidos
            'estadisticas': estadisticas, 
            'prestamos_vencidos': datosSerializados.data # se esta serializando los prestamos vencidos, el porque es para que se pueda enviar en formato json
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except:
        return Response("ERROR al obtener préstamos vencidos", status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# VISTAS DE RESERVAS CON MIXINS DRF
# ============================================================================

class ReservaAPI(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 generics.GenericAPIView):
    """Vista para gestión de reservas usando mixins DRF"""
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar reservas según el rol del usuario"""
        if self.request.user.rol == 'usuario':
            return Reserva.objects.filter(usuario=self.request.user)
        else:
            return Reserva.objects.all()
    
    def get(self, request, *args, **kwargs):
        """Obtener reservas (usuarios ven solo las suyas)"""
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Crear nueva reserva"""
        # Determinar usuario de la reserva
        if request.user.rol == 'usuario':
            usuario = request.user
        else:
            usuario_id = request.data.get("usuario_id", request.user.id)
            try:
                usuario = Usuario.objects.get(id=usuario_id)
            except Usuario.DoesNotExist:
                return Response("Usuario no encontrado", status=status.HTTP_404_NOT_FOUND)
        
        # Validar que el usuario puede hacer reservas
        if not usuario.puede_hacer_reserva():
            return Response("Usuario no puede hacer reservas", status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que el libro existe
        libro_id = request.data.get("libro_id")
        try:
            libro = Libro.objects.get(id=libro_id)
        except Libro.DoesNotExist:
            return Response("Libro no existe", status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que no tenga ya una reserva activa del mismo libro
        if Reserva.objects.filter(usuario=usuario, libro=libro, estado='activa').exists():
            return Response("Ya tienes una reserva activa para este libro", 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular posición en cola
        ultima_posicion = Reserva.objects.filter(libro=libro, estado='activa').count()
        
        # Crear reserva
        reserva = Reserva.objects.create(
            usuario=usuario,
            libro=libro,
            posicion_cola=ultima_posicion + 1
        )
        
        return Response(f"Reserva creada exitosamente. Posición en cola: {reserva.posicion_cola}", 
                       status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancelar_reserva_api(request, reserva_id):
    """Cancelar una reserva"""
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        
        # Solo el usuario propietario o bibliotecarios/administradores pueden cancelar
        if request.user.rol == 'usuario' and reserva.usuario != request.user:
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que la reserva esté activa
        if reserva.estado != 'activa':
            return Response("La reserva no está activa", status=status.HTTP_400_BAD_REQUEST)
        
        # Cancelar reserva y reorganizar cola
        reserva.cancelar()
        
        return Response("Reserva cancelada exitosamente", status=status.HTTP_200_OK)
    except Reserva.DoesNotExist:
        return Response("Reserva no encontrada", status=status.HTTP_404_NOT_FOUND)
    except:
        return Response("ERROR al cancelar reserva", status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cola_reservas_api(request, libro_id):
    """Ver la cola de reservas de un libro"""
    try:
        libro = Libro.objects.get(id=libro_id)
        
        reservas = Reserva.objects.filter(
            libro=libro, 
            estado='activa'
        ).order_by('posicion_cola')
        
        datosSerializados = ReservaSerializer(reservas, many=True)
        
        return Response({
            'libro': libro.titulo,
            'total_reservas': reservas.count(),
            'cola': datosSerializados.data
        }, status=status.HTTP_200_OK)
    except Libro.DoesNotExist:
        return Response("Libro no encontrado", status=status.HTTP_404_NOT_FOUND)
    except:
        return Response("ERROR al obtener cola de reservas", status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# VISTAS DE AUTENTICACIÓN CON MIXINS DRF
# ============================================================================

class LoginAPI(APIView):
    """Vista para autenticación"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Autenticar usuario"""
        username = request.data.get("username")
        password = request.data.get("password")
        
        if not username or not password:
            return Response("Username y password requeridos", status=status.HTTP_400_BAD_REQUEST)
        
        usuario = authenticate(username=username, password=password)
        
        if usuario is not None:
            refresh = RefreshToken.for_user(usuario)
            
            response_data = {
                'mensaje': 'Login exitoso',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'usuario': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'rol': usuario.rol
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response("Credenciales inválidas", status=status.HTTP_401_UNAUTHORIZED)

class RegistroAPI(mixins.CreateModelMixin,
                  generics.GenericAPIView):
    """Vista para registro usando mixins DRF"""
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Registrar nuevo usuario"""
        username = request.data.get("username")
        
        # Verificar que el username no exista
        if Usuario.objects.filter(username=username).exists():
            return Response("Username ya existe", status=status.HTTP_400_BAD_REQUEST)
        
        # Crear usuario con rol de usuario por defecto
        password = request.data.get("password")
        email = request.data.get("email")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")
        telefono = request.data.get("telefono", "")
        
        usuario = Usuario.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        usuario.telefono = telefono
        usuario.rol = 'usuario'
        usuario.save()
        
        return Response("Usuario registrado exitosamente", status=status.HTTP_201_CREATED)

class RefreshTokenAPI(APIView):
    """Vista para renovar tokens JWT"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Renovar token de acceso usando refresh token"""
        refresh_token = request.data.get("refresh")
        
        if not refresh_token:
            return Response("Refresh token requerido", status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            nuevo_access_token = str(refresh.access_token)
            
            response_data = {
                'access': nuevo_access_token,
                'mensaje': 'Token renovado exitosamente'
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response("Token inválido o expirado", status=status.HTTP_401_UNAUTHORIZED)

# ============================================================================
# ENDPOINTS DE PERFIL DE USUARIO
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario_api(request):
    """Obtener perfil del usuario autenticado"""
    try:
        usuario = request.user
        
        perfil_data = {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            'telefono': usuario.telefono,
            'rol': usuario.rol,
            'multas_pendientes': float(usuario.multas_pendientes),
            'fecha_registro': usuario.date_joined,
            'estado_cuenta': 'activa' if usuario.is_active else 'inactiva',
            'puede_pedir_prestamos': usuario.puede_pedir_prestamo(),
            'puede_hacer_reservas': usuario.puede_hacer_reserva()
        }
        
        return Response(perfil_data, status=status.HTTP_200_OK)
    except:
        return Response("ERROR al obtener perfil", status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_perfil_api(request):
    """Actualizar perfil del usuario autenticado"""
    try:
        usuario = request.user
        data = request.data
        
        if 'email' in data:
            usuario.email = data['email']
        if 'first_name' in data:
            usuario.first_name = data['first_name']
        if 'last_name' in data:
            usuario.last_name = data['last_name']
        if 'telefono' in data:
            usuario.telefono = data['telefono']
        
        # Cambio de contraseña (opcional)
        if 'password' in data and 'password_actual' in data:
            if authenticate(username=usuario.username, password=data['password_actual']):
                usuario.set_password(data['password'])
            else:
                return Response("Contraseña actual incorrecta", status=status.HTTP_400_BAD_REQUEST)
        
        usuario.save()
        return Response("Perfil actualizado exitosamente", status=status.HTTP_200_OK)
    except:
        return Response("ERROR al actualizar perfil", status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_prestamos_api(request):
    """Obtener historial de préstamos del usuario autenticado"""
    try:
        usuario = request.user
        
        prestamos = Prestamo.objects.filter(usuario=usuario).order_by('-fecha_prestamo')
        datosSerializados = PrestamoSerializer(prestamos, many=True)
        
        estadisticas = {
            'total_prestamos': prestamos.count(),
            'prestamos_activos': prestamos.filter(estado='activo').count(),
            'prestamos_devueltos': prestamos.filter(estado='devuelto').count(),
            'prestamos_con_multa': prestamos.filter(multa__gt=0).count(),
            'multas_totales': float(sum(p.multa for p in prestamos if p.multa))
        }
        
        response_data = {
            'estadisticas': estadisticas,
            'historial': datosSerializados.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except:
        return Response("ERROR al obtener historial", status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_reservas_api(request):
    """Obtener reservas del usuario autenticado"""
    try:
        usuario = request.user
        
        reservas = Reserva.objects.filter(usuario=usuario).order_by('-fecha_reserva')
        datosSerializados = ReservaSerializer(reservas, many=True)
        
        estadisticas = {
            'total_reservas': reservas.count(),
            'reservas_activas': reservas.filter(estado='activa').count(),
            'reservas_cumplidas': reservas.filter(estado='cumplida').count(),
            'reservas_canceladas': reservas.filter(estado='cancelada').count(),
            'reservas_expiradas': reservas.filter(estado='expirada').count()
        }
        
        response_data = {
            'estadisticas': estadisticas,
            'reservas': datosSerializados.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except:
        return Response("ERROR al obtener reservas", status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# SISTEMA DE REPORTES CON MIXINS DRF
# ============================================================================
#en esta clase se definen las vistas para los reportes y se ocupan def para obtener los reportes, tambien se ocupan mixins para obtener los reportes,e vitando repetir codigo
class ReportesAPI(mixins.ListModelMixin, 
                  generics.GenericAPIView):
    """Vista para reportes usando mixins DRF"""
    permission_classes = [IsAuthenticated] #SOLO AUTENTICADOS
    
    def get(self, request, *args, **kwargs): #se esta definiendo una vista que se llama get, se encarga de obtener los reportes basicos, 
   
        """Obtener reportes básicos"""
        if request.user.rol not in ['bibliotecario', 'administrador']:
            return Response("Sin permisos", status=status.HTTP_403_FORBIDDEN)
        
        try: # y si no hay error, se ejecuta el codigo que esta dentro de la linea
            reportes = { #se esta definiendo un diccionario que se llama reportes, que contiene los reportes basicos
                'libros_mas_populares': self.obtener_libros_populares(), #self es para obtener los reportes basicos de libros mas populares
                'usuarios_con_multas': self.obtener_usuarios_con_multas(), #self es para obtener los reportes basicos de usuarios con multas
                'prestamos_vencidos': self.obtener_prestamos_vencidos(), #self es para obtener los reportes basicos de prestamos vencidos
                'estadisticas_generales': self.obtener_estadisticas_generales() #self es para obtener los reportes basicos de estadisticas generales
            }
            
            return Response(reportes, status=status.HTTP_200_OK)
        except:
            return Response("ERROR al generar reportes", status=status.HTTP_400_BAD_REQUEST)
    
    def obtener_libros_populares(self):
        """Obtiene los 5 libros más prestados"""
        # 1. Obtener todos los libros
        libros = Libro.objects.all()

        # 2. Para cada libro, contar sus préstamos manualmente
        libros_populares = []
        for libro in libros:
            # Contar préstamos de este libro
            total = 0
            for ejemplar in libro.ejemplares.all():
                total += ejemplar.prestamos.count()
            
            # Agregar a la lista con el total
            libros_populares.append({
                'libro': libro,
                'total_prestamos': total
            })

        # 3. Ordenar por total de préstamos (más a menos)
        libros_populares.sort(key=lambda x: x['total_prestamos'], reverse=True)

        # 4. Tomar solo los primeros 10
        libros_populares = libros_populares[:10]
        
        return [
            {
                'titulo': libro.titulo,
                'autor': libro.autor,
                'total_prestamos': libro.total_prestamos
            }
            for libro in libros_populares
        ]
    
    def obtener_usuarios_con_multas(self):
        """Obtiene usuarios con multas pendientes"""
        usuarios_con_multas = Usuario.objects.filter(
            multas_pendientes__gt=0
        ).order_by('-multas_pendientes')
        
        return [
            {
                'username': usuario.username,
                'multas_pendientes': float(usuario.multas_pendientes)
            }
            for usuario in usuarios_con_multas
        ]
    
    def obtener_prestamos_vencidos(self):
        """Obtiene préstamos vencidos"""
        # 1. Obtener préstamos activos
        prestamos_activos = Prestamo.objects.filter(estado='activo')

        # 2. Filtrar vencidos manualmente
        prestamos_vencidos = []
        fecha_actual = timezone.now()

        for prestamo in prestamos_activos:
            # Verificar si está vencido
            if prestamo.fecha_devolucion_esperada < fecha_actual:
                # Calcular días de retraso
                dias_retraso = (fecha_actual.date() - prestamo.fecha_devolucion_esperada.date()).days
                
                prestamos_vencidos.append({
                    'prestamo': prestamo,
                    'dias_retraso': dias_retraso
                })
        
        return [ # despues de obtener los prestamos vencidos, se retorna un diccionario que contiene el usuario, el libro y los dias de retraso
            {
                'usuario': prestamo['prestamo'].usuario.username, #con el punto se accede a los atributos del usuario
                'libro': prestamo['prestamo'].ejemplar.libro.titulo,
                'dias_retraso': prestamo['dias_retraso']
                # .days es para obtener los dias de retraso
            }
            for prestamo in prestamos_vencidos
        ]
    
    def obtener_estadisticas_generales(self):
        """Obtiene estadísticas generales del sistema"""
        return {
            'total_libros': Libro.objects.filter(activo=True).count(),#se esta contando los libros que estan activos y se guardan en total_libros 
            'total_usuarios': Usuario.objects.count(),#se esta contando los usuarios y se guardan en total_usuarios
            'prestamos_activos': Prestamo.objects.filter(estado='activo').count(),#se esta contando los prestamos que estan activos y se guardan en prestamos_activos
            'reservas_activas': Reserva.objects.filter(estado='activa').count(),#se esta contando las reservas que estan activas y se guardan en reservas_activas
            'ejemplares_disponibles': Ejemplar.objects.filter(estado='disponible').count()
        }

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def procesar_cola_reservas(libro):
    """Procesa la cola de reservas cuando se devuelve un libro"""
    try:
        primera_reserva = Reserva.objects.filter( # estamos filtrando las reservas por el libro, estado y posicion de la cola
            libro=libro,
            estado='activa',
            posicion_cola=1
        ).first() # con esto se obtiene la primera reserva de la cola
        
        if primera_reserva: #esta linea se lee asi ; si primera_reserva es true, se ejecuta el codigo que esta dentro de la linea
            primera_reserva.estado = 'cumplida' 
            primera_reserva.save()
            
            # Reorganizar cola
            reservas_restantes = Reserva.objects.filter( # estamos filtrando las reservas por el libro, estado y posicion de la cola
                libro=libro,
                estado='activa',
                posicion_cola__gt=1 #gt es mayor que
            )
            
            for reserva in reservas_restantes: # esta linea se lee asi ; para cada reserva en reservas_restantes, se ejecuta el codigo que esta dentro de la linea, osea que se le resta 1 a la posicion de la cola
                reserva.posicion_cola -= 1 # se le resta 1 a la posicion de la cola, este es el codigo que se ejecuta para cada reserva en reservas_restantes
                reserva.save() # se guarda la reserva
    except:
        pass

@api_view(['POST']) #solo post porque se esta pagando una multa y requier un monto y POST es para crear datos
@permission_classes([IsAuthenticated]) #SOLO AUTENTICADOS
def pagar_multa_api(request): #se esta definiendo una vista que se llama pagar_multa_api, que es una vista que se encarga de pagar multas pendientes
    """Pagar multas pendientes"""
    try:
        usuario = request.user
        monto = float(request.data.get('monto', 0)) # esta linea es para obtener el monto de la multa, request.data.get('monto', 0) es para obtener el monto de la multa, 0 es el valor por defecto
        # se le dice que todo lo que esta en () es como una plantilla para el monto
        if monto <= 0: 
            return Response("El monto debe ser mayor a 0", status=status.HTTP_400_BAD_REQUEST)
        
        if monto > usuario.multas_pendientes: # si el monto es mayor a las multas pendientes, se retorna un error
            return Response("El monto excede las multas pendientes", status=status.HTTP_400_BAD_REQUEST)
        
        usuario.multas_pendientes -= monto # se le resta el monto a las multas pendientes
        usuario.save() 
        
        return Response({
            'mensaje': 'Multa pagada exitosamente',
            'monto_pagado': monto,
            'multas_restantes': float(usuario.multas_pendientes)
        }, status=status.HTTP_200_OK)
    except:
        return Response("ERROR al procesar pago", status=status.HTTP_400_BAD_REQUEST)

     