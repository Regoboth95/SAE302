import psycopg2
from psycopg2 import OperationalError

class BaseDeDonnees:
    def __init__(self):
        # Paramètres de connexion définis dans le cours [cite: 536, 540]
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "dbname": "agenda_collaboratif",
            "user": "app_agenda_user",   # Le rôle qu'on a créé en SQL
            "password": "Azerty@123"
        }

    def get_connection(self):
        """Établit la connexion à PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except OperationalError as e:
            print(f"Erreur de connexion : {e}")
            return None

    def ajouter_utilisateur(self, nom, prenom, mdp):
        """ Inscription avec COMMIT explicite """
        # Attention au schéma : gestion_agenda.UTILISATEUR ou juste UTILISATEUR selon votre choix précédent
        sql = "INSERT INTO gestion_agenda.UTILISATEUR (nom, prenom, mot_de_passe) VALUES (%s, %s, %s) RETURNING id_user;"
        
        conn = self.get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(sql, (nom, prenom, mdp))
                new_id = cur.fetchone()[0]
                
                conn.commit()  # <--- AJOUTEZ CETTE LIGNE OBLIGATOIREMENT
                
                cur.close()
                return new_id
            except Exception as e:
                print(f"Erreur inscription : {e}")
                conn.rollback() # Annule en cas d'erreur
            finally:
                conn.close()
        return None

    def recuperer_agendas_utilisateur(self, id_user):
        """
        Récupère les agendas où l'utilisateur est inscrit.
        """
        sql = """
            SELECT A.nom_agenda, R.libelle 
            FROM gestion_agenda.PARTICIPATION P
            JOIN gestion_agenda.AGENDA A ON P.id_agenda = A.id_agenda
            JOIN gestion_agenda.ROLE R ON P.id_role = R.id_role
            WHERE P.id_user = %s;
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, (id_user,))
                        resultats = cur.fetchall() # [cite: 569]
                        
                        print(f"--- Agendas pour l'utilisateur {id_user} ---")
                        for ligne in resultats:
                            print(f"Agenda : {ligne[0]} | Rôle : {ligne[1]}")
                        return resultats
            except Exception as e:
                print(f"Erreur de lecture : {e}")
            finally:
                conn.close()

    def verifier_connexion(self, pseudo, mot_de_passe):
        """ Vérifie le couple login/mdp et renvoie les infos de l'user """
        sql = """
            SELECT id_user, nom, prenom 
            FROM gestion_agenda.UTILISATEUR 
            WHERE nom = %s AND mot_de_passe = %s;
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (pseudo, mot_de_passe))
                    return cur.fetchone() # Renvoie (id, nom, prenom) ou None
            except Exception as e:
                print(f"Erreur login : {e}")
            finally:
                conn.close()
        return None

# --- EXEMPLE D'UTILISATION (Pour tester) ---
if __name__ == "__main__":
    bdd = BaseDeDonnees()
    
    # 1. Création d'un user
    # Note : Dans la vraie vie, il faudrait hasher le mot de passe avant !
    mon_id = bdd.ajouter_utilisateur("Dupont", "Jean", "Secret1234")
    
    # 2. (Supposons qu'on ait ajouté un agenda via SQL pour tester...)
    # bdd.recuperer_agendas_utilisateur(mon_id)
