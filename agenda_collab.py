import psycopg2
from psycopg2 import OperationalError

class BaseDeDonnees:
    def __init__(self):
        # Configuration BDD
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "dbname": "agenda_collaboratif",
            "user": "app_agenda_user",
            "password": "Azerty@123"
        }

    def get_connection(self):
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except OperationalError as e:
            print(f"❌ Erreur de connexion BDD : {e}")
            return None

    # --- UTILISATEURS ---
    def verifier_connexion(self, pseudo, password):
        sql = "SELECT id_user, nom, prenom, mot_de_passe FROM gestion_agenda.UTILISATEUR WHERE nom = %s;"
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (pseudo,))
                    user = cur.fetchone()
                    if user and user[3] == password:
                        return user
            finally:
                conn.close()
        return None

    def ajouter_utilisateur(self, nom, prenom, mdp):
        sql = "INSERT INTO gestion_agenda.UTILISATEUR (nom, prenom, mot_de_passe) VALUES (%s, %s, %s) RETURNING id_user;"
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, (nom, prenom, mdp))
                        return cur.fetchone()[0]
            except:
                pass
            finally:
                conn.close()
        return None

    # --- AGENDAS & PARTICIPANTS ---
    def recuperer_agendas_utilisateur(self, id_user):
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
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        # Créer agenda
                        cur.execute("INSERT INTO gestion_agenda.AGENDA (nom_agenda, id_createur) VALUES (%s, %s) RETURNING id_agenda;", (nom_agenda, id_createur))
                        new_id = cur.fetchone()[0]
                        # Récupérer id rôle Admin
                        cur.execute("SELECT id_role FROM gestion_agenda.ROLE WHERE libelle = 'Administrateur'")
                        id_role = cur.fetchone()[0]
                        # Lier
                        cur.execute("INSERT INTO gestion_agenda.PARTICIPATION (id_user, id_agenda, id_role) VALUES (%s, %s, %s);", (id_createur, new_id, id_role))
                        return new_id
            finally:
                conn.close()
        return None

    def recuperer_participants(self, id_agenda):
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
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id_user FROM gestion_agenda.UTILISATEUR WHERE nom = %s", (pseudo_invite,))
                        res_user = cur.fetchone()
                        if not res_user: return "UserIntrouvable"
                        id_invite = res_user[0]

                        cur.execute("SELECT id_role FROM gestion_agenda.ROLE WHERE libelle = %s", (role_choisi,))
                        res_role = cur.fetchone()
                        if not res_role: return "RoleIntrouvable"
                        id_role = res_role[0]

                        cur.execute("SELECT * FROM gestion_agenda.PARTICIPATION WHERE id_user=%s AND id_agenda=%s", (id_invite, id_agenda))
                        if cur.fetchone(): return "DejaMembre"

                        cur.execute("INSERT INTO gestion_agenda.PARTICIPATION (id_user, id_agenda, id_role) VALUES (%s, %s, %s)", (id_invite, id_agenda, id_role))
                        return "OK"
            except Exception as e:
                print(e)
                return "ErreurTech"
            finally:
                conn.close()
        return "ErreurConnexion"

    # --- PERMISSIONS (NOUVEAU) ---
    def recuperer_role_user(self, id_user, id_agenda):
        """ Récupère le rôle (ex: 'Collaborateur') de l'utilisateur connecté """
        sql = """
            SELECT R.libelle 
            FROM gestion_agenda.PARTICIPATION P
            JOIN gestion_agenda.ROLE R ON P.id_role = R.id_role
            WHERE P.id_user = %s AND P.id_agenda = %s;
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (id_user, id_agenda))
                    res = cur.fetchone()
                    return res[0] if res else None
            finally:
                conn.close()
        return None

    # --- ÉQUIPES ---
    def creer_equipe(self, nom_equipe, couleur, id_agenda):
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("INSERT INTO gestion_agenda.EQUIPE (nom_equipe, couleur_equipe, id_agenda) VALUES (%s, %s, %s);", (nom_equipe, couleur, id_agenda))
            finally:
                conn.close()

    def recuperer_equipes(self, id_agenda):
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id_equipe, nom_equipe, couleur_equipe FROM gestion_agenda.EQUIPE WHERE id_agenda = %s;", (id_agenda,))
                    return cur.fetchall()
            finally:
                conn.close()
        return []

    # --- ÉVÉNEMENTS (AVEC GESTION CONFLITS) ---
    def ajouter_evenement(self, titre, desc, debut, fin, id_agenda, id_equipe, id_createur):
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        # 1. Vérification Conflits
                        if id_equipe is not None:
                            sql_check = """
                                SELECT count(*) FROM gestion_agenda.EVENEMENT
                                WHERE id_agenda = %s AND id_equipe_concernee = %s
                                AND (
                                    (date_debut <= %s AND date_fin >= %s) OR
                                    (date_debut <= %s AND date_fin >= %s) OR
                                    (date_debut >= %s AND date_fin <= %s)
                                );
                            """
                            cur.execute(sql_check, (id_agenda, id_equipe, debut, debut, fin, fin, debut, fin))
                            if cur.fetchone()[0] > 0:
                                return "ConflitDetecte"

                        # 2. Insertion
                        sql = """
                            INSERT INTO gestion_agenda.EVENEMENT 
                            (titre, description, date_debut, date_fin, id_agenda, id_equipe_concernee, id_createur)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                        """
                        cur.execute(sql, (titre, desc, debut, fin, id_agenda, id_equipe, id_createur))
                        return "OK"
            except Exception as e:
                print(e)
                return "ErreurTech"
            finally:
                conn.close()
        return "ErreurConnexion"

    def recuperer_evenements(self, id_agenda):
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
