from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models import Question, User, UserRole, Quiz, Answer
from app.schemas import QuestionResponse, QuestionCreate, QuestionUpdate
from app.services.auth import get_current_user
import uuid

router = APIRouter()

@router.get("/", response_model=List[QuestionResponse])
def get_questions(
    quiz_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    query = db.query(Question)
    if quiz_id:
        query = query.filter(Question.quiz_id == quiz_id)
    return query.order_by(Question.order).all()

@router.post("/", response_model=QuestionResponse)
def create_question(question: QuestionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Check if quiz exists
    quiz = db.query(Quiz).filter(Quiz.id == question.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Check if order is unique for this quiz
    existing_question = db.query(Question).filter(
        Question.quiz_id == question.quiz_id,
        Question.order == question.order
    ).first()
    if existing_question:
        raise HTTPException(status_code=400, detail="Order must be unique for this quiz")

    db_question = Question(
        id=str(uuid.uuid4()),
        quiz_id=question.quiz_id,
        question_text=question.question_text,
        order=question.order
    )
    db.add(db_question)

    # Create answers
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

@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(question_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(question_id: str, question_update: QuestionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if order is unique for this quiz (excluding current question)
    if question_update.order != db_question.order:
        existing_question = db.query(Question).filter(
            Question.quiz_id == db_question.quiz_id,
            Question.order == question_update.order,
            Question.id != question_id
        ).first()
        if existing_question:
            raise HTTPException(status_code=400, detail="Order must be unique for this quiz")

    # Update question
    db_question.question_text = question_update.question_text
    db_question.order = question_update.order

    # Delete existing answers
    db.query(Answer).filter(Answer.question_id == question_id).delete()

    # Create new answers
    for answer_data in question_update.answers:
        db_answer = Answer(
            id=str(uuid.uuid4()),
            question_id=question_id,
            answer_text=answer_data.answer_text,
            is_correct=answer_data.is_correct,
            order=answer_data.order
        )
        db.add(db_answer)

    db.commit()
    db.refresh(db_question)
    return db_question

@router.delete("/{question_id}")
def delete_question(question_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    # Check if question has user answers (attempts)
    if db_question.user_answers:
        raise HTTPException(status_code=400, detail="Cannot delete question with associated user answers")
    db.delete(db_question)
    db.commit()
    return {"message": "Question deleted"}