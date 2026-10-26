import sys
import time
import requests

API_TED = "https://api.ted.europa.eu/v3/notices/search"


def premier_texte(valeur):
    """
    TED renvoie souvent les textes sous forme de dictionnaire par langue,
    par exemple {"fra": "Mon texte", "eng": "My text"}, parfois avec des listes.
    Cette fonction en sort un seul texte, en préférant le français.
    """
    if valeur is None:
        return None
    if isinstance(valeur, str):
        return valeur
    if isinstance(valeur, list):
        return premier_texte(valeur[0]) if valeur else None
    if isinstance(valeur, dict):
        for langue in ("fra", "FRA", "eng", "ENG"):
            if langue in valeur:
                return premier_texte(valeur[langue])
        return premier_texte(next(iter(valeur.values()), None))
    return str(valeur)


def recuperer_ao_ted(mot_cle, limite=5, tentatives=3):
    """
    Cherche les avis TED d'acheteurs français contenant le mot-clé.
    Réessaie si le réseau a un raté, et affiche la réponse de TED en cas d'erreur.
    """
    mot_cle = mot_cle.replace('"', " ")  # un guillemet casserait la requête
    corps = {
        "query": f'buyer-country=FRA AND FT~"{mot_cle}"',
        "fields": [
            "publication-number",
            "notice-title",
            "buyer-name",
            "publication-date",
            "deadline-receipt-tender-date-lot",
        ],
        "limit": limite,
        "page": 1,
        "scope": "ACTIVE",
    }
    for essai in range(1, tentatives + 1):
        try:
            r = requests.post(API_TED, json=corps, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"TED injoignable (essai {essai}/{tentatives}) : {type(e).__name__}")
            if essai < tentatives:
                time.sleep(5)
            continue

        if r.status_code != 200:
            # Erreur renvoyée par TED : on l'affiche pour comprendre (nom de champ, syntaxe...)
            print("Erreur TED :", r.status_code)
            print(r.text[:1500])
            return []

        try:
            return r.json().get("notices", [])
        except ValueError:
            print("TED a répondu, mais pas dans un format lisible :")
            print(r.text[:500])
            return []

    sys.exit("Impossible de joindre TED. Vérifie ta connexion internet puis relance le script.")


if __name__ == "__main__":
    notices = recuperer_ao_ted("informatique", limite=5)
    print(f"{len(notices)} avis TED récupérés\n")

    for n in notices:
        numero = n.get("publication-number")
        print("-" * 50)
        print("Objet    :", premier_texte(n.get("notice-title")))
        print("Acheteur :", premier_texte(n.get("buyer-name")))
        print("Date     :", premier_texte(n.get("publication-date")))
        print("Limite   :", premier_texte(n.get("deadline-receipt-tender-date-lot")))
        print("Lien     : https://ted.europa.eu/fr/notice/-/detail/" + str(numero))
