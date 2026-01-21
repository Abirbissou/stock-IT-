import sqlite3
import os
import hashlib

print("\n" + "="*60)
print("CREATION BASE DE DONNEES - TOUTES LES AGENCES PUBLICIS")
print("="*60 + "\n")

db_dir = os.path.join(os.path.dirname(__file__), '..', 'database')
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'stock_it.db')

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("CREATE TABLE agences (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE NOT NULL, code TEXT UNIQUE NOT NULL, adresse TEXT, actif BOOLEAN DEFAULT 1, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
cursor.execute("CREATE TABLE articles (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE NOT NULL, categorie TEXT NOT NULL, reference TEXT, description TEXT, actif BOOLEAN DEFAULT 1, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
cursor.execute("CREATE TABLE stock (id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER NOT NULL, agence_id INTEGER NOT NULL, quantite INTEGER DEFAULT 0, stock_min INTEGER DEFAULT 5, derniere_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (article_id) REFERENCES articles(id), FOREIGN KEY (agence_id) REFERENCES agences(id), UNIQUE(article_id, agence_id))")
cursor.execute("CREATE TABLE demandes (id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_servicenow TEXT NOT NULL, agence_id INTEGER NOT NULL, article_id INTEGER NOT NULL, client_nom TEXT NOT NULL, client_email TEXT, quantite INTEGER NOT NULL, statut TEXT DEFAULT 'en_attente', date_demande TIMESTAMP DEFAULT CURRENT_TIMESTAMP, date_validation TIMESTAMP, valide_par TEXT, commentaire TEXT, FOREIGN KEY (agence_id) REFERENCES agences(id), FOREIGN KEY (article_id) REFERENCES articles(id))")
cursor.execute("CREATE TABLE historique (id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER NOT NULL, agence_id INTEGER NOT NULL, type_mouvement TEXT NOT NULL, quantite INTEGER NOT NULL, stock_avant INTEGER NOT NULL, stock_apres INTEGER NOT NULL, demande_id INTEGER, utilisateur TEXT, commentaire TEXT, date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (article_id) REFERENCES articles(id), FOREIGN KEY (agence_id) REFERENCES agences(id), FOREIGN KEY (demande_id) REFERENCES demandes(id))")
cursor.execute("CREATE TABLE utilisateurs (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, nom TEXT NOT NULL, prenom TEXT NOT NULL, role TEXT DEFAULT 'user', actif BOOLEAN DEFAULT 1, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

print("Tables creees !\n")

print("Insertion agences...")
agences = [
    ('Publicis Conseil', 'CONSEIL', 'Site 145'),
    ('Marcel', 'MARCEL', 'Site 145'),
    ('Leo Burnett', 'LEO_BURNETT', 'Site 145'),
    ('Saatchi & Saatchi', 'SAATCHI', 'Site 145'),
    ('Publicis Consultants', 'CONSULTANTS', 'Site 145'),
    ('Publicis Live', 'LIVE', 'Site 145'),
    ('Carré Noir', 'CARRE_NOIR', 'Site 145'),
    ('Publicis Luxe', 'LUXE', 'Site 133'),
    ('Prodigious', 'PRODIGIOUS', 'Site 145'),
    ('Razorfish', 'RAZORFISH', 'Site 145'),
    ('BBH', 'BBH', 'Site 145'),
    ('LePub', 'LEPUB', 'Site 145'),
    ('Fallon', 'FALLON', 'Site 145'),
    ('MSL', 'MSL', 'Site 145'),
    ('Starcom', 'STARCOM', 'Site 133'),
    ('Zenith', 'ZENITH', 'Site 133'),
    ('Spark Foundry', 'SPARK_FOUNDRY', 'Site 133'),
    ('Blue449', 'BLUE449', 'Site 133'),
    ('Performics', 'PERFORMICS', 'Site 133'),
    ('Publicis Media', 'MEDIA', 'Site 133'),
    ('Epsilon', 'EPSILON', 'Site 145'),
    ('Conversant', 'CONVERSANT', 'Site 145'),
    ('Publicis Sapient', 'SAPIENT', 'Site 145'),
    ('Publicis Health', 'HEALTH', 'Site 145'),
    ('Publicis Activ', 'ACTIV', 'Site 145'),
    ('Digitas', 'DIGITAS', 'Site 145'),
    ('Publicis ReSources', 'RESOURCES', 'Site 145'),
]
cursor.executemany("INSERT INTO agences (nom, code, adresse) VALUES (?, ?, ?)", agences)
print(f"{len(agences)} agences ajoutees\n")

print("Insertion articles...")
articles = [
    ('Casque Jabra', 'Audio', 'CASQUE-001', 'Casque audio'),
    ('Souris filaire', 'Peripherique', 'SOURIS-001', 'Souris USB'),
    ('Souris sans fil', 'Peripherique', 'SOURIS-002', 'Souris Bluetooth'),
    ('Souris ergonomique', 'Peripherique', 'SOURIS-003', 'Souris verticale'),
    ('Magic Mouse', 'Peripherique', 'SOURIS-004', 'Apple Magic Mouse'),
    ('Magic Keyboard', 'Peripherique', 'CLAVIER-001', 'Apple Magic Keyboard'),
    ('Clavier Mac sans fil', 'Peripherique', 'CLAVIER-002', 'Clavier sans fil Mac'),
    ('Clavier filaire', 'Peripherique', 'CLAVIER-003', 'Clavier USB'),
    ('Housse 14"', 'Protection', 'HOUSSE-001', 'Housse 14 pouces'),
    ('Housse 16"', 'Protection', 'HOUSSE-002', 'Housse 16 pouces'),
    ('Hub USB-C', 'Connectique', 'HUB-001', 'Hub multi-ports'),
    ('Dock USB DICOTA', 'Connectique', 'DOCK-001', 'Station accueil'),
    ('Chargeur 65W', 'Alimentation', 'CHARGEUR-001', 'Chargeur 65W'),
    ('Chargeur 70W', 'Alimentation', 'CHARGEUR-002', 'Chargeur Apple 70W'),
    ('Chargeur 140W', 'Alimentation', 'CHARGEUR-003', 'Chargeur Apple 140W'),
    ('Cable USB-C', 'Connectique', 'CABLE-001', 'Cable USB-C 2m'),
    ('Cable HDMI', 'Connectique', 'CABLE-003', 'Cable HDMI'),
    ('Tablette Wacom', 'Creation', 'WACOM-001', 'Tablette graphique'),
    ('Ecran confidentialite', 'Protection', 'FILTRE-001', 'Filtre confidentialite'),
    ('Sacoche', 'Transport', 'SACOCHE-001', 'Sacoche ordinateur'),
    ('Tapis souris ergonomique', 'Ergonomie', 'TAPIS-001', 'Tapis avec repose-poignet'),
    ('Bloc multiprise', 'Electricite', 'BLOC-001', 'Bloc multiprise USB'),
]
cursor.executemany("INSERT INTO articles (nom, categorie, reference, description) VALUES (?, ?, ?, ?)", articles)
print(f"{len(articles)} articles ajoutes\n")

print("Initialisation stock...")
cursor.execute("SELECT id FROM agences")
agences_ids = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT id FROM articles")
articles_ids = [row[0] for row in cursor.fetchall()]

stock_data = []
for agence_id in agences_ids:
    for article_id in articles_ids:
        stock_data.append((article_id, agence_id, 0, 5))

cursor.executemany("INSERT INTO stock (article_id, agence_id, quantite, stock_min) VALUES (?, ?, ?, ?)", stock_data)
print(f"{len(stock_data)} lignes de stock\n")

print("Creation utilisateur...")
password_hash = hashlib.sha256("admin123".encode()).hexdigest()
cursor.execute("INSERT INTO utilisateurs (email, password_hash, nom, prenom, role) VALUES (?, ?, ?, ?, ?)", ('abir@publicis.com', password_hash, 'GUEBBACHE', 'Abir', 'admin'))
print("Utilisateur cree : abir@publicis.com / admin123\n")

conn.commit()
conn.close()

print("="*60)
print("BASE DE DONNEES CREEE AVEC SUCCES !")
print(f"{len(agences)} agences - {len(articles)} articles")
print("="*60 + "\n")
