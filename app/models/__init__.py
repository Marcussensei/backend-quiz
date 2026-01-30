from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"

class QuizLevel(str, enum.Enum):
    debutant = "debutant"
    intermediaire = "intermediaire"
    avance = "avance"

class QuizStatus(str, enum.Enum):
    draft = "draft"
    published = "published"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    attempts = relationship("UserQuizAttempt", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    icon_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    quizzes = relationship("Quiz", back_populates="category")
    progress = relationship("UserProgress", back_populates="category")

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(String, primary_key=True, index=True)
    category_id = Column(String, ForeignKey("categories.id"))
    title = Column(String, nullable=False)
    level = Column(Enum(QuizLevel), nullable=False)
    status = Column(Enum(QuizStatus), default=QuizStatus.draft)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("UserQuizAttempt", back_populates="quiz")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True, index=True)
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    question_text = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(String, primary_key=True, index=True)
    question_id = Column(String, ForeignKey("questions.id"))
    answer_text = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    question = relationship("Question", back_populates="answers")
    user_answers = relationship("UserAnswer", back_populates="answer")

class UserQuizAttempt(Base):
    __tablename__ = "user_quiz_attempts"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    score = Column(Float)
    passed = Column(Boolean)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="attempts")
    quiz = relationship("Quiz", back_populates="attempts")
    answers = relationship("UserAnswer", back_populates="attempt")

class UserAnswer(Base):
    __tablename__ = "user_answers"
    
    id = Column(String, primary_key=True, index=True)
    attempt_id = Column(String, ForeignKey("user_quiz_attempts.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    answer_id = Column(String, ForeignKey("answers.id"))
    is_correct = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    attempt = relationship("UserQuizAttempt", back_populates="answers")
    question = relationship("Question", back_populates="user_answers")
    answer = relationship("Answer", back_populates="user_answers")

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    category_id = Column(String, ForeignKey("categories.id"))
    current_level = Column(Enum(QuizLevel), default=QuizLevel.debutant)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="progress")
    category = relationship("Category", back_populates="progress")