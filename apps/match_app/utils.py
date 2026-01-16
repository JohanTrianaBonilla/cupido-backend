# apps/match_app/utils.py
from typing import Optional, Set, List
import json

from apps.profile_app.subapps.profile.models import Perfil
from apps.preferences_app.models import Preference
from apps.auth_app.models import Usuario


# =========================================
# Helpers
# =========================================

def normalizar_hobbies(cadena: Optional[str]) -> Set[str]:
    if not cadena:
        return set()

    cadena = cadena.strip()

    # Si parece una lista JSON, intentamos parsearla
    if cadena.startswith("[") and cadena.endswith("]"):
        try:
            items = json.loads(cadena)
        except Exception:
            items = cadena.split(",")
    else:
        items = cadena.split(",")

    return {str(h).strip().lower() for h in items if str(h).strip()}


def obtener_usuario_de_perfil(perfil: Perfil) -> Optional[Usuario]:
    """
    Devuelve el Usuario dueño de este perfil.
    """
    usuario = getattr(perfil, "usuario", None)
    if usuario is not None:
        return usuario

    user_id = getattr(perfil, "usuario_id", None)
    if user_id is None:
        return None

    return Usuario.objects.filter(usuario_id=user_id).first()


def genero_coincide_con_preferencia(perfil: Perfil, preferencias: Preference) -> bool:
    """
    Reglas:
      - genero_preferido = 'Mujer'  -> solo genero_id = 2
      - genero_preferido = 'Hombre'-> solo genero_id = 1
      - genero_preferido = 'Otros'/'Otro' -> acepta 1, 2 y 3 (no filtra)
      - genero_preferido vacío/raro -> no filtra (True)
    """
    pref = (preferencias.genero_preferido or "").strip().lower()
    if not pref:
        return True

    usuario = obtener_usuario_de_perfil(perfil)
    if not usuario:
        return False

    genero_id = getattr(usuario, "genero_id", None)
    if genero_id is None:
        return False

    if pref == "mujer":
        return genero_id == 2
    if pref == "hombre":
        return genero_id == 1
    if pref in ("otros", "otro"):
        return genero_id in {1, 2, 3}

    return True


# --- Ubicación: texto (preferences) -> id numérico (perfil.ubicacion_id) ---

def normalizar_ubicacion_texto(texto: Optional[str]) -> Optional[int]:
    """
    Convierte 'Pamplona' / 'Cúcuta' (o variaciones) al id entero que usa Perfil.ubicacion_id.
    Asumimos:
      1 -> Pamplona
      2 -> Cúcuta
    """
    if not texto:
        return None

    t = texto.strip().lower()
    # quitar acentos básicos
    t = (
        t.replace("á", "a")
         .replace("é", "e")
         .replace("í", "i")
         .replace("ó", "o")
         .replace("ú", "u")
    )

    if "pamplona" in t:
        return 1
    if "cucuta" in t:
        return 2
    return None


def ubicacion_coincide(preferencias: Preference, perfil: Perfil) -> bool:
    """
    True si la ubicación del perfil coincide con la preferida.
    Si no hay ubicación preferida, no filtra.
    """
    pref_ubi_id = normalizar_ubicacion_texto(preferencias.ubicacion)
    if pref_ubi_id is None:
        return True  # sin preferencia de ciudad

    perfil_ubi_id = getattr(perfil, "ubicacion_id", None)
    if perfil_ubi_id is None:
        return False

    return perfil_ubi_id == pref_ubi_id


def estatura_en_cm(perfil: Perfil) -> Optional[int]:
    """
    Convierte la estatura del perfil a centímetros.
    En Perfil está en metros (ej. 1.53) y en Preference en cm (ej. 153).
    """
    est = getattr(perfil, "estatura", None)
    if est is None:
        return None
    try:
        return int(round(float(est) * 100))
    except (TypeError, ValueError):
        return None


# ===============================
# Obtener perfil y preferencias
# ===============================

def obtener_perfil(user_id: int) -> Optional[Perfil]:
    return Perfil.objects.filter(usuario_id=user_id).first()


def obtener_preferencias_por_perfil(perfil: Perfil) -> Optional[Preference]:
    pref_id = getattr(perfil, "preferencias_id", None)
    if not pref_id:
        return None
    return Preference.objects.filter(id=pref_id).first()


def obtener_otros_perfiles(perfil: Perfil):
    return Perfil.objects.exclude(usuario_id=perfil.usuario_id)


# ===============================
# Validación de compatibilidad (filtros duros)
# ===============================

