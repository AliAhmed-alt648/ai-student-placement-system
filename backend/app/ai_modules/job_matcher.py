"""
Job Matching Engine
Matches students to jobs using semantic embeddings and weighted scoring
"""

import numpy as np
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger

from app.core.config import settings


class JobMatcher:
    """
    Intelligent job matching using:
    1. Sentence embeddings for semantic similarity
    2. Weighted scoring (skills, experience, education)
    3. Keyword matching for hard requirements
    """
    
    def __init__(self):
        # Load sentence transformer model
        # Options: 'all-MiniLM-L6-v2' (fast), 'all-mpnet-base-v2' (accurate)
        self.model_name = 'all-mpnet-base-v2'
        logger.info(f"Loading sentence transformer model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        
        # Matching weights (configurable)
        self.weights = {
            'skill_match': 0.60,      # 60% weight on skills
            'experience_match': 0.25,  # 25% weight on experience
            'education_match': 0.15,   # 15% weight on education
        }
        
        # Cache for embeddings
        self.embedding_cache = {}
    
    def create_student_text(self, student_data: Dict) -> str:
        """
        Create a comprehensive text representation of student profile
        for embedding generation
        """
        parts = []
        
        # Skills
        skills = student_data.get('skills', [])
        if skills:
            skill_names = [s.get('name', '') for s in skills if isinstance(s, dict)]
            if not skill_names:  # If skills are just strings
                skill_names = [s for s in skills if isinstance(s, str)]
            parts.append(f"Skills: {', '.join(skill_names)}")
        
        # Experience
        experience = student_data.get('experience', [])
        if experience:
            exp_texts = []
            for exp in experience:
                role = exp.get('role', '')
                company = exp.get('company', '')
                desc = exp.get('description', '')
                exp_texts.append(f"{role} at {company}. {desc}")
            parts.append(f"Experience: {' '.join(exp_texts)}")
        
        # Education
        education = student_data.get('education', [])
        if education:
            edu_texts = []
            for edu in education:
                degree = edu.get('degree', '')
                major = edu.get('major', '')
                institution = edu.get('institution', '')
                edu_texts.append(f"{degree} in {major} from {institution}")
            parts.append(f"Education: {' '.join(edu_texts)}")
        
        # Projects
        projects = student_data.get('projects', [])
        if projects:
            proj_texts = []
            for proj in projects:
                title = proj.get('title', '')
                desc = proj.get('description', '')
                proj_texts.append(f"{title}: {desc}")
            parts.append(f"Projects: {' '.join(proj_texts)}")
        
        # Summary
        summary = student_data.get('summary', '')
        if summary:
            parts.append(f"Summary: {summary}")
        
        return ' '.join(parts)
    
    def create_job_text(self, job_data: Dict) -> str:
        """
        Create a comprehensive text representation of job posting
        for embedding generation
        """
        parts = []
        
        # Title
        title = job_data.get('title', '')
        parts.append(f"Job Title: {title}")
        
        # Description
        description = job_data.get('description', '')
        parts.append(f"Description: {description}")
        
        # Required skills
        required_skills = job_data.get('required_skills', [])
        if required_skills:
            parts.append(f"Required Skills: {', '.join(required_skills)}")
        
        # Preferred skills
        preferred_skills = job_data.get('preferred_skills', [])
        if preferred_skills:
            parts.append(f"Preferred Skills: {', '.join(preferred_skills)}")
        
        # Requirements
        requirements = job_data.get('requirements', {})
        if requirements:
            if 'experience_years' in requirements:
                parts.append(f"Experience Required: {requirements['experience_years']} years")
            if 'education' in requirements:
                parts.append(f"Education: {', '.join(requirements['education'])}")
        
        # Responsibilities
        responsibilities = job_data.get('responsibilities', [])
        if responsibilities:
            parts.append(f"Responsibilities: {' '.join(responsibilities)}")
        
        return ' '.join(parts)
    
    def get_embedding(self, text: str, cache_key: str = None) -> np.ndarray:
        """
        Get embedding for text with optional caching
        
        Args:
            text: Text to embed
            cache_key: Optional key for caching
            
        Returns:
            Embedding vector
        """
        if cache_key and cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        if cache_key:
            self.embedding_cache[cache_key] = embedding
        
        return embedding
    
    def calculate_skill_match(self, student_skills: List, job_required_skills: List, 
                              job_preferred_skills: List = None) -> Tuple[float, List[str]]:
        """
        Calculate skill match score
        
        Returns:
            (score 0-100, list of matched skills)
        """
        if not student_skills or not job_required_skills:
            return 0.0, []
        
        # Normalize skill names
        student_skill_names = set()
        for skill in student_skills:
            if isinstance(skill, dict):
                student_skill_names.add(skill.get('name', '').lower())
            else:
                student_skill_names.add(str(skill).lower())
        
        required_skills_lower = set(s.lower() for s in job_required_skills)
        preferred_skills_lower = set(s.lower() for s in (job_preferred_skills or []))
        
        # Calculate matches
        required_matches = student_skill_names.intersection(required_skills_lower)
        preferred_matches = student_skill_names.intersection(preferred_skills_lower)
        
        # Score calculation
        required_score = len(required_matches) / len(required_skills_lower) if required_skills_lower else 0
        preferred_score = len(preferred_matches) / len(preferred_skills_lower) if preferred_skills_lower else 0
        
        # Weighted: 80% required, 20% preferred
        total_score = (required_score * 0.8 + preferred_score * 0.2) * 100
        
        # Get matched skill names
        matched_skills = list(required_matches.union(preferred_matches))
        
        return total_score, matched_skills
    
    def calculate_experience_match(self, student_experience_years: float, 
                                   job_requirements: Dict) -> float:
        """
        Calculate experience match score
        
        Returns:
            Score 0-100
        """
        required_years = job_requirements.get('experience_years', 0)
        
        if required_years == 0:
            return 100.0  # No experience required
        
        if student_experience_years >= required_years:
            # Perfect match or overqualified
            if student_experience_years <= required_years * 1.5:
                return 100.0
            else:
                # Slightly penalize overqualification
                return max(80.0, 100.0 - (student_experience_years - required_years * 1.5) * 5)
        else:
            # Underqualified - linear penalty
            ratio = student_experience_years / required_years
            return ratio * 100
    
    def calculate_education_match(self, student_education: List[Dict], 
                                  job_requirements: Dict) -> float:
        """
        Calculate education match score
        
        Returns:
            Score 0-100
        """
        required_education = job_requirements.get('education', [])
        
        if not required_education:
            return 100.0  # No specific education required
        
        if not student_education:
            return 0.0
        
        # Education level mapping
        education_levels = {
            'high school': 1,
            'diploma': 2,
            'associate': 2,
            'bachelor': 3,
            'b.tech': 3,
            'b.e.': 3,
            'b.sc': 3,
            'master': 4,
            'm.tech': 4,
            'm.e.': 4,
            'm.sc': 4,
            'mba': 4,
            'phd': 5,
            'doctorate': 5,
        }
        
        # Get student's highest education level
        student_max_level = 0
        for edu in student_education:
            degree = edu.get('degree', '').lower()
            for key, level in education_levels.items():
                if key in degree:
                    student_max_level = max(student_max_level, level)
        
        # Get required education level
        required_level = 0
        for req in required_education:
            req_lower = req.lower()
            for key, level in education_levels.items():
                if key in req_lower:
                    required_level = max(required_level, level)
        
        if student_max_level >= required_level:
            return 100.0
        else:
            # Partial credit for lower education
            return (student_max_level / required_level) * 70 if required_level > 0 else 0
    
    def calculate_semantic_similarity(self, student_text: str, job_text: str) -> float:
        """
        Calculate semantic similarity using embeddings
        
        Returns:
            Similarity score 0-100
        """
        student_embedding = self.get_embedding(student_text)
        job_embedding = self.get_embedding(job_text)
        
        # Reshape for cosine_similarity
        student_embedding = student_embedding.reshape(1, -1)
        job_embedding = job_embedding.reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(student_embedding, job_embedding)[0][0]
        
        # Convert to 0-100 scale
        return (similarity + 1) / 2 * 100  # Cosine similarity is in [-1, 1]
    
    def match_student_to_job(self, student_data: Dict, job_data: Dict) -> Dict:
        """
        Main matching function - calculates comprehensive match score
        
        Args:
            student_data: Student profile data
            job_data: Job posting data
            
        Returns:
            {
                'match_score': 0-100,
                'skill_match_score': 0-100,
                'experience_match_score': 0-100,
                'education_match_score': 0-100,
                'semantic_similarity': 0-100,
                'matched_skills': [...],
                'missing_skills': [...],
                'recommendation': 'Excellent'|'Good'|'Fair'|'Poor'
            }
        """
        # 1. Skill matching
        skill_score, matched_skills = self.calculate_skill_match(
            student_data.get('skills', []),
            job_data.get('required_skills', []),
            job_data.get('preferred_skills', [])
        )
        
        # 2. Experience matching
        experience_score = self.calculate_experience_match(
            student_data.get('total_experience_years', 0),
            job_data.get('requirements', {})
        )
        
        # 3. Education matching
        education_score = self.calculate_education_match(
            student_data.get('education', []),
            job_data.get('requirements', {})
        )
        
        # 4. Semantic similarity (optional boost)
        student_text = self.create_student_text(student_data)
        job_text = self.create_job_text(job_data)
        semantic_score = self.calculate_semantic_similarity(student_text, job_text)
        
        # 5. Calculate weighted final score
        final_score = (
            skill_score * self.weights['skill_match'] +
            experience_score * self.weights['experience_match'] +
            education_score * self.weights['education_match']
        )
        
        # 6. Apply semantic similarity as a small boost (max +5 points)
        semantic_boost = (semantic_score / 100) * 5
        final_score = min(100, final_score + semantic_boost)
        
        # 7. Determine missing skills
        student_skill_names = set()
        for skill in student_data.get('skills', []):
            if isinstance(skill, dict):
                student_skill_names.add(skill.get('name', '').lower())
            else:
                student_skill_names.add(str(skill).lower())
        
        required_skills_lower = set(s.lower() for s in job_data.get('required_skills', []))
        missing_skills = list(required_skills_lower - student_skill_names)
        
        # 8. Generate recommendation
        if final_score >= 80:
            recommendation = 'Excellent Match'
        elif final_score >= 60:
            recommendation = 'Good Match'
        elif final_score >= 40:
            recommendation = 'Fair Match'
        else:
            recommendation = 'Poor Match'
        
        return {
            'match_score': round(final_score, 2),
            'skill_match_score': round(skill_score, 2),
            'experience_match_score': round(experience_score, 2),
            'education_match_score': round(education_score, 2),
            'semantic_similarity': round(semantic_score, 2),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'recommendation': recommendation,
            'weights_used': self.weights,
        }
    
    def rank_candidates(self, candidates: List[Dict], job_data: Dict, 
                       top_k: int = None) -> List[Dict]:
        """
        Rank multiple candidates for a job
        
        Args:
            candidates: List of student data dicts
            job_data: Job posting data
            top_k: Return only top K candidates (None = all)
            
        Returns:
            List of candidates with match scores, sorted by score descending
        """
        logger.info(f"Ranking {len(candidates)} candidates for job: {job_data.get('title')}")
        
        results = []
        for candidate in candidates:
            match_result = self.match_student_to_job(candidate, job_data)
            results.append({
                'student_id': candidate.get('id'),
                'student_name': candidate.get('full_name'),
                'student_level': candidate.get('level'),
                **match_result
            })
        
        # Sort by match score descending
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Return top K if specified
        if top_k:
            results = results[:top_k]
        
        logger.info(f"Top candidate: {results[0]['student_name']} with score {results[0]['match_score']}")
        
        return results
    
    def find_jobs_for_student(self, student_data: Dict, jobs: List[Dict], 
                             top_k: int = 10) -> List[Dict]:
        """
        Find best matching jobs for a student
        
        Args:
            student_data: Student profile data
            jobs: List of job postings
            top_k: Return top K jobs
            
        Returns:
            List of jobs with match scores, sorted by score descending
        """
        logger.info(f"Finding jobs for student: {student_data.get('full_name')}")
        
        results = []
        for job in jobs:
            match_result = self.match_student_to_job(student_data, job)
            results.append({
                'job_id': job.get('id'),
                'job_title': job.get('title'),
                'company_name': job.get('company_name'),
                'location': job.get('location'),
                **match_result
            })
        
        # Sort by match score descending
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Return top K
        results = results[:top_k]
        
        logger.info(f"Top job match: {results[0]['job_title']} with score {results[0]['match_score']}")
        
        return results


# Singleton instance
job_matcher = JobMatcher()


# Convenience functions
def match_student_to_job(student_data: Dict, job_data: Dict) -> Dict:
    """Match a single student to a job"""
    return job_matcher.match_student_to_job(student_data, job_data)


def rank_candidates(candidates: List[Dict], job_data: Dict, top_k: int = None) -> List[Dict]:
    """Rank candidates for a job"""
    return job_matcher.rank_candidates(candidates, job_data, top_k)


def find_jobs_for_student(student_data: Dict, jobs: List[Dict], top_k: int = 10) -> List[Dict]:
    """Find best jobs for a student"""
    return job_matcher.find_jobs_for_student(student_data, jobs, top_k)
