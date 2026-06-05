import streamlit as st


def _deep_replace(obj, old: str, new: str):
    if isinstance(obj, str):
        return obj.replace(old, new)
    if isinstance(obj, dict):
        return {k: _deep_replace(v, old, new) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_replace(v, old, new) for v in obj]
    return obj


def _apply_gender(result, gender: str):
    """Remplace les pronoms/accords féminins par les formes masculines si gender == 'm'."""
    if gender != "m":
        return result
    # Pronom sujet en début de phrase ou après ponctuation/tiret
    for before in (". ", "— ", '" ', "\n"):
        result = _deep_replace(result, f"{before}Elle ", f"{before}Il ")
    # Majuscule en tout début de chaîne ou après guillemet ouvrant
    result = _deep_replace(result, '"Elle ', '"Il ')
    # Pronom disjoint après prépositions (pour elle → pour lui, etc.)
    for prep in ("pour", "chez", "derrière", "avec", "sur", "sans", "par", "d'", "de"):
        result = _deep_replace(result, f"{prep} elle", f"{prep} lui")
    # "qu'elle " → "qu'il "
    result = _deep_replace(result, "qu'elle ", "qu'il ")
    # Pronom sujet minuscule au milieu après virgule ou point-virgule
    result = _deep_replace(result, ", elle ", ", il ")
    result = _deep_replace(result, "; elle ", "; il ")
    # Accords adjectivaux — phrases complètes d'abord pour éviter les articles orphelins
    result = _deep_replace(result, "une nouvelle employée", "un nouvel employé")
    result = _deep_replace(result, "Mais elle ", "Mais il ")
    result = _deep_replace(result, "puis elle ", "puis il ")
    result = _deep_replace(result, "lequel elle ", "lequel il ")
    # Adjectifs attributs ou appositions liés au personnage
    result = _deep_replace(result, "est prête à", "est prêt à")
    result = _deep_replace(result, ", prête à", ", prêt à")
    result = _deep_replace(result, "est pressée de", "est pressé de")
    result = _deep_replace(result, ", rassurée ", ", rassuré ")
    result = _deep_replace(result, ", épuisée ", ", épuisé ")
    result = _deep_replace(result, "arrive épuisée", "arrive épuisé")
    result = _deep_replace(result, "immédiatement interrompue", "immédiatement interrompu")
    result = _deep_replace(result, "sera tenue co-responsable", "sera tenu co-responsable")
    # Formule de politesse
    result = _deep_replace(result, "Chère ", "Cher ")
    return result


_GENDER_V = 3  # incrémenter pour invalider le cache après correctif d'accords

@st.cache_data(show_spinner=False)
def _resolve_cached(scene_index: int, company: str, player: str,
                    gender: str = "f", _v: int = _GENDER_V) -> dict:
    """Calcul une seule fois par (scène, entreprise, joueur, genre) — résultat mis en cache."""
    scenario = SCENARIOS[scene_index]
    result = scenario
    if company != "NovaCorp":
        result = _deep_replace(result, "NovaCorp", company)
        result = _deep_replace(result, "novacorp", company.lower())
    if player != "Alice":
        first_name  = player.split()[0]
        first_lower = first_name.lower()
        result = _deep_replace(result, "Alice", first_name)
        result = _deep_replace(result, "alice", first_lower)
    result = _apply_gender(result, gender)
    return result


def resolve_scenario(scenario: dict) -> dict:
    """Wrapper qui lit session_state et délègue au cache."""
    company = (st.session_state.get("company_name") or "NovaCorp").strip() or "NovaCorp"
    player  = (st.session_state.get("display_name") or "Alice").strip() or "Alice"
    gender  = st.session_state.get("gender", "f")

    # Retrouve l'index pour la clé de cache
    scene_index = next(
        (i for i, s in enumerate(SCENARIOS) if s is scenario),
        None,
    )
    if scene_index is None:
        return scenario
    return _resolve_cached(scene_index, company, player, gender)


