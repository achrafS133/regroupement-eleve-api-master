from pydantic import BaseModel
from typing import List, Optional

class EleveBase(BaseModel):
    nom: str
    latitude: float
    longitude: float

class EleveCreate(EleveBase):
    pass

class Eleve(EleveBase):
    id: int
    class Config:
        from_attributes = True

class GroupeBase(BaseModel):
    nom: str
    taille: int

class GroupeCreate(GroupeBase):
    pass

class Groupe(GroupeBase):
    id: int
    eleves: List[Eleve] = []
    class Config:
        from_attributes = True
