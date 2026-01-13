from agenda_collab import BaseDeDonnees

"""Script permettant d'implémenter la nouvelle BDD de la V2"""

def initialiser_bdd():
    """
    Fonction principale d'initialisation de la base de données.
    
    Elle réalise les opérations suivantes :
    1. Connexion à PostgreSQL.
    2. Suppression propre de l'existant (DROP CASCADE) pour repartir de zéro.
    3. Création du schéma 'gestion_agenda' et des tables.
    4. Insertion des données de référence (Rôles).
    
    Cette fonction est critique et doit être exécutée une seule fois lors de l'installation.
    Attention : Elle efface toutes les données existantes !
    """
    print("🔌 Connexion à la base de données...")
    bdd = BaseDeDonnees()
    conn = bdd.get_connection()
    
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    print("🧹 Nettoyage de l'ancienne base (DROP)...")
                    # On reprend la logique de votre fichier SQL : On efface tout pour être propre
                    # L'ordre de suppression est important pour respecter les contraintes de clés étrangères
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.HISTORIQUE CASCADE;") # V2
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.EVENEMENT CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.PARTICIPATION CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.EQUIPE CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.AGENDA CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.ROLE CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.UTILISATEUR CASCADE;")

                    print("🏗️ Création du Schéma et des Tables...")
                    
                    # 1. Configuration du schéma
                    # Permet d'isoler nos tables du schéma 'public' par défaut
                    cur.execute("CREATE SCHEMA IF NOT EXISTS gestion_agenda;")

                    # 2. Table UTILISATEUR
                    # Stocke les identifiants de connexion
                    cur.execute("""
                        CREATE TABLE gestion_agenda.UTILISATEUR (
                            id_user SERIAL PRIMARY KEY,
                            nom VARCHAR(50) NOT NULL,
                            prenom VARCHAR(50) NOT NULL,
                            mot_de_passe VARCHAR(100) NOT NULL
                        );
                    """)

                    # 3. Table ROLE
                    # Définit les niveaux d'accès (Admin, Chef, Collaborateur)
                    cur.execute("""
                        CREATE TABLE gestion_agenda.ROLE (
                            id_role SERIAL PRIMARY KEY,
                            libelle VARCHAR(50) UNIQUE NOT NULL
                        );
                    """)

                    # 4. Table AGENDA
                    # Un agenda est un conteneur principal créé par un utilisateur
                    cur.execute("""
                        CREATE TABLE gestion_agenda.AGENDA (
                            id_agenda SERIAL PRIMARY KEY,
                            nom_agenda VARCHAR(100) NOT NULL,
                            id_createur INT NOT NULL,
                            FOREIGN KEY (id_createur) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE CASCADE
                        );
                    """)

                    # 5. Table ÉQUIPE
                    # Permet de regrouper des membres et des tickets sous une même couleur
                    cur.execute("""
                        CREATE TABLE gestion_agenda.EQUIPE (
                            id_equipe SERIAL PRIMARY KEY,
                            nom_equipe VARCHAR(50) NOT NULL,
                            couleur_equipe VARCHAR(7) DEFAULT '#0d6efd',
                            id_agenda INT NOT NULL,
                            FOREIGN KEY (id_agenda) REFERENCES gestion_agenda.AGENDA(id_agenda) ON DELETE CASCADE
                        );
                    """)

                    # 6. Table PARTICIPATION
                    # Table d'association centrale : Qui fait quoi dans quel agenda ?
                    cur.execute("""
                        CREATE TABLE gestion_agenda.PARTICIPATION (
                            id_user INT NOT NULL,
                            id_agenda INT NOT NULL,
                            id_role INT NOT NULL,
                            id_equipe INT,
                            PRIMARY KEY (id_user, id_agenda),
                            FOREIGN KEY (id_user) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE CASCADE,
                            FOREIGN KEY (id_agenda) REFERENCES gestion_agenda.AGENDA(id_agenda) ON DELETE CASCADE,
                            FOREIGN KEY (id_role) REFERENCES gestion_agenda.ROLE(id_role) ON DELETE RESTRICT,
                            FOREIGN KEY (id_equipe) REFERENCES gestion_agenda.EQUIPE(id_equipe) ON DELETE SET NULL
                        );
                    """)

                    # 7. Table EVENEMENT (Mise à jour pour V1.6 : Suppression équipe = Suppression event)
                    # Contient les tickets du calendrier
                    cur.execute("""
                        CREATE TABLE gestion_agenda.EVENEMENT (
                            id_event SERIAL PRIMARY KEY,
                            titre VARCHAR(100) NOT NULL,
                            description TEXT,
                            date_debut TIMESTAMP NOT NULL,
                            date_fin TIMESTAMP NOT NULL,
                            id_agenda INT NOT NULL,
                            id_equipe_concernee INT,
                            id_createur INT,
                            FOREIGN KEY (id_agenda) REFERENCES gestion_agenda.AGENDA(id_agenda) ON DELETE CASCADE,
                            FOREIGN KEY (id_equipe_concernee) REFERENCES gestion_agenda.EQUIPE(id_equipe) ON DELETE CASCADE, 
                            FOREIGN KEY (id_createur) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE SET NULL
                        );
                    """)
                    # Note : J'ai mis ON DELETE CASCADE pour l'équipe pour respecter la demande "Supprimer équipe efface tickets"

                    # 8. Table HISTORIQUE (NOUVEAUTÉ V2)
                    # Assure la traçabilité des actions sur les événements
                    cur.execute("""
                        CREATE TABLE gestion_agenda.HISTORIQUE (
                            id_hist SERIAL PRIMARY KEY,
                            id_event INTEGER NOT NULL,
                            action VARCHAR(50),
                            details TEXT,
                            date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            id_user INTEGER,
                            FOREIGN KEY (id_event) REFERENCES gestion_agenda.EVENEMENT(id_event) ON DELETE CASCADE,
                            FOREIGN KEY (id_user) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE SET NULL
                        );
                    """)

                    # Insertion des rôles
                    print("🔄 Insertion des données de base...")
                    cur.execute("INSERT INTO gestion_agenda.ROLE (libelle) VALUES ('Administrateur');")
                    cur.execute("INSERT INTO gestion_agenda.ROLE (libelle) VALUES ('Chef d''équipe');")
                    cur.execute("INSERT INTO gestion_agenda.ROLE (libelle) VALUES ('Collaborateur');")

            print("✅ Base de données V2 installée avec succès !")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation : {e}")
        finally:
            conn.close()
    else:
        print("❌ Impossible de se connecter à PostgreSQL. Vérifiez vos identifiants.")

if __name__ == "__main__":
    initialiser_bdd()
