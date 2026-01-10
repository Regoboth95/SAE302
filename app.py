from flask import Flask, render_template, request, redirect, url_for, session, flash
from agenda_collab import BaseDeDonnees

app = Flask(__name__)
app.secret_key = 'cle_secrete_projet_agenda'

bdd = BaseDeDonnees()

# --- ACCUEIL & LOGIN ---
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
        flash("Erreur : Ce pseudo est déjà pris.")
    return render_template('login.html', mode='register')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/nouveau_agenda', methods=['POST'])
def nouveau_agenda():
    if 'user_id' in session:
        bdd.creer_agenda(request.form['nom_agenda'], session['user_id'])
        flash("Agenda créé avec succès !")
    return redirect(url_for('index'))

# --- VUE AGENDA SÉCURISÉE ---
@app.route('/agenda/<int:id_agenda>')
def voir_agenda(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Récupération du rôle pour sécuriser l'affichage
    mon_role = bdd.recuperer_role_user(session['user_id'], id_agenda)
    
    return render_template('agenda.html', 
                           id_agenda=id_agenda, 
                           equipes=bdd.recuperer_equipes(id_agenda), 
                           evenements=bdd.recuperer_evenements(id_agenda),
                           membres=bdd.recuperer_participants(id_agenda),
                           mon_role=mon_role)

@app.route('/agenda/<int:id_agenda>/nouvelle_equipe', methods=['POST'])
def nouvelle_equipe(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # SÉCURITÉ : Admin seulement
    role = bdd.recuperer_role_user(session['user_id'], id_agenda)
    if role != 'Administrateur':
        flash("⛔ Accès refusé : Seul l'Administrateur peut créer des équipes.")
        return redirect(url_for('voir_agenda', id_agenda=id_agenda))
    
    bdd.creer_equipe(request.form['nom_equipe'], request.form['couleur_equipe'], id_agenda)
    flash("Équipe ajoutée !")
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/nouvel_evenement', methods=['POST'])
def nouvel_evenement(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # SÉCURITÉ : Pas de Collaborateur
    role = bdd.recuperer_role_user(session['user_id'], id_agenda)
    if role == 'Collaborateur':
        flash("⛔ Accès refusé : Les collaborateurs ne peuvent pas créer d'événements.")
        return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    id_equipe = request.form.get('id_equipe')
    if id_equipe == "": id_equipe = None
    
    res = bdd.ajouter_evenement(request.form['titre'], request.form['description'], 
                                request.form['date_debut'], request.form['date_fin'], 
                                id_agenda, id_equipe, session['user_id'])
    
    if res == "OK": flash("Événement ajouté !")
    elif res == "ConflitDetecte": flash("⚠️ IMPOSSIBLE : Cette équipe est déjà occupée sur ce créneau !")
    else: flash("Erreur technique.")
    
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/inviter_membre', methods=['POST'])
def inviter_membre(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # SÉCURITÉ : Admin seulement
    role = bdd.recuperer_role_user(session['user_id'], id_agenda)
    if role != 'Administrateur':
        flash("⛔ Accès refusé.")
        return redirect(url_for('voir_agenda', id_agenda=id_agenda))

    res = bdd.ajouter_membre(id_agenda, request.form['pseudo_invite'], request.form['role_invite'])
    if res == "OK": flash("Membre invité !")
    elif res == "UserIntrouvable": flash("Utilisateur introuvable.")
    elif res == "DejaMembre": flash("Déjà membre.")
    else: flash("Erreur technique.")
    
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

if __name__ == '__main__':
    app.run(debug=True)
