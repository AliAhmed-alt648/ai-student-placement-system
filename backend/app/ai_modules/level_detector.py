"""
Student Level Detector Module
Classifies students as Beginner/Intermediate/Expert using heuristics and ML
"""

import numpy as np
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path
from loguru import logger

from app.core.config import settings


class LevelDetector:
    """
    Detects student skill level using:
    1. Heuristic rules (experience, projects, skills)
    2. ML classifier (Random Forest) trained on features
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.classifier = None
        self.model_path = Path("models/level_classifier.pkl")
        
        # Thresholds for heuristic classification
        self.thresholds = {
            'beginner': {
                'max_experience_years': 2,
                'max_projects': 3,
                'max_skills': 10,
            },
            'intermediate': {
                'min_experience_years': 2,
                'max_experience_years': 5,
                'min_projects': 3,
                'max_projects': 8,
                'min_skills': 10,
                'max_skills': 25,
            },
            'expert': {
                'min_experience_years': 5,
                'min_projects': 8,
                'min_skills': 25,
            }
        }
        
        # Seniority keywords
        self.seniority_keywords = {
            'beginner': ['intern', 'trainee', 'junior', 'fresher', 'entry', 'graduate'],
            'intermediate': ['developer', 'engineer', 'analyst', 'associate', 'mid-level'],
            'expert': ['senior', 'lead', 'principal', 'architect', 'manager', 'expert', 'specialist', 'head']
        }
        
        # Load pre-trained model if exists
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained classifier if available"""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.classifier = model_data['classifier']
                    self.scaler = model_data['scaler']
                logger.info("Loaded pre-trained level classifier")
            except Exception as e:
                logger.warning(f"Could not load model: {str(e)}")
    
    def extract_features(self, resume_data: Dict) -> np.ndarray:
        """
        Extract numerical features from resume data
        
        Features:
        1. Total experience years
        2. Number of projects
        3. Number of skills
        4. Number of certifications
        5. Education level (0=Bachelor, 1=Master, 2=PhD)
        6. Average skill proficiency
        7. Has leadership experience (0/1)
        8. Number of companies worked at
        """
        features = []
        
        # 1. Total experience years
        experience_years = resume_data.get('total_experience_years', 0)
        features.append(experience_years)
        
        # 2. Number of projects
        projects = resume_data.get('projects', [])
        features.append(len(projects))
        
        # 3. Number of skills
        skills = resume_data.get('skills', [])
        features.append(len(skills))
        
        # 4. Number of certifications
        certifications = resume_data.get('certifications', [])
        features.append(len(certifications))
        
        # 5. Education level
        education = resume_data.get('education', [])
        education_level = 0
        for edu in education:
            degree = edu.get('degree', '').lower()
            if 'phd' in degree or 'doctorate' in degree:
                education_level = max(education_level, 2)
            elif 'master' in degree or 'm.tech' in degree or 'm.sc' in degree:
                education_level = max(education_level, 1)
        features.append(education_level)
        
        # 6. Average skill proficiency
        proficiency_map = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3, 'Expert': 4}
        avg_proficiency = 0
        if skills:
            proficiencies = [proficiency_map.get(s.get('proficiency', 'Beginner'), 1) for s in skills]
            avg_proficiency = np.mean(proficiencies)
        features.append(avg_proficiency)
        
        # 7. Has leadership experience
        experience = resume_data.get('experience', [])
        has_leadership = 0
        leadership_keywords = ['lead', 'manager', 'head', 'director', 'chief', 'senior']
        for exp in experience:
            role = exp.get('role', '').lower()
            if any(keyword in role for keyword in leadership_keywords):
                has_leadership = 1
                break
        features.append(has_leadership)
        
        # 8. Number of companies
        features.append(len(experience))
        
        return np.array(features).reshape(1, -1)
    
    def detect_with_heuristics(self, resume_data: Dict) -> Tuple[str, float]:
        """
        Classify using rule-based heuristics
        
        Returns:
            (level, confidence_score)
        """
        experience_years = resume_data.get('total_experience_years', 0)
        num_projects = len(resume_data.get('projects', []))
        num_skills = len(resume_data.get('skills', []))
        experience = resume_data.get('experience', [])
        
        # Check for seniority keywords in job titles
        seniority_score = {'beginner': 0, 'intermediate': 0, 'expert': 0}
        
        for exp in experience:
            role = exp.get('role', '').lower()
            for level, keywords in self.seniority_keywords.items():
                if any(keyword in role for keyword in keywords):
                    seniority_score[level] += 1
        
        # Rule-based classification
        scores = {
            'Beginner': 0,
            'Intermediate': 0,
            'Expert': 0
        }
        
        # Experience-based scoring
        if experience_years <= self.thresholds['beginner']['max_experience_years']:
            scores['Beginner'] += 3
        elif experience_years <= self.thresholds['intermediate']['max_experience_years']:
            scores['Intermediate'] += 3
        else:
            scores['Expert'] += 3
        
        # Project-based scoring
        if num_projects <= self.thresholds['beginner']['max_projects']:
            scores['Beginner'] += 2
        elif num_projects <= self.thresholds['intermediate']['max_projects']:
            scores['Intermediate'] += 2
        else:
            scores['Expert'] += 2
        
        # Skill-based scoring
        if num_skills <= self.thresholds['beginner']['max_skills']:
            scores['Beginner'] += 2
        elif num_skills <= self.thresholds['intermediate']['max_skills']:
            scores['Intermediate'] += 2
        else:
            scores['Expert'] += 2
        
        # Seniority keyword scoring
        scores['Beginner'] += seniority_score['beginner']
        scores['Intermediate'] += seniority_score['intermediate']
        scores['Expert'] += seniority_score['expert']
        
        # Determine level
        max_score = max(scores.values())
        level = max(scores, key=scores.get)
        
        # Calculate confidence (0-100)
        total_score = sum(scores.values())
        confidence = (max_score / total_score * 100) if total_score > 0 else 50
        
        return level, confidence
    
    def detect_with_ml(self, resume_data: Dict) -> Tuple[str, float]:
        """
        Classify using ML model
        
        Returns:
            (level, confidence_score)
        """
        if not self.classifier:
            logger.warning("ML classifier not available, falling back to heuristics")
            return self.detect_with_heuristics(resume_data)
        
        try:
            # Extract features
            features = self.extract_features(resume_data)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict
            prediction = self.classifier.predict(features_scaled)[0]
            probabilities = self.classifier.predict_proba(features_scaled)[0]
            
            # Map prediction to level
            level_map = {0: 'Beginner', 1: 'Intermediate', 2: 'Expert'}
            level = level_map[prediction]
            
            # Confidence is the probability of predicted class
            confidence = probabilities[prediction] * 100
            
            return level, confidence
        
        except Exception as e:
            logger.error(f"ML classification failed: {str(e)}")
            return self.detect_with_heuristics(resume_data)
    
    def detect_level(self, resume_data: Dict, use_ml: bool = False) -> Dict[str, any]:
        """
        Main detection function
        
        Args:
            resume_data: Parsed resume data
            use_ml: Whether to use ML classifier (if available)
            
        Returns:
            {
                'level': 'Beginner'|'Intermediate'|'Expert',
                'confidence': 0-100,
                'method': 'heuristic'|'ml',
                'features': {...}
            }
        """
        if use_ml and self.classifier:
            level, confidence = self.detect_with_ml(resume_data)
            method = 'ml'
        else:
            level, confidence = self.detect_with_heuristics(resume_data)
            method = 'heuristic'
        
        # Extract features for transparency
        features = self.extract_features(resume_data).flatten().tolist()
        feature_names = [
            'experience_years', 'num_projects', 'num_skills', 'num_certifications',
            'education_level', 'avg_skill_proficiency', 'has_leadership', 'num_companies'
        ]
        
        return {
            'level': level,
            'confidence': round(confidence, 2),
            'method': method,
            'features': dict(zip(feature_names, features)),
            'reasoning': self._generate_reasoning(resume_data, level)
        }
    
    def _generate_reasoning(self, resume_data: Dict, level: str) -> str:
        """Generate human-readable reasoning for classification"""
        experience_years = resume_data.get('total_experience_years', 0)
        num_projects = len(resume_data.get('projects', []))
        num_skills = len(resume_data.get('skills', []))
        
        if level == 'Beginner':
            return f"Classified as Beginner based on {experience_years:.1f} years of experience, {num_projects} projects, and {num_skills} skills."
        elif level == 'Intermediate':
            return f"Classified as Intermediate with {experience_years:.1f} years of experience, {num_projects} projects, and {num_skills} skills."
        else:
            return f"Classified as Expert with {experience_years:.1f} years of experience, {num_projects} projects, and {num_skills} skills."
    
    def train_classifier(self, training_data: List[Dict], labels: List[str]):
        """
        Train the ML classifier on labeled data
        
        Args:
            training_data: List of resume data dicts
            labels: List of labels ('Beginner', 'Intermediate', 'Expert')
        """
        logger.info(f"Training classifier on {len(training_data)} samples...")
        
        # Extract features
        X = np.vstack([self.extract_features(data) for data in training_data])
        
        # Encode labels
        label_map = {'Beginner': 0, 'Intermediate': 1, 'Expert': 2}
        y = np.array([label_map[label] for label in labels])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Random Forest
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.classifier.fit(X_scaled, y)
        
        # Save model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'classifier': self.classifier,
                'scaler': self.scaler
            }, f)
        
        logger.info(f"Classifier trained and saved to {self.model_path}")
        
        # Print feature importances
        feature_names = [
            'experience_years', 'num_projects', 'num_skills', 'num_certifications',
            'education_level', 'avg_skill_proficiency', 'has_leadership', 'num_companies'
        ]
        importances = self.classifier.feature_importances_
        for name, importance in zip(feature_names, importances):
            logger.info(f"  {name}: {importance:.3f}")


# Singleton instance
level_detector = LevelDetector()


# Convenience function
def detect_level(resume_data: Dict, use_ml: bool = False) -> Dict[str, any]:
    """Detect student level from resume data"""
    return level_detector.detect_level(resume_data, use_ml)
