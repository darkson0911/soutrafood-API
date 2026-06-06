from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==========================================
# Schémas pour l'entité User
# ==========================================

class UserCreate(BaseModel):
    """Schéma utilisé pour la création d'un utilisateur (données attendues en entrée)."""
    nom_complet: str
    telephone: str
    mot_de_passe: str


class UserResponse(BaseModel):
    """Schéma utilisé pour renvoyer les informations de l'utilisateur (on exclut le mot de passe)."""
    id: int
    nom_complet: str
    telephone: str

    # Permet à Pydantic de lire les données issues des modèles SQLAlchemy (ex orm_mode=True)
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Schémas pour l'entité Store
# ==========================================

class StoreCreate(BaseModel):
    """Schéma pour l'ajout d'un nouveau magasin."""
    nom: str
    adresse: str
    telephone_gerant: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class StoreResponse(BaseModel):
    """Schéma de réponse pour un magasin."""
    id: int
    nom: str
    adresse: str
    telephone_gerant: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Schémas pour l'entité Box
# ==========================================

class BoxCreate(BaseModel):
    """Schéma pour la création d'un panier Too Good To Go."""
    store_id: int
    titre: str
    prix_original: int
    prix_reduit: int
    heure_recuperation: str
    quantite_dispo: int = Field(..., le=200)
    photo_base64: Optional[str] = None


class BoxUpdate(BaseModel):
    """Schéma pour la mise à jour partielle d'un panier."""
    titre: Optional[str] = None
    photo_base64: Optional[str] = None
    prix_original: Optional[int] = None
    prix_reduit: Optional[int] = None
    quantite_dispo: Optional[int] = Field(None, le=200)
    heure_recuperation: Optional[str] = None


class BoxResponse(BaseModel):
    """Schéma de réponse complet pour un panier."""
    id: int
    store_id: int
    titre: str
    prix_original: int
    prix_reduit: int
    quantite_dispo: int
    heure_recuperation: str
    photo_base64: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Schémas pour l'entité Order
# ==========================================

class OrderCreate(BaseModel):
    """Schéma de création basique pour passer une commande."""
    user_id: int
    box_id: int


class OrderRate(BaseModel):
    """Schéma pour la notation d'une commande."""
    note: int


class OrderResponse(BaseModel):
    """Schéma de réponse renvoyant tous les détails générés (date, statut, code secret...)."""
    id: int
    user_id: int
    box_id: int
    date_commande: datetime
    statut: str
    code_validation: str
    note: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Routes pour le Coin des Voisins
# ==========================================

class CommunityMealCreate(BaseModel):
    titre: str
    quantite_dispo: int
    zone: str
    adresse_exacte: str
    description: str
    photo_base64: Optional[str] = None

class CommunityMealResponse(BaseModel):
    id: int
    user_id: int
    titre: str
    quantite_dispo: int
    zone: str
    description: str
    date_creation: datetime
    photo_base64: Optional[str] = None
    # On n'inclut délibérément PAS adresse_exacte ni date_fermeture ici par sécurité.

    model_config = ConfigDict(from_attributes=True)

class CommunityOrderCreate(BaseModel):
    user_id: int
    meal_id: int

class CommunityOrderSuccess(BaseModel):
    code_validation: str
    adresse_exacte: str
    telephone_cuisinier: str
