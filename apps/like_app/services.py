# apps/like_app/services.py

from django.db import transaction
from django.db import IntegrityError
from django.db.models import Q
from django.contrib.auth import get_user_model
from apps.like_app.models import DetallesLike
from apps.match_app.models import Match
from rest_framework.exceptions import ValidationError

User = get_user_model()

def process_user_interaction(emisor_id, receptor_id, accion):
    """
    Lógica del sistema de likes:
    
    1. Cada interacción genera un registro en detalles_like
    2. Para un match se necesitan 2 registros: A->B LIKE y B->A LIKE
    3. Cuando ocurre la segunda interacción, se detecta reciprocidad:
       - Ambos registros actualizan esMutuo = True
       - Se crea UN SOLO registro en match
    4. Si no hay reciprocidad, solo se crea like con esMutuo = False
    """
    
    # Asegurar que los IDs son enteros
    emisor_id = int(emisor_id)
    receptor_id = int(receptor_id)
    
    # --- 1. Validaciones básicas ---
    if emisor_id == receptor_id:
        raise ValidationError({"message": "No puedes interactuar contigo mismo."})
    
    try:
        User.objects.get(usuario_id=receptor_id) 
    except User.DoesNotExist:
        raise ValidationError({"message": "Perfil receptor no encontrado."})

    # --- 2. Verificar si ya existe interacción A->B ---
    interaccion_existente = DetallesLike.objects.filter(
        usuarioEmisor_id=emisor_id,
        usuarioReceptor_id=receptor_id
    ).first()
    
    if interaccion_existente:
        if interaccion_existente.esMutuo:
            raise ValidationError({"message": "Ya tienes un match con este usuario."})
        if interaccion_existente.estado == accion:
            raise ValidationError({"message": "Ya has interactuado con este perfil."})

    # --- 3. Lógica principal ---
    try:
        with transaction.atomic():
            es_match = False
            
            # Solo verificar match mutuo si la acción es LIKE
            if accion == 'LIKE':
                # Buscar si existe LIKE en sentido contrario (B->A con LIKE)
                like_reciproco = DetallesLike.objects.filter(
                    usuarioEmisor_id=receptor_id,
                    usuarioReceptor_id=emisor_id,
                    estado='LIKE',
                    esMutuo=False  # Solo si aún no es mutuo
                ).first()

                if like_reciproco:
                    # ¡HAY MATCH MUTUO!
                    es_match = True
                    
                    # a) Actualizar el like recíproco (B->A) a esMutuo=True
                    like_reciproco.esMutuo = True
                    like_reciproco.save()
                    
                    # b) Verificar que no exista ya un match entre esta pareja
                    # Ordenamos los IDs para consistencia (siempre menor primero)
                    usuario_a = min(emisor_id, receptor_id)
                    usuario_b = max(emisor_id, receptor_id)
                    
                    match_existe = Match.objects.filter(
                        usuarioA_id=usuario_a,
                        usuarioB_id=usuario_b
                    ).exists()
                    
                    # c) Crear match SOLO si no existe
                    if not match_existe:
                        Match.objects.create(
                            usuarioA_id=usuario_a,
                            usuarioB_id=usuario_b,
                            estadoMatch='ACTIVO'
                        )
            
            # --- 4. Crear o actualizar el registro de interacción A->B ---
            if interaccion_existente:
                # Actualizar (ej: cambiaron de DISLIKE a LIKE)
                interaccion_existente.estado = accion
                interaccion_existente.esMutuo = es_match
                interaccion_existente.save()
            else:
                # Crear nuevo registro
                DetallesLike.objects.create(
                    usuarioEmisor_id=emisor_id,
                    usuarioReceptor_id=receptor_id,
                    estado=accion,
                    esMutuo=es_match
                )
            
            # --- 5. Respuesta ---
            if es_match:
                return {
                    "match_found": True, 
                    "message": "¡Match Mutuo!", 
                    "usuario_match": receptor_id,
                    "status_code": 201
                }
            elif accion == 'LIKE':
                return {
                    "match_found": False, 
                    "message": "Like registrado.",
                    "status_code": 201
                }
            else:  # DISLIKE
                return {
                    "match_found": False, 
                    "message": "Descarte registrado.",
                    "status_code": 201
                }

    except IntegrityError as e:
        raise ValidationError({"message": f"Error de base de datos: {str(e)}"})