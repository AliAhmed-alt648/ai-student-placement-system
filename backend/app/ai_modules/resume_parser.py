"""
AI Resume Parser Module
Extracts structured data from PDF/text resumes using NLP and GPT-4
"""

import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import PyPDF2
from pdfminer.high_level import extract_text as pdfminer_extract
import spacy
from openai import OpenAI
from loguru import logger

from app.core.config import settings


class ResumeParser:
    """
    AI-powered resume parser using multiple techniques:
    1. PDF text extraction (PyPDF2 + pdfminer fallback)
    2. spaCy NER for entity extraction
    3. Regex patterns for structured data
    4. GPT-4 for complex parsing and validation
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Load spaCy model (download with: python -m spacy download en_core_web_sm)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Common patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.url_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)')
        
        # Education keywords
        self.education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'diploma', 'degree',
            'b.tech', 'm.tech', 'b.e.', 'm.e.', 'b.sc', 'm.sc', 'mba', 'bba',
            'university', 'college', 'institute', 'school'
        ]
        
        # Skill categories
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'go', 'rust', 'php', 'swift', 'kotlin'],
            'web': ['react', 'angular', 'vue', 'node.js', 'django', 'flask', 'fastapi', 'express', 'html', 'css'],
            'database': ['sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins'],
            'ml_ai': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'nlp', 'computer vision'],
            'tools': ['git', 'jira', 'confluence', 'slack', 'figma', 'postman'],
        }
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF using PyPDF2 with pdfminer fallback
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            # Try PyPDF2 first (faster)
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                # If extraction is poor, try pdfminer
                if len(text.strip()) < 100:
                    logger.info("PyPDF2 extraction poor, trying pdfminer...")
                    text = pdfminer_extract(file_path)
                
                return text.strip()
        
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            # Fallback to pdfminer
            try:
                return pdfminer_extract(file_path)
            except Exception as e2:
                logger.error(f"pdfminer extraction also failed: {str(e2)}")
                raise ValueError(f"Could not extract text from PDF: {str(e2)}")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s@.+\-(),:/]', '', text)
        return text.strip()
    
    def extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extract email, phone, and URLs using regex"""
        contact = {
            'email': None,
            'phone': None,
            'linkedin': None,
            'github': None,
            'portfolio': None,
        }
        
        # Extract email
        emails = self.email_pattern.findall(text)
        if emails:
            contact['email'] = emails[0]
        
        # Extract phone
        phones = self.phone_pattern.findall(text)
        if phones:
            contact['phone'] = ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
        
        # Extract URLs
        urls = self.url_pattern.findall(text)
        for url in urls:
            url_lower = url.lower()
            if 'linkedin.com' in url_lower:
                contact['linkedin'] = url
            elif 'github.com' in url_lower:
                contact['github'] = url
            elif not contact['portfolio']:
                contact['portfolio'] = url
        
        return contact
    
    def extract_name_with_spacy(self, text: str) -> Optional[str]:
        """Extract person name using spaCy NER"""
        if not self.nlp:
            return None
        
        # Process first 500 characters (name usually at top)
        doc = self.nlp(text[:500])
        
        # Find PERSON entities
        persons = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        
        if persons:
            # Return first person name found
            return persons[0]
        
        return None
    
    def extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """Extract skills from text using keyword matching"""
        text_lower = text.lower()
        found_skills = []
        
        for category, skills in self.skill_categories.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    # Count occurrences as proficiency indicator
                    count = text_lower.count(skill.lower())
                    found_skills.append({
                        'name': skill.title(),
                        'category': category,
                        'mentions': count,
                        'proficiency': 'Advanced' if count >= 3 else 'Intermediate' if count >= 2 else 'Beginner'
                    })
        
        # Remove duplicates
        unique_skills = {skill['name']: skill for skill in found_skills}
        return list(unique_skills.values())
    
    def parse_with_gpt(self, text: str) -> Dict[str, Any]:
        """
        Use GPT-4 to parse resume and extract structured data
        This is the most powerful method but also most expensive
        """
        prompt = f"""You are an expert resume parser. Extract the following information from the resume text and return it as a JSON object.

Extract:
1. name (full name)
2. email
3. phone
4. summary (professional summary/objective)
5. education (array of objects with: degree, institution, year, gpa, major)
6. experience (array of objects with: company, role, start_date, end_date, description, achievements)
7. skills (array of objects with: name, proficiency, years_of_experience)
8. certifications (array of objects with: name, issuer, date, credential_url)
9. projects (array of objects with: title, description, technologies, url, date)
10. languages (array of objects with: language, proficiency)

For each field, also provide a confidence score (0-100) indicating how certain you are about the extraction.

Return ONLY valid JSON in this format:
{{
  "name": {{"value": "...", "confidence": 95}},
  "email": {{"value": "...", "confidence": 100}},
  "phone": {{"value": "...", "confidence": 90}},
  "summary": {{"value": "...", "confidence": 85}},
  "education": {{
    "value": [
      {{"degree": "...", "institution": "...", "year": "...", "gpa": "...", "major": "..."}}
    ],
    "confidence": 90
  }},
  "experience": {{
    "value": [
      {{"company": "...", "role": "...", "start_date": "...", "end_date": "...", "description": "...", "achievements": ["..."]}}
    ],
    "confidence": 85
  }},
  "skills": {{
    "value": [
      {{"name": "...", "proficiency": "...", "years": 3}}
    ],
    "confidence": 80
  }},
  "certifications": {{
    "value": [
      {{"name": "...", "issuer": "...", "date": "...", "url": "..."}}
    ],
    "confidence": 75
  }},
  "projects": {{
    "value": [
      {{"title": "...", "description": "...", "technologies": ["..."], "url": "...", "date": "..."}}
    ],
    "confidence": 70
  }},
  "languages": {{
    "value": [
      {{"language": "...", "proficiency": "..."}}
    ],
    "confidence": 85
  }}
}}

Resume Text:
{text[:4000]}  # Limit to 4000 chars to avoid token limits
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # or gpt-4-turbo
                messages=[
                    {"role": "system", "content": "You are an expert resume parser. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            parsed_data = json.loads(result_text)
            return parsed_data
        
        except Exception as e:
            logger.error(f"GPT parsing failed: {str(e)}")
            return {}
    
    def calculate_total_experience(self, experience: List[Dict]) -> float:
        """Calculate total years of experience from experience array"""
        # Simple heuristic: count number of positions
        # TODO: Parse dates and calculate actual duration
        return len(experience) * 1.5  # Assume 1.5 years per position on average
    
    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """
        Main parsing function - combines all techniques
        
        Args:
            file_path: Path to resume PDF file
            
        Returns:
            Structured resume data with confidence scores
        """
        logger.info(f"Parsing resume: {file_path}")
        
        # Step 1: Extract text
        text = self.extract_text_from_pdf(file_path)
        cleaned_text = self.clean_text(text)
        
        logger.info(f"Extracted {len(cleaned_text)} characters")
        
        # Step 2: Extract contact info with regex
        contact_info = self.extract_contact_info(cleaned_text)
        
        # Step 3: Extract name with spaCy
        name = self.extract_name_with_spacy(cleaned_text)
        
        # Step 4: Extract skills with keyword matching
        skills = self.extract_skills(cleaned_text)
        
        # Step 5: Use GPT for comprehensive parsing
        gpt_result = self.parse_with_gpt(cleaned_text)
        
        # Step 6: Merge results (GPT takes precedence, fallback to regex/spacy)
        final_result = {
            'name': gpt_result.get('name', {}).get('value') or name or contact_info.get('email', '').split('@')[0],
            'email': gpt_result.get('email', {}).get('value') or contact_info['email'],
            'phone': gpt_result.get('phone', {}).get('value') or contact_info['phone'],
            'linkedin': contact_info.get('linkedin'),
            'github': contact_info.get('github'),
            'portfolio': contact_info.get('portfolio'),
            'summary': gpt_result.get('summary', {}).get('value'),
            'education': gpt_result.get('education', {}).get('value', []),
            'experience': gpt_result.get('experience', {}).get('value', []),
            'skills': gpt_result.get('skills', {}).get('value', skills),
            'certifications': gpt_result.get('certifications', {}).get('value', []),
            'projects': gpt_result.get('projects', {}).get('value', []),
            'languages': gpt_result.get('languages', {}).get('value', []),
            'raw_text': cleaned_text,
            'confidence_scores': {
                'name': gpt_result.get('name', {}).get('confidence', 50),
                'email': gpt_result.get('email', {}).get('confidence', 100 if contact_info['email'] else 0),
                'phone': gpt_result.get('phone', {}).get('confidence', 90 if contact_info['phone'] else 0),
                'education': gpt_result.get('education', {}).get('confidence', 70),
                'experience': gpt_result.get('experience', {}).get('confidence', 70),
                'skills': gpt_result.get('skills', {}).get('confidence', 80),
                'overall': 75,  # Average confidence
            }
        }
        
        # Calculate total experience
        final_result['total_experience_years'] = self.calculate_total_experience(
            final_result['experience']
        )
        
        logger.info(f"Parsing complete. Found {len(final_result['skills'])} skills, "
                   f"{len(final_result['experience'])} experiences")
        
        return final_result


# Singleton instance
resume_parser = ResumeParser()


# Convenience function
def parse_resume(file_path: str) -> Dict[str, Any]:
    """Parse resume from file path"""
    return resume_parser.parse_resume(file_path)
