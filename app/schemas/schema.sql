-- Quiz Programming Database Schema
-- PostgreSQL

-- Users table
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    role VARCHAR NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Categories table
CREATE TABLE categories (
    id VARCHAR PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    description TEXT,
    icon_url VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Quizzes table
CREATE TABLE quizzes (
    id VARCHAR PRIMARY KEY,
    category_id VARCHAR REFERENCES categories(id),
    title VARCHAR NOT NULL,
    level VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Questions table
CREATE TABLE questions (
    id VARCHAR PRIMARY KEY,
    quiz_id VARCHAR REFERENCES quizzes(id),
    question_text TEXT NOT NULL,
    "order" INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Answers table
CREATE TABLE answers (
    id VARCHAR PRIMARY KEY,
    question_id VARCHAR REFERENCES questions(id),
    answer_text VARCHAR NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    "order" INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Quiz Attempts table
CREATE TABLE user_quiz_attempts (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    quiz_id VARCHAR REFERENCES quizzes(id),
    score DECIMAL(5,2),
    passed BOOLEAN,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- User Answers table
CREATE TABLE user_answers (
    id VARCHAR PRIMARY KEY,
    attempt_id VARCHAR REFERENCES user_quiz_attempts(id),
    question_id VARCHAR REFERENCES questions(id),
    answer_id VARCHAR REFERENCES answers(id),
    is_correct BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Progress table
CREATE TABLE user_progress (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    category_id VARCHAR REFERENCES categories(id),
    current_level VARCHAR DEFAULT 'debutant',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category_id)
);

-- Indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_categories_is_active ON categories(is_active);
CREATE INDEX idx_quizzes_category_id ON quizzes(category_id);
CREATE INDEX idx_quizzes_status ON quizzes(status);
CREATE INDEX idx_questions_quiz_id ON questions(quiz_id);
CREATE INDEX idx_answers_question_id ON answers(question_id);
CREATE INDEX idx_user_quiz_attempts_user_id ON user_quiz_attempts(user_id);
CREATE INDEX idx_user_quiz_attempts_quiz_id ON user_quiz_attempts(quiz_id);
CREATE INDEX idx_user_answers_attempt_id ON user_answers(attempt_id);
CREATE INDEX idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX idx_user_progress_category_id ON user_progress(category_id);