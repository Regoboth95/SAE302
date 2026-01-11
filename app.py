from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from agenda_collab import BaseDeDonnees
from datetime import datetime
import re 
import socket

# Configuration des cibles 
SERVEUR_IP = "127.0.0.1" # localhost 
PORT_TCP_LOGS = 9000 
PORT_UDP_NOTIFS = 9001

def envoyer_tcp_critique(message):
    """Envoie un message important via TCP (fiable, connecté)"""
    try:
        # Création socket TCP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVEUR_IP, PORT_TCP_LOGS))
        s.send(message.encode('utf-8'))
        s.close()
    except Exception as e:
        print(f"Erreur envoi TCP: {e}")

def envoyer_udp_rapide(message):
    """Envoie une notification légère via UDP (non connecté, rapide)"""
    try:
        # Création socket UDP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(message.encode('utf-8'), (SERVEUR_IP, PORT_UDP_NOTIFS)) # [cite: 923]
        s.close()
    except:
        pass # UDP ne garantit pas l'arrivée, on ignore les erreurs

app = Flask(__name__)
app.secret_key = 'cle_secrete_projet_agenda'

bdd = BaseDeDonnees()

# ==========================================
# 1. AUTH & DASHBOARD
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
        else: flash("Identifiants incorrects")
    return render_template('login.html', mode='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        pseudo = request.form['pseudo']
        mdp = request.form['password']
        
        # Vérif Robustesse
        if len(mdp) < 8 or not re.search(r"\d", mdp) or not re.search(r"[A-Z]", mdp) or not re.search(r"[\W_]", mdp):
            flash("⚠️ Mot de passe faible ! (8 carac, 1 Maj, 1 Chiffre, 1 Symbole)")
            return render_template('login.html', mode='register')

        # Appel BDD
        resultat = bdd.ajouter_utilisateur(pseudo, "User", mdp)
        
        if resultat == "OK":
            # [TCP] On loggue l'inscription de manière fiable
            envoyer_tcp_critique(f"AUTH: Nouvel utilisateur inscrit : {pseudo}")
            
            flash("Compte créé ! Connectez-vous.")
            return redirect(url_for('login'))
        elif resultat == "ExisteDeja":
            flash("⛔ Ce pseudo est déjà utilisé. Veuillez en choisir un autre.")
        else:
            flash("Erreur technique.")
            
    return render_template('login.html', mode='register')

@app.route('/changer_mot_de_passe', methods=['POST'])
def changer_mot_de_passe():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    nouveau_mdp = request.form['nouveau_mdp']
    
    if len(nouveau_mdp) < 8 or not re.search(r"\d", nouveau_mdp) or not re.search(r"[A-Z]", nouveau_mdp) or not re.search(r"[\W_]", nouveau_mdp):
        flash("⚠️ Mot de passe trop faible.")
    else:
        res = bdd.modifier_mot_de_passe(session['user_id'], nouveau_mdp)
        if res == "OK":
            flash("✅ Mot de passe modifié avec succès !")
        elif res == "MemeMdp":
            flash("⚠️ Le nouveau mot de passe est identique à l'ancien !")
        else:
            flash("❌ Erreur lors de la modification.")
            
    return redirect(request.referrer or url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/nouveau_agenda', methods=['POST'])
def nouveau_agenda():
    if 'user_id' in session:
        bdd.creer_agenda(request.form['nom_agenda'], session['user_id'])

        # [TCP] Création importante
        envoyer_tcp_critique(f"ADMIN: Agenda '{request.form['nom_agenda']}' créé par ID {session['user_id']}")

        flash("Agenda créé !")
    return redirect(url_for('index'))

# ==========================================
# 2. VUE AGENDA
# ==========================================
@app.route('/agenda/<int:id_agenda>')
def voir_agenda(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    if not infos: return redirect(url_for('index'))
    return render_template('agenda.html', id_agenda=id_agenda, 
                           equipes=bdd.recuperer_equipes(id_agenda), 
                           membres=bdd.recuperer_participants(id_agenda),
                           mon_info=infos)

# ==========================================
# 3. GESTION ÉQUIPES & MEMBRES
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
    if infos['role'] == 'Administrateur':
        bdd.supprimer_equipe(id_equipe)
        flash("Équipe supprimée.")
    else: flash("⛔ Accès refusé.")
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/inviter_membre', methods=['POST'])
def inviter_membre(id_agenda):
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    if infos['role'] == 'Collaborateur': return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    pseudo = request.form['pseudo_invite']
    role_invite = request.form['role_invite']
    equipe_invite_id = None
    if infos['role'] == 'Administrateur':
        val = request.form.get('equipe_invite')
        equipe_invite_id = val if val != "" else None
    elif infos['role'] == 'Chef d\'équipe':
        equipe_invite_id = infos['id_equipe']

    bdd.ajouter_membre(id_agenda, pseudo, role_invite, equipe_invite_id)
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/modifier_membre_equipe', methods=['POST'])
def modifier_membre_equipe(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    if infos['role'] == 'Administrateur':
        id_user_cible = request.form['id_user_cible']
        id_new_equipe = request.form['id_new_equipe']
        if id_new_equipe == "": id_new_equipe = None
        
        if bdd.modifier_equipe_membre(id_agenda, id_user_cible, id_new_equipe):
            flash("Équipe du membre modifiée.")
        else:
            flash("Erreur modification membre.")
    else:
        flash("⛔ Seul l'Admin peut modifier les membres.")
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
# 4. GESTION ÉVÉNEMENTS
# ==========================================
@app.route('/agenda/<int:id_agenda>/nouvel_evenement', methods=['POST'])
def nouvel_evenement(id_agenda):
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    if infos['role'] == 'Collaborateur': return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    id_equipe_cible = request.form.get('id_equipe')
    if id_equipe_cible == "": id_equipe_cible = None
    if infos['role'] == 'Chef d\'équipe': id_equipe_cible = infos['id_equipe']
    
    res = bdd.ajouter_evenement(request.form['titre'], request.form['description'], 
                                request.form['date_debut'], request.form['date_fin'], 
                                id_agenda, id_equipe_cible, session['user_id'])
    if res == "OK":
        # [UDP] Notification rapide qu'un ticket est arrivé
        envoyer_udp_rapide(f"EVENT: Nouveau ticket '{request.form['titre']}' (Agenda {id_agenda})")
    
    if res == "ConflitDetecte": flash("⚠️ Conflit d'horaire !")
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/modifier_evenement_complet', methods=['POST'])
def modifier_evenement_complet(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    id_event = request.form['id_event']
    eq_event_actuelle = bdd.recuperer_info_event_basic(id_event)
    nouvelle_equipe_id = request.form.get('id_equipe')
    if nouvelle_equipe_id == "": nouvelle_equipe_id = None
    
    autorise = False
    if infos['role'] == 'Administrateur': autorise = True
    elif infos['role'] == "Chef d'équipe":
        if eq_event_actuelle == infos['id_equipe'] and eq_event_actuelle is not None:
            autorise = True
            nouvelle_equipe_id = infos['id_equipe']

    if autorise:
        res = bdd.modifier_infos_evenement(id_event, request.form['titre'], request.form['description'], request.form['date_debut'], request.form['date_fin'], nouvelle_equipe_id, session['user_id'])
        if res == "Conflit": flash("⚠️ Conflit d'horaire !")
        elif res == "OK": flash("Événement modifié !")
    else: flash("⛔ Modification interdite.")
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/supprimer_evenement_complet/<int:id_event>', methods=['POST'])
def supprimer_evenement_complet(id_agenda, id_event):
    if 'user_id' not in session: return redirect(url_for('login'))
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    eq_event = bdd.recuperer_info_event_basic(id_event)
    autorise = False
    if infos['role'] == 'Administrateur': autorise = True
    elif infos['role'] == "Chef d'équipe" and eq_event == infos['id_equipe']: autorise = True
    if autorise: 
        bdd.supprimer_evenement(id_event)
        flash("Supprimé.")
    else: flash("⛔ Interdit")
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

# ==========================================
# 5. API JSON
# ==========================================
@app.route('/api/events/<int:id_agenda>')
def api_get_events(id_agenda):
    if 'user_id' not in session: return jsonify([])
    infos = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    raw_events = bdd.recuperer_evenements_filtres(id_agenda, infos['role'], infos['id_equipe'])
    json_events = []
    for ev in raw_events:
        is_editable = False
        if infos['role'] == 'Administrateur': is_editable = True
        elif infos['role'] == 'Chef d\'équipe' and ev[5]: is_editable = True 
        json_events.append({
            'id': ev[0], 'title': ev[1], 'start': ev[2].isoformat(), 'end': ev[3].isoformat(),
            'backgroundColor': ev[5] or '#6c757d', 'borderColor': ev[5] or '#6c757d',
            'description': ev[6], 'editable': is_editable, 'extendedProps': { 'equipe': ev[4] or 'Général' }
        })
    return jsonify(json_events)

@app.route('/api/move_event', methods=['POST'])
def api_move_event():
    if 'user_id' not in session: return jsonify({'status': 'error'})
    data = request.json
    res = bdd.modifier_dates_evenement(data['id'], data['start'][:16].replace('T', ' '), data['end'][:16].replace('T', ' '), session['user_id'])
    if res == "OK": 
        # UDP] Log très rapide du mouvement
        envoyer_udp_rapide(f"MOUVEMENT: Ticket {data['id']} déplacé par User {session['user_id']}")
        return jsonify({'status': 'ok'})
    elif res == "Conflit": return jsonify({'status': 'conflict', 'message': 'Conflit.'})
    return jsonify({'status': 'error'})

@app.route('/api/historique/<int:id_agenda>/<int:id_event>')
def api_get_historique(id_agenda, id_event):
    if 'user_id' not in session: return jsonify({'status': 'error'})
    infos_moi = bdd.recuperer_infos_membre(session['user_id'], id_agenda)
    equipe_event = bdd.recuperer_info_event_basic(id_event)
    droit_acces = False
    if infos_moi['role'] == 'Administrateur': droit_acces = True
    elif infos_moi['role'] == 'Chef d\'équipe' and equipe_event == infos_moi['id_equipe']: droit_acces = True
    if not droit_acces: return jsonify({'status': 'forbidden', 'data': []})
    historique = bdd.recuperer_historique(id_event)
    data = []
    for h in historique: data.append({'action': h[0], 'details': h[1], 'date': h[2], 'auteur': h[3]})
    return jsonify({'status': 'ok', 'data': data})

if __name__ == '__main__':
    app.run(debug=True)
