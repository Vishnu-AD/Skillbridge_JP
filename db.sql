CREATE DATABASE IF NOT EXISTS skillbridge_jp;
USE skillbridge_jp;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  role ENUM('candidate','recruiter','admin') NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(180) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate_profiles (
  user_id INT PRIMARY KEY,
  nationality VARCHAR(80),
  years_exp INT DEFAULT 0,
  desired_role VARCHAR(120),
  jlpt_level ENUM('N5','N4','N3','N2','N1') DEFAULT 'N5',
  jlpt_score INT DEFAULT 0,
  keigo_score INT DEFAULT 0,
  tech_score INT DEFAULT 0,
  readiness_score INT DEFAULT 0,
  verified TINYINT(1) DEFAULT 0,
  resume_file VARCHAR(255),
  resume_text MEDIUMTEXT,
  resume_skills TEXT,
  encrypted_phone TEXT,
  encrypted_address TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  recruiter_id INT NOT NULL,
  title VARCHAR(180) NOT NULL,
  company VARCHAR(180) NOT NULL,
  location VARCHAR(120),
  jd_text MEDIUMTEXT NOT NULL,
  extracted_skills TEXT,
  years_required INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (recruiter_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assessments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  kind ENUM('tech','jlpt','keigo','interview') NOT NULL,
  score INT NOT NULL,
  details MEDIUMTEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS matches (
  id INT AUTO_INCREMENT PRIMARY KEY,
  job_id INT NOT NULL,
  candidate_id INT NOT NULL,
  match_score INT NOT NULL,
  gap_summary TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  FOREIGN KEY (candidate_id) REFERENCES users(id) ON DELETE CASCADE
);