def perfil_cumple_preferencias(perfil: Perfil, preferencias: Preference) -> bool:
    # 0) Género: filtro duro obligatorio
    if not genero_coincide_con_preferencia(perfil, preferencias):
        return False

    # 1) Rango de estatura (en cm)
    estatura_cm = estatura_en_cm(perfil)

    if preferencias.rango_estatura_min is not None and estatura_cm is not None:
        if estatura_cm < preferencias.rango_estatura_min:
            return False

    if preferencias.rango_estatura_max is not None and estatura_cm is not None:
        if estatura_cm > preferencias.rango_estatura_max:
            return False

    # 2) Hobbies: si hay hobbies preferidos, al menos 1 en común
    pref_hobbies = normalizar_hobbies(preferencias.hobbies_preferidos)
    perfil_hobbies = normalizar_hobbies(perfil.hobbies)

    if pref_hobbies:
        if not (pref_hobbies & perfil_hobbies):
            return False

    # 3) Edad
    edad_perfil = getattr(perfil, "edad", None)

    if preferencias.rango_edad_min is not None and edad_perfil is not None:
        if edad_perfil < preferencias.rango_edad_min:
            return False

    if preferencias.rango_edad_max is not None and edad_perfil is not None:
        if edad_perfil > preferencias.rango_edad_max:
            return False

    # 4) Ubicación (Pamplona/Cúcuta)
    if not ubicacion_coincide(preferencias, perfil):
        return False

    return True


# ===============================
# Score de compatibilidad
# ===============================

def calcular_score(preferencias: Preference, perfil: Perfil) -> float:
    """
    Puntaje:
      +1  si género coincide (obligatorio)
      +N  hobbies en común
      +1  estatura dentro de rango (cm)
      +1  edad dentro de rango (si tiene)
      +1  ubicación coincide (Pamplona/Cúcuta)
    """
    # Género obligatorio para cualquier puntaje
    if not genero_coincide_con_preferencia(perfil, preferencias):
        return 0.0

    score = 0.0

    # 1) Género
    score += 1.0

    # 2) Hobbies
    pref_hobbies = normalizar_hobbies(preferencias.hobbies_preferidos)
    perfil_hobbies = normalizar_hobbies(perfil.hobbies)
    comunes = pref_hobbies & perfil_hobbies
    score += float(len(comunes))

    # 3) Estatura (cm)
    estatura_cm = estatura_en_cm(perfil)
    if (
        preferencias.rango_estatura_min is not None
        and preferencias.rango_estatura_max is not None
        and estatura_cm is not None
    ):
        if preferencias.rango_estatura_min <= estatura_cm <= preferencias.rango_estatura_max:
            score += 1.0

    # 4) Edad
    edad_perfil = getattr(perfil, "edad", None)
    if (
        preferencias.rango_edad_min is not None
        and preferencias.rango_edad_max is not None
        and edad_perfil is not None
    ):
        if preferencias.rango_edad_min <= edad_perfil <= preferencias.rango_edad_max:
            score += 1.0

    # 5) Ubicación
    if ubicacion_coincide(preferencias, perfil):
        score += 1.0

    return score


# ===============================
# Perfiles sugeridos (feed)
# ===============================

def obtener_usuarios_ya_interactuados(user_id: int) -> Set[int]:
    """
    Obtiene los IDs de usuarios con los que ya hubo interacción (LIKE o DISLIKE).
    Estos usuarios no deben aparecer en las recomendaciones.
    """
    from apps.like_app.models import DetallesLike
    
    # Obtener todos los usuarios a los que este usuario ya dio like/dislike
    interacciones = DetallesLike.objects.filter(
        usuarioEmisor_id=user_id
    ).values_list('usuarioReceptor_id', flat=True)
    
    return set(interacciones)


def obtener_perfiles_sugeridos(
    perfil_usuario: Perfil,
    preferencias: Preference,
    limite: int = 100,  # Aumentado para compensar los filtrados
    con_score: bool = False,
):
    """
    Devuelve:
      - si con_score == False: lista de Perfiles sugeridos
      - si con_score == True: lista de tuplas (Perfil, score)
    
    Excluye usuarios con los que ya hubo interacción (like/dislike previo).
    """
    otros = obtener_otros_perfiles(perfil_usuario)
    
    # Obtener usuarios ya interactuados para excluirlos
    usuarios_excluidos = obtener_usuarios_ya_interactuados(perfil_usuario.usuario_id)

    compatibles: List[tuple[Perfil, float]] = []

    for p in otros:
        # Excluir usuarios con interacción previa
        if p.usuario_id in usuarios_excluidos:
            continue
            
        hard_ok = perfil_cumple_preferencias(p, preferencias)
        score = calcular_score(preferencias, p)

        if hard_ok:
            compatibles.append((p, score))
        else:
            # aún si no pasa todos los filtros, dejamos pasar
            # si tiene score >= 1 (pero género ya está garantizado por calcular_score)
            if score >= 1:
                compatibles.append((p, score))

    compatibles.sort(key=lambda x: x[1], reverse=True)

    if con_score:
        return compatibles[:limite]

    return [p for p, _ in compatibles[:limite]]

