from agenda_collab import BaseDeDonnees
import random

"""
Script de test du bon fonctionnementde la BDD
Note : Ce fichier a été créé en début de phase V1 et n'est plus utile (à archiver)
"""

def test_backend():
    print("--- 1. Démarrage du test BDD ---")
    bdd = BaseDeDonnees()
    
    # TEST DE CONNEXION PURE
    conn = bdd.get_connection()
    if conn:
        print("✅ Connexion à PostgreSQL réussie !")
        conn.close()
    else:
        print("❌ ÉCHEC : Impossible de se connecter à PostgreSQL.")
        print("Vérifiez que le serveur est lancé et les identifiants corrects dans agenda_collab.py")
        return

    # TEST D'INSCRIPTION
    # On ajoute un chiffre aléatoire pour ne pas avoir l'erreur "Pseudo déjà pris" si on relance le test
    pseudo_test = f"Testeur_{random.randint(1, 1000)}"
    mdp_test = "Secret123"
    
    print(f"\n--- 2. Tentative d'inscription de '{pseudo_test}' ---")
    id_user = bdd.ajouter_utilisateur(pseudo_test, "PrenomTest", mdp_test)
    
    if id_user:
        print(f"✅ Utilisateur créé avec succès ! ID = {id_user}")
    else:
        print("❌ ÉCHEC de l'inscription.")
        return

    # TEST DE LOGIN
    print(f"\n--- 3. Vérification du Login ---")
    user_info = bdd.verifier_connexion(pseudo_test, mdp_test)
    
    if user_info and user_info[0] == id_user:
        print(f"✅ Login validé ! PostgreSQL a renvoyé : {user_info}")
    else:
        print("❌ ÉCHEC du login (Utilisateur introuvable ou mauvais mot de passe).")

    # TEST CRÉATION AGENDA
    print(f"\n--- 4. Création d'un agenda ---")
    id_agenda = bdd.creer_agenda("Mon Super Agenda", id_user)
    
    if id_agenda:
        print(f"✅ Agenda créé avec succès ! ID = {id_agenda}")
    else:
        print("❌ ÉCHEC de la création d'agenda.")

    # TEST LECTURE AGENDAS
    print(f"\n--- 5. Récupération des agendas ---")
    liste = bdd.recuperer_agendas_utilisateur(id_user)
    if len(liste) > 0:
        print(f"✅ Agendas trouvés : {liste}")
    else:
        print("⚠️ Aucun agenda trouvé (Bizarre si l'étape 4 a marché).")

if __name__ == "__main__":
    test_backend()
