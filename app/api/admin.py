from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from sqlalchemy import Integer
from typing import List, Optional
from app.db.session import get_db
from app.models import User, Quiz, Category, UserQuizAttempt, UserProgress, UserRole, UserAnswer
from app.schemas import AdminStats, UserResponse, UserUpdate
from app.services.auth import get_current_user
import math

router = APIRouter()

@router.get("/stats", response_model=AdminStats)
def get_admin_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère les statistiques administrateur"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Statistiques de base
    total_users = db.query(func.count(User.id)).scalar()
    total_quizzes = db.query(func.count(Quiz.id)).scalar()
    total_categories = db.query(func.count(Category.id)).scalar()

    # Quiz populaires (par nombre de tentatives)
    popular_quizzes_query = db.query(
        Quiz.title,
        func.count(UserQuizAttempt.id).label('attempts_count'),
        func.avg(UserQuizAttempt.score).label('avg_score')
    ).join(UserQuizAttempt).group_by(Quiz.id, Quiz.title).order_by(
        func.count(UserQuizAttempt.id).desc()
    ).limit(5).all()

    popular_quizzes = [
        {
            "title": quiz.title,
            "attempts": quiz.attempts_count,
            "avg_score": round(quiz.avg_score, 2) if quiz.avg_score else 0
        }
        for quiz in popular_quizzes_query
    ]

    # Taux de réussite par niveau
    success_rates_query = db.query(
        Quiz.level,
        func.avg(UserQuizAttempt.score).label('avg_score'),
        (func.sum(func.cast(UserQuizAttempt.passed, Integer)) * 100.0 / func.count(UserQuizAttempt.id)).label('success_rate')
    ).join(UserQuizAttempt).group_by(Quiz.level).all()

    success_rates = {}
    for rate in success_rates_query:
        success_rates[rate.level] = {
            "avg_score": round(rate.avg_score, 2) if rate.avg_score else 0,
            "success_rate": round(rate.success_rate, 2) if rate.success_rate else 0
        }

    return {
        "total_users": total_users,
        "total_quizzes": total_quizzes,
        "total_categories": total_categories,
        "popular_quizzes": popular_quizzes,
        "success_rates": success_rates
    }

@router.get("/users")
def get_users(
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste des utilisateurs avec pagination"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Construire la requête de base
    query = db.query(User)
    
    # Appliquer le filtre de recherche si fourni
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    # Compter le total avant pagination
    total = query.count()
    
    # Appliquer la pagination
    offset = (page - 1) * per_page
    users = query.order_by(User.created_at.desc()).offset(offset).limit(per_page).all()
    
    # Calculer le nombre total de pages
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    
    # Formater les utilisateurs
    data = []
    for user in users:
        data.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None
        })
    
    return {
        "data": data,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    }

@router.get("/users/stats", response_model=List[dict])
def get_users_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère les statistiques détaillées des utilisateurs"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    users = db.query(User).all()
    result = []

    for user in users:
        # Nombre de tentatives
        attempts_count = db.query(func.count(UserQuizAttempt.id)).filter(
            UserQuizAttempt.user_id == user.id
        ).scalar()

        # Score moyen
        avg_score_query = db.query(func.avg(UserQuizAttempt.score)).filter(
            UserQuizAttempt.user_id == user.id
        ).scalar()
        avg_score = round(avg_score_query, 2) if avg_score_query else 0

        # Nombre de quiz réussis
        passed_count = db.query(func.count(UserQuizAttempt.id)).filter(
            UserQuizAttempt.user_id == user.id,
            UserQuizAttempt.passed == True
        ).scalar()

        # Progrès par catégorie
        progress_count = db.query(func.count(UserProgress.id)).filter(
            UserProgress.user_id == user.id
        ).scalar()

        result.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "attempts_count": attempts_count,
            "avg_score": avg_score,
            "passed_quizzes": passed_count,
            "categories_mastered": progress_count,
            "created_at": user.created_at
        })

    return result

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère un utilisateur spécifique"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modifie un utilisateur (admin seulement)"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Vérifier si l'email est déjà utilisé par un autre utilisateur
    if user_update.email and user_update.email != user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Mettre à jour les champs
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Supprime un utilisateur (admin seulement)"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Empêcher la suppression de son propre compte
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Supprimer les réponses utilisateur associées
    user_answers = db.query(UserAnswer).join(UserQuizAttempt).filter(UserQuizAttempt.user_id == user_id).all()
    for answer in user_answers:
        db.delete(answer)

    # Supprimer les tentatives de quiz
    attempts = db.query(UserQuizAttempt).filter(UserQuizAttempt.user_id == user_id).all()
    for attempt in attempts:
        db.delete(attempt)

    # Supprimer le progrès utilisateur
    progress_records = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    for progress in progress_records:
        db.delete(progress)

    # Supprimer l'utilisateur
    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}
