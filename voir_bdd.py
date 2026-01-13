from agenda_collab import BaseDeDonnees

"""
Script utilitaire de vérification de la base de données.
Permet de lister le contenu brut de la table UTILISATEUR pour le débogage.

NOTE : Ce fichier a été créé lors de la V1 et n'est plus essentiel pour l'application finale (à archiver).
"""

bdd = BaseDeDonnees()
conn = bdd.get_connection()

if conn:
    print("--- CONTENU DE LA TABLE UTILISATEUR ---")
    cur = conn.cursor()
    
    # Gestion de la compatibilité des schémas (V1 vs V2)
    # On essaie d'abord avec le schéma explicite 'gestion_agenda'
    try:
        cur.execute("SELECT id_user, nom, mot_de_passe FROM gestion_agenda.UTILISATEUR;")
    except:
        # En cas d'erreur (si le schéma n'existe pas ou ancienne version), on annule la transaction
        conn.rollback()
        # Et on réessaie sur le schéma par défaut (public)
        cur.execute("SELECT id_user, nom, mot_de_passe FROM UTILISATEUR;")
        
    users = cur.fetchall()
    
    if not users:
        print("❌ La table est VIDE ! Le problème vient de l'inscription (Cause n°1).")
    else:
        # Affichage formaté pour détecter les erreurs d'espaces invisibles
        for u in users:
            print(f"ID: {u[0]} | Login: '{u[1]}' | Mdp: '{u[2]}'")
            # Note : Les guillemets '' autour des variables permettent de voir s'il y a des espaces en trop !
            
    conn.close()
else:
    print("Impossible de se connecter à la base.")
