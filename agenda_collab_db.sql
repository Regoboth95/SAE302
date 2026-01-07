-- 1. Création d'un Rôle de connexion pour votre application Python
-- On évite d'utiliser le superuser 'postgres' dans le code Python par sécurité.
CREATE ROLE app_agenda_user LOGIN PASSWORD 'Azerty@123';

-- 2. Création de la base de données (si elle n'existe pas déjà)
CREATE DATABASE agenda_collaboratif OWNER app_agenda_user;

-- \c agenda_collaboratif -- (Commande pour se connecter à la base si vous êtes dans psql)

-- 3. Création d'un Schéma pour organiser proprement nos tables
CREATE SCHEMA gestion_agenda AUTHORIZATION app_agenda_user;

-- 4. Création des Tables dans le schéma 'gestion_agenda'
-- Note : On utilise SERIAL pour l'auto-incrémentation PostgreSQL

-- Table Rôle (Rôles fonctionnels de l'appli : Admin, Chef d'équipe...)
CREATE TABLE gestion_agenda.ROLE (
    id_role SERIAL PRIMARY KEY,
    libelle VARCHAR(50) NOT NULL UNIQUE
);

-- Table Utilisateur
CREATE TABLE gestion_agenda.UTILISATEUR (
    id_user SERIAL PRIMARY KEY, -- Correspond à 'id_usu' de votre schéma
    nom VARCHAR(50) NOT NULL,   -- [cite: 277]
    prenom VARCHAR(50) NOT NULL,
    mot_de_passe VARCHAR(255) NOT NULL
);

-- Table Agenda
CREATE TABLE gestion_agenda.AGENDA (
    id_agenda SERIAL PRIMARY KEY,
    nom_agenda VARCHAR(100) NOT NULL,
    id_createur INT NOT NULL,
    -- Clé étrangère vers Utilisateur
    FOREIGN KEY (id_createur) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE CASCADE
);

-- Table Equipe
CREATE TABLE gestion_agenda.EQUIPE (
    id_equipe SERIAL PRIMARY KEY,
    nom_equipe VARCHAR(100) NOT NULL,
    code_couleur VARCHAR(7) NOT NULL, -- Ex: #FF0000
    id_agenda INT NOT NULL,
    FOREIGN KEY (id_agenda) REFERENCES gestion_agenda.AGENDA(id_agenda) ON DELETE CASCADE
);

-- Table Participation (Liaison)
CREATE TABLE gestion_agenda.PARTICIPATION (
    id_role INT NOT NULL,
    id_user INT NOT NULL,
    id_agenda INT NOT NULL,
    id_equipe_managee INT, -- NULLABLE (Vide si pas chef d'équipe)
    
    PRIMARY KEY (id_user, id_agenda),
    FOREIGN KEY (id_role) REFERENCES gestion_agenda.ROLE(id_role),
    FOREIGN KEY (id_user) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_agenda) REFERENCES gestion_agenda.AGENDA(id_agenda) ON DELETE CASCADE,
    FOREIGN KEY (id_equipe_managee) REFERENCES gestion_agenda.EQUIPE(id_equipe)
);

-- Table Ticket
CREATE TABLE gestion_agenda.TICKET (
    id_ticket SERIAL PRIMARY KEY,
    titre VARCHAR(100) NOT NULL,
    description TEXT,
    date_debut TIMESTAMP NOT NULL, -- TIMESTAMP pour PostgreSQL
    date_fin TIMESTAMP NOT NULL,
    id_agenda INT NOT NULL,
    id_equipe INT NOT NULL,
    
    FOREIGN KEY (id_agenda) REFERENCES gestion_agenda.AGENDA(id_agenda) ON DELETE CASCADE,
    FOREIGN KEY (id_equipe) REFERENCES gestion_agenda.EQUIPE(id_equipe)
);

-- 5. Attribution des droits (GRANT)
-- On s'assure que notre utilisateur Python a bien le droit de tout faire dans ce schéma
GRANT USAGE, CREATE ON SCHEMA gestion_agenda TO app_agenda_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA gestion_agenda TO app_agenda_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA gestion_agenda TO app_agenda_user; -- Pour les SERIAL

-- Insertion des rôles de base
INSERT INTO gestion_agenda.ROLE (libelle) VALUES ('Administrateur'), ('Collaborateur'), ('Chef d''équipe');