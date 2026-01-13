import psycopg2
from psycopg2 import OperationalError

class BaseDeDonnees:
    """
    Gère la connexion et les opérations CRUD sur la base de données PostgreSQL 'agenda_collaboratif'.
    Utilise le schéma 'gestion_agenda' pour toutes les tables.
    """

    def __init__(self):
        """Initialise les paramètres de connexion à PostgreSQL."""
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "dbname": "agenda_collaboratif",
            "user": "app_agenda_user",
            "password": "Azerty@123"
        }

    def get_connection(self):
        """
        Établit une connexion à la base de données.
        Retourne l'objet de connexion ou None en cas d'échec (OperationalError).
        """
        try:
            return psycopg2.connect(**self.db_config)
        except OperationalError as e:
            print(f"❌ Erreur BDD : {e}")
            return None

    # --- UTILISATEURS ---
    def verifier_connexion(self, pseudo, password):
        """
        Vérifie les identifiants d'un utilisateur lors de la connexion.
        
        Args:
            pseudo (str): Le nom d'utilisateur.
            password (str): Le mot de passe (en clair).
            
        Returns:
            tuple: (id_user, nom, prenom, mot_de_passe) si valide, None sinon.
        """
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
        """
        Inscrit un nouvel utilisateur en vérifiant d'abord l'unicité du pseudo.
        
        Returns:
            str: 'OK', 'ExisteDeja' ou 'Erreur'.
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        # 1. VERIFICATION DOUBLON (Nouveau)
                        # Empêche de créer deux utilisateurs avec le même nom
                        cur.execute("SELECT count(*) FROM gestion_agenda.UTILISATEUR WHERE nom = %s", (nom,))
                        if cur.fetchone()[0] > 0:
                            return "ExisteDeja"

                        # 2. INSERTION
                        sql = "INSERT INTO gestion_agenda.UTILISATEUR (nom, prenom, mot_de_passe) VALUES (%s, %s, %s) RETURNING id_user;"
                        cur.execute(sql, (nom, prenom, mdp))
                        return "OK"
            except Exception as e:
                print(e)
                return "Erreur"
            finally:
                conn.close()
        return "Erreur"
    
    def modifier_mot_de_passe(self, id_user, nouveau_mdp):
        """
        Modifie le mot de passe d'un utilisateur existant.
        Vérifie que le nouveau mot de passe est différent de l'actuel.
        
        Returns:
            str: 'OK', 'MemeMdp' ou 'Erreur'.
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        # 1. RECUPERER ANCIEN MDP (Nouveau)
                        cur.execute("SELECT mot_de_passe FROM gestion_agenda.UTILISATEUR WHERE id_user = %s", (id_user,))
                        res = cur.fetchone()
                        if res and res[0] == nouveau_mdp:
                            return "MemeMdp" # C'est le même !

                        # 2. UPDATE
                        cur.execute("UPDATE gestion_agenda.UTILISATEUR SET mot_de_passe = %s WHERE id_user = %s", (nouveau_mdp, id_user))
                        return "OK"
            except: return "Erreur"
            finally: conn.close()
        return "Erreur"

    # --- AGENDAS & PARTICIPATION ---
    def recuperer_agendas_utilisateur(self, id_user):
        """
        Récupère la liste de tous les agendas auxquels un utilisateur participe.
        Effectue une jointure entre PARTICIPATION, AGENDA et ROLE.
        
        Returns:
            list: Liste de tuples [(nom_agenda, role, id_agenda), ...].
        """
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
        """
        Crée un nouvel agenda et assigne automatiquement le créateur comme 'Administrateur'.
        
        Returns:
            int: L'ID du nouvel agenda ou None en cas d'erreur.
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        # Crée l'agenda
                        cur.execute("INSERT INTO gestion_agenda.AGENDA (nom_agenda, id_createur) VALUES (%s, %s) RETURNING id_agenda;", (nom_agenda, id_createur))
                        new_id = cur.fetchone()[0]
                        # Récupère l'ID du rôle Admin
                        cur.execute("SELECT id_role FROM gestion_agenda.ROLE WHERE libelle = 'Administrateur'")
                        id_role = cur.fetchone()[0]
                        # Ajoute le créateur dans la table PARTICIPATION
                        cur.execute("INSERT INTO gestion_agenda.PARTICIPATION (id_user, id_agenda, id_role, id_equipe) VALUES (%s, %s, %s, NULL);", (id_createur, new_id, id_role))
                        return new_id
            finally:
                conn.close()
        return None

    # --- NOYAU DE SÉCURITÉ ---
    def recuperer_infos_membre(self, id_user, id_agenda):
        """
        Récupère les informations de rôle et d'équipe d'un utilisateur pour un agenda spécifique.
        Sert à vérifier les droits d'accès.
        
        Returns:
            dict: {'role': str, 'id_equipe': int} ou None.
        """
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
        """
        Ajoute un nouveau membre à un agenda.
        
        Returns:
            str: 'OK', 'UserIntrouvable', 'RoleIntrouvable', 'DejaMembre', 'ErreurTech'.
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        # Vérif User
                        cur.execute("SELECT id_user FROM gestion_agenda.UTILISATEUR WHERE nom = %s", (pseudo_invite,))
                        res_user = cur.fetchone()
                        if not res_user: return "UserIntrouvable"
                        id_invite = res_user[0]

                        # Vérif Role
                        cur.execute("SELECT id_role FROM gestion_agenda.ROLE WHERE libelle = %s", (role_choisi,))
                        res_role = cur.fetchone()
                        if not res_role: return "RoleIntrouvable"
                        id_role = res_role[0]

                        # Vérif déjà membre
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
        """
        Change l'équipe d'un membre existant dans un agenda (Action Admin).
        
        Returns:
            bool: True si réussi, False sinon.
        """
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
        """
        Récupère la liste complète des membres d'un agenda (Nom, Rôle, Équipe).
        Utilisé pour afficher la liste des membres dans la sidebar.
        """
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
        """Retire un membre d'un agenda."""
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
        """Crée une nouvelle équipe dans un agenda."""
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("INSERT INTO gestion_agenda.EQUIPE (nom_equipe, couleur_equipe, id_agenda) VALUES (%s, %s, %s);", (nom_equipe, couleur, id_agenda))
            finally:
                conn.close()

    def supprimer_equipe(self, id_equipe):
        """Supprime une équipe."""
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
        """Récupère toutes les équipes d'un agenda (ID, Nom, Couleur)."""
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
        """
        Enregistre une action (Création, Modif, Déplacement) dans la table HISTORIQUE.
        Appelé automatiquement par les fonctions de modification d'événements.
        """
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
        """
        Récupère l'historique complet d'un événement, trié par date décroissante.
        Inclut le nom de l'utilisateur qui a fait l'action.
        """
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
        """Helper pour récupérer juste l'équipe concernée par un événement (utile pour les vérifs de droits)."""
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
        """
        Crée un événement si aucun conflit n'est détecté.
        Vérifie si la plage horaire est libre pour l'équipe spécifiée.
        Enregistre l'action dans l'historique.
        
        Returns:
            str: 'OK', 'ConflitDetecte', 'ErreurTech', 'ErreurConnexion'.
        """
        conn = self.get_connection()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        if id_equipe is not None:
                            # Vérification stricte des conflits :
                            # On cherche s'il existe déjà un événement pour la MEME équipe sur la MEME plage horaire.
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
                        # Log l'action
                        self.ajouter_historique(new_id, "Création", f"Ticket créé : {titre}", id_createur)
                        return "OK"
            except: return "ErreurTech"
            finally: conn.close()
        return "ErreurConnexion"

    def recuperer_evenements_filtres(self, id_agenda, role_user, id_equipe_user):
        """
        Récupère les événements à afficher sur le calendrier.
        FILTRAGE IMPORTANT :
        - Admin : voit tout.
        - Chef/Collab : ne voit que les événements de SON équipe + les événements Généraux (sans équipe).
        """
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
        """
        Gère le Drag & Drop : modifie les dates et vérifie les conflits.
        Enregistre l'action dans l'historique.
        """
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
                            # Vérifie conflit en excluant l'événement actuel (id_event != %s)
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
        """
        Modifie toutes les infos d'un événement (Titre, Desc, Dates, Equipe).
        Gère les conflits si l'équipe ou les dates changent.
        """
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
        """Supprime un événement (et son historique via la cascade en BDD)."""
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
