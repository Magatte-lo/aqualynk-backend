"""
Vues API Aqualynk - avec logs détaillés
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import SystemState, SensorReading
from .weather_service import get_weather_data

from .ai_service import ask_aqualynk_ai
# =====================================================
# AUTHENTIFICATION
# =====================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """POST /api/register/ - Créer un nouveau compte"""
    print("=" * 50)
    print("📥 REGISTER reçu :", request.data)
    print("=" * 50)

    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({
            'success': False,
            'message': 'Tous les champs sont requis'
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 6:
        return Response({
            'success': False,
            'message': 'Mot de passe trop court (min 6 caractères)'
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({
            'success': False,
            'message': 'Ce nom d\'utilisateur est déjà pris'
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({
            'success': False,
            'message': 'Cet email est déjà utilisé'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        print(f"✅ Utilisateur créé : {user.username} ({user.email})")

        return Response({
            'success': True,
            'message': 'Compte créé avec succès',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return Response({
            'success': False,
            'message': f'Erreur : {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """POST /api/login/ - Connexion par email + mot de passe"""
    print("=" * 50)
    print("📥 LOGIN reçu :", request.data)
    print("=" * 50)

    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({
            'detail': 'Email et mot de passe requis'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_obj = User.objects.get(email=email)
        user = authenticate(username=user_obj.username, password=password)
    except User.DoesNotExist:
        user = None

    if user is None:
        print(f"❌ Login échoué pour {email}")
        return Response({
            'detail': 'Email ou mot de passe incorrect'
        }, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    print(f"✅ Login réussi : {user.username}")

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        }
    })


# =====================================================
# DONNÉES CAPTEURS
# =====================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_data(request):
    """GET /api/get_data/ - Retourne l'etat + rafraichit la meteo automatiquement"""
    import sys
    from datetime import timedelta
    from django.utils import timezone

    state = SystemState.get_instance()

    # Force le flush des logs sur Render
    print(f"[GET_DATA] temp={state.temperature}, last_update={state.last_update}", flush=True)
    sys.stdout.flush()

    needs_weather_refresh = (
        state.temperature == 0
        or state.last_update is None
        or (timezone.now() - state.last_update) > timedelta(minutes=10)
    )

    print(f"[GET_DATA] needs_refresh={needs_weather_refresh}", flush=True)
    sys.stdout.flush()

    if needs_weather_refresh:
        try:
            print(f"[METEO] Appel Open-Meteo lat={state.latitude} lon={state.longitude}", flush=True)
            sys.stdout.flush()
            weather = get_weather_data(state.latitude, state.longitude)
            print(f"[METEO] Reponse: {weather}", flush=True)
            sys.stdout.flush()

            if weather and weather.get("success"):
                state.temperature = weather["temperature"]
                state.rain_expected = weather["rain_expected"]
                state.esp32_connected = True
                state.save()
                print(f"[METEO] Sauvegarde OK: {state.temperature}C, pluie={state.rain_expected}", flush=True)
                sys.stdout.flush()
            else:
                print(f"[METEO] Pas success dans la reponse: {weather}", flush=True)
                sys.stdout.flush()
        except Exception as e:
            print(f"[METEO] ERREUR: {type(e).__name__}: {str(e)}", flush=True)
            sys.stdout.flush()
            import traceback
            traceback.print_exc()

    return Response({
        "humidity": state.humidity,
        "temperature": state.temperature,
        "pump_status": state.pump_status,
        "esp32_connected": state.esp32_connected,
        "mode": state.mode,
        "threshold_min": state.threshold_min,
        "threshold_max": state.threshold_max,
        "city": state.city,
        "rain_expected": state.rain_expected,
    })
