from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models import Category, User, UserRole, Quiz, UserQuizAttempt
from app.schemas import CategoryResponse, CategoryCreate, CategoryUpdate
from app.services.auth import get_current_user
import uuid

router = APIRouter()
 
@router.get("/", response_model=List[CategoryResponse])
def get_categories(is_active: Optional[bool] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Category)
    if current_user.role != UserRole.admin:
        query = query.filter(Category.is_active == True)
    if is_active is not None:
        query = query.filter(Category.is_active == is_active)
    return query.all()

@router.post("/", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Vérifier l'unicité du nom
    existing_category = db.query(Category).filter(Category.name == category.name).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category name already exists")
    
    db_category = Category(
        id=str(uuid.uuid4()),
        name=category.name,
        description=category.description,
        icon_url=category.icon_url,
        is_active=category.is_active
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if current_user.role != UserRole.admin and not category.is_active:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: str, category_update: CategoryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category_update.dict().items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/{category_id}")
def delete_category(category_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    # Check if category has quizzes
    if db_category.quizzes:
        raise HTTPException(status_code=400, detail="Cannot delete category with associated quizzes")
    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted"}

@router.get("/{category_id}/quizzes/available")
def get_available_quizzes(category_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retourne les quiz disponibles pour une catégorie avec is_accessible selon la progression"""
    # Vérifier que la catégorie existe et est active
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if current_user.role != UserRole.admin and not category.is_active:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Récupérer tous les quiz publiés de cette catégorie
    quizzes = db.query(Quiz).filter(
        Quiz.category_id == category_id,
        Quiz.status == "published"
    ).all()
    
    # Récupérer le meilleur score de l'utilisateur pour chaque niveau dans cette catégorie
    def get_level_order(level: str) -> int:
        levels = {"debutant": 1, "intermediaire": 2, "avance": 3}
        return levels.get(level, 0)
    
    result = []
    for quiz in quizzes:
        is_accessible = False
        
        # Débutant: toujours accessible
        if quiz.level == "debutant":
            is_accessible = True
        # Intermédiaire: accessible si quiz débutant passé avec ≥ 80%
        elif quiz.level == "intermediaire":
            beginner_quiz = db.query(Quiz).filter(
                Quiz.category_id == category_id,
                Quiz.level == "debutant",
                Quiz.status == "published"
            ).first()
            if beginner_quiz:
                best_attempt = db.query(UserQuizAttempt).filter(
                    UserQuizAttempt.user_id == current_user.id,
                    UserQuizAttempt.quiz_id == beginner_quiz.id,
                    UserQuizAttempt.passed == True,
                    UserQuizAttempt.score >= 80
                ).order_by(UserQuizAttempt.score.desc()).first()
                is_accessible = best_attempt is not None
        # Avancé: accessible si quiz intermédiaire passé avec ≥ 80%
        elif quiz.level == "avance":
            intermediate_quiz = db.query(Quiz).filter(
                Quiz.category_id == category_id,
                Quiz.level == "intermediaire",
                Quiz.status == "published"
            ).first()
            if intermediate_quiz:
                best_attempt = db.query(UserQuizAttempt).filter(
                    UserQuizAttempt.user_id == current_user.id,
                    UserQuizAttempt.quiz_id == intermediate_quiz.id,
                    UserQuizAttempt.passed == True,
                    UserQuizAttempt.score >= 80
                ).order_by(UserQuizAttempt.score.desc()).first()
                is_accessible = best_attempt is not None
        
        result.append({
            "id": quiz.id,
            "title": quiz.title,
            "level": quiz.level,
            "category_id": quiz.category_id,
            "status": quiz.status,
            "is_accessible": is_accessible
        })
    
    return {
        "data": result,
        "meta": {},
        "message": "Quiz disponibles récupérés avec succès"
    }