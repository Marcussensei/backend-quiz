from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models import Quiz, User, UserRole, Category, Question, Answer
from app.schemas import QuizResponse, QuizCreate, QuizUpdate, QuestionCreateForQuiz, QuestionResponse
from app.services.auth import get_current_user
import uuid

router = APIRouter()

@router.get("/", response_model=List[QuizResponse])
def get_quizzes(
    category_id: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Quiz)
    if current_user.role != UserRole.admin:
        query = query.filter(Quiz.status == "published")
    if category_id:
        query = query.filter(Quiz.category_id == category_id)
    if level:
        query = query.filter(Quiz.level == level)
    if status:
        query = query.filter(Quiz.status == status)
    return query.all()

@router.post("/", response_model=QuizResponse)
def create_quiz(quiz: QuizCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Check if category exists
    category = db.query(Category).filter(Category.id == quiz.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db_quiz = Quiz(
        id=str(uuid.uuid4()),
        category_id=quiz.category_id,
        title=quiz.title,
        level=quiz.level,
        status=quiz.status
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if current_user.role != UserRole.admin and quiz.status != "published":
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

@router.put("/{quiz_id}", response_model=QuizResponse)
def update_quiz(quiz_id: str, quiz_update: QuizUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    for key, value in quiz_update.dict().items():
        setattr(db_quiz, key, value)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    # Check if quiz has attempts
    if db_quiz.attempts:
        raise HTTPException(status_code=400, detail="Cannot delete quiz with attempts")
    db.delete(db_quiz)
    db.commit()
    return {"message": "Quiz deleted"}

@router.post("/{quiz_id}/questions", response_model=QuestionResponse)
def create_question_for_quiz(quiz_id: str, question: QuestionCreateForQuiz, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Ajouter une question à un quiz spécifique"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Vérifier que le quiz existe
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Vérifier que l'ordre est unique pour ce quiz
    existing_question = db.query(Question).filter(
        Question.quiz_id == quiz_id,
        Question.order == question.order
    ).first()
    if existing_question:
        raise HTTPException(status_code=400, detail="Order must be unique for this quiz")

    db_question = Question(
        id=str(uuid.uuid4()),
        quiz_id=quiz_id,
        question_text=question.question_text,
        order=question.order
    )
    db.add(db_question)

    # Créer les réponses
    for answer_data in question.answers:
        db_answer = Answer(
            id=str(uuid.uuid4()),
            question_id=db_question.id,
            answer_text=answer_data.answer_text,
            is_correct=answer_data.is_correct,
            order=answer_data.order
        )
        db.add(db_answer)

    db.commit()
    db.refresh(db_question)
    return db_question