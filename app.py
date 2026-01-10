from flask import Flask, render_template, request, redirect, url_for, session, flash
from agenda_collab import BaseDeDonnees

app = Flask(__name__)
app.secret_key = 'cle_secrete_projet_agenda'

bdd = BaseDeDonnees()

# --- ROUTES CLASSIQUES (Login, Logout, etc. inchangées) ---
@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    agendas = bdd.recuperer_agendas_utilisateur(session['user_id'])
    return render_template('dashboard.html', pseudo=session['pseudo'], agendas=agendas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = bdd.verifier_connexion(request.form['pseudo'], request.form['password'])
        if user:
            session['user_id'] = user[0]
            session['pseudo'] = user[1]
            return redirect(url_for('index'))
        else: flash("Identifiants incorrects")
    return render_template('login.html', mode='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if bdd.ajouter_utilisateur(request.form['pseudo'], "User", request.form['password']):
            flash("Compte créé ! Connectez-vous.")
            return redirect(url_for('login'))
        flash("Erreur pseudo.")
    return render_template('login.html', mode='register')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/nouveau_agenda', methods=['POST'])
def nouveau_agenda():
    if 'user_id' in session:
        bdd.creer_agenda(request.form['nom_agenda'], session['user_id'])
        flash("Agenda créé !")
    return redirect(url_for('index'))

# --- VUE AGENDA SÉCURISÉE V2 ---
@app.route('/agenda/<int:id_agenda>')
def voir_agenda(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # 1. Qui suis-je dans cet agenda ?
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    
    # Si je ne suis pas membre (accès direct par URL), on vire
    if not infos: return redirect(url_for('index'))

    # 2. Récupération filtrée (Selon mon équipe)
    evenements = bdd.recuperer_evenements_filtres(id_agenda, infos['role'], infos['id_equipe'])
    
    return render_template('agenda.html', 
                           id_agenda=id_agenda, 
                           equipes=bdd.recuperer_equipes(id_agenda), 
                           evenements=evenements,
                           membres=bdd.recuperer_participants(id_agenda),
                           mon_info=infos) # On passe toutes les infos (role + id_equipe)

@app.route('/agenda/<int:id_agenda>/nouvelle_equipe', methods=['POST'])
def nouvelle_equipe(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # SEUL L'ADMIN PEUT CREER DES EQUIPES
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    if infos['role'] != 'Administrateur':
        flash("⛔ Seul l'Admin peut créer des équipes.")
        return redirect(url_for('voir_agenda', id_agenda=id_agenda))
    
    bdd.creer_equipe(request.form['nom_equipe'], request.form['couleur_equipe'], id_agenda)
    flash("Équipe ajoutée !")
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/nouvel_evenement', methods=['POST'])
def nouvel_evenement(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    role = infos['role']
    mon_equipe_id = infos['id_equipe']

    # SÉCURITÉ CRÉATION
    if role == 'Collaborateur':
        flash("⛔ Les collaborateurs ne peuvent pas créer d'événements.")
        return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    # LOGIQUE D'ATTRIBUTION D'ÉQUIPE
    id_equipe_cible = request.form.get('id_equipe')
    if id_equipe_cible == "": id_equipe_cible = None

    # Si je suis Chef d'équipe, je force l'événement SUR MON ÉQUIPE
    if role == 'Chef d\'équipe':
        if mon_equipe_id is None:
            flash("Erreur: Vous êtes Chef mais sans équipe assignée.")
            return redirect(url_for('voir_agenda', id_agenda=id_agenda))
        id_equipe_cible = mon_equipe_id # <--- LE CHEF NE PEUT PAS CHOISIR AILLEURS
    
    res = bdd.ajouter_evenement(request.form['titre'], request.form['description'], 
                                request.form['date_debut'], request.form['date_fin'], 
                                id_agenda, id_equipe_cible, session['user_id'])
    
    if res == "OK": flash("Événement ajouté !")
    elif res == "ConflitDetecte": flash("⚠️ IMPOSSIBLE : Créneau déjà pris !")
    else: flash("Erreur technique.")
    
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/inviter_membre', methods=['POST'])
def inviter_membre(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    role_moi = infos['role']

    # SÉCURITÉ INVITATION
    if role_moi == 'Collaborateur':
        flash("⛔ Accès refusé.")
        return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    pseudo = request.form['pseudo_invite']
    role_invite = request.form['role_invite']
    
    # LOGIQUE D'AFFECTATION D'ÉQUIPE
    equipe_invite_id = None
    
    if role_moi == 'Administrateur':
        # L'admin choisit l'équipe dans le formulaire
        val = request.form.get('equipe_invite')
        equipe_invite_id = val if val != "" else None
    
    elif role_moi == 'Chef d\'équipe':
        # Le chef invite AUTOMATIQUEMENT dans SON équipe
        equipe_invite_id = infos['id_equipe']
        # Et il ne peut inviter que des collaborateurs (optionnel, mais logique)
        if role_invite == 'Administrateur':
            flash("⛔ Un chef ne peut pas nommer un Administrateur.")
            return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    # Si on invite un Collaborateur ou Chef, il FAUT une équipe
    if role_invite != 'Administrateur' and equipe_invite_id is None:
        flash("⚠️ Erreur : Un Collaborateur ou Chef doit appartenir à une équipe.")
        return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    res = bdd.ajouter_membre(id_agenda, pseudo, role_invite, equipe_invite_id)
    
    if res == "OK": flash("Membre invité avec succès !")
    elif res == "UserIntrouvable": flash("Utilisateur introuvable.")
    elif res == "DejaMembre": flash("Déjà membre.")
    else: flash("Erreur technique.")
    
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))
    
@app.route('/agenda/<int:id_agenda>/supprimer_membre/<int:id_membre>', methods=['POST'])
def supprimer_membre(id_agenda, id_membre):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # 1. Qui suis-je ?
    infos_moi = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    role_moi = infos_moi['role']
    
    # 2. Qui est la cible ?
    infos_cible = bdd.recuperer_infos_membre(id_membre, id_agenda)
    
    # Sécurité de base
    if not infos_cible:
        flash("Utilisateur introuvable.")
        return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    # --- LOGIQUE DE PERMISSION ---
    autorise = False
    
    if role_moi == 'Administrateur':
        # L'admin peut tout faire
        autorise = True
        
    elif role_moi == 'Chef d\'équipe':
        # Le chef ne peut supprimer QUE quelqu'un de son équipe
        if infos_cible['id_equipe'] == infos_moi['id_equipe']:
            autorise = True
        
        # PROTECTION : Un chef ne peut pas virer un Admin (même s'il bug)
        if infos_cible['role'] == 'Administrateur':
            autorise = False
            flash("⛔ Un chef ne peut pas supprimer un Administrateur.")
            return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    if autorise:
        bdd.supprimer_membre(id_agenda, id_membre)
        flash("Membre retiré de l'agenda.")
    else:
        flash("⛔ Vous n'avez pas le droit de supprimer ce membre.")
        
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

if __name__ == '__main__':
    app.run(debug=True)
