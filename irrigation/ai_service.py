"""
Service IA Aqualynk - Chatbot agronome contextuel
Utilise Gemini si disponible, sinon fallback intelligent avec contexte
"""
import os
import sys
import random
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


def analyser_question(question):
    """Detecte le sujet principal de la question"""
    q = question.lower()
    
    # Cultures
    if any(w in q for w in ['tomate', 'domate']): return 'tomate'
    if any(w in q for w in ['salade', 'laitue']): return 'salade'
    if any(w in q for w in ['mil', 'mbey']): return 'mil'
    if any(w in q for w in ['arachide', 'gerte']): return 'arachide'
    if any(w in q for w in ['mais', 'mais']): return 'mais'
    if any(w in q for w in ['oignon', 'soble']): return 'oignon'
    if any(w in q for w in ['manioc']): return 'manioc'
    if any(w in q for w in ['chou']): return 'chou'
    if any(w in q for w in ['gombo', 'kandja']): return 'gombo'
    if any(w in q for w in ['piment']): return 'piment'
    if any(w in q for w in ['carotte']): return 'carotte'
    if any(w in q for w in ['pomme de terre', 'patate']): return 'patate'
    
    # Themes
    if any(w in q for w in ['humid', 'sec', 'seche', 'ndox', 'suuf']): return 'humidite'
    if any(w in q for w in ['pluie', 'pluvieux', 'taw']): return 'pluie'
    if any(w in q for w in ['temperature', 'chaleur', 'chaud', 'froid', 'tang']): return 'temperature'
    if any(w in q for w in ['pompe', 'arros', 'irrigation']): return 'pompe'
    if any(w in q for w in ['seuil', 'threshold']): return 'seuil'
    if any(w in q for w in ['engrais', 'fumure', 'ndim']): return 'engrais'
    if any(w in q for w in ['maladie', 'insect', 'ravageur']): return 'maladie'
    if any(w in q for w in ['saison', 'nawet', 'noor']): return 'saison'
    if any(w in q for w in ['bonjour', 'hello', 'salam', 'nanga def']): return 'salutation'
    if any(w in q for w in ['aide', 'help', 'ndimbal']): return 'aide'
    
    return 'general'


