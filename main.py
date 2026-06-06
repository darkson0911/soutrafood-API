import random
import string
import asyncio
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel

# Importation du moteur de base de données et de la classe de base des modèles
from database import engine, get_db
from models import Base, Store, Box, User, Order, CommunityMeal, CommunityOrder
from schemas import StoreCreate, StoreResponse, BoxCreate, BoxUpdate, BoxResponse, UserCreate, UserResponse, OrderCreate, OrderResponse, OrderRate, CommunityMealCreate, CommunityMealResponse, CommunityOrderCreate, CommunityOrderSuccess

# Création de toutes les tables dans la base de données au démarrage
# Si les tables existent déjà, SQLAlchemy s'assure de ne pas les écraser
Base.metadata.create_all(bind=engine)

# Initialisation de l'application FastAPI avec un titre personnalisé
app = FastAPI(title="SoutraFood API")

# Configuration CORS (Cross-Origin Resource Sharing)
# Essentiel pour que notre frontend HTML (servi sur un port différent ou via file://) puisse interroger l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En developpement, on autorise tout
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

class UserLogin(BaseModel):
    telephone: str
    mot_de_passe: str

# Route racine (Root endpoint)
# Permet de vérifier rapidement que le serveur est bien démarré et fonctionnel
@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API de SoutraFood, le Too Good To Go Ivoirien !"}


# ==========================================
# Routes pour la gestion des magasins (Store)
# ==========================================

@app.post("/stores/", response_model=StoreResponse)
def create_store(store: StoreCreate, db: Session = Depends(get_db)):
    """Crée un nouveau magasin dans la base de données."""
    # Création de l'objet SQLAlchemy (modèle ORM) à partir des données de la requête
    db_store = Store(**store.model_dump())
    db.add(db_store)
    db.commit()
    db.refresh(db_store)  # Récupère le Store avec son nouvel 'id' généré par la DB
    return db_store


@app.get("/stores/", response_model=list[StoreResponse])
def get_stores(db: Session = Depends(get_db)):
    """Retourne la liste de tous les magasins de la plateforme."""
    stores = db.query(Store).all()
    return stores


# ==========================================
# Routes pour la gestion des paniers (Box)
# ==========================================

@app.post("/boxes/", response_model=BoxResponse)
def create_box(box: BoxCreate, db: Session = Depends(get_db)):
    """Crée un nouveau panier (Box) lié à un magasin."""
    if box.prix_reduit >= box.prix_original:
        raise HTTPException(status_code=400, detail="Le prix réduit doit être strictement inférieur au prix original.")
    # Création de l'objet SQLAlchemy (modèle ORM) à partir des données de la requête
    db_box = Box(**box.model_dump())
    db.add(db_box)
    db.commit()
    db.refresh(db_box)  # Récupère le Box avec son nouvel 'id' généré par la DB
    return db_box


@app.get("/boxes/", response_model=list[BoxResponse])
def get_boxes(db: Session = Depends(get_db)):
    """Retourne la liste de tous les paniers disponibles sur la plateforme."""
    boxes = db.query(Box).all()
    return boxes


@app.put("/boxes/{box_id}", response_model=BoxResponse)
def update_box(box_id: int, box_update: BoxUpdate, db: Session = Depends(get_db)):
    """Modifie un panier existant."""
    db_box = db.query(Box).filter(Box.id == box_id).first()
    if not db_box:
        raise HTTPException(status_code=404, detail="Panier introuvable")
    
    update_data = box_update.model_dump(exclude_unset=True)
    
    # Validation logique des prix si on les met à jour
    new_prix_reduit = update_data.get("prix_reduit", db_box.prix_reduit)
    new_prix_original = update_data.get("prix_original", db_box.prix_original)
    
    if new_prix_reduit >= new_prix_original:
        raise HTTPException(status_code=400, detail="Le prix réduit doit être strictement inférieur au prix original.")

    for key, value in update_data.items():
        setattr(db_box, key, value)
        
    db.commit()
    db.refresh(db_box)
    return db_box


@app.delete("/boxes/{box_id}")
def delete_box(box_id: int, db: Session = Depends(get_db)):
    """Supprime un panier de la plateforme."""
    db_box = db.query(Box).filter(Box.id == box_id).first()
    if not db_box:
        raise HTTPException(status_code=404, detail="Panier introuvable")
    
    db.delete(db_box)
    db.commit()
    return {"message": "Panier supprimé avec succès"}


# ==========================================
# Routes pour la gestion des Utilisateurs (User)
# ==========================================

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Crée un nouvel utilisateur."""
    # Vérification des doublons sur le numéro de téléphone
    existing_user = db.query(User).filter(User.telephone == user.telephone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Ce numéro de téléphone est déjà utilisé.")
        
    # Instanciation de l'objet SQLAlchemy pour l'utilisateur
    user_data = user.model_dump()
    # On mappe manuellement le mot de passe vers le bon nom de colonne
    db_user = User(
        nom_complet=user_data["nom_complet"],
        telephone=user_data["telephone"],
        mot_de_passe_hash=get_password_hash(user_data["mot_de_passe"])
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """Renvoie la liste de tous les utilisateurs inscrits."""
    return db.query(User).all()


@app.post("/login/")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Connecte l'utilisateur et vérifie son mot de passe."""
    db_user = db.query(User).filter(User.telephone == user.telephone).first()
    if not db_user or not verify_password(user.mot_de_passe, db_user.mot_de_passe_hash):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    
    return {"id": db_user.id, "telephone": db_user.telephone, "nom_complet": db_user.nom_complet}


