from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.db.session import get_db
from app.models import User, UserQuizAttempt, UserProgress, Category, Quiz
from app.schemas import UserStats
from app.services.auth import get_current_user

router = APIRouter()

@router.get("/me/stats", response_model=UserStats)
def get_user_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère les statistiques de l'utilisateur"""
    # Nombre total de tentatives
    total_attempts = db.query(func.count(UserQuizAttempt.id)).filter(
        UserQuizAttempt.user_id == current_user.id
    ).scalar()

    # Score moyen
    avg_score_query = db.query(func.avg(UserQuizAttempt.score)).filter(
        UserQuizAttempt.user_id == current_user.id
    ).scalar()
    average_score = round(avg_score_query, 2) if avg_score_query else 0.0

    # Nombre de catégories maîtrisées
    categories_mastered = db.query(func.count(UserProgress.id)).filter(
        UserProgress.user_id == current_user.id
    ).scalar()

    # Tentatives récentes (5 dernières)
    recent_attempts_query = db.query(UserQuizAttempt).filter(
        UserQuizAttempt.user_id == current_user.id,
        UserQuizAttempt.completed_at != None
    ).order_by(UserQuizAttempt.completed_at.desc()).limit(5).all()

    recent_attempts = []
    for attempt in recent_attempts_query:
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        recent_attempts.append({
            "id": attempt.id,
            "quiz_title": quiz.title if quiz else "Unknown Quiz",
            "score": attempt.score,
            "passed": attempt.passed,
            "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None
        })

    return {
        "total_attempts": total_attempts,
        "average_score": average_score,
        "categories_mastered": categories_mastered,
        "recent_attempts": recent_attempts
    }

@router.get("/me/attempts", response_model=List[dict])
def get_user_attempts_alias(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Alias pour GET /attempts/attempts - Historique des tentatives de l'utilisateur"""
    attempts = db.query(UserQuizAttempt).filter(
        UserQuizAttempt.user_id == current_user.id
    ).order_by(UserQuizAttempt.completed_at.desc()).all()

    result = []
    for attempt in attempts:
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        result.append({
            "id": attempt.id,
            "quiz_title": quiz.title if quiz else "Unknown Quiz",
            "score": attempt.score,
            "passed": attempt.passed,
            "completed_at": attempt.completed_at
        })

    return result

@router.get("/me/progress", response_model=List[dict])
def get_user_progress_alias(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Alias pour GET /attempts/progress - Progression de l'utilisateur par catégorie"""
    progress_list = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id
    ).all()

    result = []
    for progress in progress_list:
        category = db.query(Category).filter(Category.id == progress.category_id).first()
        if category:
            result.append({
                "category": {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "icon_url": category.icon_url,
                    "is_active": category.is_active,
                    "created_at": category.created_at,
                    "updated_at": category.updated_at
                },
                "current_level": progress.current_level,
                "updated_at": progress.updated_at
            })

    return result
