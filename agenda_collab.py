import psycopg2
from psycopg2 import OperationalError

class BaseDeDonnees:
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "dbname": "agenda_collaboratif",
            "user": "app_agenda_user",
            "password": "Azerty@123"
        }

    def get_connection(self):
        try:
            return psycopg2.connect(**self.db_config)
        except OperationalError as e:
            print(f"❌ Erreur BDD : {e}")
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
                    if user and user[3] == password: return user
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
            except: pass
            finally:
                conn.close()
        return None
    
    def modifier_mot_de_passe(self, id_user, nouveau_mdp):
        """ (NOUVEAU) Change le mot de passe de l'utilisateur """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE gestion_agenda.UTILISATEUR SET mot_de_passe = %s WHERE id_user = %s", (nouveau_mdp, id_user))
                        return True
            except: return False
            finally: conn.close()
        return False

    # --- AGENDAS & PARTICIPATION ---
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
                        cur.execute("INSERT INTO gestion_agenda.AGENDA (nom_agenda, id_createur) VALUES (%s, %s) RETURNING id_agenda;", (nom_agenda, id_createur))
                        new_id = cur.fetchone()[0]
                        cur.execute("SELECT id_role FROM gestion_agenda.ROLE WHERE libelle = 'Administrateur'")
                        id_role = cur.fetchone()[0]
                        cur.execute("INSERT INTO gestion_agenda.PARTICIPATION (id_user, id_agenda, id_role, id_equipe) VALUES (%s, %s, %s, NULL);", (id_createur, new_id, id_role))
                        return new_id
            finally:
                conn.close()
        return None

    # --- NOYAU DE SÉCURITÉ ---
    def recuperer_infos_membre(self, id_user, id_agenda):
        sql = """
            SELECT R.libelle, P.id_equipe
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
                    if res: return {'role': res[0], 'id_equipe': res[1]}
            finally:
                conn.close()
        return None

    def ajouter_membre(self, id_agenda, pseudo_invite, role_choisi, id_equipe):
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

                        sql = "INSERT INTO gestion_agenda.PARTICIPATION (id_user, id_agenda, id_role, id_equipe) VALUES (%s, %s, %s, %s)"
                        cur.execute(sql, (id_invite, id_agenda, id_role, id_equipe))
                        return "OK"
            except Exception as e:
                print(e)
                return "ErreurTech"
            finally:
                conn.close()
        return "ErreurConnexion"
    
    def modifier_equipe_membre(self, id_agenda, id_user_cible, id_new_equipe):
        """ (NOUVEAU) Change l'équipe d'un membre existant """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        sql = "UPDATE gestion_agenda.PARTICIPATION SET id_equipe = %s WHERE id_agenda = %s AND id_user = %s;"
                        cur.execute(sql, (id_new_equipe, id_agenda, id_user_cible))
                        return True
            except: return False
            finally: conn.close()
        return False

    def recuperer_participants(self, id_agenda):
        sql = """
            SELECT U.nom, R.libelle, E.nom_equipe, E.couleur_equipe, U.id_user, P.id_equipe
            FROM gestion_agenda.PARTICIPATION P
            JOIN gestion_agenda.UTILISATEUR U ON P.id_user = U.id_user
            JOIN gestion_agenda.ROLE R ON P.id_role = R.id_role
            LEFT JOIN gestion_agenda.EQUIPE E ON P.id_equipe = E.id_equipe
            WHERE P.id_agenda = %s
            ORDER BY E.nom_equipe, U.nom;
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

    def supprimer_membre(self, id_agenda, id_user_cible):
        sql = "DELETE FROM gestion_agenda.PARTICIPATION WHERE id_agenda = %s AND id_user = %s;"
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, (id_agenda, id_user_cible))
            finally:
                conn.close()

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

    def supprimer_equipe(self, id_equipe):
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM gestion_agenda.EQUIPE WHERE id_equipe = %s;", (id_equipe,))
            except Exception as e:
                print(f"Erreur suppression équipe : {e}")
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

    # --- HISTORIQUE ---
    def ajouter_historique(self, id_event, action, details, id_user):
        sql = "INSERT INTO gestion_agenda.HISTORIQUE (id_event, action, details, id_user) VALUES (%s, %s, %s, %s);"
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, (id_event, action, details, id_user))
            except: pass
            finally: conn.close()

    def recuperer_historique(self, id_event):
        sql = """
            SELECT H.action, H.details, to_char(H.date_action, 'DD/MM/YYYY HH24:MI'), U.nom
            FROM gestion_agenda.HISTORIQUE H
            LEFT JOIN gestion_agenda.UTILISATEUR U ON H.id_user = U.id_user
            WHERE H.id_event = %s ORDER BY H.date_action DESC;
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (id_event,))
                    return cur.fetchall()
            finally: conn.close()
        return []

    # --- ÉVÉNEMENTS ---
    def recuperer_info_event_basic(self, id_event):
        sql = "SELECT id_equipe_concernee FROM gestion_agenda.EVENEMENT WHERE id_event = %s"
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (id_event,))
                    res = cur.fetchone()
                    return res[0] if res else None
            finally: conn.close()
        return None

    def ajouter_evenement(self, titre, desc, debut, fin, id_agenda, id_equipe, id_createur):
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        if id_equipe is not None:
                            sql_check = """
                                SELECT count(*) FROM gestion_agenda.EVENEMENT
                                WHERE id_agenda = %s AND id_equipe_concernee = %s
                                AND ((date_debut <= %s AND date_fin >= %s) OR (date_debut <= %s AND date_fin >= %s) OR (date_debut >= %s AND date_fin <= %s));
                            """
                            cur.execute(sql_check, (id_agenda, id_equipe, debut, debut, fin, fin, debut, fin))
                            if cur.fetchone()[0] > 0: return "ConflitDetecte"

                        sql = "INSERT INTO gestion_agenda.EVENEMENT (titre, description, date_debut, date_fin, id_agenda, id_equipe_concernee, id_createur) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_event;"
                        cur.execute(sql, (titre, desc, debut, fin, id_agenda, id_equipe, id_createur))
                        new_id = cur.fetchone()[0]
                        self.ajouter_historique(new_id, "Création", f"Ticket créé : {titre}", id_createur)
                        return "OK"
            except: return "ErreurTech"
            finally: conn.close()
        return "ErreurConnexion"

    def recuperer_evenements_filtres(self, id_agenda, role_user, id_equipe_user):
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    if role_user == 'Administrateur':
                        sql = """
                            SELECT E.id_event, E.titre, E.date_debut, E.date_fin, EQ.nom_equipe, EQ.couleur_equipe, E.description
                            FROM gestion_agenda.EVENEMENT E
                            LEFT JOIN gestion_agenda.EQUIPE EQ ON E.id_equipe_concernee = EQ.id_equipe
                            WHERE E.id_agenda = %s ORDER BY E.date_debut ASC;
                        """
                        cur.execute(sql, (id_agenda,))
                    else:
                        sql = """
                            SELECT E.id_event, E.titre, E.date_debut, E.date_fin, EQ.nom_equipe, EQ.couleur_equipe, E.description
                            FROM gestion_agenda.EVENEMENT E
                            LEFT JOIN gestion_agenda.EQUIPE EQ ON E.id_equipe_concernee = EQ.id_equipe
                            WHERE E.id_agenda = %s 
                            AND (E.id_equipe_concernee = %s OR E.id_equipe_concernee IS NULL)
                            ORDER BY E.date_debut ASC;
                        """
                        cur.execute(sql, (id_agenda, id_equipe_user))
                    return cur.fetchall()
            finally: conn.close()
        return []

    def modifier_dates_evenement(self, id_event, nouv_debut, nouv_fin, id_user_modif):
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id_agenda, id_equipe_concernee FROM gestion_agenda.EVENEMENT WHERE id_event = %s", (id_event,))
                        info = cur.fetchone()
                        if not info: return "Erreur"
                        id_agenda, id_equipe = info

                        if id_equipe is not None:
                            sql_check = "SELECT count(*) FROM gestion_agenda.EVENEMENT WHERE id_agenda = %s AND id_equipe_concernee = %s AND id_event != %s AND ((date_debut < %s AND date_fin > %s));"
                            cur.execute(sql_check, (id_agenda, id_equipe, id_event, nouv_fin, nouv_debut))
                            if cur.fetchone()[0] > 0: return "Conflit"

                        cur.execute("UPDATE gestion_agenda.EVENEMENT SET date_debut = %s, date_fin = %s WHERE id_event = %s;", (nouv_debut, nouv_fin, id_event))
                        self.ajouter_historique(id_event, "Déplacement", f"Nouv. horaire : {nouv_debut}", id_user_modif)
                        return "OK"
            except: return "Erreur"
            finally: conn.close()
        return "Erreur"

    def modifier_infos_evenement(self, id_event, titre, description, debut, fin, id_nouvelle_equipe, id_user_modif):
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        if id_nouvelle_equipe is not None:
                            sql_check = "SELECT count(*) FROM gestion_agenda.EVENEMENT WHERE id_agenda = (SELECT id_agenda FROM gestion_agenda.EVENEMENT WHERE id_event = %s) AND id_equipe_concernee = %s AND id_event != %s AND ((date_debut < %s AND date_fin > %s));"
                            cur.execute(sql_check, (id_event, id_nouvelle_equipe, id_event, fin, debut))
                            if cur.fetchone()[0] > 0: return "Conflit"

                        cur.execute("UPDATE gestion_agenda.EVENEMENT SET titre=%s, description=%s, date_debut=%s, date_fin=%s, id_equipe_concernee=%s WHERE id_event=%s;", (titre, description, debut, fin, id_nouvelle_equipe, id_event))
                        self.ajouter_historique(id_event, "Modification", "Détails ou Équipe mis à jour", id_user_modif)
                        return "OK"
            except: return "Erreur"
            finally: conn.close()
        return "Erreur"

    def supprimer_evenement(self, id_event):
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM gestion_agenda.EVENEMENT WHERE id_event = %s;", (id_event,))
                        return True
            except: return False
            finally: conn.close()
        return False