@api_view(['POST'])
@permission_classes([AllowAny])
def update_sensor(request):
    """
    POST /api/update_sensor/ - L'ESP32 envoie l'humidité
    Le serveur applique la logique d'arrosage intelligent
    """
    humidity = request.data.get('humidity')

    if humidity is None:
        return Response(
            {"error": "humidity requis"},
            status=status.HTTP_400_BAD_REQUEST
        )

    state = SystemState.get_instance()
    state.humidity = float(humidity)
    state.esp32_connected = True

    # === RÉCUPÉRER LA MÉTÉO VIA OPEN-METEO ===
    weather = get_weather_data(state.latitude, state.longitude)
    if weather.get("success"):
        state.temperature = weather["temperature"]
        state.rain_expected = weather["rain_expected"]

    # === LOGIQUE D'ARROSAGE INTELLIGENT ===
    if state.mode == 'auto':
        # NE PAS arroser si pluie prévue (économie d'eau)
        if state.rain_expected:
            state.pump_status = False
        # Activer la pompe si humidité sous le seuil MIN
        elif state.humidity < state.threshold_min:
            state.pump_status = True
        # Désactiver la pompe si humidité au-dessus du seuil MAX
        elif state.humidity > state.threshold_max:
            state.pump_status = False
        # Sinon, garder l'état actuel (zone optimale)

    state.save()

    # Sauvegarder dans l'historique
    SensorReading.objects.create(
        humidity=state.humidity,
        temperature=state.temperature,
    )

    return Response({
        'success': True,
        'pump_status': state.pump_status,
        'mode': state.mode,
        'rain_expected': state.rain_expected,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pump(request):
    """GET /api/get_pump/ - Retourne juste l'état de la pompe"""
    state = SystemState.get_instance()
    return Response({
        'pump_status': state.pump_status,
        'mode': state.mode,
        'threshold_min': state.threshold_min,
        'threshold_max': state.threshold_max,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def control_pump(request):
    """
    POST /api/control_pump/ - Contrôle de la pompe et configuration
    Accepte : pump_on, mode, threshold_min, threshold_max
    """
    state = SystemState.get_instance()

    # Contrôle manuel de la pompe
    if 'pump_on' in request.data:
        state.pump_status = bool(request.data['pump_on'])

    # Changement de mode (auto/manuel)
    if 'mode' in request.data:
        mode = request.data['mode']
        if mode in ['auto', 'manual']:
            state.mode = mode

    # Seuil minimum (déclenchement)
    if 'threshold_min' in request.data:
        threshold_min = float(request.data['threshold_min'])
        if not 0 <= threshold_min <= 100:
            return Response(
                {"error": "threshold_min doit être entre 0 et 100"},
                status=status.HTTP_400_BAD_REQUEST
            )
        state.threshold_min = threshold_min

    # Seuil maximum (arrêt)
    if 'threshold_max' in request.data:
        threshold_max = float(request.data['threshold_max'])
        if not 0 <= threshold_max <= 100:
            return Response(
                {"error": "threshold_max doit être entre 0 et 100"},
                status=status.HTTP_400_BAD_REQUEST
            )
        state.threshold_max = threshold_max

    # Validation : min doit être inférieur à max
    if state.threshold_min >= state.threshold_max:
        return Response(
            {"error": "threshold_min doit être < threshold_max"},
            status=status.HTTP_400_BAD_REQUEST
        )

    state.save()

    return Response({
        'success': True,
        'pump_status': state.pump_status,
        'mode': state.mode,
        'threshold_min': state.threshold_min,
        'threshold_max': state.threshold_max,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_threshold(request):
    """
    POST /api/set_threshold/ - Met à jour les 2 seuils
    Accepte : threshold_min, threshold_max
    """
    threshold_min = request.data.get('threshold_min')
    threshold_max = request.data.get('threshold_max')

    state = SystemState.get_instance()

    if threshold_min is not None:
        threshold_min = float(threshold_min)
        if not 0 <= threshold_min <= 100:
            return Response(
                {"error": "threshold_min doit être entre 0 et 100"},
                status=status.HTTP_400_BAD_REQUEST
            )
        state.threshold_min = threshold_min

    if threshold_max is not None:
        threshold_max = float(threshold_max)
        if not 0 <= threshold_max <= 100:
            return Response(
                {"error": "threshold_max doit être entre 0 et 100"},
                status=status.HTTP_400_BAD_REQUEST
            )
        state.threshold_max = threshold_max

    if state.threshold_min >= state.threshold_max:
        return Response(
            {"error": "threshold_min doit être < threshold_max"},
            status=status.HTTP_400_BAD_REQUEST
        )

    state.save()

    return Response({
        'success': True,
        'threshold_min': state.threshold_min,
        'threshold_max': state.threshold_max,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    """POST /api/ai_chat/ - Chatbot agronome Gemini"""
    question = request.data.get('question', '').strip()

    if not question:
        return Response({'error': 'Question requise'}, status=status.HTTP_400_BAD_REQUEST)

    if len(question) > 500:
        return Response({'error': 'Question trop longue (max 500 caracteres)'}, status=status.HTTP_400_BAD_REQUEST)

    state = SystemState.get_instance()
    context = {
        'humidity': state.humidity,
        'temperature': state.temperature,
        'pump_status': state.pump_status,
        'rain_expected': state.rain_expected,
        'city': state.city,
    }

    print(f"🤖 Question IA : {question}")
    answer = ask_aqualynk_ai(question, context)
    print(f"💬 Reponse : {answer[:100]}...")

    return Response({
        'question': question,
        'answer': answer,
    })    