# ==========================================
# Routes pour la gestion des Commandes (Order)
# ==========================================

@app.post("/orders/", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """
    Logique métier d'une commande :
    1. Validation du panier (existe-t-il ? reste-t-il du stock ?).
    2. Génération automatique d'un code de retrait secret.
    3. Enregistrement de la commande en base.
    4. Décrémentation de la quantité disponible du panier.
    """
    # 1. On cherche la boite correspondante
    box = db.query(Box).filter(Box.id == order.box_id).first()
    
    # 2. Vérification de la disponibilité
    if not box or box.quantite_dispo < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Panier non disponible ou épuisé"
        )
        
    # 3. Génération du code de validation à 6 caractères (lettres majuscules + chiffres)
    caracteres = string.ascii_uppercase + string.digits
    code_secret = ''.join(random.choices(caracteres, k=6))
    
    # 4. Création de la commande
    db_order = Order(
        user_id=order.user_id,
        box_id=order.box_id,
        code_validation=code_secret
    )
    db.add(db_order)
    
    # 5. Décrémentation du stock disponible pour ce panier
    box.quantite_dispo -= 1
    
    db.commit()
    db.refresh(db_order)
    
    return db_order


@app.get("/orders/", response_model=list[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    """Liste l'historique complet de toutes les commandes passées."""
    return db.query(Order).all()


@app.post("/orders/{order_id}/rate", response_model=OrderResponse)
def rate_order(order_id: int, order_rate: OrderRate, db: Session = Depends(get_db)):
    """Permet d'ajouter ou mettre à jour la note d'une commande."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    
    order.note = order_rate.note
    db.commit()
    db.refresh(order)
    return order


# ==========================================
# Routes pour le Coin des Voisins
# ==========================================

@app.post("/community-meals/", response_model=CommunityMealResponse)
def create_community_meal(meal: CommunityMealCreate, user_id: int = Query(...), db: Session = Depends(get_db)):
    # Vérifier que l'utilisateur existe
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    db_meal = CommunityMeal(**meal.model_dump(), user_id=user_id)
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

@app.get("/community-meals/", response_model=list[CommunityMealResponse])
def get_community_meals(db: Session = Depends(get_db)):
    return db.query(CommunityMeal).filter(CommunityMeal.quantite_dispo > 0).order_by(CommunityMeal.id.desc()).all()

@app.post("/community-orders/", response_model=CommunityOrderSuccess)
def create_community_order(order: CommunityOrderCreate, db: Session = Depends(get_db)):
    # Vérifier si l'utilisateur existe
    db_user = db.query(User).filter(User.id == order.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        
    # Vérifier si le plat existe
    db_meal = db.query(CommunityMeal).filter(CommunityMeal.id == order.meal_id).first()
    if not db_meal:
        raise HTTPException(status_code=404, detail="Plat introuvable")
        
    # Sécurité: empêcher la réservation de son propre plat
    if db_meal.user_id == order.user_id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas réserver votre propre plat.")
        
    if db_meal.quantite_dispo <= 0:
        raise HTTPException(status_code=400, detail="Ce plat n'est plus disponible.")
        
    # Décrémenter la quantité
    db_meal.quantite_dispo -= 1
    
    # Si la quantité tombe à 0, marquer la date_fermeture
    if db_meal.quantite_dispo == 0:
        db_meal.date_fermeture = datetime.utcnow()
        
    # Créer le code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Créer la réservation
    db_order = CommunityOrder(user_id=order.user_id, meal_id=order.meal_id, code_validation=code)
    db.add(db_order)
    db.commit()
    
    # Récupérer le téléphone du créateur
    creator = db.query(User).filter(User.id == db_meal.user_id).first()
    
    return CommunityOrderSuccess(
        code_validation=code,
        adresse_exacte=db_meal.adresse_exacte,
        telephone_cuisinier=creator.telephone if creator else "Inconnu"
    )

@app.delete("/community-meals/{meal_id}")
def delete_community_meal(meal_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    db_meal = db.query(CommunityMeal).filter(CommunityMeal.id == meal_id).first()
    if not db_meal:
        raise HTTPException(status_code=404, detail="Plat introuvable")
    
    if db_meal.user_id != user_id:
        raise HTTPException(status_code=403, detail="Non autorisé à supprimer ce plat")
        
    db.delete(db_meal)
    db.commit()
    return {"message": "Plat supprimé avec succès"}

async def cleanup_community_meals():
    """Tâche de fond asynchrone qui tourne toutes les 15 minutes pour purger les photos après 3h de fermeture."""
    while True:
        await asyncio.sleep(900)  # 15 minutes (900 sec)
        with Session(engine) as db:
            three_hours_ago = datetime.utcnow() - timedelta(hours=3)
            meals_to_clean = db.query(CommunityMeal).filter(
                CommunityMeal.date_fermeture.isnot(None),
                CommunityMeal.date_fermeture < three_hours_ago,
                CommunityMeal.photo_base64.isnot(None)
            ).all()
            
            if meals_to_clean:
                for meal in meals_to_clean:
                    meal.photo_base64 = None
                db.commit()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_community_meals())

