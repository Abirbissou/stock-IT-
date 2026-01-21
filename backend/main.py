from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import hashlib
import os

app = FastAPI(title="Stock IT Publicis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'stock_it.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class LoginRequest(BaseModel):
    email: str
    password: str

class DemandeCreate(BaseModel):
    ticket_servicenow: str
    agence_id: int
    article_id: int
    client_nom: str
    client_email: Optional[str] = None
    quantite: int
    commentaire: Optional[str] = None

class StockUpdate(BaseModel):
    article_id: int
    agence_id: int
    quantite: int
    commentaire: Optional[str] = None

@app.on_event("startup")
async def startup():
    print("\nAPI STOCK IT DEMARREE")
    print("API : http://localhost:8000")
    print("Docs : http://localhost:8000/docs\n")

@app.get("/")
def root():
    return {"message": "API Stock IT Publicis", "version": "2.0", "status": "online"}

@app.post("/api/login")
def login(credentials: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    password_hash = hash_password(credentials.password)
    cursor.execute("SELECT id, email, nom, prenom, role FROM utilisateurs WHERE email = ? AND password_hash = ? AND actif = 1", (credentials.email, password_hash))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    return {"success": True, "user": {"id": user[0], "email": user[1], "nom": user[2], "prenom": user[3], "role": user[4]}}

@app.get("/api/agences")
def get_agences():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, code, adresse FROM agences WHERE actif = 1 ORDER BY nom")
    agences = [{"id": row[0], "nom": row[1], "code": row[2], "adresse": row[3]} for row in cursor.fetchall()]
    conn.close()
    return {"agences": agences}

@app.get("/api/articles")
def get_articles():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, categorie, reference, description FROM articles WHERE actif = 1 ORDER BY categorie, nom")
    articles = [{"id": row[0], "nom": row[1], "categorie": row[2], "reference": row[3], "description": row[4]} for row in cursor.fetchall()]
    conn.close()
    return {"articles": articles}

@app.get("/api/stock")
def get_stock():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT s.id, ag.id as agence_id, ag.nom as agence_nom, ag.code as agence_code, ag.adresse as agence_site, ar.id as article_id, ar.nom as article_nom, ar.categorie, s.quantite, s.stock_min, s.derniere_maj FROM stock s JOIN agences ag ON s.agence_id = ag.id JOIN articles ar ON s.article_id = ar.id WHERE ag.actif = 1 AND ar.actif = 1 ORDER BY ag.nom, ar.categorie, ar.nom")
    stock = [{"id": row[0], "agence_id": row[1], "agence_nom": row[2], "agence_code": row[3], "agence_site": row[4], "article_id": row[5], "article_nom": row[6], "categorie": row[7], "quantite": row[8], "stock_min": row[9], "derniere_maj": row[10], "alerte": row[8] < row[9]} for row in cursor.fetchall()]
    conn.close()
    return {"stock": stock}

@app.post("/api/stock/update")
def update_stock(data: StockUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT quantite FROM stock WHERE article_id = ? AND agence_id = ?", (data.article_id, data.agence_id))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Stock non trouve")
    stock_avant = result[0]
    stock_apres = stock_avant + data.quantite
    if stock_apres < 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Stock insuffisant")
    cursor.execute("UPDATE stock SET quantite = ?, derniere_maj = CURRENT_TIMESTAMP WHERE article_id = ? AND agence_id = ?", (stock_apres, data.article_id, data.agence_id))
    type_mouvement = "entree" if data.quantite > 0 else "sortie"
    cursor.execute("INSERT INTO historique (article_id, agence_id, type_mouvement, quantite, stock_avant, stock_apres, commentaire) VALUES (?, ?, ?, ?, ?, ?, ?)", (data.article_id, data.agence_id, type_mouvement, abs(data.quantite), stock_avant, stock_apres, data.commentaire))
    conn.commit()
    conn.close()
    return {"success": True, "stock_avant": stock_avant, "stock_apres": stock_apres, "message": f"Stock mis a jour : {stock_avant} -> {stock_apres}"}

@app.get("/api/demandes")
def get_demandes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT d.id, d.ticket_servicenow, ag.nom as agence_nom, ar.nom as article_nom, d.client_nom, d.client_email, d.quantite, d.statut, d.date_demande, d.date_validation, d.valide_par, d.commentaire FROM demandes d JOIN agences ag ON d.agence_id = ag.id JOIN articles ar ON d.article_id = ar.id ORDER BY d.date_demande DESC")
    demandes = [{"id": row[0], "ticket_servicenow": row[1], "agence_nom": row[2], "article_nom": row[3], "client_nom": row[4], "client_email": row[5], "quantite": row[6], "statut": row[7], "date_demande": row[8], "date_validation": row[9], "valide_par": row[10], "commentaire": row[11]} for row in cursor.fetchall()]
    conn.close()
    return {"demandes": demandes}

@app.post("/api/demandes/create")
def create_demande(demande: DemandeCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM agences WHERE id = ?", (demande.agence_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Agence non trouvee")
    cursor.execute("SELECT id FROM articles WHERE id = ?", (demande.article_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Article non trouve")
    cursor.execute("INSERT INTO demandes (ticket_servicenow, agence_id, article_id, client_nom, client_email, quantite, commentaire) VALUES (?, ?, ?, ?, ?, ?, ?)", (demande.ticket_servicenow, demande.agence_id, demande.article_id, demande.client_nom, demande.client_email, demande.quantite, demande.commentaire))
    demande_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "demande_id": demande_id, "message": "Demande creee avec succes"}

@app.post("/api/demandes/{demande_id}/valider")
def valider_demande(demande_id: int, utilisateur: str = "admin"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT agence_id, article_id, quantite, statut FROM demandes WHERE id = ?", (demande_id,))
    demande = cursor.fetchone()
    if not demande:
        conn.close()
        raise HTTPException(status_code=404, detail="Demande non trouvee")
    if demande[3] != "en_attente":
        conn.close()
        raise HTTPException(status_code=400, detail="Demande deja traitee")
    agence_id, article_id, quantite = demande[0], demande[1], demande[2]
    cursor.execute("SELECT quantite FROM stock WHERE article_id = ? AND agence_id = ?", (article_id, agence_id))
    stock = cursor.fetchone()
    if not stock or stock[0] < quantite:
        conn.close()
        raise HTTPException(status_code=400, detail="Stock insuffisant")
    stock_avant = stock[0]
    stock_apres = stock_avant - quantite
    cursor.execute("UPDATE stock SET quantite = ?, derniere_maj = CURRENT_TIMESTAMP WHERE article_id = ? AND agence_id = ?", (stock_apres, article_id, agence_id))
    cursor.execute("UPDATE demandes SET statut = 'validee', date_validation = CURRENT_TIMESTAMP, valide_par = ? WHERE id = ?", (utilisateur, demande_id))
    cursor.execute("INSERT INTO historique (article_id, agence_id, type_mouvement, quantite, stock_avant, stock_apres, demande_id, utilisateur) VALUES (?, ?, 'demande', ?, ?, ?, ?, ?)", (article_id, agence_id, quantite, stock_avant, stock_apres, demande_id, utilisateur))
    conn.commit()
    conn.close()
    return {"success": True, "stock_avant": stock_avant, "stock_apres": stock_apres, "message": "Demande validee et stock mis a jour"}

@app.get("/api/stats")
def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM agences WHERE actif = 1")
    total_agences = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM articles WHERE actif = 1")
    total_articles = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM demandes")
    total_demandes = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM demandes WHERE statut = 'en_attente'")
    demandes_attente = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM stock WHERE quantite < stock_min")
    alertes_stock = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(quantite) FROM stock")
    total_items = cursor.fetchone()[0] or 0
    conn.close()
    return {"total_agences": total_agences, "total_articles": total_articles, "total_demandes": total_demandes, "demandes_attente": demandes_attente, "alertes_stock": alertes_stock, "total_items": total_items}

@app.get("/api/historique")
def get_historique(limit: int = 50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT h.id, ag.nom as agence_nom, ar.nom as article_nom, h.type_mouvement, h.quantite, h.stock_avant, h.stock_apres, h.utilisateur, h.commentaire, h.date_mouvement FROM historique h JOIN agences ag ON h.agence_id = ag.id JOIN articles ar ON h.article_id = ar.id ORDER BY h.date_mouvement DESC LIMIT ?", (limit,))
    historique = [{"id": row[0], "agence_nom": row[1], "article_nom": row[2], "type_mouvement": row[3], "quantite": row[4], "stock_avant": row[5], "stock_apres": row[6], "utilisateur": row[7], "commentaire": row[8], "date_mouvement": row[9]} for row in cursor.fetchall()]
    conn.close()
    return {"historique": historique}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
