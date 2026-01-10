from flask import Flask, render_template, request, redirect, url_for, session, flash
from agenda_collab import BaseDeDonnees

app = Flask(__name__)
app.secret_key = 'cle_secrete_projet_agenda'

bdd = BaseDeDonnees()

# --- ACCUEIL & LOGIN ---
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    agendas = bdd.recuperer_agendas_utilisateur(session['user_id'])
    return render_template('dashboard.html', pseudo=session['pseudo'], agendas=agendas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pseudo = request.form['pseudo']
        password = request.form['password']
        
        user = bdd.verifier_connexion(pseudo, password)
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
        pseudo = request.form['pseudo']
        password = request.form['password']
        
        try:
            new_id = bdd.ajouter_utilisateur(pseudo, "User", password)
            if new_id:
                flash("Compte créé avec succès ! Connectez-vous.")
                return redirect(url_for('login'))
        except:
            flash("Erreur : Ce pseudo est peut-être déjà pris.")
            
    return render_template('login.html', mode='register')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- AGENDAS ---
@app.route('/nouveau_agenda', methods=['POST'])
def nouveau_agenda():
    if 'user_id' in session:
        nom = request.form['nom_agenda']
        bdd.creer_agenda(nom, session['user_id'])
        flash("Agenda créé avec succès !")
    return redirect(url_for('index'))

# --- VUE CALENDRIER & ÉQUIPES (V1 COMPLETE) ---
@app.route('/agenda/<int:id_agenda>')
def voir_agenda(id_agenda):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 1. Équipes
    equipes = bdd.recuperer_equipes(id_agenda)
    # 2. Événements
    evenements = bdd.recuperer_evenements(id_agenda)
    # 3. Participants (Nouveau !)
    membres = bdd.recuperer_participants(id_agenda)
    
    return render_template('agenda.html', 
                           id_agenda=id_agenda, 
                           equipes=equipes, 
                           evenements=evenements,
                           membres=membres)

@app.route('/agenda/<int:id_agenda>/nouvelle_equipe', methods=['POST'])
def nouvelle_equipe(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    nom = request.form['nom_equipe']
    couleur = request.form['couleur_equipe']
    
    bdd.creer_equipe(nom, couleur, id_agenda)
    flash("Équipe ajoutée !")
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

@app.route('/agenda/<int:id_agenda>/nouvel_evenement', methods=['POST'])
def nouvel_evenement(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    titre = request.form['titre']
    desc = request.form['description']
    debut = request.form['date_debut']
    fin = request.form['date_fin']
    id_equipe = request.form.get('id_equipe') 
    
    if id_equipe == "":
        id_equipe = None
    
    bdd.ajouter_evenement(titre, desc, debut, fin, id_agenda, id_equipe, session['user_id'])
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

# --- ROUTE INVITATION (NOUVEAU) ---
@app.route('/agenda/<int:id_agenda>/inviter_membre', methods=['POST'])
def inviter_membre(id_agenda):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    pseudo = request.form['pseudo_invite']
    role = request.form['role_invite']
    
    resultat = bdd.ajouter_membre(id_agenda, pseudo, role)
    
    if resultat == "OK":
        flash(f"{pseudo} a été ajouté en tant que {role} !")
    elif resultat == "UserIntrouvable":
        flash(f"Erreur : L'utilisateur '{pseudo}' n'existe pas.")
    elif resultat == "DejaMembre":
        flash(f"Erreur : {pseudo} est déjà dans l'agenda.")
    else:
        flash("Erreur lors de l'invitation.")
        
    return redirect(url_for('voir_agenda', id_agenda=id_agenda))

if __name__ == '__main__':
    app.run(debug=True)
