from sqlalchemy.orm import Session
from models import Eleve
import random

def init_data(db: Session):
    """Insère des élèves de test s'il n'y en a pas déjà."""
    if db.query(Eleve).count() > 0:
        print("[INFO] Données déjà présentes, aucune insertion.")
        return

    noms = [
        "Ali", "Fatima", "Youssef", "Sara", "Omar", "Aya",
        "Rania", "Karim", "Hassan", "Imane", "Nour", "Soufiane"
    ]

    # Coordonnées approximatives autour de Rabat
    base_lat, base_lon = 34.020882, -6.841650

    for nom in noms:
        lat = base_lat + random.uniform(-0.05, 0.05)
        lon = base_lon + random.uniform(-0.05, 0.05)
        eleve = Eleve(nom=nom, latitude=lat, longitude=lon)
        db.add(eleve)

    db.commit()
    print(f"[INFO] {len(noms)} élèves ajoutés avec succès !")
