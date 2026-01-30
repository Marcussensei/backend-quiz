
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth import authenticate_user, create_access_token, create_user, get_current_user, verify_password, get_password_hash
from app.schemas import UserCreate, UserLogin, Token, UserResponse, UserProfileUpdate
from app.models import User
from .categories import router as categories_router
from .quizzes import router as quizzes_router
from .questions import router as questions_router
from .attempts import router as attempts_router
from .admin import router as admin_router
from .users import router as users_router

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

@router.post("/auth/register", tags=["Auth"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Inscription d'un nouvel utilisateur
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = create_user(db=db, user=user)
    #retourner aussi le access_token
    return {"message": "Utilisateur créé avec succès", "user_id": str(db_user.id)}


@router.post("/auth/login", tags=["Auth"])
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    Connexion - définit un cookie HTTP-only avec le token JWT
    """
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": db_user.email})

    # Définir le cookie HTTP-only avec le token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,  # 30 minutes
        expires=1800,
        secure=False,  # False pour développement HTTP
        samesite=None  # None pour permettre cross-origin en développement
    )
    #reourner le access token aussi dans le corps de la réponse
    # return {"message": "Utilisateur créé avec succès", "user_id": str(db_user.id)}
    return {"access_token": access_token, "token_type": "bearer", "user_id": str(db_user.id)}

@router.get("/auth/me", response_model=UserResponse, tags=["Auth"])
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/auth/me", response_model=UserResponse, tags=["Auth"])
def update_user_profile(
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modifie le profil de l'utilisateur connecté"""
    # Vérifier l'ancien mot de passe
    if not verify_password(profile_update.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")

    # Vérifier si l'email est déjà utilisé par un autre utilisateur
    if profile_update.email and profile_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == profile_update.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Mettre à jour les champs
    if profile_update.name is not None:
        current_user.name = profile_update.name
    if profile_update.email is not None:
        current_user.email = profile_update.email
    if profile_update.new_password is not None:
        current_user.password = get_password_hash(profile_update.new_password)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/auth/logout", tags=["Auth"])
def logout(response: Response):
    """
    Déconnexion - supprime le cookie HTTP-only
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,  # False pour développement HTTP
        samesite=None  # None pour permettre cross-origin en développement
    )
    return {"message": "Déconnexion réussie"}

router.include_router(categories_router, prefix="/categories", tags=["Categories"])
router.include_router(quizzes_router, prefix="/quizzes", tags=["Quizzes"])
router.include_router(questions_router, prefix="/questions", tags=["Questions"])
router.include_router(attempts_router, prefix="/attempts", tags=["Attempts"])
router.include_router(admin_router, prefix="/admin", tags=["Admin"])
router.include_router(users_router, prefix="/users", tags=["Users"])