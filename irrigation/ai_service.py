"""
Service IA Gemini pour Aqualynk - Chatbot Agronome
Repond en francais OU en wolof selon la langue de la question.
"""
import google.generativeai as genai
from django.conf import settings


# Initialiser Gemini avec la cle du settings.py
api_key = getattr(settings, 'GEMINI_API_KEY', '')
if api_key:
    genai.configure(api_key=api_key)


def ask_aqualynk_ai(question, context=None):
    """
    Pose une question a l'IA agronome d'Aqualynk.
    Repond en francais OU en wolof selon la langue de la question.
    """
    if not api_key:
        return "L'assistant IA n'est pas configure. Contactez l'administrateur."

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-001')

        context_str = ""
        if context:
            context_str = f"""
Contexte actuel du systeme Aqualynk :
- Humidite du sol : {context.get('humidity', 'N/A')}%
- Temperature : {context.get('temperature', 'N/A')} degres
- Pompe : {'Activee' if context.get('pump_status') else 'Desactivee'}
- Pluie prevue : {'Oui' if context.get('rain_expected') else 'Non'}
- Localisation : {context.get('city', 'Dakar')}, Senegal
"""

        prompt = f"""Tu es Aqualynk AI, un assistant agronome expert pour les agriculteurs senegalais.

{context_str}

REGLE LINGUISTIQUE TRES IMPORTANTE :
- Detecte automatiquement la langue de la question (francais ou wolof)
- Si la question est en WOLOF, reponds EN WOLOF
- Si la question est en FRANCAIS, reponds EN FRANCAIS
- Si la question melange les deux, reponds dans la langue dominante
- Exemples de mots wolof : nanga def, naka, ndax, kan, fan, fii, suba, ndox, suuf, garab, mbey, beykat
- Pour le wolof, utilise une orthographe simple comprehensible (pas l'orthographe academique stricte)

Autres regles :
- Sois concis (max 4-5 phrases)
- Donne des conseils pratiques adaptes au climat sahelien et au Senegal
- Utilise des connaissances agronomiques de la FAO et de l'ISRA
- Si la question n'est pas liee a l'agriculture, redirige poliment vers l'agriculture
- N'utilise pas de markdown (pas de **, pas de #)
- Sois chaleureux comme un voisin agriculteur experimente

Question de l'agriculteur : {question}

Reponse :"""

        response = model.generate_content(
    prompt,
    request_options={"timeout": 25}  # Max 25 sec pour eviter les timeouts
)
        return response.text.strip()

    except Exception as e:
        print(f"Erreur Gemini : {e}")
        return "Desole, l'assistant IA n'est pas disponible pour le moment. Reessayez plus tard."