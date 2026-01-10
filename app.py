from flask import Flask, render_template, request, redirect, url_for, session, flash
from agenda_collab import BaseDeDonnees

app = Flask(__name__)
app.secret_key = 'Aqwzsx12!'

# On crée une instance de connexion
bdd = BaseDeDonnees()

@app.route('/')
def index():
    # Protection : Si pas connecté, on renvoie au login
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # On récupère les données depuis PostgreSQL
    mes_agendas = bdd.recuperer_agendas_utilisateur(session['user_id'])
    
    return render_template('dashboard.html', 
                           pseudo=session['pseudo'], 
                           agendas=mes_agendas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pseudo = request.form['pseudo']
        password = request.form['password']
        
        # On interroge PostgreSQL
        user = bdd.verifier_connexion(pseudo, password)
        
        if user:
            # user contient (id, nom, prenom)
            session['user_id'] = user[0]
            session['pseudo'] = user[1]
            return redirect(url_for('index'))
        else:
            flash("Identifiant ou mot de passe incorrect")
            
    return render_template('login.html', mode='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        pseudo = request.form['pseudo']
        password = request.form['password']
        # On met un prénom par défaut pour l'instant
        bdd.ajouter_utilisateur(pseudo, "User", password)
        flash("Compte créé avec succès !")
        return redirect(url_for('login'))
        
    return render_template('login.html', mode='register')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
    
@app.route('/nouveau_agenda', methods=['POST'])
def nouveau_agenda():
    # 1. Vérifier si on est connecté
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # 2. Récupérer le nom écrit dans le formulaire
    nom = request.form['nom_agenda']
    
    # 3. Appeler la BDD pour créer l'agenda
    # (Cette méthode doit exister dans agenda_collab.py)
    bdd.creer_agenda(nom, session['user_id'])
    
    # 4. Revenir au dashboard
    flash("Agenda créé avec succès !")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
