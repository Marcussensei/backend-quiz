from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models import UserQuizAttempt, User, Quiz, Question, Answer, UserAnswer, UserProgress, Category
from app.schemas import QuizStartResponse, QuizSubmit, QuizResult
from app.services.auth import get_current_user
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/start/{quiz_id}", response_model=QuizStartResponse)
def start_quiz(quiz_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Démarre une tentative de quiz pour l'utilisateur"""
    # Vérifier que le quiz existe et est publié
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.status == "published").first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found or not published")

    # Vérifier si l'utilisateur a déjà une tentative en cours pour ce quiz
    existing_attempt = db.query(UserQuizAttempt).filter(
        UserQuizAttempt.user_id == current_user.id,
        UserQuizAttempt.quiz_id == quiz_id,
        UserQuizAttempt.completed_at == None
    ).first()

    if existing_attempt:
        # Retourner la tentative existante
        attempt_id = existing_attempt.id
    else:
        # Créer une nouvelle tentative
        attempt = UserQuizAttempt(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            quiz_id=quiz_id
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        attempt_id = attempt.id

    # Récupérer le quiz avec ses questions et réponses
    quiz_data = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).order_by(Question.order).all()

    # Pour chaque question, récupérer les réponses (sans indiquer laquelle est correcte)
    for question in questions:
        question.answers = db.query(Answer).filter(Answer.question_id == question.id).order_by(Answer.order).all()

    return {
        "attempt_id": attempt_id,
        "quiz": quiz_data,
        "questions": questions
    }

@router.post("/submit/{attempt_id}", response_model=QuizResult)
def submit_quiz(attempt_id: str, submission: QuizSubmit, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Soumet les réponses du quiz et calcule le résultat"""
    # Vérifier que la tentative appartient à l'utilisateur et n'est pas terminée
    attempt = db.query(UserQuizAttempt).filter(
        UserQuizAttempt.id == attempt_id,
        UserQuizAttempt.user_id == current_user.id,
        UserQuizAttempt.completed_at == None
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found or already completed")

    # Récupérer toutes les questions du quiz
    questions = db.query(Question).filter(Question.quiz_id == attempt.quiz_id).all()
    total_questions = len(questions)
    correct_answers = 0
    details = []

    # Traiter chaque réponse soumise
    for answer_submit in submission.answers:
        question = db.query(Question).filter(Question.id == answer_submit.question_id).first()
        if not question or question.quiz_id != attempt.quiz_id:
            continue

        # Récupérer les bonnes réponses pour cette question
        correct_answer_ids = db.query(Answer.id).filter(
            Answer.question_id == question.id,
            Answer.is_correct == True
        ).all()
        correct_answer_ids = [aid[0] for aid in correct_answer_ids]

        # Vérifier si les réponses de l'utilisateur sont correctes
        user_correct = set(answer_submit.answer_ids) == set(correct_answer_ids)
        if user_correct:
            correct_answers += 1

        # Enregistrer chaque réponse de l'utilisateur
        for answer_id in answer_submit.answer_ids:
            user_answer = UserAnswer(
                id=str(uuid.uuid4()),
                attempt_id=attempt_id,
                question_id=question.id,
                answer_id=answer_id,
                is_correct=user_correct
            )
            db.add(user_answer)

        # Ajouter les détails pour la réponse
        details.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "user_answers": answer_submit.answer_ids,
            "correct_answers": correct_answer_ids,
            "is_correct": user_correct
        })

    # Calculer le score
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    passed = score >= 80  # Seuil de réussite à 80% (selon cahier des charges)

    # Mettre à jour la tentative
    attempt.score = score
    attempt.passed = passed
    attempt.completed_at = datetime.utcnow()

    # Si le quiz est réussi, mettre à jour le progrès de l'utilisateur
    if passed:
        update_user_progress(db, current_user.id, attempt.quiz_id)

    db.commit()

    return {
        "score": score,
        "passed": passed,
        "correct_answers": correct_answers,
        "total_questions": total_questions,
        "details": details
    }

@router.get("/progress", response_model=List[dict])
def get_user_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère le progrès de l'utilisateur par catégorie"""
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

@router.get("/attempts", response_model=List[dict])
def get_user_attempts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère l'historique des tentatives de l'utilisateur"""
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

@router.get("/{attempt_id}")
def get_attempt_detail(attempt_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Récupère le détail d'une tentative avec quiz, questions et réponses"""
    # Vérifier que la tentative appartient à l'utilisateur
    attempt = db.query(UserQuizAttempt).filter(
        UserQuizAttempt.id == attempt_id,
        UserQuizAttempt.user_id == current_user.id
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Récupérer le quiz
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Récupérer les questions du quiz
    questions = db.query(Question).filter(Question.quiz_id == attempt.quiz_id).order_by(Question.order).all()

    # Construire les questions avec réponses
    questions_with_answers = []
    for question in questions:
        # Récupérer toutes les réponses possibles
        all_answers = db.query(Answer).filter(Answer.question_id == question.id).order_by(Answer.order).all()

        # Récupérer les réponses de l'utilisateur pour cette question
        user_answers = db.query(UserAnswer).filter(
            UserAnswer.attempt_id == attempt_id,
            UserAnswer.question_id == question.id
        ).all()
        user_answer_ids = [ua.answer_id for ua in user_answers]

        questions_with_answers.append({
            "id": question.id,
            "question_text": question.question_text,
            "order": question.order,
            "answers": [
                {
                    "id": answer.id,
                    "answer_text": answer.answer_text,
                    "is_correct": answer.is_correct,
                    "order": answer.order,
                    "user_selected": answer.id in user_answer_ids
                }
                for answer in all_answers
            ]
        })

    return {
        "data": {
            "attempt": {
                "id": attempt.id,
                "score": attempt.score,
                "passed": attempt.passed,
                "completed_at": attempt.completed_at
            },
            "quiz": {
                "id": quiz.id,
                "title": quiz.title,
                "level": quiz.level,
                "category_id": quiz.category_id
            },
            "questions_with_answers": questions_with_answers
        },
        "meta": {},
        "message": "Détail de la tentative récupéré avec succès"
    }

def update_user_progress(db: Session, user_id: str, quiz_id: str):
    """Met à jour le progrès de l'utilisateur après avoir réussi un quiz"""
    # Récupérer le quiz et sa catégorie
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return

    # Vérifier si l'utilisateur a déjà un progrès pour cette catégorie
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.category_id == quiz.category_id
    ).first()

    if progress:
        # Mettre à jour le niveau si nécessaire
        current_level_order = get_level_order(progress.current_level)
        quiz_level_order = get_level_order(quiz.level)

        if quiz_level_order > current_level_order:
            progress.current_level = quiz.level
            progress.updated_at = datetime.utcnow()
    else:
        # Créer un nouveau progrès
        progress = UserProgress(
            id=str(uuid.uuid4()),
            user_id=user_id,
            category_id=quiz.category_id,
            current_level=quiz.level
        )
        db.add(progress)

def get_level_order(level: str) -> int:
    """Retourne l'ordre numérique du niveau"""
    levels = {"debutant": 1, "intermediaire": 2, "avance": 3}
    return levels.get(level, 0)
