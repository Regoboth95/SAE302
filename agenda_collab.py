import psycopg2
from psycopg2 import OperationalError

class BaseDeDonnees:
    def __init__(self):
        # Configuration BDD (PC Local)
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "dbname": "agenda_collaboratif",
            "user": "app_agenda_user",
            "password": "Azerty@123"
        }

    def get_connection(self):
        """Établit la connexion à PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except OperationalError as e:
            print(f"❌ Erreur de connexion BDD : {e}")
            return None

    # --- UTILISATEURS ---

    def verifier_connexion(self, pseudo, password):
        """ Vérifie le login """
        sql = """
            SELECT id_user, nom, prenom, mot_de_passe 
            FROM gestion_agenda.UTILISATEUR 
            WHERE nom = %s;
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (pseudo,))
                    user = cur.fetchone()
                    if user and user[3] == password: 
                        return user
            except Exception as e:
                print(f"Erreur login : {e}")
            finally:
                conn.close()
        return None

    def ajouter_utilisateur(self, nom, prenom, mdp):
        """ Inscription """
        sql = """
            INSERT INTO gestion_agenda.UTILISATEUR (nom, prenom, mot_de_passe) 
            VALUES (%s, %s, %s) 
            RETURNING id_user;
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, (nom, prenom, mdp))
                        return cur.fetchone()[0]
            except Exception as e:
                print(f"Erreur inscription : {e}")
            finally:
                conn.close()
        return None

    # --- AGENDAS & PARTICIPANTS (INVITATIONS) ---

    def recuperer_agendas_utilisateur(self, id_user):
        """ Récupère les agendas """
        sql = """
            SELECT A.nom_agenda, R.libelle, A.id_agenda
            FROM gestion_agenda.PARTICIPATION P
            JOIN gestion_agenda.AGENDA A ON P.id_agenda = A.id_agenda
            JOIN gestion_agenda.ROLE R ON P.id_role = R.id_role
            WHERE P.id_user = %s;
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (id_user,))
                    return cur.fetchall()
            finally:
                conn.close()
        return []

    def creer_agenda(self, nom_agenda, id_createur):
        """ Crée un agenda et set le rôle Admin """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        # 1. Créer l'agenda
                        sql_agenda = "INSERT INTO gestion_agenda.AGENDA (nom_agenda, id_createur) VALUES (%s, %s) RETURNING id_agenda;"
                        cur.execute(sql_agenda, (nom_agenda, id_createur))
                        new_id = cur.fetchone()[0]

                        # 2. Récupérer l'ID du rôle 'Administrateur'
                        cur.execute("SELECT id_role FROM gestion_agenda.ROLE WHERE libelle = 'Administrateur'")
                        id_role_admin = cur.fetchone()[0]

                        # 3. Créer la participation
                        sql_part = "INSERT INTO gestion_agenda.PARTICIPATION (id_user, id_agenda, id_role) VALUES (%s, %s, %s);"
                        cur.execute(sql_part, (id_createur, new_id, id_role_admin))
                        return new_id
            except Exception as e:
                print(f"Erreur création agenda : {e}")
            finally:
                conn.close()
        return None

    def recuperer_participants(self, id_agenda):
        """ Récupère la liste des membres d'un agenda """
        sql = """
            SELECT U.nom, R.libelle 
            FROM gestion_agenda.PARTICIPATION P
            JOIN gestion_agenda.UTILISATEUR U ON P.id_user = U.id_user
            JOIN gestion_agenda.ROLE R ON P.id_role = R.id_role
            WHERE P.id_agenda = %s;
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (id_agenda,))
                    return cur.fetchall()
            finally:
                conn.close()
        return []

    def ajouter_membre(self, id_agenda, pseudo_invite, role_choisi):
        """ Invite un utilisateur dans l'agenda """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        # 1. Trouver l'ID du user
                        cur.execute("SELECT id_user FROM gestion_agenda.UTILISATEUR WHERE nom = %s", (pseudo_invite,))
                        res_user = cur.fetchone()
                        if not res_user:
                            return "UserIntrouvable"
                        id_invite = res_user[0]

                        # 2. Trouver l'ID du rôle
                        cur.execute("SELECT id_role FROM gestion_agenda.ROLE WHERE libelle = %s", (role_choisi,))
                        res_role = cur.fetchone()
                        if not res_role:
                            return "RoleIntrouvable"
                        id_role = res_role[0]

                        # 3. Vérifier s'il est déjà dedans
                        cur.execute("SELECT * FROM gestion_agenda.PARTICIPATION WHERE id_user=%s AND id_agenda=%s", (id_invite, id_agenda))
                        if cur.fetchone():
                            return "DejaMembre"

                        # 4. Insérer
                        sql = "INSERT INTO gestion_agenda.PARTICIPATION (id_user, id_agenda, id_role) VALUES (%s, %s, %s)"
                        cur.execute(sql, (id_invite, id_agenda, id_role))
                        return "OK"
            except Exception as e:
                print(f"Erreur invitation : {e}")
                return "ErreurTech"
            finally:
                conn.close()
        return "ErreurConnexion"


    # --- ÉQUIPES (V1) ---

    def creer_equipe(self, nom_equipe, couleur, id_agenda):
        """ Crée une équipe avec une couleur dans un agenda """
        sql = """
            INSERT INTO gestion_agenda.EQUIPE (nom_equipe, couleur_equipe, id_agenda)
            VALUES (%s, %s, %s);
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, (nom_equipe, couleur, id_agenda))
            except Exception as e:
                print(f"Erreur création équipe : {e}")
            finally:
                conn.close()

    def recuperer_equipes(self, id_agenda):
        """ Récupère la liste des équipes d'un agenda """
        sql = "SELECT id_equipe, nom_equipe, couleur_equipe FROM gestion_agenda.EQUIPE WHERE id_agenda = %s;"
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (id_agenda,))
                    return cur.fetchall()
            finally:
                conn.close()
        return []

    # --- ÉVÉNEMENTS (CALENDRIER V1) ---

    def ajouter_evenement(self, titre, desc, debut, fin, id_agenda, id_equipe, id_createur):
        """ Ajoute un événement (plage horaire) """
        sql = """
            INSERT INTO gestion_agenda.EVENEMENT 
            (titre, description, date_debut, date_fin, id_agenda, id_equipe_concernee, id_createur)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, (titre, desc, debut, fin, id_agenda, id_equipe, id_createur))
            except Exception as e:
                print(f"Erreur ajout événement : {e}")
            finally:
                conn.close()

    def recuperer_evenements(self, id_agenda):
        """ Récupère les événements pour le calendrier """
        sql = """
            SELECT E.id_event, E.titre, E.date_debut, E.date_fin, EQ.nom_equipe, EQ.couleur_equipe, E.description
            FROM gestion_agenda.EVENEMENT E
            LEFT JOIN gestion_agenda.EQUIPE EQ ON E.id_equipe_concernee = EQ.id_equipe
            WHERE E.id_agenda = %s
            ORDER BY E.date_debut ASC;
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (id_agenda,))
                    return cur.fetchall()
            finally:
                conn.close()
        return []
