from agenda_collab import BaseDeDonnees

def initialiser_bdd():
    print("🔌 Connexion à la base de données...")
    bdd = BaseDeDonnees()
    conn = bdd.get_connection()
    
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    print("🧹 Nettoyage de l'ancienne base (DROP)...")
                    # On reprend la logique de votre fichier SQL : On efface tout pour être propre
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.HISTORIQUE CASCADE;") # V2
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.EVENEMENT CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.PARTICIPATION CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.EQUIPE CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.AGENDA CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.ROLE CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS gestion_agenda.UTILISATEUR CASCADE;")

                    print("🏗️ Création du Schéma et des Tables...")
                    
                    # 1. Configuration du schéma
                    cur.execute("CREATE SCHEMA IF NOT EXISTS gestion_agenda;")

                    # 2. Table UTILISATEUR
                    cur.execute("""
                        CREATE TABLE gestion_agenda.UTILISATEUR (
                            id_user SERIAL PRIMARY KEY,
                            nom VARCHAR(50) NOT NULL,
                            prenom VARCHAR(50) NOT NULL,
                            mot_de_passe VARCHAR(100) NOT NULL
                        );
                    """)

                    # 3. Table ROLE
                    cur.execute("""
                        CREATE TABLE gestion_agenda.ROLE (
                            id_role SERIAL PRIMARY KEY,
                            libelle VARCHAR(50) UNIQUE NOT NULL
                        );
                    """)

                    # 4. Table AGENDA
                    cur.execute("""
                        CREATE TABLE gestion_agenda.AGENDA (
                            id_agenda SERIAL PRIMARY KEY,
                            nom_agenda VARCHAR(100) NOT NULL,
                            id_createur INT NOT NULL,
                            FOREIGN KEY (id_createur) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE CASCADE
                        );
                    """)

                    # 5. Table ÉQUIPE
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
