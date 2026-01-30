from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, QuizLevel, QuizStatus

# Auth schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    old_password: str
    new_password: Optional[str] = None

# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Quiz schemas
class QuizBase(BaseModel):
    title: str
    level: QuizLevel
    status: QuizStatus = QuizStatus.draft

class QuizCreate(QuizBase):
    category_id: str

class QuizUpdate(QuizBase):
    pass

class QuizResponse(QuizBase):
    id: str
    category_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Question schemas
class AnswerBase(BaseModel):
    answer_text: str
    is_correct: bool
    order: int

class AnswerCreate(AnswerBase):
    pass

class AnswerResponse(AnswerBase):
    id: str
    question_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    question_text: str
    order: int

class QuestionCreate(QuestionBase):
    quiz_id: str
    answers: List[AnswerCreate]

class QuestionCreateForQuiz(QuestionBase):
    answers: List[AnswerCreate]

class QuestionUpdate(QuestionBase):
    answers: List[AnswerCreate]

class QuestionResponse(QuestionBase):
    id: str
    quiz_id: str
    created_at: datetime
    answers: List[AnswerResponse]

    class Config:
        from_attributes = True

# Attempt schemas
class QuizStartResponse(BaseModel):
    attempt_id: str
    quiz: QuizResponse
    questions: List[QuestionResponse]

class AnswerSubmit(BaseModel):
    question_id: str
    answer_ids: List[str]

class QuizSubmit(BaseModel):
    answers: List[AnswerSubmit]

class QuizResult(BaseModel):
    score: float
    passed: bool
    correct_answers: int
    total_questions: int
    details: List[dict]

# Progress schemas
class UserProgress(BaseModel):
    category: CategoryResponse
    current_level: QuizLevel
    unlocked_levels: List[QuizLevel]

class UserStats(BaseModel):
    total_attempts: int
    average_score: float
    categories_mastered: int
    recent_attempts: List[dict]

# Admin stats
class AdminStats(BaseModel):
    total_users: int
    total_quizzes: int
    total_categories: int
    popular_quizzes: List[dict]
    success_rates: dict