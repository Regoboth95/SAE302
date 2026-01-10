from agenda_collab import BaseDeDonnees

bdd = BaseDeDonnees()
conn = bdd.get_connection()

if conn:
    print("--- CONTENU DE LA TABLE UTILISATEUR ---")
    cur = conn.cursor()
    # Si ça plante, essayez sans 'gestion_agenda.'
    try:
        cur.execute("SELECT id_user, nom, mot_de_passe FROM gestion_agenda.UTILISATEUR;")
    except:
        conn.rollback()
        cur.execute("SELECT id_user, nom, mot_de_passe FROM UTILISATEUR;")
        
    users = cur.fetchall()
    
    if not users:
        print("❌ La table est VIDE ! Le problème vient de l'inscription (Cause n°1).")
    else:
        for u in users:
            print(f"ID: {u[0]} | Login: '{u[1]}' | Mdp: '{u[2]}'")
            # Les guillemets '' permettent de voir s'il y a des espaces en trop !
            
    conn.close()
else:
    print("Impossible de se connecter à la base.")
