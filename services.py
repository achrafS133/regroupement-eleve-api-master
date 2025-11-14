from sklearn.cluster import KMeans, DBSCAN
from sqlalchemy.orm import Session
from models import Eleve, Groupe
import math
import numpy as np

from sqlalchemy.orm import Session
from models import Eleve, Groupe

def generate_groups(db: Session, group_size: int = 4):
    # Get all students
    eleves = db.query(Eleve).all()

    if not eleves:
        return []

    # Sort by latitude for deterministic grouping (optional)
    eleves.sort(key=lambda e: e.latitude)

    # Remove existing groups before creating new ones
    db.query(Groupe).delete()
    db.commit()

    groupes = []
    total_eleves = len(eleves)
    group_count = 0

    for i in range(0, total_eleves, group_size):
        group_count += 1
        # Slice exactly 'group_size' students (or remaining)
        subset = eleves[i:i + group_size]
        groupe = Groupe(nom=f"Groupe {group_count}", taille=len(subset))
        db.add(groupe)
        db.flush()  # get group ID

        for e in subset:
            e.groupe_id = groupe.id

        groupes.append(groupe)

    db.commit()
    return groupes

def generate_groups_dbscan(db: Session, eps: float = 0.5, min_samples: int = 2):
    """
    Generate groups using DBSCAN clustering based on geographic coordinates.
    This approach clusters students based on their proximity to each other.
    """
    # Get all students
    eleves = db.query(Eleve).all()

    if not eleves:
        return []

    # Extract coordinates for clustering
    coords = np.array([[e.latitude, e.longitude] for e in eleves])

    if len(coords) < 2:
        # If there's only one student, create a single group
        db.query(Groupe).delete()
        db.commit()
        
        if len(coords) == 1:
            groupe = Groupe(nom="Groupe 1", taille=1)
            db.add(groupe)
            db.flush()
            eleves[0].groupe_id = groupe.id
            db.commit()
            return [groupe]
        return []

    # Apply DBSCAN clustering
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    cluster_labels = dbscan.fit_predict(coords)

    # Remove existing groups before creating new ones
    db.query(Groupe).delete()
    db.commit()

    # Create groups based on DBSCAN clusters
    groupes = []
    unique_labels = set(cluster_labels)
    
    for label in unique_labels:
        if label == -1:  # -1 represents noise points (outliers)
            continue
        
        # Get students belonging to this cluster
        cluster_eleves = [eleves[i] for i in range(len(eleves)) if cluster_labels[i] == label]
        
        # Create a new group for this cluster
        groupe_num = len(groupes) + 1
        groupe = Groupe(nom=f"Groupe {groupe_num}", taille=len(cluster_eleves))
        db.add(groupe)
        db.flush()  # get group ID
        
        # Assign students to the group
        for e in cluster_eleves:
            e.groupe_id = groupe.id
        
        groupes.append(groupe)

    # Handle noise points (outliers) - assign them to the nearest cluster or create small groups
    noise_indices = [i for i, label in enumerate(cluster_labels) if label == -1]
    for idx in noise_indices:
        noise_eleve = eleves[idx]
        
        # Find the nearest group and assign the student to it if possible
        min_distance = float('inf')
        nearest_group = None
        noise_coords = coords[idx].reshape(1, -1)
        
        for i, label in enumerate(cluster_labels):
            if label != -1:  # Not a noise point
                other_coords = coords[i].reshape(1, -1)
                distance = np.linalg.norm(noise_coords - other_coords)
                if distance < min_distance:
                    min_distance = distance
                    # Find the group this student belongs to
                    other_eleve = eleves[i]
                    if other_eleve.groupe_id:
                        nearest_group = db.query(Groupe).filter(Groupe.id == other_eleve.groupe_id).first()
        
        # If found a nearby group and it's not too large, add the noise point to it
        if nearest_group and nearest_group.taille < 10:  # Arbitrary max size to prevent groups from getting too large
            noise_eleve.groupe_id = nearest_group.id
            # Update the group size
            nearest_group.taille += 1
        else:
            # Create a new small group for the noise point
            groupe_num = len(groupes) + 1
            groupe = Groupe(nom=f"Groupe {groupe_num}", taille=1)
            db.add(groupe)
            db.flush()
            noise_eleve.groupe_id = groupe.id
            groupes.append(groupe)

    db.commit()
    return groupes