def reponse_intelligente(question, langue, context):
    """Genere une reponse contextuelle intelligente sans Gemini"""
    sujet = analyser_question(question)
    
    humidity = context.get('humidity', 0)
    temperature = context.get('temperature', 28)
    rain = context.get('rain_expected', False)
    pump = context.get('pump_status', False)
    city = context.get('city', 'Dakar')
    
    # === Diagnostic du sol ===
    if humidity < 30:
        etat_sol_fr = f"Votre sol est actuellement TRES SEC ({humidity} pourcent)"
        etat_sol_wo = f"Sa suuf am na yoor-yoor ({humidity} pourcent ndox rekk)"
    elif humidity < 50:
        etat_sol_fr = f"Votre sol est SEC ({humidity} pourcent)"
        etat_sol_wo = f"Sa suuf dafa noy ({humidity} pourcent ndox)"
    elif humidity < 70:
        etat_sol_fr = f"Votre sol a une humidite OPTIMALE ({humidity} pourcent)"
        etat_sol_wo = f"Sa suuf am na ndox mu baax ({humidity} pourcent)"
    else:
        etat_sol_fr = f"Votre sol est TRES HUMIDE ({humidity} pourcent)"
        etat_sol_wo = f"Sa suuf am na ndox bari ({humidity} pourcent)"
    
    # ===================== FRANCAIS =====================
    if langue == 'francais':
        # Salutations
        if sujet == 'salutation':
            return f"Bonjour ! Je suis Aqualynk AI, votre assistant agronome. {etat_sol_fr} et la temperature est de {temperature} degres. Comment puis-je vous aider aujourd'hui ?"
        
        # Aide generale
        if sujet == 'aide':
            return f"Je peux vous conseiller sur l'arrosage de vos cultures (tomate, salade, mil, arachide, mais, oignon, manioc, gombo...), analyser l'etat de votre sol, ou vous informer sur les conditions meteo. {etat_sol_fr}."
        
        # Etat du sol/humidite
        if sujet == 'humidite':
            conseil = "Il faut arroser rapidement." if humidity < 30 else ("Un arrosage leger suffira." if humidity < 50 else ("Pas besoin d'arroser pour l'instant." if humidity < 70 else "Attention, evitez d'arroser pour ne pas noyer les racines."))
            return f"{etat_sol_fr}. {conseil} La temperature actuelle est de {temperature} degres a {city}."
        
        # Meteo/pluie
        if sujet == 'pluie':
            if rain:
                return f"Oui, de la pluie est prevue a {city}. Nous vous recommandons de ne pas activer la pompe pour economiser l'eau. {etat_sol_fr}."
            else:
                return f"Non, aucune pluie prevue a {city} pour le moment. {etat_sol_fr}. Il faut donc surveiller l'arrosage."
        
        # Temperature
        if sujet == 'temperature':
            if temperature > 32:
                conseil_t = "Il fait tres chaud. Arrosez tot le matin ou en soiree pour eviter l'evaporation."
            elif temperature > 25:
                conseil_t = "Temperature normale pour la saison. Arrosage regulier recommande."
            else:
                conseil_t = "Temperature relativement fraiche. L'evaporation sera moins forte, arrosez moderement."
            return f"La temperature actuelle a {city} est de {temperature} degres. {conseil_t} {etat_sol_fr}."
        
        # Pompe
        if sujet == 'pompe':
            etat_pompe = "actuellement ACTIVE" if pump else "actuellement ARRETEE"
            recommandation = ""
            if humidity < 30 and not pump:
                recommandation = " Nous vous recommandons de l'activer immediatement car votre sol est trop sec."
            elif humidity > 70 and pump:
                recommandation = " Nous vous recommandons de l'arreter car votre sol est deja tres humide."
            return f"La pompe est {etat_pompe}. {etat_sol_fr}.{recommandation}"
        
        # Seuils
        if sujet == 'seuil':
            return "Les seuils MIN et MAX definissent la plage optimale d'humidite pour vos cultures. La pompe s'active automatiquement en dessous du MIN et s'arrete au dessus du MAX. Pour les cultures maraicheres, un MIN de 40 pourcent et un MAX de 60 pourcent conviennent bien."
        
        # Saisons
        if sujet == 'saison':
            return f"Au Senegal, on distingue la saison des pluies (juin-octobre) et la saison seche (novembre-mai). Actuellement a {city}, il fait {temperature} degres. Adaptez votre irrigation : moins d'arrosage en saison humide, plus intensif en saison seche."
        
        # Engrais
        if sujet == 'engrais':
            return "Un bon amendement du sol ameliore la retention d'eau. Utilisez du compost, du fumier bien decompose ou des engrais NPK selon vos cultures. Appliquez avant la plantation puis en cours de croissance. Pour votre sol actuel, un apport organique aiderait a mieux retenir l'humidite."
        
        # Maladies
        if sujet == 'maladie':
            humidity_high = humidity > 70
            risque = "Le fort taux d'humidite actuel augmente le risque de maladies fongiques (mildiou, oidium). Aerez bien vos cultures et evitez d'arroser le feuillage." if humidity_high else "Surveillez regulierement vos plants. En cas de taches ou d'insectes, isolez les plants atteints et utilisez des traitements bio comme le neem."
            return f"{risque} {etat_sol_fr}."
        
        # Cultures specifiques
        conseils_cultures = {
            'tomate': f"Pour les tomates, l'humidite ideale est entre 40 et 60 pourcent. {etat_sol_fr}. " + ("Arrosez maintenant." if humidity < 40 else ("Conditions parfaites." if humidity < 60 else "Reduisez l'arrosage pour eviter les maladies.")),
            'salade': f"La salade prefere une humidite entre 50 et 70 pourcent. {etat_sol_fr}. Arrosez le matin pour limiter les maladies fongiques.",
            'mil': f"Le mil est resistant a la secheresse. {etat_sol_fr}. Un arrosage tous les 4-5 jours suffit generalement.",
            'arachide': f"L'arachide a besoin d'humidite pendant la floraison (45-65 pourcent). {etat_sol_fr}. Evitez l'exces d'eau qui pourrit les gousses.",
            'mais': f"Le mais consomme beaucoup d'eau, surtout pendant la formation des epis. {etat_sol_fr}. Arrosez 2-3 fois par semaine.",
            'oignon': f"L'oignon prefere 45-55 pourcent d'humidite. {etat_sol_fr}. Reduisez l'arrosage 2 semaines avant recolte.",
            'manioc': f"Le manioc est tres resistant. {etat_sol_fr}. Un arrosage hebdomadaire suffit sauf jeunes plants.",
            'chou': f"Le chou aime l'humidite constante (60-75 pourcent). {etat_sol_fr}. Arrosez regulierement et paillez.",
            'gombo': f"Le gombo tolere la chaleur, humidite ideale 45-65 pourcent. {etat_sol_fr}. Arrosez 2-3 fois par semaine.",
            'piment': f"Le piment prefere 50-65 pourcent d'humidite. {etat_sol_fr}. Attention aux exces qui font pourrir les racines.",
            'carotte': f"La carotte demande un sol frais et meuble (55-65 pourcent). {etat_sol_fr}. Arrosez regulierement mais sans exces.",
            'patate': f"La pomme de terre aime 60-70 pourcent d'humidite. {etat_sol_fr}. Arrosez regulierement, surtout a la tuberisation."
        }
        if sujet in conseils_cultures:
            return conseils_cultures[sujet]
        
        # Reponse generale (n'importe quelle question)
        return f"Je suis votre assistant agronome Aqualynk. {etat_sol_fr}, temperature {temperature} degres a {city}, pluie prevue : {'oui' if rain else 'non'}. Precisez votre question pour une reponse plus ciblee (culture specifique, arrosage, meteo...)."
    
    # ===================== WOLOF =====================
    else:
        if sujet == 'salutation':
            return f"Nanga def ! Man mooy Aqualynk AI. {etat_sol_wo} ak tang bi mooy {temperature} degres. Naka laa la mena dimbali tey ?"
        
        if sujet == 'humidite':
            conseil = "Wara nga arroser leegi." if humidity < 30 else ("Arroser tuuti doy na." if humidity < 50 else "Bul arroser leegi.")
            return f"{etat_sol_wo}. {conseil} Tang bi mooy {temperature} degres ci {city}."
        
        if sujet == 'pluie':
            if rain:
                return f"Waaw, taw dina daaneel ci {city}. Bul indi pompe bi ngir bagn ndox. {etat_sol_wo}."
            else:
                return f"Deedeet, amul taw ci {city} leegi. {etat_sol_wo}. Nag arroser dafa laaj."
        
        if sujet == 'pompe':
            etat = "dafa dox" if pump else "dafa taxaw"
            return f"Pompe bi {etat}. {etat_sol_wo}."
        
        if sujet == 'tomate':
            return f"Ngir domate, ndox bu baax mooy 40 ba 60 pourcent. {etat_sol_wo}. " + ("Arroser leegi." if humidity < 40 else "Baax na nii.")
        
        if sujet == 'mil':
            return f"Mbey mi baax na ngir yoor-yoor. {etat_sol_wo}. Arroser 4 wala 5 fan bi doy na."
        
        # Reponse generale en wolof
        return f"Man mooy sa assistant agronome. {etat_sol_wo}, tang bi {temperature} degres ci {city}. Wax ma sa laaj bu gudd."


def ask_aqualynk_ai(question, context):
    """
    Pose une question a l'assistant IA Aqualynk
    Utilise Gemini si disponible, sinon reponse intelligente contextuelle
    """
    langue = detecter_langue(question)
    print(f"[AI] Question ({langue}) : {question}", flush=True)
    sys.stdout.flush()

    if not GEMINI_API_KEY:
        print("[AI] Pas de cle API, fallback intelligent active", flush=True)
        return reponse_intelligente(question, langue, context)

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

QUESTION : {question}

REPONSE :"""

    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(
    prompt,
    request_options={"timeout": 60}
)
        answer = response.text.strip()
        print(f"[AI] Reponse Gemini OK", flush=True)
        return answer

    except Exception as e:
        error_type = type(e).__name__
        print(f"[AI] Exception {error_type}: {str(e)[:150]}", flush=True)
        print(f"[AI] Utilisation du fallback intelligent ({langue})", flush=True)
        sys.stdout.flush()
        return reponse_intelligente(question, langue, context)