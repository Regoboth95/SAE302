from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from agenda_collab import BaseDeDonnees
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cle_secrete_projet_agenda'

bdd = BaseDeDonnees()

# ==========================================
# ROUTES DE BASE (AUTH & DASHBOARD)
# ==========================================

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
        else:
            flash("Identifiants incorrects")
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

# ==========================================
# VUE PRINCIPALE (AGENDA)
# ==========================================

@app.route('/agenda/<int:id_agenda>')
def voir_agenda(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    if not infos: return redirect(url_for('index'))

    return render_template('agenda.html', 
                           id_agenda=id_agenda, 
                           equipes=bdd.recuperer_equipes(id_agenda), 
                           membres=bdd.recuperer_participants(id_agenda),
                           mon_info=infos)

# ==========================================
# GESTION DES ÉQUIPES (CRÉATION / SUPPRESSION)
# ==========================================

@app.route('/agenda/<int:id_agenda>/nouvelle_equipe', methods=['POST'])
def nouvelle_equipe(id_agenda):
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    if infos['role'] == 'Administrateur':
        bdd.creer_equipe(request.form['nom_equipe'], request.form['couleur_equipe'], id_agenda)
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/supprimer_equipe/<int:id_equipe>', methods=['POST'])
def supprimer_equipe(id_agenda, id_equipe):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    
    # SÉCURITÉ : Seul l'Admin peut supprimer une équipe
    if infos['role'] == 'Administrateur':
        bdd.supprimer_equipe(id_equipe)
        flash("Équipe supprimée avec succès.")
    else:
        flash("⛔ Accès refusé : Seul l'Admin peut supprimer des équipes.")
        
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

# ==========================================
# GESTION DES MEMBRES (INVITATION / SUPPRESSION)
# ==========================================

@app.route('/agenda/<int:id_agenda>/inviter_membre', methods=['POST'])
def inviter_membre(id_agenda):
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    role_moi = infos['role']
    
    if role_moi == 'Collaborateur': return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    pseudo = request.form['pseudo_invite']
    role_invite = request.form['role_invite']
    equipe_invite_id = None
    
    if role_moi == 'Administrateur':
        val = request.form.get('equipe_invite')
        equipe_invite_id = val if val != "" else None
    elif role_moi == 'Chef d\'équipe':
        equipe_invite_id = infos['id_equipe']

    bdd.ajouter_membre(id_agenda, pseudo, role_invite, equipe_invite_id)
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/supprimer_membre/<int:id_membre>', methods=['POST'])
def supprimer_membre(id_agenda, id_membre):
    infos_moi = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    infos_cible = bdd.recuperer_infos_membre(id_membre, id_agenda)
    
    autorise = False
    if infos_moi['role'] == 'Administrateur': autorise = True
    elif infos_moi['role'] == 'Chef d\'équipe':
        if infos_cible['id_equipe'] == infos_moi['id_equipe'] and infos_cible['role'] != 'Administrateur':
            autorise = True
            
    if autorise: bdd.supprimer_membre(id_agenda, id_membre)
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

# ==========================================
# GESTION DES ÉVÉNEMENTS (CRUD COMPLET)
# ==========================================

@app.route('/agenda/<int:id_agenda>/nouvel_evenement', methods=['POST'])
def nouvel_evenement(id_agenda):
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    role = infos['role']
    mon_equipe_id = infos['id_equipe']

    if role == 'Collaborateur':
        return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    id_equipe_cible = request.form.get('id_equipe')
    if id_equipe_cible == "": id_equipe_cible = None
    if role == 'Chef d\'équipe': id_equipe_cible = mon_equipe_id
    
    res = bdd.ajouter_evenement(request.form['titre'], request.form['description'], 
                                request.form['date_debut'], request.form['date_fin'], 
                                id_agenda, id_equipe_cible, session['user_id'])
    if res == "ConflitDetecte": flash("⚠️ Conflit d'horaire !")
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/modifier_evenement_complet', methods=['POST'])
def modifier_evenement_complet(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    id_event = request.form['id_event']
    eq_event_actuelle = bdd.recuperer_info_event_basic(id_event)
    
    # 1. Récupération de la nouvelle équipe souhaitée
    nouvelle_equipe_id = request.form.get('id_equipe')
    if nouvelle_equipe_id == "": nouvelle_equipe_id = None
    
    # 2. Vérification des droits
    autorise = False
    
    if infos['role'] == 'Administrateur': 
        autorise = True
        # L'admin a le droit de choisir n'importe quelle équipe (ou None)
        
    elif infos['role'] == "Chef d'équipe":
        # Le chef ne peut modifier que SI c'est son équipe actuelle
        if eq_event_actuelle == infos['id_equipe'] and eq_event_actuelle is not None:
            autorise = True
            # IMPORTANT : Le chef NE PEUT PAS changer l'équipe pour une autre.
            # On force la nouvelle équipe à être son équipe actuelle pour éviter qu'il ne "vole" ou "pousse" des tickets.
            nouvelle_equipe_id = infos['id_equipe']

    if autorise:
        res = bdd.modifier_infos_evenement(
            id_event, 
            request.form['titre'], 
            request.form['description'], 
            request.form['date_debut'], 
            request.form['date_fin'],
            nouvelle_equipe_id, # <--- Nouveau paramètre
            session['user_id']
        )
        if res == "Conflit": flash("⚠️ Conflit d'horaire dans l'équipe de destination !")
        elif res == "OK": flash("Événement modifié !")
    else:
        flash("⛔ Modification interdite.")

    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/supprimer_evenement_complet/<int:id_event>', methods=['POST'])
def supprimer_evenement_complet(id_agenda, id_event):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    equipe_event = bdd.recuperer_info_event_basic(id_event)
    
    autorise = False
    if infos['role'] == 'Administrateur': 
        autorise = True
    elif infos['role'] == "Chef d'équipe" and equipe_event == infos['id_equipe']: 
        autorise = True
    
    if autorise:
        bdd.supprimer_evenement(id_event)
        flash("Événement supprimé.")
    else:
        flash("⛔ Suppression interdite.")
        
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

# ==========================================
# API JSON (POUR FULLCALENDAR & DRAG/DROP)
# ==========================================

@app.route('/api/events/<int:id_agenda>')
def api_get_events(id_agenda):
    """ Renvoie les événements en JSON pour le calendrier JS """
    if 'user_id' not in session: return jsonify([])

    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    role = infos['role']
    mon_equipe_id = infos['id_equipe']

    raw_events = bdd.recuperer_evenements_filtres(id_agenda, role, mon_equipe_id)
    
    json_events = []
    for ev in raw_events:
        # ev = [id, titre, debut, fin, nom_equipe, couleur, desc]
        is_editable = False
        if role == 'Administrateur':
            is_editable = True
        elif role == 'Chef d\'équipe':
            if ev[5]: # Si le ticket a une couleur (donc une équipe)
                is_editable = True 
        
        json_events.append({
            'id': ev[0],
            'title': ev[1],
            'start': ev[2].isoformat(),
            'end': ev[3].isoformat(),
            'backgroundColor': ev[5] or '#6c757d',
            'borderColor': ev[5] or '#6c757d',
            'description': ev[6],
            'editable': is_editable,
            'extendedProps': {
                'equipe': ev[4] or 'Général'
            }
        })
    
    return jsonify(json_events)

@app.route('/api/move_event', methods=['POST'])
def api_move_event():
    """ Appelé par le JS quand on lâche la souris """
    if 'user_id' not in session: return jsonify({'status': 'error'})
    
    data = request.json
    id_event = data['id']
    start = data['start'].replace('T', ' ')[:16] 
    end = data['end'].replace('T', ' ')[:16] if data['end'] else start

    # V2 (Compatible V1) : On passe l'ID user mais pour la V1 ça sera ignoré par la fonction SQL V1
    # Pour que ça marche avec ta BDD V1, j'utilise la signature V1 (sans user_id)
    # SI TU UTILISES AGENDA_COLLAB V1 :
    resultat = bdd.modifier_dates_evenement(id_event, start, end)
    
    if resultat == "OK":
        return jsonify({'status': 'ok'})
    elif resultat == "Conflit":
        return jsonify({'status': 'conflict', 'message': 'L\'équipe est déjà occupée sur ce créneau.'})
    else:
        return jsonify({'status': 'error'})

if __name__ == '__main__':
    app.run(debug=True)
