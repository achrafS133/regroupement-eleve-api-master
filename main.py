from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Eleve, Groupe
from schemas import EleveCreate, Eleve as EleveSchema, Groupe as GroupeSchema
from services import generate_groups, generate_groups_dbscan
from config import DEFAULT_GROUP_SIZE
from init_data import init_data
from sklearn.cluster import KMeans
import numpy as np

# ---------------------- #
# 🔹 Initialisation base #
# ---------------------- #

Base.metadata.create_all(bind=engine)

# Insère les élèves de test si nécessaire
db = SessionLocal()
init_data(db)
db.close()

# ---------------------- #
# 🔹 Création FastAPI     #
# ---------------------- #

app = FastAPI(title="Microservice Groupement d'Élèves")

group_size = DEFAULT_GROUP_SIZE  # Taille du groupe par défaut


# ---------------------- #
# 🔹 Dépendance DB       #
# ---------------------- #

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------- #
# 🔹 Route d'accueil      #
# ---------------------- #

@app.get("/")
def root():
    return {
        "message": "Bienvenue dans le microservice de groupement d'élèves 👋",
        "endpoints": [
            "/groups/generate",
            "/groups",
            "/groups/{id}",
            "/config",
            "/groups/pickup-points"
        ]
    }


@app.get("/health")
def health():
    """Simple health endpoint for Docker healthchecks and monitoring."""
    return {"status": "ok"}


# ---------------------- #
# 🔹 Endpoints principaux #
# ---------------------- #

@app.post("/groups/generate", response_model=list[GroupeSchema])
def generate(db: Session = Depends(get_db)):
    groupes = generate_groups(db, group_size)
    return groupes


# ---------------------- #
# 🔹 Endpoints élèves     #
# ---------------------- #


@app.post("/students", response_model=EleveSchema)
def create_student(eleve: EleveCreate, db: Session = Depends(get_db)):
    """Ajoute un élève à la base."""
    new_eleve = Eleve(nom=eleve.nom, latitude=eleve.latitude, longitude=eleve.longitude)
    db.add(new_eleve)
    db.commit()
    db.refresh(new_eleve)
    return new_eleve


@app.get("/students", response_model=list[EleveSchema])
def get_students(db: Session = Depends(get_db)):
    return db.query(Eleve).all()


@app.get("/students/{id}", response_model=EleveSchema)
def get_student(id: int, db: Session = Depends(get_db)):
    eleve = db.query(Eleve).filter(Eleve.id == id).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    return eleve


@app.put("/students/{id}", response_model=EleveSchema)
def update_student(id: int, eleve_in: EleveCreate, db: Session = Depends(get_db)):
    eleve = db.query(Eleve).filter(Eleve.id == id).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    eleve.nom = eleve_in.nom
    eleve.latitude = eleve_in.latitude
    eleve.longitude = eleve_in.longitude
    db.commit()
    db.refresh(eleve)
    return eleve


@app.delete("/students/{id}")
def delete_student(id: int, db: Session = Depends(get_db)):
    deleted = db.query(Eleve).filter(Eleve.id == id).delete()
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    return {"message": "Élève supprimé"}


@app.get("/groups", response_model=list[GroupeSchema])
def get_groups(db: Session = Depends(get_db)):
    return db.query(Groupe).all()


@app.get("/groups/{id}", response_model=GroupeSchema)
def get_group(id: int, db: Session = Depends(get_db)):
    groupe = db.query(Groupe).filter(Groupe.id == id).first()
    if not groupe:
        raise HTTPException(status_code=404, detail="Groupe non trouvé")
    return groupe


@app.put("/groups/{id}", response_model=GroupeSchema)
def update_group(id: int, nom: str = Query(...), taille: int = Query(...), db: Session = Depends(get_db)):
    groupe = db.query(Groupe).filter(Groupe.id == id).first()
    if not groupe:
        raise HTTPException(status_code=404, detail="Groupe non trouvé")
    groupe.nom = nom
    groupe.taille = taille
    db.commit()
    db.refresh(groupe)
    return groupe


@app.delete("/groups/{id}")
def delete_group(id: int, db: Session = Depends(get_db)):
    db.query(Groupe).filter(Groupe.id == id).delete()
    db.commit()
    return {"message": "Groupe supprimé"}


# ---------------------- #
# 🔹 Configuration groupe #
# ---------------------- #

@app.get("/config")
def get_config():
    return {"group_size": group_size}


@app.put("/config")
def update_config(size: int):
    global group_size
    group_size = size
    return {"message": f"Taille des groupes mise à jour à {size}"}


# ---------------------- #
# 🧭 Points de ramassage (K-Means) #
# ---------------------- #

@app.get("/groups/pickup-points")
def get_pickup_points(db: Session = Depends(get_db)):
    """
    Calcule les points de ramassage optimaux via K-Means pour chaque groupe.
    """
    groupes = db.query(Groupe).all()
    resultats = []

    for g in groupes:
        eleves = g.eleves
        if not eleves:
            continue

        coords = np.array([[e.latitude, e.longitude] for e in eleves])

        # Si le groupe contient peu d'élèves, on garde la moyenne simple
        if len(coords) < 3:
            centre = np.mean(coords, axis=0)
            centre_lat, centre_lon = centre[0], centre[1]
        else:
            # K-Means pour déterminer le centre géographique optimal
            kmeans = KMeans(n_clusters=1, n_init=10)
            kmeans.fit(coords)
            centre_lat, centre_lon = kmeans.cluster_centers_[0]

        resultats.append({
            "groupe": g.nom,
            "point_ramassage_optimal": {
                "latitude": round(float(centre_lat), 6),
                "longitude": round(float(centre_lon), 6)
            }
        })

    return resultats


# ---------------------- #
# 🔹 Lancement serveur   #
# ---------------------- #

if __name__ == "__main__":
    import uvicorn
    # Bind to 0.0.0.0 so the server is reachable from Docker networks/host
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
