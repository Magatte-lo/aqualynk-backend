"""
Service IA Gemini - Aqualynk
Chatbot agronome contextuel francais + wolof
Avec fallback intelligent en cas d'echec Gemini
"""
import os
import sys
import google.generativeai as genai

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MOTS_WOLOF = [
    'nanga', 'def', 'naka', 'ndax', 'kan', 'fan', 'fii', 'suba',
    'ndox', 'suuf', 'garab', 'mbey', 'beykat', 'yaay', 'yow',
    'noo', 'lan', 'laa', 'ci', 'ak', 'wara', 'dañu', 'baax', 'domate'
]


def detecter_langue(texte):
    """Detecte si le texte est en wolof"""
    texte_lower = texte.lower()
    return 'wolof' if sum(1 for mot in MOTS_WOLOF if mot in texte_lower) >= 1 else 'francais'


REPONSES_FALLBACK = {
    'francais': {
        'tomate': "Pour les tomates au Senegal, arrosez tot le matin ou en soiree pour eviter l'evaporation. Maintenez l'humidite du sol entre 40 et 60 pourcent. En saison seche, un arrosage tous les 2 jours suffit. Attention aux exces d'eau qui favorisent les maladies fongiques.",
        'salade': "La salade demande un arrosage regulier mais modere. Gardez l'humidite entre 50 et 70 pourcent. Preferez l'arrosage matinal pour eviter le mildiou. Un paillage aide a conserver l'humidite du sol.",
        'mil': "Le mil est resistant a la secheresse, adapte au climat sahelien. Un arrosage abondant tous les 4 a 5 jours suffit en periode seche. Verifiez l'humidite reguliere du sol autour des racines.",
        'arachide': "L'arachide necessite une bonne humidite surtout pendant la floraison et le remplissage des gousses. Maintenez le sol legerement humide entre 45 et 65 pourcent. Evitez les exces d'eau qui pourrissent les gousses.",
        'mais': "Le mais consomme beaucoup d'eau. Arrosez abondamment 2 a 3 fois par semaine, surtout pendant la formation des epis. Un manque d'eau a ce stade reduit fortement le rendement.",
        'oignon': "L'oignon prefere un sol modere en humidite. Arrosez tous les 2 a 3 jours en evitant de mouiller le feuillage pour prevenir les maladies. Reduire l'arrosage 2 semaines avant la recolte.",
        'manioc': "Le manioc est tres resistant a la secheresse. Un arrosage hebdomadaire suffit sauf pendant les 3 premiers mois de croissance ou il faut arroser 2 fois par semaine.",
        'chou': "Le chou aime l'humidite constante. Arrosez tous les 2 jours en periode seche, en gardant l'humidite entre 60 et 75 pourcent. Un paillage epais est recommande.",
        'gombo': "Le gombo tolere la chaleur mais apprecie l'humidite. Arrosez 2 a 3 fois par semaine. Maintenez le sol humide entre 45 et 65 pourcent pour une bonne production.",
        'defaut': "Pour une reponse personnalisee, verifiez le niveau d'humidite actuel de votre sol et ajustez selon votre culture. Un sol entre 40 et 60 pourcent d'humidite convient a la plupart des legumes maraichers. Arrosez tot le matin ou en soiree pour reduire l'evaporation."
    },
    'wolof': {
        'domate': "Ngir domate ci Senegaal, wara nga arroser ci suba wala ngoon ngir moytu chaleur. Suuf si wara am 40 ba 60 pourcent ndox. Ci nawet, benn arrosage ci 2 fan doy na. Moytu bari ndox rekk buleen bari maladie.",
        'salade': "Salade dafa laaj ndox waaye du bari. Sa suuf wara am 50 ba 70 pourcent ndox. Suba mooy jamono baax ngir arroser. Ligeeyal paillage ngir suuf gi bagn suuf.",
        'mbey': "Mbey mi baax na ngir yoor-yoor. Arroser 4 wala 5 fan bi. Seetal ndox si sa suuf ci racines yi.",
        'defaut': "Ngir jang lu gën, seetal ndox si sa suuf ak toppatoo ni sa mbey bindu. Suuf bu am 40 ba 60 pourcent ndox baax na ngir mbay yu bari. Arroser suba wala ngoon ngir moytu chaleur bi."
    }
}


def reponse_fallback(question, langue):
    """Reponse de secours si Gemini est indisponible"""
    question_lower = question.lower()
    reponses = REPONSES_FALLBACK.get(langue, REPONSES_FALLBACK['francais'])
    
    for mot_cle, reponse in reponses.items():
        if mot_cle != 'defaut' and mot_cle in question_lower:
            return reponse
    
    return reponses['defaut']


def ask_aqualynk_ai(question, context):
    """
    Pose une question a l'assistant IA Aqualynk
    Utilise Gemini si disponible, sinon fallback intelligent
    """
    langue = detecter_langue(question)
    print(f"[AI] Question ({langue}) : {question}", flush=True)
    sys.stdout.flush()

    if not GEMINI_API_KEY:
        print("[AI] Pas de cle API, fallback active", flush=True)
        return reponse_fallback(question, langue)

    prompt = f"""Tu es Aqualynk AI, un assistant agronome expert pour les agriculteurs senegalais.

CONTEXTE ACTUEL DU SYSTEME :
- Humidite du sol : {context.get('humidity', 0)} pourcent
- Temperature : {context.get('temperature', 0)} degres Celsius
- Ville : {context.get('city', 'Dakar')}
- Pluie prevue : {'Oui' if context.get('rain_expected') else 'Non'}
- Pompe active : {'Oui' if context.get('pump_status') else 'Non'}

CONSIGNES :
1. Reponds de maniere concise et pratique (max 4-5 phrases)
2. {"Reponds EN WOLOF simple et clair" if langue == 'wolof' else "Reponds en francais simple"}
3. Base-toi sur le contexte actuel du systeme
4. Sois pragmatique, oriente terrain senegalais
5. Si la question n'est pas agronome, redirige poliment

QUESTION DU AGRICULTEUR : {question}

REPONSE :"""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-001')
        response = model.generate_content(
            prompt,
            request_options={"timeout": 25}
        )
        answer = response.text.strip()
        print(f"[AI] Reponse Gemini OK ({len(answer)} chars)", flush=True)
        return answer

    except Exception as e:
        error_type = type(e).__name__
        print(f"[AI] Exception {error_type}: {str(e)[:150]}", flush=True)
        print(f"[AI] Utilisation du fallback ({langue})", flush=True)
        sys.stdout.flush()
        return reponse_fallback(question, langue)