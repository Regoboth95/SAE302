-- =============================================================================
-- SCRIPT DE CRÉATION DE LA BDD - AGENDA COLLABORATIF (V1 - VALIDÉE)
-- Comprend : Utilisateurs, Agendas, Équipes, Événements (Calendrier)
-- =============================================================================

-- 1. Configuration du schéma
CREATE SCHEMA IF NOT EXISTS gestion_agenda;

-- Nettoyage (DROP) pour repartir à zéro si on relance le script
DROP TABLE IF EXISTS gestion_agenda.EVENEMENT CASCADE;
DROP TABLE IF EXISTS gestion_agenda.PARTICIPATION CASCADE;
DROP TABLE IF EXISTS gestion_agenda.EQUIPE CASCADE;
DROP TABLE IF EXISTS gestion_agenda.AGENDA CASCADE;
DROP TABLE IF EXISTS gestion_agenda.ROLE CASCADE;
DROP TABLE IF EXISTS gestion_agenda.UTILISATEUR CASCADE;

-- 2. Table UTILISATEUR
CREATE TABLE gestion_agenda.UTILISATEUR (
    id_user SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    mot_de_passe VARCHAR(100) NOT NULL
);

-- 3. Table ROLE
CREATE TABLE gestion_agenda.ROLE (
    id_role SERIAL PRIMARY KEY,
    libelle VARCHAR(50) UNIQUE NOT NULL
);

-- Insertion des rôles imposés par le cahier des charges
INSERT INTO gestion_agenda.ROLE (libelle) VALUES ('Administrateur');
INSERT INTO gestion_agenda.ROLE (libelle) VALUES ('Chef d''équipe');
INSERT INTO gestion_agenda.ROLE (libelle) VALUES ('Collaborateur');

-- 4. Table AGENDA
CREATE TABLE gestion_agenda.AGENDA (
    id_agenda SERIAL PRIMARY KEY,
    nom_agenda VARCHAR(100) NOT NULL,
    id_createur INT NOT NULL,
    FOREIGN KEY (id_createur) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE CASCADE
);

-- 5. Table ÉQUIPE (Nouvelle !)
CREATE TABLE gestion_agenda.EQUIPE (
    id_equipe SERIAL PRIMARY KEY,
    nom_equipe VARCHAR(50) NOT NULL,
    couleur_equipe VARCHAR(7) DEFAULT '#0d6efd', -- Stocke le code couleur Hexa (ex: #FF0000)
    id_agenda INT NOT NULL,
    FOREIGN KEY (id_agenda) REFERENCES gestion_agenda.AGENDA(id_agenda) ON DELETE CASCADE
);

-- 6. Table PARTICIPATION (Lien User <-> Agenda <-> Role <-> Equipe)
CREATE TABLE gestion_agenda.PARTICIPATION (
    id_user INT NOT NULL,
    id_agenda INT NOT NULL,
    id_role INT NOT NULL,
    id_equipe INT, -- Un utilisateur peut appartenir à une équipe (optionnel au début)
    
    PRIMARY KEY (id_user, id_agenda),
    
    FOREIGN KEY (id_user) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_agenda) REFERENCES gestion_agenda.AGENDA(id_agenda) ON DELETE CASCADE,
    FOREIGN KEY (id_role) REFERENCES gestion_agenda.ROLE(id_role) ON DELETE RESTRICT,
    FOREIGN KEY (id_equipe) REFERENCES gestion_agenda.EQUIPE(id_equipe) ON DELETE SET NULL
);

-- 7. Table EVENEMENT (Remplace les Tâches pour le mode Calendrier)
CREATE TABLE gestion_agenda.EVENEMENT (
    id_event SERIAL PRIMARY KEY,
    titre VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Gestion des plages horaires (ex: Lundi 14h00 à 16h00)
    date_debut TIMESTAMP NOT NULL,
    date_fin TIMESTAMP NOT NULL,
    
    id_agenda INT NOT NULL,
    id_equipe_concernee INT, -- L'événement est lié à une équipe (pour la couleur)
    id_createur INT,

    FOREIGN KEY (id_agenda) REFERENCES gestion_agenda.AGENDA(id_agenda) ON DELETE CASCADE,
    FOREIGN KEY (id_equipe_concernee) REFERENCES gestion_agenda.EQUIPE(id_equipe) ON DELETE SET NULL,
    FOREIGN KEY (id_createur) REFERENCES gestion_agenda.UTILISATEUR(id_user) ON DELETE SET NULL
);

-- Fin du script