SCENARIOS = [
    # ══════════════════════════════════════════════════════════════
    # FACILE — Jours 1, 3, 5, 7, 9, 11
    # ══════════════════════════════════════════════════════════════
    {
        "id": "scene_1",
        "day": 1,
        "title": "Premier email d'activation",
        "category": "phishing",
        "difficulty": "Facile",
        "subtitle": "Jour 1 — Premier email d'activation chez NovaCorp",
        "learn_more_url": "https://www.cybermalveillance.gouv.fr/tous-nos-contenus/actualites/comment-reconnaitre-un-mail-de-phishing-ou-dhameconnage",
        "learn_more_title": "Cybermalveillance.gouv.fr — Comment reconnaître un email de phishing ?",
        "hero": {
            "emoji": "📧",
            "css_class": "hero-phishing",
            "label": "PHISHING",
            "svg": "phishing",
        },
        "scene_card": {
            "title": "🏢 Bienvenue chez NovaCorp",
            "body": (
                "Tu incarnes Alice, une nouvelle employée qui commence sa première journée. "
                "Elle découvre les outils internes, les procédures et ses premiers accès."
            ),
        },
        "dialogues": [
            {
                "avatar": "👨‍💻",
                "speaker": "Bob",
                "text": (
                    "Salut Alice, bienvenue chez NovaCorp ! Le support IT va sûrement "
                    "t'envoyer un email pour activer ton compte. Fais-le rapidement, "
                    "sinon tu risques de ne pas pouvoir accéder aux outils."
                ),
            },
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": "Quelques minutes plus tard, Alice reçoit un email marqué comme urgent.",
            },
        ],
        "artifact": {
            "type": "email",
            "sender": "support-it@novacorp-login.com",
            "recipient": "alice@novacorp.local",
            "subject": "Activation urgente de votre compte",
            "body": (
                "Bonjour Alice,<br><br>"
                "Votre compte NovaCorp sera désactivé dans <strong>30 minutes</strong> "
                "si vous ne confirmez pas vos informations.<br><br>"
                "Cliquez ici pour activer votre accès :<br>"
                "<strong>https://novacorp-login.com/activate</strong><br><br>"
                "Cordialement,<br>Support IT"
            ),
        },
        "indices": [
            "🔴 Le domaine expéditeur est <strong>novacorp-login.com</strong>, pas <strong>novacorp.com</strong>",
            "🔴 L'urgence artificielle ('30 minutes') est une technique de manipulation classique",
            "🔴 L'URL du lien pointe vers un domaine différent de l'entreprise",
            "🟡 Le vrai support IT envoie les liens depuis le domaine officiel de l'entreprise",
        ],
        "choices": [
            {
                "label": "Cliquer sur le lien",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "Tu as cliqué sur un lien de phishing.",
                "consequence_title": "Compte compromis",
                "consequence_story": (
                    "Le lien ouvre un faux portail NovaCorp. Alice saisit ses identifiants. "
                    "Quelques minutes plus tard, Eve utilise ces identifiants pour tenter "
                    "une connexion au VPN de l'entreprise. Une alerte est déclenchée : "
                    "le compte d'Alice est considéré comme compromis."
                ),
                "lesson": (
                    "Ne clique jamais sur un lien d'activation reçu par email sans vérifier le domaine. "
                    "En cas de doute, accède au service via l'adresse officielle ou contacte l'IT."
                ),
            },
            {
                "label": "Vérifier le domaine et contacter l'IT",
                "score_delta": 7,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Tu as identifié un domaine suspect.",
                "consequence_title": "Menace évitée",
                "consequence_story": (
                    "Alice remarque que le domaine novacorp-login.com ne correspond pas au domaine officiel. "
                    "Elle contacte Charlie du support IT via l'annuaire interne. Charlie confirme qu'il s'agit "
                    "d'une tentative de phishing et bloque le domaine dans la passerelle de messagerie."
                ),
                "lesson": (
                    "Les attaquants utilisent souvent des domaines ressemblants. "
                    "Il faut vérifier l'expéditeur, le lien, le ton du message et l'urgence imposée."
                ),
            },
            {
                "label": "Répondre avec ses identifiants",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "Tu as transmis des informations sensibles par email.",
                "consequence_title": "Identifiants exposés",
                "consequence_story": (
                    "Alice répond à l'email avec son identifiant. L'attaquant confirme que la boîte mail est active "
                    "et tente ensuite d'obtenir le mot de passe via un second message. "
                    "Le risque de compromission augmente fortement."
                ),
                "lesson": (
                    "Aucun support IT légitime ne doit demander un mot de passe ou des informations sensibles par email. "
                    "Les identifiants doivent rester strictement personnels."
                ),
            },
            {
                "label": "Transférer l'email à tous les collègues pour les prévenir",
                "score_delta": 4,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Bonne intention, mais tu viens de propager le lien de phishing.",
                "consequence_title": "Alerte mal gérée",
                "consequence_story": (
                    "Alice transfère l'email à toute l'équipe avec le message 'Attention, arnaque !'. "
                    "Deux collègues cliquent sur le lien par curiosité sans lire le contexte. "
                    "L'IT doit analyser plusieurs postes au lieu d'un seul."
                ),
                "lesson": (
                    "Prévenir ses collègues est une bonne intention, mais transférer un email suspect propage la menace. "
                    "Le bon réflexe : signaler à l'IT d'abord. C'est l'IT qui décide comment alerter l'équipe."
                ),
            },
        ],
    },
    {
        "id": "scene_2",
        "day": 2,
        "title": "La clé USB mystérieuse",
        "category": "physical_security",
        "difficulty": "Facile",
        "subtitle": "Jour 2 — Une clé USB dans le parking",
        "learn_more_url": "https://odyssix.fr/blog/cybersecurite/cles-usb-peripheriques-vecteurs-attaque-physiques-2/",
        "learn_more_title": "Odyssix — Clés USB : vecteurs d'attaques physiques, comment s'en protéger",
        "hero": {
            "emoji": "💾",
            "css_class": "hero-physical",
            "label": "SÉCURITÉ PHYSIQUE",
            "svg": "physical",
        },
        "scene_card": {
            "title": "🅿️ Parking de NovaCorp — 8h15",
            "body": (
                "En arrivant au bureau, Alice remarque une clé USB sur le sol du parking. "
                "Une étiquette collée dessus indique : « Salaires Q4 - NovaCorp - CONFIDENTIEL »."
            ),
        },
        "dialogues": [
            {
                "avatar": "👨‍💻",
                "speaker": "Bob",
                "text": "Oh, quelqu'un a dû la perdre. Curieux qu'elle soit là dans le parking...",
            },
            {
                "avatar": "👩‍💼",
                "speaker": "Alice",
                "text": "Elle semble appartenir à NovaCorp. Qu'est-ce que je fais avec ça ?",
            },
        ],
        "artifact": {
            "type": "file",
            "icon": "💾",
            "label": "Clé USB trouvée — Parking NovaCorp",
            "filename": "Salaires_Q4_NovaCorp.xlsx",
            "detail": "Étiquette manuscrite : « CONFIDENTIEL — Salaires Q4 »",
        },
        "indices": [
            "🔴 Une clé abandonnée dans un parking est souvent placée <strong>intentionnellement</strong> (technique du Baiting)",
            "🔴 L'étiquette 'CONFIDENTIEL' est conçue pour piquer la curiosité et inciter à brancher la clé",
            "🔴 Windows peut <strong>exécuter automatiquement</strong> du code au branchement (AutoRun)",
            "🟡 La procédure correcte est de remettre tout support inconnu au service IT sans le connecter",
        ],
        "choices": [
            {
                "label": "La brancher sur mon PC pro pour identifier le propriétaire",
                "score_delta": 0,
                "risk_delta": 4,
                "outcome": "danger",
                "feedback": "Brancher une clé inconnue, c'est risqué.",
                "consequence_title": "Malware installé",
                "consequence_story": (
                    "La clé contenait un script malveillant qui s'est exécuté automatiquement. "
                    "En quelques secondes, un keylogger s'est installé en arrière-plan. "
                    "L'attaquant intercepte désormais tout ce qu'Alice tape sur son clavier."
                ),
                "lesson": (
                    "Les clés USB abandonnées sont une technique classique : le Baiting. "
                    "Ne jamais brancher un support externe inconnu sur un poste de travail, même pour 'juste vérifier'."
                ),
            },
            {
                "label": "La remettre au service sécurité IT sans la brancher",
                "score_delta": 5,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "La bonne réaction face à un support inconnu.",
                "consequence_title": "Menace neutralisée",
                "consequence_story": (
                    "Alice remet la clé à Charlie, le responsable sécurité. "
                    "Analysée en environnement isolé (sandbox), la clé contient effectivement un script malveillant. "
                    "Charlie alerte l'équipe et envoie une note de sensibilisation à tous les employés."
                ),
                "lesson": (
                    "Face à un objet suspect, la règle est simple : ne pas l'utiliser et le remettre au service compétent. "
                    "L'équipe sécurité dispose d'outils pour analyser ces supports sans risque."
                ),
            },
            {
                "label": "La brancher sur mon PC personnel chez moi ce soir",
                "score_delta": 0,
                "risk_delta": 4,
                "outcome": "danger",
                "feedback": "Ton PC perso n'est pas protégé non plus.",
                "consequence_title": "Réseau personnel compromis",
                "consequence_story": (
                    "Le malware infecte le PC personnel d'Alice et, via le réseau WiFi domestique, "
                    "se propage sur les autres appareils connectés. Les identifiants de ses comptes personnels "
                    "sont exfiltrés vers un serveur distant."
                ),
                "lesson": (
                    "Un malware ne fait pas la différence entre un PC pro et perso. "
                    "Brancher une clé inconnue est dangereux partout — le domicile n'est pas un endroit sûr pour l'analyser."
                ),
            },
            {
                "label": "La déposer à l'accueil de l'immeuble",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Tu évites le danger immédiat mais tu transfères le risque.",
                "consequence_title": "Risque déplacé",
                "consequence_story": (
                    "La réceptionniste, voulant aider, branche la clé sur son PC pour identifier le propriétaire. "
                    "Le malware s'exécute automatiquement et infecte un poste connecté au cœur du réseau de NovaCorp. "
                    "Alice aurait dû remettre la clé directement au service IT."
                ),
                "lesson": (
                    "Remettre un support suspect à une personne non formée transfère le risque sans l'éliminer. "
                    "Seul le service IT dispose d'un environnement isolé (sandbox) pour analyser ce type d'objet."
                ),
            },
        ],
    },
    {
        "id": "scene_3",
        "day": 3,
        "title": "Le mot de passe faible",
        "category": "password",
        "difficulty": "Facile",
        "subtitle": "Jour 3 — Création du mot de passe CRM",
        "learn_more_url": "https://www.it-connect.fr/politique-de-mot-de-passe-comment-appliquer-les-bonnes-pratiques-de-lanssi/",
        "learn_more_title": "IT-Connect — Politique de mot de passe : les bonnes pratiques de l'ANSSI",
        "hero": {
            "emoji": "🔑",
            "css_class": "hero-password",
            "label": "GESTION DES MOTS DE PASSE",
            "svg": "password",
        },
        "scene_card": {
            "title": "🖥️ Accès au nouveau CRM — 09h00",
            "body": (
                "L'équipe IT vient de déployer le nouveau CRM de NovaCorp. "
                "Alice doit créer son mot de passe pour accéder au système "
                "qui contient les données de 12 000 clients."
            ),
        },
        "dialogues": [
            {
                "avatar": "👨‍💻",
                "speaker": "Bob",
                "text": (
                    "Attention Alice, le CRM contient toutes nos données clients. "
                    "Le RSSI exige au minimum 12 caractères avec majuscules, chiffres et symboles."
                ),
            },
            {
                "avatar": "👩‍💼",
                "speaker": "Alice",
                "text": "Facile, j'utilise toujours 'NovaCorp2024!' pour ce genre de compte, ça respecte les règles.",
            },
        ],
        "artifact": {
            "type": "form",
            "title": "🔐 Création de votre mot de passe CRM",
            "field_label": "Nouveau mot de passe",
            "field_value": "NovaCorp2024!",
            "hint": "⚠️ Contient le nom de l'entreprise et l'année en cours — facilement devinable.",
        },
        "indices": [
            "🔴 <strong>NovaCorp2024!</strong> contient le nom de l'entreprise : premier mot essayé par les attaquants",
            "🔴 Les mots de passe basés sur l'année en cours sont <strong>changés chaque année</strong> et donc prévisibles",
            "🔴 Utiliser le même mot de passe partout : si un compte est compromis, <strong>tous le sont</strong>",
            "🟡 Un gestionnaire de mots de passe génère et retient des mots de passe <strong>uniques et aléatoires</strong>",
        ],
        "choices": [
            {
                "label": "Utiliser 'NovaCorp2024!'",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "Ce mot de passe est trop prévisible pour un accès critique.",
                "consequence_title": "Compte CRM compromis",
                "consequence_story": (
                    "Trois mois plus tard, un attaquant teste des combinaisons courantes : "
                    "'NovaCorp2024!' est dans sa liste des 500 premiers essais. "
                    "Il accède aux données de 12 000 clients. NovaCorp reçoit une mise en demeure RGPD."
                ),
                "lesson": (
                    "Un mot de passe prévisible est aussi mauvais qu'aucun mot de passe. "
                    "Éviter tout lien avec l'entreprise, la date, ou des mots du dictionnaire."
                ),
            },
            {
                "label": "Utiliser un gestionnaire de mots de passe",
                "score_delta": 7,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "La meilleure pratique pour des mots de passe forts et uniques.",
                "consequence_title": "Accès sécurisé",
                "consequence_story": (
                    "Alice utilise Bitwarden (approuvé par NovaCorp) pour générer "
                    "'K#9mPvL2@xQr$7nW' — un mot de passe de 16 caractères aléatoires. "
                    "Elle n'a pas besoin de le mémoriser, le gestionnaire le fait pour elle."
                ),
                "lesson": (
                    "Un gestionnaire de mots de passe est la solution la plus sûre et la plus pratique. "
                    "Il génère des mots de passe uniques et forts pour chaque compte, sans effort de mémorisation."
                ),
            },
            {
                "label": "Utiliser 'P@$$w0rd_alice.martin2'",
                "score_delta": 4,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Les substitutions de lettres (@ pour a) sont connues des attaquants.",
                "consequence_title": "Mot de passe trop prévisible",
                "consequence_story": (
                    "Le mot de passe contient le prénom et le nom d'Alice, visibles sur LinkedIn. "
                    "Les outils de brute force modernes testent automatiquement toutes les "
                    "substitutions connues (@ → a, 0 → o, $ → s). Il est cassé en 4 heures."
                ),
                "lesson": (
                    "Les substitutions de caractères (leet speak) donnent une fausse impression de sécurité. "
                    "Les outils d'attaque les connaissent toutes. Privilégier la longueur et l'aléatoire."
                ),
            },
            {
                "label": "Réutiliser mon mot de passe habituel — il est déjà fort",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "Un bon mot de passe réutilisé partout reste une bombe à retardement.",
                "consequence_title": "Credential stuffing réussi",
                "consequence_story": (
                    "Trois mois plus tard, un site partenaire est victime d'une fuite. "
                    "Le mot de passe d'Alice est revendu sur le dark web. "
                    "L'attaquant l'essaie sur le CRM NovaCorp — et accède aux données de 12 000 clients. "
                    "Un seul mot de passe réutilisé a compromis toute l'entreprise."
                ),
                "lesson": (
                    "La réutilisation de mots de passe, même forts, est la première cause de compromission en chaîne. "
                    "Les attaquants utilisent le 'credential stuffing' : tester des identifiants volés ailleurs. "
                    "Un gestionnaire génère un mot de passe unique par service — c'est la seule vraie protection."
                ),
            },
        ],
    },
    {
        "id": "scene_4",
        "day": 4,
        "title": "Le bureau en désordre",
        "category": "clean_desk",
        "difficulty": "Facile",
        "subtitle": "Jour 4 — 18h, Alice s'apprête à quitter le bureau",
        "learn_more_url": "https://anny.co/fr/blog/clean-desk-policy-order-and-safety-in-the-modern-workplace",
        "learn_more_title": "Anny — Clean Desk Policy : ordre et sécurité dans le lieu de travail moderne",
        "hero": {
            "emoji": "🗂️",
            "css_class": "hero-clean-desk",
            "label": "CLEAN DESK POLICY",
            "svg": "physical",
        },
        "scene_card": {
            "title": "🏢 Bureau d'Alice — 18h05",
            "body": (
                "Alice est pressée de partir pour attraper son train. "
                "En se levant, elle réalise que son bureau est dans un état inhabituel : "
                "son badge d'accès, un post-it avec un mot de passe et un dossier client confidentiel "
                "sont visibles sur son bureau ouvert."
            ),
        },
        "dialogues": [
            {
                "avatar": "👩‍💼",
                "speaker": "Alice",
                "text": "Mon train est dans 12 minutes... Je range ça rapidement ou je fonce ?",
            },
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "L'open space de NovaCorp reçoit chaque soir des agents de nettoyage externes "
                    "et parfois des visiteurs en visite tardive. La politique Clean Desk est obligatoire."
                ),
            },
        ],
        "artifact": {
            "type": "file",
            "icon": "🗂️",
            "label": "Bureau non sécurisé",
            "filename": "Badge · Post-it mot de passe · Dossier CONFIDENTIEL ouvert",
            "detail": "Politique Clean Desk NovaCorp : bureau vide obligatoire en dehors des heures de travail",
        },
        "indices": [
            "🔴 Un badge laissé sur un bureau peut être <strong>utilisé ou cloné</strong> par un intrus",
            "🔴 Un mot de passe écrit sur un post-it est visible par <strong>toute personne passant dans l'open space</strong>",
            "🔴 Les agents de nettoyage externes <strong>ne sont pas soumis aux mêmes accords de confidentialité</strong>",
            "🟡 La politique Clean Desk de NovaCorp impose un bureau vide et un PC verrouillé en dehors des heures de travail",
        ],
        "choices": [
            {
                "label": "Partir en laissant le bureau tel quel — personne ne regardera",
                "score_delta": 0,
                "risk_delta": 3,
                "outcome": "danger",
                "feedback": "Le bureau non sécurisé représente une violation de la politique interne.",
                "consequence_title": "Violation de la Clean Desk Policy",
                "consequence_story": (
                    "Un agent de nettoyage photographie par curiosité le post-it avec le mot de passe. "
                    "Le lendemain, un accès suspect depuis une adresse IP inconnue est détecté "
                    "sur le compte d'Alice à 2h du matin. "
                    "L'enquête interne révèle la violation de la politique Clean Desk."
                ),
                "lesson": (
                    "La Clean Desk Policy protège contre les menaces internes et externes. "
                    "Un badge, un mot de passe visible ou un document confidentiel laissé sur un bureau "
                    "sont des vecteurs d'attaque physique aussi dangereux qu'un email de phishing."
                ),
            },
            {
                "label": "Ranger le badge, jeter le post-it, fermer le dossier et verrouiller le PC",
                "score_delta": 4,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "60 secondes de rangement pour éviter une semaine d'incident — ça vaut le coup.",
                "consequence_title": "Bureau sécurisé",
                "consequence_story": (
                    "Alice prend 90 secondes pour sécuriser son poste : "
                    "badge dans son sac, post-it détruit, dossier dans le tiroir verrouillé, PC verrouillé (Win+L). "
                    "Elle manque son train mais dort tranquille. "
                    "Le responsable sécurité, lors d'une ronde, note que le bureau d'Alice est exemplaire."
                ),
                "lesson": (
                    "La politique Clean Desk prend moins de 2 minutes à appliquer. "
                    "Les mots de passe ne s'écrivent jamais sur papier — un gestionnaire de mots de passe les retient. "
                    "Verrouiller son PC (Win+L ou Cmd+Ctrl+Q) est un réflexe à systématiser."
                ),
            },
            {
                "label": "Cacher le dossier sous d'autres papiers et partir vite",
                "score_delta": 2,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Un dossier caché reste accessible — et le post-it et le badge sont toujours là.",
                "consequence_title": "Sécurité partielle",
                "consequence_story": (
                    "Alice cache le dossier mais oublie le badge et le post-it. "
                    "Un visiteur tardif remarque le post-it et prend une photo. "
                    "Le dossier caché est retrouvé intact, mais le mot de passe a été compromis."
                ),
                "lesson": (
                    "La sécurité physique est un tout. Sécuriser un élément sans les autres "
                    "ne protège pas réellement. "
                    "La règle : bureau vide, tiroirs fermés, badge en poche, PC verrouillé — tout ou rien."
                ),
            },
            {
                "label": "Appeler un collègue pour qu'il range à sa place",
                "score_delta": 2,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Tu délègues la sécurité de tes accès à quelqu'un d'autre.",
                "consequence_title": "Responsabilité transférée",
                "consequence_story": (
                    "Le collègue range le dossier mais met le badge dans le tiroir du bureau d'Alice "
                    "sans le fermer à clé. Le mot de passe reste visible. "
                    "De plus, un collègue connaît maintenant le contenu du post-it d'Alice."
                ),
                "lesson": (
                    "Le badge d'accès et les mots de passe sont des éléments strictement personnels. "
                    "Les confier à un collègue, même de confiance, crée une vulnérabilité. "
                    "La sécurité physique de son poste est une responsabilité individuelle non délégable."
                ),
            },
        ],
    },
    {
        "id": "scene_5",
        "day": 5,
        "title": "Le regard indiscret",
        "category": "physical_security",
        "difficulty": "Facile",
        "subtitle": "Jour 5 — Quelqu'un regarde ton écran dans le train",
        "learn_more_url": "https://www.manageengine.com/fr/blog/general/shoulder-surfing-risques-consequences-et-solutions-pour-se-proteger.html",
        "learn_more_title": "ManageEngine — Shoulder surfing : risques, conséquences et solutions",
        "hero": {
            "emoji": "👁️",
            "css_class": "hero-physical",
            "label": "SHOULDER SURFING",
            "svg": "physical",
        },
        "scene_card": {
            "title": "🚆 TGV Paris-Lyon — 08h40",
            "body": (
                "Alice travaille dans le TGV sur un rapport financier confidentiel. "
                "Elle remarque que le passager assis derrière elle se penche régulièrement "
                "pour lire son écran. Il tient son téléphone orienté vers l'écran d'Alice."
            ),
        },
        "dialogues": [
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Le rapport contient les marges commerciales de NovaCorp et les conditions "
                    "contractuelles d'un appel d'offres en cours. "
                    "Alice a son badge NovaCorp visible autour du cou."
                ),
            },
            {
                "avatar": "💭",
                "speaker": "Voix intérieure d'Alice",
                "text": "Est-ce qu'il prend des photos de mon écran ? Je me sens observée...",
            },
        ],
        "artifact": {
            "type": "file",
            "icon": "📊",
            "label": "Rapport financier ouvert",
            "filename": "Marges_Commerciales_Q4_NovaCorp_CONFIDENTIEL.xlsx",
            "detail": "Données financières sensibles visibles sur l'écran dans un espace public",
        },
        "indices": [
            "🔴 Un badge visible dans un lieu public identifie l'entreprise et peut cibler des espions industriels",
            "🔴 Les espaces publics (transports, cafés) sont des zones à risque pour les <strong>données visibles</strong>",
            "🔴 Photographier un écran est silencieux et indétectable en quelques secondes",
            "🟡 Un filtre de confidentialité (privacy screen) limite le champ de vision latéral à 60°",
        ],
        "choices": [
            {
                "label": "Continuer à travailler — j'en ai besoin pour la réunion",
                "score_delta": 0,
                "risk_delta": 3,
                "outcome": "danger",
                "feedback": "Tu as exposé des données confidentielles dans un lieu public.",
                "consequence_title": "Données visibles photographiées",
                "consequence_story": (
                    "Le passager a photographié discrètement plusieurs slides du rapport. "
                    "Ses photos révèlent les marges de NovaCorp sur un contrat stratégique. "
                    "Deux semaines plus tard, un concurrent dépose une offre légèrement inférieure "
                    "sur le même appel d'offres. NovaCorp perd le contrat."
                ),
                "lesson": (
                    "Le shoulder surfing (espionnage visuel) est une menace réelle en lieu public. "
                    "Dans les transports : travailler dos à la fenêtre, utiliser un filtre de confidentialité "
                    "ou ne pas ouvrir de données sensibles si ce n'est pas urgent."
                ),
            },
            {
                "label": "Fermer l'écran et travailler sur des documents non sensibles",
                "score_delta": 5,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Bonne décision — les données confidentielles restent confidentielles.",
                "consequence_title": "Données protégées",
                "consequence_story": (
                    "Alice ferme le rapport et travaille sur ses emails non sensibles. "
                    "À la réunion, elle ouvre le rapport dans la salle de conférence sécurisée. "
                    "Le passager, un consultant concurrent, n'a rien obtenu."
                ),
                "lesson": (
                    "La règle simple : les données confidentielles ne s'ouvrent pas dans les lieux publics. "
                    "Si c'est urgent, utiliser un filtre de confidentialité ET s'asseoir dos au mur. "
                    "Un café ou un train n'est jamais un espace de travail sécurisé."
                ),
            },
            {
                "label": "Réduire la luminosité de l'écran au minimum",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Ça réduit la visibilité mais ne protège pas vraiment.",
                "consequence_title": "Protection insuffisante",
                "consequence_story": (
                    "La luminosité réduite ralentit l'espion mais ne l'arrête pas. "
                    "Il se rapproche légèrement et réussit à lire les chiffres clés. "
                    "Un filtre de confidentialité ou fermer l'écran auraient été plus efficaces."
                ),
                "lesson": (
                    "Réduire la luminosité est un geste partiel. Un filtre de confidentialité "
                    "limite physiquement l'angle de vue à 60°, rendant l'écran illisible sur le côté. "
                    "C'est l'investissement à faire avant tout déplacement avec des données sensibles."
                ),
            },
            {
                "label": "Se retourner et confronter le passager directement",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "La confrontation crée une tension sans protéger les données déjà vues.",
                "consequence_title": "Incident inutile",
                "consequence_story": (
                    "La confrontation gêne les autres passagers. Le suspect nie et sort son propre laptop. "
                    "Les données qu'il a déjà vues ne peuvent plus être effacées de sa mémoire. "
                    "Alice aurait mieux fait de simplement fermer l'écran discrètement."
                ),
                "lesson": (
                    "Confronter un suspect en public n'efface pas les données déjà vues et peut créer un incident. "
                    "La bonne réaction est de fermer ou cacher les données, puis de changer de position. "
                    "Signaler ensuite à la sécurité si l'individu semble avoir photographié l'écran."
                ),
            },
        ],
    },
    {
        "id": "scene_6",
        "day": 6,
        "title": "Le convertisseur PDF en ligne",
        "category": "shadow_it",
        "difficulty": "Facile",
        "subtitle": "Jour 6 — L'outil non approuvé qui semble pratique",
        "learn_more_url": "https://lemonlearning.com/fr/blog/les-risques-du-shadow-it-pour-la-cybers%C3%A9curit%C3%A9",
        "learn_more_title": "Lemon Learning — Les risques du Shadow IT pour la cybersécurité",
        "hero": {
            "emoji": "☁️",
            "css_class": "hero-shadow-it",
            "label": "SHADOW IT",
            "svg": "wifi",
        },
        "scene_card": {
            "title": "🖥️ Bureau d'Alice — 11h00",
            "body": (
                "Alice doit convertir en urgence un contrat client confidentiel de PDF en Word "
                "pour y apporter des modifications. L'outil officiel de NovaCorp est lent et "
                "son collègue Bob lui recommande un site gratuit très pratique."
            ),
        },
        "dialogues": [
            {
                "avatar": "👨‍💻",
                "speaker": "Bob",
                "text": (
                    "Utilise smallpdf.com ou ilovepdf.com, c'est ultra rapide ! "
                    "Tout le monde l'utilise dans l'équipe, personne n'a jamais eu de problème."
                ),
            },
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Le contrat contient les conditions tarifaires confidentielles de NovaCorp "
                    "avec un client grand compte, les coordonnées du client et une clause exclusive."
                ),
            },
        ],
        "artifact": {
            "type": "file",
            "icon": "📑",
            "label": "Contrat confidentiel",
            "filename": "Contrat_GrandCompte_Airbus_2025_CONFIDENTIEL.pdf",
            "detail": "Tarifs exclusifs · Clause de confidentialité · Ne pas diffuser",
        },
        "indices": [
            "🔴 Les fichiers uploadés sur ces sites <strong>transitent et sont stockés sur des serveurs tiers</strong>",
            "🔴 Certains services gratuits <strong>analysent le contenu</strong> des fichiers pour monétiser les données",
            "🔴 Utiliser un outil non approuvé viole la <strong>politique de sécurité NovaCorp</strong> (Shadow IT)",
            "🟡 Microsoft Word intégré à Office 365 peut ouvrir et convertir les PDF directement",
        ],
        "choices": [
            {
                "label": "Utiliser le site recommandé par Bob — c'est rapide",
                "score_delta": 0,
                "risk_delta": 4,
                "outcome": "danger",
                "feedback": "Le contrat confidentiel vient d'être uploadé sur un serveur tiers non contrôlé.",
                "consequence_title": "Violation de la clause de confidentialité",
                "consequence_story": (
                    "Le site stocke le fichier 30 jours sur ses serveurs américains. "
                    "6 mois plus tard, lors d'un audit de sécurité, l'outil est identifié "
                    "dans les logs réseau de NovaCorp. "
                    "Le client Airbus est informé de la violation de la clause de confidentialité. "
                    "NovaCorp risque des pénalités contractuelles."
                ),
                "lesson": (
                    "Le Shadow IT (utiliser des outils non approuvés) expose les données de l'entreprise "
                    "à des tiers sans garanties de sécurité. "
                    "Un outil 'gratuit' se rémunère souvent sur les données. "
                    "La DSI publie une liste des outils approuvés — s'y référer avant tout usage."
                ),
            },
            {
                "label": "Ouvrir le PDF directement avec Microsoft Word",
                "score_delta": 5,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "L'outil Office 365 intégré fait le travail sans quitter l'environnement NovaCorp.",
                "consequence_title": "Conversion sécurisée",
                "consequence_story": (
                    "Alice fait un clic droit sur le PDF et l'ouvre avec Word. "
                    "La conversion est automatique en quelques secondes. "
                    "Le fichier ne quitte pas l'infrastructure NovaCorp, "
                    "la clause de confidentialité est respectée."
                ),
                "lesson": (
                    "La suite Office 365 inclut nativement la conversion PDF→Word. "
                    "Avant d'utiliser un outil externe, vérifier si la solution existe déjà "
                    "dans les outils approuvés — c'est souvent le cas."
                ),
            },
            {
                "label": "Demander à l'IT de convertir le fichier à sa place",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Sécurisé, mais le service IT n'est pas un service de conversion de fichiers.",
                "consequence_title": "Bonne intention, mauvais réflexe",
                "consequence_story": (
                    "L'IT convertit le fichier mais signale à Alice que Word peut le faire directement. "
                    "Alice réalise qu'elle a mobilisé l'équipe IT inutilement pour une tâche en 10 secondes. "
                    "La prochaine fois, elle saura utiliser Word directement."
                ),
                "lesson": (
                    "Contacter l'IT pour éviter une erreur est un bon réflexe. "
                    "Mais connaître les outils disponibles dans son environnement de travail "
                    "permet de gagner du temps tout en restant dans le périmètre sécurisé."
                ),
            },
            {
                "label": "Utiliser le site recommandé mais supprimer le fichier après",
                "score_delta": 0,
                "risk_delta": 4,
                "outcome": "danger",
                "feedback": "Supprimer côté client ne supprime pas les données côté serveur.",
                "consequence_title": "Fausse sécurité",
                "consequence_story": (
                    "Alice clique sur 'Supprimer le fichier' après conversion. "
                    "Mais le serveur du site conserve une copie 30 jours pour des raisons techniques. "
                    "De plus, certains services ne suppriment jamais réellement les données — "
                    "elles sont archivées dans des bases de données de formation IA."
                ),
                "lesson": (
                    "'Supprimer' un fichier sur un service tiers ne garantit pas sa suppression réelle. "
                    "Les copies de sauvegarde, les logs et les bases d'entraînement peuvent conserver les données. "
                    "La seule vraie protection : ne pas uploader des données sensibles sur ces services."
                ),
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════
    # MOYEN — Jours 14, 17, 20, 23, 26, 29, 32
    # ══════════════════════════════════════════════════════════════
    {
        "id": "scene_7",
        "day": 7,
        "title": "L'appel du faux support IT",
        "category": "vishing",
        "difficulty": "Moyen",
        "timer": 45,
        "subtitle": "Jour 7 — Un appel inattendu du « support IT »",
        "learn_more_url": "https://www.adista.fr/blog/cybersecurite-vishing-entreprise-arnaque-telephonique/",
        "learn_more_title": "Adista — Vishing en entreprise : comprendre et déjouer l'arnaque téléphonique",
        "hero": {
            "emoji": "📞",
            "css_class": "hero-vishing",
            "label": "VISHING",
            "svg": "vishing",
        },
        "scene_card": {
            "title": "📞 Bureau d'Alice — 14h30",
            "body": (
                "Alice travaille sur un rapport quand son téléphone de bureau sonne. "
                "La voix à l'autre bout se présente comme un technicien du support informatique interne."
            ),
        },
        "dialogues": [
            {
                "avatar": "🎭",
                "speaker": "Voix inconnue",
                "text": (
                    "Bonjour, ici Marc du support IT. On a détecté une connexion suspecte depuis votre poste. "
                    "Pour sécuriser votre compte en urgence, j'ai besoin de votre mot de passe temporairement. "
                    "C'est une procédure standard, ça prend 30 secondes."
                ),
            },
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": "Alice n'a jamais rencontré ce 'Marc'. Son numéro ne correspond à rien dans l'annuaire interne.",
            },
        ],
        "artifact": {
            "type": "phone",
            "icon": "📱",
            "caller": "Numéro entrant : +33 1 85 XX XX XX",
            "label": "Marc — Support IT",
            "detail": "Numéro non répertorié dans l'annuaire interne de NovaCorp",
        },
        "indices": [
            "🔴 Le numéro appelant <strong>n'est pas répertorié</strong> dans l'annuaire de NovaCorp",
            "🔴 Aucun technicien IT légitime ne demande un mot de passe par téléphone — <strong>jamais</strong>",
            "🔴 L'urgence et le contexte technique vague sont des signaux d'alerte classiques",
            "🟡 La bonne pratique : raccrocher et rappeler le service IT via son numéro officiel",
        ],
        "choices": [
            {
                "label": "Lui donner mon mot de passe pour l'aider",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "Aucun technicien légitime ne demande un mot de passe par téléphone.",
                "consequence_title": "Accès total compromis",
                "consequence_story": (
                    "L'attaquant utilise le mot de passe pour accéder au système de fichiers interne. "
                    "En 10 minutes, il exfiltre des dossiers clients confidentiels. "
                    "NovaCorp découvrira la fuite 3 jours plus tard lors d'un audit de sécurité."
                ),
                "lesson": (
                    "Le vishing (voice phishing) est une attaque par manipulation téléphonique. "
                    "Aucun support IT légitime ne demande jamais un mot de passe — ni par téléphone, ni par email."
                ),
            },
            {
                "label": "Raccrocher et rappeler via l'annuaire officiel",
                "score_delta": 6,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Vérifier avant d'agir — le bon réflexe.",
                "consequence_title": "Tentative de vishing déjouée",
                "consequence_story": (
                    "Alice raccroche poliment, consulte l'annuaire interne et appelle directement le service IT. "
                    "Personne ne se prénomme 'Marc' dans l'équipe. Alice signale l'incident. "
                    "La DSI lance une campagne de sensibilisation au vishing dans toute l'entreprise."
                ),
                "lesson": (
                    "Toujours raccrocher et rappeler via un numéro officiel. "
                    "Un vrai technicien comprendra. Un attaquant, lui, essaiera de t'en dissuader."
                ),
            },
            {
                "label": "Donner mon identifiant mais pas le mot de passe",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Mieux, mais ton identifiant a de la valeur pour l'attaquant.",
                "consequence_title": "Exposition partielle",
                "consequence_story": (
                    "L'attaquant connaît maintenant l'identifiant d'Alice. "
                    "Il peut utiliser cette information pour des tentatives de force brute "
                    "ou cibler Alice avec des emails de phishing encore plus crédibles."
                ),
                "lesson": (
                    "Même un identifiant seul a de la valeur. Il permet de cibler une attaque ultérieure. "
                    "Ne jamais divulguer d'information d'authentification, même partielle."
                ),
            },
            {
                "label": "Lui demander d'envoyer un email officiel pour confirmer",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "L'attaquant peut aussi falsifier un email.",
                "consequence_title": "Vishing + Phishing enchaînés",
                "consequence_story": (
                    "L'attaquant envoie immédiatement un email depuis support-it@novacorp-secure.com — "
                    "un domaine presque identique à l'officiel. Alice, rassurée par cet 'email de confirmation', "
                    "coopère et transmet son mot de passe. Elle vient de tomber dans une attaque combinée."
                ),
                "lesson": (
                    "Un email de confirmation peut être falsifié aussi facilement qu'un appel. "
                    "Le seul canal fiable pour vérifier est un numéro officiel que tu as toi-même cherché — "
                    "jamais un contact fourni par l'appelant."
                ),
            },
        ],
    },
    {
        "id": "scene_8",
        "day": 8,
        "title": "La fausse mise à jour",
        "category": "malware",
        "difficulty": "Moyen",
        "subtitle": "Jour 8 — Un popup suspect bloque l'écran d'Alice",
        "learn_more_url": "https://cybersecurite.orange.fr/la-cybersecurite/protection-des-donnees/faux-messages-de-mise-a-jour-quand-un-clic-suffit-pour-infecter-votre-ordinateur.html",
        "learn_more_title": "Orange Cybersécurité — Faux messages de mise à jour : un clic peut tout infecter",
        "hero": {
            "emoji": "☠️",
            "css_class": "hero-malware",
            "label": "MALWARE / RANSOMWARE",
            "svg": "malware",
        },
        "scene_card": {
            "title": "💻 Écran d'Alice — 10h45",
            "body": (
                "Alice travaille sur un document confidentiel quand une fenêtre surgit "
                "sur son écran en plein milieu de sa saisie. Elle demande des droits administrateur."
            ),
        },
        "dialogues": [
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Le popup s'affiche avec un design officiel et un compte à rebours. "
                    "Alice n'a rien téléchargé et n'a rien fait d'inhabituel."
                ),
            },
            {
                "avatar": "👨‍💻",
                "speaker": "Bob",
                "text": "J'en ai eu un pareil hier... J'ai cliqué sur 'Plus tard', mais il revient tout le temps.",
            },
        ],
        "artifact": {
            "type": "popup",
            "title": "⚠️ Mise à jour critique requise",
            "message": (
                "Une mise à jour de sécurité critique a été détectée pour votre système. "
                "Installez-la immédiatement pour protéger vos données.<br><br>"
                "<strong>NovaCorp Security Suite v4.2.1</strong><br>"
                "Cette mise à jour requiert des droits administrateur."
            ),
            "button_text": "Installer maintenant",
            "timer": "04:47",
        },
        "indices": [
            "🔴 Le compte à rebours est une <strong>technique de pression</strong> pour empêcher la réflexion",
            "🔴 Les mises à jour NovaCorp passent par un outil centralisé — jamais via un popup navigateur",
            "🔴 Aucune mise à jour légitime ne surgit <strong>sans action préalable</strong> de l'utilisateur",
            "🟡 Demander des droits administrateur pour une mise à jour non sollicitée est un signe fort de malware",
        ],
        "choices": [
            {
                "label": "Cliquer sur 'Installer maintenant'",
                "score_delta": 0,
                "risk_delta": 6,
                "outcome": "danger",
                "feedback": "Un ransomware vient de chiffrer tes fichiers.",
                "consequence_title": "Ransomware déclenché",
                "consequence_story": (
                    "Le fichier téléchargé était un ransomware. En quelques minutes, "
                    "tous les fichiers du poste d'Alice sont chiffrés. "
                    "Un message s'affiche : 'Vos fichiers sont chiffrés. Payez 2 BTC pour les récupérer.' "
                    "La DSI isole immédiatement le poste du réseau de l'entreprise."
                ),
                "lesson": (
                    "Les fausses mises à jour (fake updates) sont un vecteur d'infection majeur. "
                    "Les mises à jour légitimes ne surgissent pas avec un compte à rebours. "
                    "Ne jamais accorder de droits admin à une application non sollicitée."
                ),
            },
            {
                "label": "Fermer le popup et appeler l'IT",
                "score_delta": 7,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Signaler avant d'agir — la bonne démarche.",
                "consequence_title": "Malware bloqué",
                "consequence_story": (
                    "Alice ferme le popup, prend une capture d'écran et contacte Charlie. "
                    "L'équipe IT identifie un script malveillant injecté via une publicité sur un site externe. "
                    "Le poste est analysé et nettoyé sans perte de données."
                ),
                "lesson": (
                    "Signaler un comportement suspect à l'IT est toujours la bonne démarche. "
                    "Les mises à jour d'entreprise se font via des outils centralisés, jamais via des popups navigateur."
                ),
            },
            {
                "label": "Cliquer sur 'Plus tard' pour l'ignorer",
                "score_delta": 4,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Ajourner ne résout pas le problème.",
                "consequence_title": "Menace en suspens",
                "consequence_story": (
                    "Le popup continue à apparaître toutes les heures. Bob finit par cliquer sur 'Installer' "
                    "sur son propre poste, ce qui déclenche l'infection sur son PC. "
                    "Alice aurait pu éviter cela en signalant le problème dès le début."
                ),
                "lesson": (
                    "Ignorer un popup suspect ne le fait pas disparaître. "
                    "Signaler immédiatement permet à l'IT d'agir avant que d'autres collègues ne soient touchés."
                ),
            },
            {
                "label": "Prendre une capture d'écran et l'archiver sans rien signaler",
                "score_delta": 4,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Documenter c'est bien, mais signaler c'est indispensable.",
                "consequence_title": "Information non exploitée",
                "consequence_story": (
                    "Alice prend une capture soignée mais la garde dans un dossier personnel. "
                    "Le popup réapparaît chaque jour. Une semaine plus tard, un collègue clique dessus. "
                    "La capture aurait été précieuse pour l'IT — si Alice la lui avait transmise immédiatement."
                ),
                "lesson": (
                    "Documenter sans signaler n'est qu'une demi-mesure. "
                    "La capture d'écran est utile, mais sa valeur est nulle si elle ne parvient pas à l'IT "
                    "pour qu'il puisse agir rapidement."
                ),
            },
        ],
    },
    {
        "id": "scene_9",
        "day": 9,
        "title": "Le WiFi du café",
        "category": "wifi_mitm",
        "difficulty": "Moyen",
        "subtitle": "Jour 9 — En déplacement dans un café",
        "learn_more_url": "https://www.assurances-casterot.fr/man-in-the-middle/",
        "learn_more_title": "Casterot — Man in the Middle : les dangers du WiFi public expliqués",
        "hero": {
            "emoji": "📶",
            "css_class": "hero-wifi",
            "label": "WiFi PUBLIC / MITM",
            "svg": "wifi",
        },
        "scene_card": {
            "title": "☕ Café Le Central — 11h20",
            "body": (
                "Alice est en déplacement professionnel. En attendant sa réunion, "
                "elle s'installe dans un café et sort son laptop pour avancer sur un dossier confidentiel. "
                "Son téléphone est en mode avion pour économiser la batterie."
            ),
        },
        "dialogues": [
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Le café propose un réseau WiFi gratuit. La charte sécurité NovaCorp impose "
                    "l'utilisation du VPN sur tout réseau non-entreprise."
                ),
            },
            {
                "avatar": "👩‍💼",
                "speaker": "Alice",
                "text": (
                    "J'ai une heure à tuer avant la réunion... Je dois finir ce compte-rendu client. "
                    "Le WiFi du café a l'air rapide."
                ),
            },
        ],
        "artifact": {
            "type": "wifi",
            "icon": "📶",
            "ssid": "Free_Cafe_WiFi",
            "detail": "Réseau ouvert — Sans mot de passe — 31 appareils connectés",
            "security": "🔓 Aucun chiffrement — Trafic visible par tous",
        },
        "indices": [
            "🔴 Un réseau WiFi public <strong>sans mot de passe</strong> est lisible par n'importe qui sur le même réseau",
            "🔴 Un attaquant peut créer un faux réseau avec le même nom (Evil Twin) pour capturer le trafic",
            "🔴 Même HTTPS ne protège pas contre certaines attaques MITM sur réseau ouvert",
            "🟡 La charte NovaCorp exige le <strong>VPN</strong> sur tout réseau non-entreprise",
        ],
        "choices": [
            {
                "label": "Se connecter et travailler directement",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "Tu as exposé des données confidentielles sur un réseau public.",
                "consequence_title": "Données interceptées",
                "consequence_story": (
                    "Un attaquant sur le même réseau utilise un outil de capture de trafic. "
                    "Il intercepte les identifiants de session d'Alice et les cookies de sa session. "
                    "Le dossier client sur lequel elle travaillait est accessible depuis son appareil."
                ),
                "lesson": (
                    "Un réseau WiFi public est équivalent à parler fort dans un café. "
                    "N'importe qui peut écouter le trafic non chiffré ou intercepter des sessions."
                ),
            },
            {
                "label": "Activer le VPN NovaCorp avant de se connecter",
                "score_delta": 6,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Bonne pratique — le VPN chiffre tout le trafic.",
                "consequence_title": "Connexion sécurisée",
                "consequence_story": (
                    "Alice active le VPN NovaCorp avant de se connecter au WiFi. "
                    "Même si un attaquant capture son trafic, tout est chiffré de bout en bout. "
                    "L'attaquant ne voit que du bruit incompréhensible."
                ),
                "lesson": (
                    "Le VPN chiffre tout le trafic entre l'appareil et les serveurs de l'entreprise. "
                    "C'est la protection indispensable sur tout réseau non maîtrisé (café, hôtel, aéroport)."
                ),
            },
            {
                "label": "Désactiver le mode avion et utiliser son 4G",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "La 4G est plus sûre mais sans VPN tu contournes la charte.",
                "consequence_title": "Solution partielle",
                "consequence_story": (
                    "La connexion 4G est plus sécurisée qu'un WiFi public. "
                    "Cependant, Alice ne passe pas par le VPN et donc contourne "
                    "les filtres de sécurité de NovaCorp. Le RSSI le détecte lors d'un audit mensuel."
                ),
                "lesson": (
                    "La 4G est plus sûre qu'un WiFi public mais n'est pas équivalente au VPN d'entreprise. "
                    "Les politiques de sécurité existent pour une raison — les respecter protège tout le monde."
                ),
            },
            {
                "label": "Créer un partage de connexion avec son téléphone",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Mieux que le WiFi public, mais sans VPN tu restes hors charte.",
                "consequence_title": "Hotspot sans VPN",
                "consequence_story": (
                    "Le hotspot mobile d'Alice est bien plus sûr qu'un réseau ouvert. "
                    "Mais elle ne connecte pas le VPN et accède aux serveurs NovaCorp en dehors du tunnel chiffré. "
                    "Le RSSI détecte une connexion non sécurisée aux ressources internes lors de l'audit du mois."
                ),
                "lesson": (
                    "Le partage de connexion (hotspot) élimine le risque du WiFi public mais ne remplace pas le VPN. "
                    "La combinaison idéale en déplacement : hotspot personnel + VPN d'entreprise activé."
                ),
            },
        ],
    },
    {
        "id": "scene_10",
        "day": 10,
        "title": "Le résumé via ChatGPT",
        "category": "ai_leak",
        "difficulty": "Moyen",
        "subtitle": "Jour 10 — Un raccourci tentant avec l'IA",
        "learn_more_url": "https://www.riskinsight-wavestone.com/2025/05/fuite-de-donnees-comment-les-chatbots-dia-peuvent-faire-fuiter-vos-informations/",
        "learn_more_title": "Wavestone — Comment les chatbots d'IA peuvent faire fuiter vos données",
        "hero": {
            "emoji": "🤖",
            "css_class": "hero-ai",
            "label": "FUITE VIA IA",
            "svg": "password",
        },
        "scene_card": {
            "title": "💻 Bureau d'Alice — 16h45",
            "body": (
                "Alice doit rédiger en urgence un résumé d'un rapport stratégique confidentiel "
                "de 80 pages pour une réunion demain matin. Un collègue lui suggère d'utiliser "
                "ChatGPT pour gagner du temps."
            ),
        },
        "dialogues": [
            {
                "avatar": "👨‍💻",
                "speaker": "Bob",
                "text": (
                    "ChatGPT est incroyable pour résumer des documents longs. "
                    "Tu colles le texte, tu lui demandes un résumé en 5 points, et c'est plié en 30 secondes."
                ),
            },
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Le rapport contient les projections financières de NovaCorp pour les 3 prochaines années, "
                    "les noms des clients stratégiques et une acquisition confidentielle en cours."
                ),
            },
        ],
        "artifact": {
            "type": "file",
            "icon": "📄",
            "label": "Document confidentiel",
            "filename": "Strategie_NovaCorp_2025-2027_CONFIDENTIEL.pdf",
            "detail": "Classifié CONFIDENTIEL — Diffusion restreinte — Direction uniquement",
        },
        "indices": [
            "🔴 Les données envoyées à ChatGPT peuvent être <strong>utilisées pour entraîner les modèles</strong> selon les CGU",
            "🔴 Une fois envoyées, les données <strong>quittent le périmètre de sécurité</strong> de NovaCorp — sans retour possible",
            "🔴 Les noms de clients, chiffres financiers et acquisitions sont des <strong>données ultra-sensibles</strong>",
            "🟡 NovaCorp dispose d'un outil d'IA interne approuvé (Copilot for Microsoft 365) pour ces usages",
        ],
        "choices": [
            {
                "label": "Coller le rapport complet dans ChatGPT",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "Des données confidentielles viennent de quitter le périmètre de NovaCorp.",
                "consequence_title": "Fuite de données vers un tiers",
                "consequence_story": (
                    "Le rapport complet est transmis aux serveurs d'OpenAI. "
                    "Selon les conditions d'utilisation, ces données peuvent être utilisées pour améliorer le modèle. "
                    "Le DPO de NovaCorp est alerté 2 semaines plus tard via un audit : "
                    "une violation de données potentielle sous le RGPD doit être déclarée à la CNIL."
                ),
                "lesson": (
                    "Envoyer des données confidentielles à un service IA public, c'est les transmettre à un tiers. "
                    "Les outils IA grand public ne sont pas couverts par les accords de confidentialité de l'entreprise. "
                    "Utiliser uniquement les outils IA approuvés par la DSI."
                ),
            },
            {
                "label": "Utiliser l'outil IA interne approuvé par NovaCorp",
                "score_delta": 6,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Le bon outil pour le bon usage — les données restent dans le périmètre.",
                "consequence_title": "Résumé sécurisé",
                "consequence_story": (
                    "Alice utilise Microsoft Copilot intégré à Teams, approuvé par la DSI. "
                    "Les données ne quittent pas l'infrastructure NovaCorp. "
                    "Le résumé est prêt en 2 minutes et la conformité RGPD est préservée."
                ),
                "lesson": (
                    "Les outils IA internes (Microsoft Copilot, etc.) sont contractuellement tenus "
                    "à la confidentialité des données de l'entreprise. "
                    "La DSI valide les outils autorisés — les utiliser est la seule option sûre."
                ),
            },
            {
                "label": "Anonymiser les données sensibles avant de les coller",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Mieux, mais l'anonymisation manuelle est rarement complète.",
                "consequence_title": "Anonymisation incomplète",
                "consequence_story": (
                    "Alice remplace les noms de clients par 'Client A' et masque les chiffres. "
                    "Mais elle oublie un nom dans une note de bas de page et une date d'acquisition révélatrice. "
                    "Un concurrent pourrait croiser ces informations résiduelles pour identifier l'opération."
                ),
                "lesson": (
                    "L'anonymisation manuelle est fastidieuse et rarement exhaustive. "
                    "Elle ne dispense pas d'utiliser l'outil approuvé. "
                    "La règle : si le document est confidentiel, il ne sort pas du périmètre — même anonymisé partiellement."
                ),
            },
            {
                "label": "Résumer le document manuellement sans IA",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Sécurisé, mais tu n'as pas utilisé les ressources approuvées disponibles.",
                "consequence_title": "Travail sécurisé mais inefficace",
                "consequence_story": (
                    "Alice passe 3 heures à résumer manuellement le rapport. "
                    "Elle arrive épuisée à la réunion du lendemain. "
                    "NovaCorp dispose d'un outil IA interne approuvé qui aurait permis de faire le même travail "
                    "en 5 minutes, de façon sécurisée."
                ),
                "lesson": (
                    "La sécurité ne signifie pas se priver d'outils modernes. "
                    "Les outils IA approuvés par la DSI permettent de travailler efficacement "
                    "tout en respectant la confidentialité. Connaître et utiliser ces outils est une compétence clé."
                ),
            },
        ],
    },
    {
        "id": "scene_11",
        "day": 11,
        "title": "Le recruteur LinkedIn suspect",
        "category": "osint",
        "difficulty": "Moyen",
        "subtitle": "Jour 11 — Une demande de connexion trop belle pour être vraie",
        "learn_more_url": "https://www.journaldunet.com/cybersecurite/1547881-faux-recruteurs-investisseurs-belles-femmes-comment-linkedin-est-devenu-le-terrain-de-jeu-favori-des-cyberespions/",
        "learn_more_title": "Journal du Net — Comment LinkedIn est devenu le terrain de jeu des cyberespions",
        "hero": {
            "emoji": "🔍",
            "css_class": "hero-osint",
            "label": "OSINT / RÉSEAUX SOCIAUX",
            "svg": "phishing",
        },
        "scene_card": {
            "title": "📱 LinkedIn d'Alice — 09h30",
            "body": (
                "Alice reçoit une demande de connexion LinkedIn d'un certain 'Thomas Durand', "
                "recruteur senior chez un concurrent direct de NovaCorp. "
                "Son message est très flatteur et propose un salaire 40% supérieur."
            ),
        },
        "dialogues": [
            {
                "avatar": "👩‍💼",
                "speaker": "Alice",
                "text": "Wow, 40% d'augmentation... Son profil a l'air sérieux. Mais quelque chose me semble bizarre.",
            },
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Le profil de Thomas Durand : photo parfaite, 87 relations, créé il y a 3 mois, "
                    "pas de recommandations, entreprise non vérifiée. "
                    "Il demande à Alice de lui envoyer son CV complet et ses projets actuels chez NovaCorp."
                ),
            },
        ],
        "artifact": {
            "type": "file",
            "icon": "💼",
            "label": "Profil LinkedIn suspect",
            "filename": "Thomas_Durand — Senior Recruiter @ TechRival Corp",
            "detail": "87 relations · Membre depuis 3 mois · Photo IA détectée · Aucune recommandation",
        },
        "indices": [
            "🔴 La photo est <strong>générée par IA</strong> (visage parfait, fond lisse, pas de métadonnées)",
            "🔴 Profil créé il y a <strong>3 mois seulement</strong> avec très peu de relations et zéro recommandation",
            "🔴 Il demande des informations sur tes <strong>projets actuels confidentiels</strong> chez NovaCorp",
            "🟡 Les attaques OSINT commencent souvent par une collecte d'informations via les réseaux professionnels",
        ],
        "choices": [
            {
                "label": "Accepter et lui envoyer le CV avec mes projets actuels",
                "score_delta": 0,
                "risk_delta": 4,
                "outcome": "danger",
                "feedback": "Tu viens de livrer des informations stratégiques à un concurrent potentiel.",
                "consequence_title": "Espionnage industriel",
                "consequence_story": (
                    "Le 'recruteur' était en réalité un consultant mandaté par un concurrent. "
                    "Les projets confidentiels qu'Alice a mentionnés dans son CV personnalisé "
                    "se retrouvent dans une présentation concurrente 6 semaines plus tard. "
                    "NovaCorp perd un appel d'offres stratégique."
                ),
                "lesson": (
                    "Les attaques OSINT (Open Source Intelligence) utilisent les réseaux sociaux professionnels "
                    "pour collecter des informations stratégiques. "
                    "Ne jamais mentionner de projets confidentiels dans un contexte externe, "
                    "même à quelqu'un qui se présente comme un recruteur."
                ),
            },
            {
                "label": "Vérifier le profil et signaler à la DSI avant de répondre",
                "score_delta": 5,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Bonne vigilance — vérifier avant d'agir protège l'entreprise.",
                "consequence_title": "Tentative d'OSINT déjouée",
                "consequence_story": (
                    "Alice fait une recherche inversée de la photo (Google Images) : "
                    "le visage apparaît sur plusieurs faux profils avec des noms différents. "
                    "Elle signale le profil à la DSI et à LinkedIn. "
                    "L'équipe de sécurité identifie 3 autres collègues ciblés par la même campagne."
                ),
                "lesson": (
                    "Vérifier une photo de profil (recherche inversée), l'ancienneté du compte et les relations "
                    "permet de détecter un faux profil. "
                    "Signaler à la DSI protège toute l'entreprise — pas seulement toi."
                ),
            },
            {
                "label": "Accepter la connexion sans donner d'informations",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Tu lui donnes accès à ton réseau et tes informations publiques.",
                "consequence_title": "Exposition partielle",
                "consequence_story": (
                    "En acceptant, Alice donne accès au profil de ses 340 relations LinkedIn. "
                    "L'attaquant cartographie le réseau de NovaCorp, identifie les responsables clés "
                    "et lance des attaques ciblées sur d'autres employés."
                ),
                "lesson": (
                    "Même sans envoyer d'informations, accepter une connexion suspecte expose ton réseau. "
                    "Un attaquant peut utiliser la liste de tes relations pour cartographier l'organisation "
                    "et lancer des attaques ciblées (spear phishing)."
                ),
            },
            {
                "label": "Ignorer et bloquer le profil sans le signaler",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Tu te protèges, mais tes collègues restent exposés.",
                "consequence_title": "Protection individuelle insuffisante",
                "consequence_story": (
                    "Alice bloque le profil. Mais 4 collègues moins vigilants acceptent la connexion "
                    "et partagent des informations sur leurs projets. "
                    "En signalant à la DSI, Alice aurait pu protéger toute l'équipe."
                ),
                "lesson": (
                    "Bloquer un profil suspect te protège toi, mais pas l'entreprise. "
                    "Signaler à la DSI et à LinkedIn permet de protéger tous tes collègues "
                    "qui pourraient recevoir la même demande."
                ),
            },
        ],
    },
    {
        "id": "scene_12",
        "day": 12,
        "title": "L'inconnu à la porte",
        "category": "physical_security",
        "difficulty": "Moyen",
        "subtitle": "Jour 12 — Un inconnu veut accéder à la zone sécurisée",
        "learn_more_url": "https://www.metacompliance.com/fr/blog/cyber-security-awareness/c-est-quoi-tailgating-au-travail",
        "learn_more_title": "MetaCompliance — C'est quoi le tailgating au travail et comment s'en protéger ?",
        "hero": {
            "emoji": "🚪",
            "css_class": "hero-physical",
            "label": "TAILGATING",
            "svg": "physical",
        },
        "scene_card": {
            "title": "🏢 Entrée zone R&D — 08h50",
            "body": (
                "Alice badge pour entrer dans la zone R&D de NovaCorp, une zone à accès restreint. "
                "Au moment où la porte s'ouvre, un homme en costume se retrouve juste derrière elle, "
                "les bras chargés de cartons, et lui sourit en disant qu'il a oublié son badge."
            ),
        },
        "dialogues": [
            {
                "avatar": "🧑‍💼",
                "speaker": "L'inconnu",
                "text": (
                    "Oh merci ! J'ai oublié mon badge en bas... Je suis Marc, consultant externe. "
                    "Je viens pour la réunion avec l'équipe produit à 9h. Vous pouvez me laisser passer ?"
                ),
            },
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Alice ne reconnaît pas cet homme. La zone R&D contient des prototypes et "
                    "des données de propriété intellectuelle classifiées. Les visiteurs externes "
                    "doivent obligatoirement être accompagnés et inscrits au registre d'accueil."
                ),
            },
        ],
        "artifact": {
            "type": "chat",
            "sender": "Règlement zone R&D — NovaCorp",
            "avatar": "🔒",
            "messages": [
                "Accès restreint — Personnel accrédité uniquement.",
                "Tout visiteur externe doit être inscrit au registre d'accueil et accompagné en permanence.",
                "Le tailgating (suivre quelqu'un sans badge) est une violation de sécurité.",
                "En cas de doute, contacter la sécurité au poste 5555.",
            ],
        },
        "indices": [
            "🔴 Personne ne peut entrer dans une zone sécurisée <strong>sans badge valide</strong> — même avec des cartons",
            "🔴 Le 'tailgating' est une technique classique d'intrusion physique — l'inconnu n'est pas forcément consultant",
            "🔴 Les visiteurs externes doivent être <strong>enregistrés à l'accueil</strong> et accompagnés",
            "🟡 En cas de doute, escorter vers l'accueil est plus sûr que refuser sèchement ou laisser entrer",
        ],
        "choices": [
            {
                "label": "Tenir la porte et le laisser entrer — il a l'air légitime",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "Tu viens de laisser entrer un inconnu dans une zone sécurisée.",
                "consequence_title": "Intrusion physique réussie",
                "consequence_story": (
                    "L'inconnu n'était pas un consultant. Une fois dans la zone R&D, "
                    "il a photographié des prototypes sur les bureaux et téléchargé des fichiers "
                    "depuis un poste laissé déverrouillé. "
                    "NovaCorp découvrira l'intrusion 3 semaines plus tard lors d'un audit."
                ),
                "lesson": (
                    "Le tailgating est l'une des techniques d'intrusion physique les plus efficaces. "
                    "L'apparence professionnelle et les cartons pleins sont des classiques. "
                    "Aucune exception à la règle : pas de badge = pas d'accès, peu importe les circonstances."
                ),
            },
            {
                "label": "Lui demander poliment de badger ou d'appeler son contact",
                "score_delta": 6,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Bonne posture — appliquer la règle sans agressivité.",
                "consequence_title": "Accès refusé, protocole respecté",
                "consequence_story": (
                    "Alice explique calmement qu'elle ne peut pas laisser entrer quelqu'un sans badge. "
                    "Elle propose d'appeler la sécurité (poste 5555) pour vérifier son identité. "
                    "L'inconnu hésite, puis repart sans insister. "
                    "Le responsable sécurité confirme qu'aucun consultant n'était attendu ce jour-là."
                ),
                "lesson": (
                    "Refuser poliment mais fermement est la bonne posture. "
                    "Un visiteur légitime comprendra la procédure. "
                    "Un attaquant, lui, cherchera à contourner ou à partir rapidement."
                ),
            },
            {
                "label": "L'accompagner à l'accueil pour régulariser son accès",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Mieux que de le laisser entrer, mais tu perds de vue la zone pendant ce temps.",
                "consequence_title": "Protocole partiellement respecté",
                "consequence_story": (
                    "Alice escorte l'inconnu vers l'accueil. Pendant qu'elle s'éloigne, "
                    "la porte de la zone R&D n'est pas sécurisée et un second individu en profite pour entrer. "
                    "La procédure correcte aurait été d'appeler la sécurité sans quitter son poste."
                ),
                "lesson": (
                    "Escorter vers l'accueil est une bonne intention, mais la procédure correcte "
                    "est d'appeler la sécurité directement (poste 5555) sans quitter la zone. "
                    "Ne jamais laisser une porte sécurisée sans surveillance."
                ),
            },
            {
                "label": "Le laisser entrer car il a l'air d'un collègue qu'on n'a pas encore rencontré",
                "score_delta": 0,
                "risk_delta": 5,
                "outcome": "danger",
                "feedback": "L'apparence n'est pas une preuve d'identité.",
                "consequence_title": "Intrusion par social engineering",
                "consequence_story": (
                    "L'inconnu avait étudié les photos LinkedIn de l'équipe pour adopter le bon look. "
                    "Une fois dans la zone, il accède à plusieurs postes non verrouillés. "
                    "Des données de propriété intellectuelle sont exfiltrées via une clé USB."
                ),
                "lesson": (
                    "Les attaquants font des recherches OSINT pour adopter l'apparence et le vocabulaire "
                    "appropriés à l'environnement cible. L'apparence ne remplace jamais un badge valide. "
                    "La règle : pas de badge = pas d'accès, sans exception."
                ),
            },
        ],
    },
    {
        "id": "scene_13",
        "day": 13,
        "title": "L'imprimante oubliée",
        "category": "clean_desk",
        "difficulty": "Moyen",
        "subtitle": "Jour 13 — Un contrat confidentiel oublié dans la salle d'impression",
        "learn_more_url": "https://profficium.fr/blog/rgpd-impression/",
        "learn_more_title": "Profficium — RGPD et impression : ce que les entreprises doivent savoir",
        "hero": {
            "emoji": "🖨️",
            "css_class": "hero-clean-desk",
            "label": "SÉCURITÉ DOCUMENTAIRE",
            "svg": "physical",
        },
        "scene_card": {
            "title": "🖨️ Salle d'impression — 14h15",
            "body": (
                "Alice lance l'impression d'un contrat confidentiel depuis son bureau, "
                "puis elle est immédiatement interrompue par un appel urgent. "
                "30 minutes plus tard, elle reçoit un message de Bob : "
                "'Hé, j'ai trouvé des docs NovaCorp à ton nom sur l'imprimante commune.'"
            ),
        },
        "dialogues": [
            {
                "avatar": "👨‍💻",
                "speaker": "Bob",
                "text": (
                    "J'ai mis les feuilles de côté pour toi. Mais plusieurs personnes sont passées "
                    "par là depuis... je ne sais pas si quelqu'un a lu."
                ),
            },
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Le contrat contient les clauses financières et les données personnelles d'un client grand compte. "
                    "La salle d'impression est accessible à tout le personnel et aux prestataires externes."
                ),
            },
        ],
        "artifact": {
            "type": "file",
            "icon": "📄",
            "label": "Contrat imprimé — oublié 30 min",
            "filename": "Contrat_Client_Renault_2025_CONFIDENTIEL.pdf",
            "detail": "Clauses financières + données personnelles client — laissé sans surveillance 30 min",
        },
        "indices": [
            "🔴 Un document oublié 30 minutes sur une imprimante commune = <strong>exposition à toutes les personnes passées</strong>",
            "🔴 Les prestataires et visiteurs ont potentiellement accès à la salle d'impression",
            "🔴 L'impression contient des <strong>données personnelles client</strong> → violation potentielle RGPD",
            "🟡 L'impression sécurisée (PIN code) retient les documents jusqu'à la présence physique de l'utilisateur",
        ],
        "choices": [
            {
                "label": "Récupérer les feuilles et faire comme si rien ne s'était passé",
                "score_delta": 0,
                "risk_delta": 4,
                "outcome": "danger",
                "feedback": "Ne pas signaler une exposition de données est une faute grave.",
                "consequence_title": "Violation RGPD non déclarée",
                "consequence_story": (
                    "Deux semaines plus tard, le client apprend que ses données ont circulé. "
                    "Il demande à NovaCorp de justifier l'accès à ses informations personnelles. "
                    "Sans signalement interne, NovaCorp ne peut pas démontrer qu'elle a réagi. "
                    "Le DPO reçoit une mise en demeure de la CNIL pour non-déclaration d'incident."
                ),
                "lesson": (
                    "Toute exposition de données personnelles (même accidentelle) doit être signalée au DPO. "
                    "Le RGPD impose une notification sous 72h si l'incident présente un risque pour les personnes. "
                    "Récupérer les feuilles sans signaler ne résout pas l'incident — il le dissimule."
                ),
            },
            {
                "label": "Récupérer les feuilles, signaler au DPO et utiliser l'impression sécurisée à l'avenir",
                "score_delta": 5,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Réaction exemplaire : action immédiate + signalement + mesure corrective.",
                "consequence_title": "Incident géré correctement",
                "consequence_story": (
                    "Alice récupère les feuilles, rédige un rapport d'incident au DPO en 10 minutes. "
                    "Le DPO évalue le risque, documente l'incident et informe le client par précaution. "
                    "Alice active l'impression sécurisée (PIN) pour tous ses futurs documents sensibles. "
                    "NovaCorp démontre sa réactivité face à un incident potentiel."
                ),
                "lesson": (
                    "La bonne séquence : récupérer → signaler au DPO → activer l'impression sécurisée. "
                    "L'impression sécurisée (pull printing) retient le document sur le serveur "
                    "jusqu'à ce que l'utilisateur s'authentifie physiquement à l'imprimante avec son badge ou PIN."
                ),
            },
            {
                "label": "Demander à Bob de vérifier si quelqu'un a lu le document",
                "score_delta": 3,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Mieux que rien, mais Bob n'est pas le bon interlocuteur.",
                "consequence_title": "Signalement partiel",
                "consequence_story": (
                    "Bob n'a pas vu qui est passé, l'information est inutilisable. "
                    "Alice récupère les feuilles mais ne signale pas au DPO. "
                    "Sans documentation de l'incident, NovaCorp ne peut pas évaluer le risque RGPD "
                    "ni prouver sa bonne foi en cas de contrôle."
                ),
                "lesson": (
                    "Le bon interlocuteur pour une exposition de données est le DPO (Délégué à la Protection des Données), "
                    "pas un collègue. Le DPO évalue si l'incident doit être déclaré à la CNIL. "
                    "Ignorer l'étape de signalement expose l'entreprise à des sanctions."
                ),
            },
            {
                "label": "Annuler le travail d'impression depuis le PC pour effacer les traces",
                "score_delta": 0,
                "risk_delta": 4,
                "outcome": "danger",
                "feedback": "Le document est déjà imprimé — annuler le job ne change rien.",
                "consequence_title": "Action inefficace",
                "consequence_story": (
                    "Alice annule le job depuis son PC. Mais les feuilles sont déjà imprimées "
                    "et ont été vues par plusieurs personnes. "
                    "En ne signalant pas l'incident, elle viole son obligation RGPD "
                    "et empêche le DPO d'évaluer le risque pour le client."
                ),
                "lesson": (
                    "Annuler une impression depuis le PC n'efface pas les feuilles déjà produites. "
                    "La priorité est de récupérer physiquement le document, puis de signaler. "
                    "Pour éviter ce scénario : utiliser l'impression sécurisée pour tout document confidentiel."
                ),
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════
    # DIFFICILE — Jours 35, 38, 42
    # ══════════════════════════════════════════════════════════════
    {
        "id": "scene_14",
        "day": 14,
        "title": "Le message du faux PDG",
        "category": "ceo_fraud",
        "difficulty": "Difficile",
        "timer": 60,
        "subtitle": "Jour 14 — Un WhatsApp du « PDG »",
        "learn_more_url": "https://www.economie.gouv.fr/dgccrf/les-fiches-pratiques/se-premunir-contre-lescroquerie-aux-faux-ordres-de-virement-ou-arnaque",
        "learn_more_title": "Économie.gouv.fr — Se prémunir contre l'escroquerie aux faux ordres de virement",
        "hero": {
            "emoji": "💸",
            "css_class": "hero-ceo-fraud",
            "label": "FRAUDE AU PRÉSIDENT",
            "svg": "ceo_fraud",
        },
        "scene_card": {
            "title": "📲 Téléphone d'Alice — 17h50",
            "body": (
                "C'est vendredi soir. La plupart des collègues sont partis. "
                "Alice reçoit un message WhatsApp d'un numéro inconnu "
                "se présentant comme le PDG de NovaCorp."
            ),
        },
        "dialogues": [
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Jean Martin, le PDG, est connu pour utiliser WhatsApp ponctuellement. "
                    "Mais Alice n'a jamais eu son contact personnel — et le bureau est presque vide."
                ),
            },
            {
                "avatar": "💭",
                "speaker": "Voix intérieure d'Alice",
                "text": "C'est inhabituel... mais si c'est vraiment le PDG, je ne peux pas ignorer ça.",
            },
        ],
        "artifact": {
            "type": "chat",
            "sender": "Jean Martin — PDG NovaCorp",
            "avatar": "👔",
            "messages": [
                "Alice, j'ai besoin de toi. Je suis en déplacement à l'étranger.",
                "J'ai un virement urgent à effectuer pour finaliser un contrat stratégique : 47 500 €.",
                "Je suis en réunion, je ne peux pas appeler. Fais-le maintenant, je t'envoie les détails de compte.",
                "C'est strictement confidentiel. N'en parle à personne avant que j'aie signé le contrat.",
            ],
        },
        "indices": [
            "🔴 Le numéro WhatsApp est <strong>inconnu</strong> — le PDG ne t'a jamais contactée ainsi",
            "🔴 Trois signaux classiques : <strong>urgence + confidentialité + canal inhabituel</strong>",
            "🔴 Le PDG demande à ne pas en parler — pour t'empêcher de vérifier avec quelqu'un",
            "🟡 Toute demande de virement inhabituelle doit être vérifiée par un second canal officiel",
        ],
        "choices": [
            {
                "label": "Effectuer le virement immédiatement",
                "score_delta": 0,
                "risk_delta": 8,
                "outcome": "danger",
                "feedback": "Tu viens de tomber dans un piège de fraude au président.",
                "consequence_title": "47 500 € perdus",
                "consequence_story": (
                    "Alice effectue le virement. L'argent transite par plusieurs comptes offshore en quelques minutes. "
                    "Quand elle joint le vrai Jean Martin le lendemain matin, il n'est au courant de rien. "
                    "L'argent est irrécupérable. NovaCorp ouvre une enquête interne et un dépôt de plainte."
                ),
                "lesson": (
                    "La fraude au président (BEC - Business Email/Messaging Compromise) est l'attaque la plus coûteuse en entreprise. "
                    "Les 3 signaux d'alerte : urgence, confidentialité imposée, et canal de communication inhabituel."
                ),
            },
            {
                "label": "Appeler le PDG sur son numéro officiel pour vérifier",
                "score_delta": 10,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Vérification multi-canal — le bon réflexe.",
                "consequence_title": "Fraude déjouée",
                "consequence_story": (
                    "Alice appelle Jean Martin via le répertoire de l'entreprise. "
                    "Il ne sait rien de ce message — il est bien en déplacement mais n'a envoyé aucun WhatsApp. "
                    "L'incident est signalé à la DSI et à la direction financière. "
                    "Le numéro de l'attaquant est transmis aux autorités."
                ),
                "lesson": (
                    "Face à une demande financière urgente, toujours vérifier par un second canal officiel. "
                    "Un vrai PDG comprendra. La légitimité d'une demande se confirme — elle ne se suppose pas."
                ),
            },
            {
                "label": "Transférer la demande à la comptabilité pour qu'elle gère",
                "score_delta": 5,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Tu propagules la demande sans vérifier.",
                "consequence_title": "La fraude continue",
                "consequence_story": (
                    "L'assistante comptable, pressée par l'apparent PDG et par Alice, effectue le virement. "
                    "Alice sera tenue co-responsable de n'avoir pas signalé le caractère suspect du message "
                    "avant de le transmettre."
                ),
                "lesson": (
                    "Transmettre une demande suspecte sans la signaler, c'est transmettre aussi la responsabilité. "
                    "Le bon réflexe est de vérifier et signaler — pas de déléguer sans contrôle."
                ),
            },
            {
                "label": "Demander au PDG de confirmer la demande par email d'entreprise",
                "score_delta": 5,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Un email peut aussi être falsifié avec un domaine similaire.",
                "consequence_title": "Fausse confirmation acceptée",
                "consequence_story": (
                    "L'attaquant envoie aussitôt un email depuis jean.martin@novacorp-direction.com — "
                    "quasi identique au domaine officiel. Alice effectue le virement, convaincue. "
                    "Le vrai Jean Martin n'apprendra la fraude que le lendemain matin."
                ),
                "lesson": (
                    "Un email de confirmation ne garantit rien si on ne vérifie pas le domaine expéditeur. "
                    "Face à une demande financière urgente, seul un appel vocal via le répertoire officiel "
                    "de l'entreprise peut authentifier l'identité de l'interlocuteur."
                ),
            },
        ],
    },
    {
        "id": "scene_15",
        "day": 15,
        "title": "La saturation MFA",
        "category": "mfa_bombing",
        "difficulty": "Difficile",
        "timer": 30,
        "subtitle": "Jour 15 — Des notifications MFA arrivent sans que tu te connectes",
        "learn_more_url": "https://www.proofpoint.com/fr/threat-reference/mfa-fatigue-attack",
        "learn_more_title": "Proofpoint — Attaque par fatigue MFA : comprendre et se protéger",
        "hero": {
            "emoji": "📲",
            "css_class": "hero-vishing",
            "label": "MFA BOMBING",
            "svg": "vishing",
        },
        "scene_card": {
            "title": "📱 Téléphone d'Alice — 22h15",
            "body": (
                "Alice est chez elle, prête à dormir. Son téléphone vibre : "
                "une notification d'approbation MFA pour son compte NovaCorp. "
                "Puis une deuxième. Puis une troisième. Elle n'essaie pas de se connecter."
            ),
        },
        "dialogues": [
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "Un attaquant a obtenu le mot de passe d'Alice (probablement via une fuite de données). "
                    "Il tente de se connecter répétitivement en espérant qu'Alice, épuisée par les notifications, "
                    "finira par en accepter une — c'est le MFA bombing (ou MFA fatigue)."
                ),
            },
            {
                "avatar": "💭",
                "speaker": "Voix intérieure d'Alice",
                "text": "Encore une... c'est peut-être un bug ? Si j'en accepte une pour que ça s'arrête...",
            },
        ],
        "artifact": {
            "type": "phone",
            "icon": "📲",
            "caller": "NovaCorp Security — Approbation MFA",
            "label": "Notification × 7 en 3 minutes",
            "detail": "Demande de connexion depuis Paris, France — Appareil inconnu — 22h15",
        },
        "indices": [
            "🔴 Tu ne te connectes pas — ces notifications sont envoyées par <strong>quelqu'un d'autre</strong> avec ton mot de passe",
            "🔴 Accepter <strong>une seule notification</strong> suffit à donner un accès total à l'attaquant",
            "🔴 La répétition est intentionnelle : créer de la <strong>fatigue</strong> pour te faire craquer",
            "🟡 Signaler à l'IT + changer de mot de passe immédiatement est la seule réponse correcte",
        ],
        "choices": [
            {
                "label": "Accepter une notification pour que ça s'arrête",
                "score_delta": 0,
                "risk_delta": 7,
                "outcome": "danger",
                "feedback": "Tu viens d'ouvrir la porte à l'attaquant.",
                "consequence_title": "Compte compromis par fatigue MFA",
                "consequence_story": (
                    "L'attaquant accède immédiatement au compte NovaCorp d'Alice. "
                    "En 20 minutes, il exfiltre des emails, modifie des règles de redirection "
                    "et accède à des dossiers partagés sensibles. "
                    "L'IT découvrira la compromission le lendemain lors d'une détection d'anomalie."
                ),
                "lesson": (
                    "Le MFA bombing (fatigue MFA) mise sur l'épuisement pour faire accepter une notification. "
                    "Ne jamais approuver une demande MFA que tu n'as pas toi-même initiée. "
                    "Zéro exception — même à 3h du matin après 20 notifications."
                ),
            },
            {
                "label": "Refuser toutes les notifications, changer le mot de passe et alerter l'IT",
                "score_delta": 8,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Réaction exemplaire face à une attaque MFA.",
                "consequence_title": "Attaque bloquée",
                "consequence_story": (
                    "Alice refuse toutes les notifications et appelle immédiatement la hotline sécurité NovaCorp. "
                    "L'IT bloque le compte pendant 15 minutes, identifie l'IP de l'attaquant "
                    "et réinitialise les credentials d'Alice. "
                    "L'attaquant avait obtenu le mot de passe via une fuite sur un site partenaire."
                ),
                "lesson": (
                    "La bonne séquence : refuser toutes les notifications, changer le mot de passe "
                    "depuis un appareil connu, alerter l'IT immédiatement. "
                    "Ces trois actions ensemble coupent l'accès et donnent à l'IT les informations pour investiguer."
                ),
            },
            {
                "label": "Refuser les notifications mais ne rien signaler — ça s'arrêtera tout seul",
                "score_delta": 4,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Tu résistes, mais l'attaquant garde ton mot de passe et réessaiera.",
                "consequence_title": "Menace suspendue, pas éliminée",
                "consequence_story": (
                    "Les notifications s'arrêtent après 15 minutes. "
                    "L'attaquant réessaie 3 jours plus tard à 4h du matin. "
                    "Cette fois, Alice dort profondément et accepte une notification dans son sommeil. "
                    "Signaler à l'IT aurait permis de changer les credentials et de clore l'incident."
                ),
                "lesson": (
                    "Refuser sans signaler laisse l'attaquant avec un mot de passe valide. "
                    "Il peut réessayer indéfiniment. Signaler à l'IT permet de changer les credentials "
                    "et d'analyser comment le mot de passe a été compromis."
                ),
            },
            {
                "label": "Accepter une notification en pensant que c'est un bug système",
                "score_delta": 0,
                "risk_delta": 7,
                "outcome": "danger",
                "feedback": "Un bug système n'envoie pas de demandes MFA depuis un appareil inconnu.",
                "consequence_title": "Compromission par rationalisation",
                "consequence_story": (
                    "Alice se convainc que c'est une erreur technique. Elle accepte une notification. "
                    "L'attaquant est maintenant connecté à son compte. "
                    "Le lendemain matin, Alice reçoit un email l'informant d'une modification "
                    "de ses règles de messagerie — elle comprend alors ce qui s'est passé."
                ),
                "lesson": (
                    "Les notifications MFA non sollicitées ne sont jamais des bugs. "
                    "Elles signalent toujours que quelqu'un tente de se connecter avec tes identifiants. "
                    "L'appareil inconnu dans la notification est le signal d'alarme le plus clair."
                ),
            },
        ],
    },
    {
        "id": "scene_16",
        "day": 16,
        "title": "La fausse alerte antivirus",
        "category": "malware",
        "difficulty": "Difficile",
        "subtitle": "Jour 16 — Un email d'alerte de sécurité qui semble urgent",
        "learn_more_url": "https://www.jedha.co/formation-cybersecurite/tout-savoir-sur-le-scareware-l-arnaque-au-faux-virus",
        "learn_more_title": "Jedha — Tout savoir sur le scareware : l'arnaque au faux virus",
        "hero": {
            "emoji": "🦠",
            "css_class": "hero-malware",
            "label": "FAUX ANTIVIRUS",
            "svg": "malware",
        },
        "scene_card": {
            "title": "📧 Boîte mail d'Alice — 09h20",
            "body": (
                "Alice reçoit un email de 'NovaCorp Security' l'informant qu'une menace critique "
                "a été détectée sur son poste. L'email demande de télécharger et installer "
                "un patch de sécurité en urgence pour protéger les données de l'entreprise."
            ),
        },
        "dialogues": [
            {
                "avatar": "🎙️",
                "speaker": "Narrateur",
                "text": (
                    "L'email semble officiel avec le logo NovaCorp. "
                    "Mais Alice n'a reçu aucune notification de son antivirus habituel, "
                    "et elle n'a rien fait d'inhabituel sur son poste depuis hier."
                ),
            },
            {
                "avatar": "👨‍💻",
                "speaker": "Bob",
                "text": (
                    "Moi aussi j'ai reçu ce mail... J'allais cliquer. "
                    "Tu penses que c'est légitime ? Le logo NovaCorp est là."
                ),
            },
        ],
        "artifact": {
            "type": "email",
            "sender": "security@novacorp-protect.net",
            "recipient": "alice@novacorp.local",
            "subject": "⚠️ ALERTE CRITIQUE — Menace détectée sur votre poste",
            "body": (
                "Chère Alice,<br><br>"
                "Notre système de détection a identifié une <strong>menace critique</strong> "
                "sur votre poste de travail.<br><br>"
                "Vous devez installer le patch de sécurité d'urgence dans les "
                "<strong>2 heures</strong> pour éviter la propagation :<br>"
                "<strong>https://antivirus-patch-update.com/critical_fix.exe</strong><br><br>"
                "Ne pas agir peut entraîner la perte de vos données et "
                "compromettre le réseau NovaCorp.<br><br>"
                "NovaCorp Security Team"
            ),
        },
        "indices": [
            "🔴 L'expéditeur utilise <strong>novacorp-protect.net</strong> — pas le domaine officiel novacorp.com",
            "🔴 Le lien pointe vers <strong>antivirus-patch-update.com</strong> — serveur externe non NovaCorp",
            "🔴 Ton antivirus habituel <strong>n'a rien signalé</strong> — contradiction avec l'alerte",
            "🟡 Les mises à jour de sécurité légitimes passent par le système centralisé IT, jamais par email",
        ],
        "choices": [
            {
                "label": "Désactiver l'antivirus officiel et installer le patch proposé",
                "score_delta": 0,
                "risk_delta": 7,
                "outcome": "danger",
                "feedback": "Tu viens d'installer un malware en désactivant ta protection.",
                "consequence_title": "Poste compromis — malware installé",
                "consequence_story": (
                    "Le fichier téléchargé était un RAT (Remote Access Trojan). "
                    "L'attaquant a maintenant un accès complet et silencieux au poste d'Alice. "
                    "Il observe ses actions, capture ses frappes clavier et exfiltre les fichiers. "
                    "L'IT découvrira l'infection 2 semaines plus tard lors d'une analyse forensique."
                ),
                "lesson": (
                    "Un faux antivirus (scareware) crée une fausse urgence pour pousser l'utilisateur "
                    "à désactiver ses protections réelles. "
                    "Ne jamais désactiver un antivirus sur instruction d'un email. "
                    "Les mises à jour de sécurité légitimes ne passent jamais par ce canal."
                ),
            },
            {
                "label": "Ne pas cliquer et appeler l'IT via le numéro officiel",
                "score_delta": 8,
                "risk_delta": 0,
                "outcome": "success",
                "feedback": "Vérification par canal officiel — la bonne réaction.",
                "consequence_title": "Scareware détecté et signalé",
                "consequence_story": (
                    "Alice appelle la hotline IT (poste 4444) sans cliquer sur aucun lien. "
                    "L'équipe confirme qu'aucune alerte réelle n'a été émise. "
                    "L'email est identifié comme un scareware ciblant plusieurs employés NovaCorp. "
                    "Bob et 3 autres collègues sont prévenus avant de cliquer."
                ),
                "lesson": (
                    "Vérifier via un canal officiel indépendant (appel téléphonique à l'IT) "
                    "est la seule façon de valider une alerte de sécurité reçue par email. "
                    "Ne jamais utiliser les contacts ou liens fournis dans l'email suspect lui-même."
                ),
            },
            {
                "label": "Prévenir son manager par email mais ne pas contacter l'IT",
                "score_delta": 4,
                "risk_delta": 0,
                "outcome": "neutral",
                "feedback": "Tu signales, mais au mauvais interlocuteur.",
                "consequence_title": "Signalement inefficace",
                "consequence_story": (
                    "Alice transfère l'email à son manager qui ne sait pas quoi faire. "
                    "Il répond 'Je vais voir' et oublie de contacter l'IT. "
                    "Bob, lui, clique sur le lien une heure plus tard. "
                    "Le bon interlocuteur pour une alerte de sécurité est toujours l'IT, pas le management."
                ),
                "lesson": (
                    "Signaler une menace de sécurité est la bonne intention. "
                    "Mais le bon interlocuteur est toujours le service IT ou la hotline sécurité, "
                    "pas le manager (sauf si celui-ci relaie directement à l'IT). "
                    "Chaque minute compte quand plusieurs collègues peuvent recevoir le même email."
                ),
            },
            {
                "label": "Désactiver temporairement l'AV 'juste pour voir' ce que le patch fait",
                "score_delta": 0,
                "risk_delta": 7,
                "outcome": "danger",
                "feedback": "Désactiver son antivirus pour tester un fichier suspect — l'erreur classique.",
                "consequence_title": "Infection confirmée",
                "consequence_story": (
                    "Alice désactive l'antivirus 'quelques minutes' et lance le fichier. "
                    "Le malware s'installe en moins de 3 secondes et réactive sa persistance "
                    "avant qu'Alice ne relance l'antivirus. "
                    "L'antivirus ne détecte plus rien car le malware est déjà profondément ancré."
                ),
                "lesson": (
                    "Désactiver un antivirus pour tester un fichier suspect est l'erreur la plus courante. "
                    "Les malwares modernes s'installent en millisecondes. "
                    "Si tu veux analyser un fichier suspect, l'envoyer à l'IT pour analyse en sandbox — "
                    "jamais l'exécuter soi-même, même 'pour voir'."
                ),
            },
        ],
    },
]
