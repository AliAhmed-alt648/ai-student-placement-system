"""
AI Interview Agent
Generates tailored interview questions and auto-evaluates answers using GPT-4
"""

import json
from typing import Dict, List, Any
from openai import OpenAI
from loguru import logger

from app.core.config import settings


class InterviewAgent:
    """
    AI-powered interview system that:
    1. Generates 10 tailored questions based on job and student level
    2. Evaluates text/audio answers using LLM scoring
    3. Produces detailed evaluation reports
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Interview configuration
        self.config = {
            'total_questions': 10,
            'mcq_count': 4,
            'scenario_count': 3,
            'technical_count': 3,
        }
        
        # Question types
        self.question_types = ['MCQ', 'ShortAnswer', 'Coding', 'Scenario']
    
    def generate_interview_questions(self, job_data: Dict, student_data: Dict) -> Dict:
        """
        Generate 10 tailored interview questions
        
        Args:
            job_data: Job posting data
            student_data: Student profile data
            
        Returns:
            {
                'questions': [...],
                'total_points': X,
                'estimated_duration_minutes': Y
            }
        """
        job_title = job_data.get('title', 'Software Developer')
        required_skills = job_data.get('required_skills', [])
        job_description = job_data.get('description', '')
        seniority = job_data.get('seniority', 'Mid')
        
        student_level = student_data.get('level', 'Intermediate')
        student_skills = [s.get('name') if isinstance(s, dict) else s 
                         for s in student_data.get('skills', [])]
        
        # Create prompt for GPT-4
        prompt = f"""You are an expert technical interviewer. Generate 10 interview questions for the following job and candidate profile.

**Job Details:**
- Title: {job_title}
- Seniority: {seniority}
- Required Skills: {', '.join(required_skills[:10])}
- Description: {job_description[:500]}

**Candidate Profile:**
- Level: {student_level}
- Skills: {', '.join(student_skills[:15])}

**Requirements:**
1. Generate exactly 10 questions with this distribution:
   - 4 Multiple Choice Questions (MCQ) - concept checks
   - 3 Scenario-based questions - problem-solving and decision-making
   - 3 Technical questions - coding/design/explanation based on required skills

2. Tailor difficulty to candidate level:
   - Beginner: Focus on fundamentals and basic concepts
   - Intermediate: Mix of concepts and practical application
   - Expert: Advanced topics, system design, best practices

3. For each question, provide:
   - id: Unique identifier (Q1, Q2, etc.)
   - type: "MCQ", "Scenario", "Technical", or "ShortAnswer"
   - text: The question text
   - options: Array of 4 options (for MCQ only)
   - correct_answer: Correct option letter (for MCQ) or expected keywords (for others)
   - points: Points for this question (total should be 100)
   - difficulty: "Easy", "Medium", or "Hard"
   - skill_tested: Primary skill being tested
   - rubric: Scoring criteria with point breakdown

**Output Format (JSON only):**
```json
{{
  "questions": [
    {{
      "id": "Q1",
      "type": "MCQ",
      "text": "What is...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_answer": "B",
      "points": 8,
      "difficulty": "Easy",
      "skill_tested": "Python",
      "rubric": "Correct answer: 8 points. Incorrect: 0 points."
    }},
    {{
      "id": "Q2",
      "type": "Scenario",
      "text": "You are tasked with...",
      "correct_answer": ["scalability", "caching", "load balancing"],
      "points": 12,
      "difficulty": "Medium",
      "skill_tested": "System Design",
      "rubric": "Mentions scalability (4 pts), caching (4 pts), load balancing (4 pts). Clear explanation (bonus 2 pts)."
    }}
  ],
  "total_points": 100,
  "estimated_duration_minutes": 30
}}
```

Generate the questions now:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer. Generate interview questions in valid JSON format only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Some creativity for varied questions
                max_tokens=3000,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            questions_data = json.loads(result_text)
            
            logger.info(f"Generated {len(questions_data['questions'])} questions for {job_title}")
            
            return questions_data
        
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            # Return fallback generic questions
            return self._generate_fallback_questions(job_title, student_level)
    
    def _generate_fallback_questions(self, job_title: str, level: str) -> Dict:
        """Generate basic fallback questions if GPT fails"""
        return {
            "questions": [
                {
                    "id": "Q1",
                    "type": "MCQ",
                    "text": "What is your primary motivation for applying to this position?",
                    "options": [
                        "A) Career growth and learning opportunities",
                        "B) Competitive salary and benefits",
                        "C) Company reputation and culture",
                        "D) Work-life balance"
                    ],
                    "correct_answer": "A",
                    "points": 10,
                    "difficulty": "Easy",
                    "skill_tested": "Motivation",
                    "rubric": "Any answer acceptable. Looking for genuine interest."
                },
                {
                    "id": "Q2",
                    "type": "ShortAnswer",
                    "text": f"Describe your experience with the key technologies required for this {job_title} role.",
                    "correct_answer": ["experience", "projects", "skills"],
                    "points": 15,
                    "difficulty": "Medium",
                    "skill_tested": "Technical Background",
                    "rubric": "Mentions relevant experience (5 pts), specific projects (5 pts), demonstrates depth (5 pts)."
                },
                # Add 8 more generic questions...
            ],
            "total_points": 100,
            "estimated_duration_minutes": 25
        }
    
    def evaluate_answer(self, question: Dict, student_answer: str) -> Dict:
        """
        Evaluate a single answer using GPT-4
        
        Args:
            question: Question dict with rubric
            student_answer: Student's text answer
            
        Returns:
            {
                'score': X,
                'max_score': Y,
                'feedback': '...',
                'key_points_covered': [...],
                'key_points_missed': [...]
            }
        """
        question_type = question.get('type')
        
        # For MCQ, simple comparison
        if question_type == 'MCQ':
            return self._evaluate_mcq(question, student_answer)
        
        # For other types, use GPT for evaluation
        return self._evaluate_with_gpt(question, student_answer)
    
    def _evaluate_mcq(self, question: Dict, student_answer: str) -> Dict:
        """Evaluate MCQ answer"""
        correct_answer = question.get('correct_answer', '').upper()
        student_answer_clean = student_answer.strip().upper()
        
        # Extract letter from answer (handles "A", "A)", "Option A", etc.)
        import re
        match = re.search(r'[ABCD]', student_answer_clean)
        if match:
            student_letter = match.group(0)
        else:
            student_letter = student_answer_clean[0] if student_answer_clean else ''
        
        is_correct = student_letter == correct_answer
        max_score = question.get('points', 10)
        score = max_score if is_correct else 0
        
        return {
            'score': score,
            'max_score': max_score,
            'feedback': f"{'Correct!' if is_correct else f'Incorrect. The correct answer is {correct_answer}.'}",
            'key_points_covered': [correct_answer] if is_correct else [],
            'key_points_missed': [] if is_correct else [correct_answer],
        }
    
    def _evaluate_with_gpt(self, question: Dict, student_answer: str) -> Dict:
        """Evaluate open-ended answer using GPT-4"""
        prompt = f"""You are an expert interviewer evaluating a candidate's answer. Be fair but thorough.

**Question:**
{question.get('text')}

**Expected Answer/Keywords:**
{question.get('correct_answer')}

**Scoring Rubric:**
{question.get('rubric')}

**Maximum Points:** {question.get('points')}

**Student's Answer:**
{student_answer}

**Evaluation Task:**
1. Score the answer based on the rubric (0 to {question.get('points')} points)
2. Provide constructive feedback (2-3 sentences)
3. List key points the student covered
4. List key points the student missed

**Output Format (JSON only):**
```json
{{
  "score": X,
  "max_score": {question.get('points')},
  "feedback": "...",
  "key_points_covered": ["...", "..."],
  "key_points_missed": ["...", "..."]
}}
```

Evaluate now:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a fair and thorough interviewer. Evaluate answers objectively and provide constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for consistent scoring
                max_tokens=500,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            evaluation = json.loads(result_text)
            return evaluation
        
        except Exception as e:
            logger.error(f"Answer evaluation failed: {str(e)}")
            # Fallback: basic keyword matching
            return self._evaluate_with_keywords(question, student_answer)
    
    def _evaluate_with_keywords(self, question: Dict, student_answer: str) -> Dict:
        """Fallback evaluation using keyword matching"""
        expected_keywords = question.get('correct_answer', [])
        if isinstance(expected_keywords, str):
            expected_keywords = [expected_keywords]
        
        answer_lower = student_answer.lower()
        keywords_found = [kw for kw in expected_keywords if kw.lower() in answer_lower]
        
        max_score = question.get('points', 10)
        score = (len(keywords_found) / len(expected_keywords)) * max_score if expected_keywords else max_score * 0.5
        
        return {
            'score': round(score, 1),
            'max_score': max_score,
            'feedback': f"Found {len(keywords_found)} out of {len(expected_keywords)} key concepts.",
            'key_points_covered': keywords_found,
            'key_points_missed': [kw for kw in expected_keywords if kw not in keywords_found],
        }
    
    def evaluate_interview(self, questions: List[Dict], answers: List[Dict]) -> Dict:
        """
        Evaluate complete interview
        
        Args:
            questions: List of question dicts
            answers: List of answer dicts with {question_id, answer_text}
            
        Returns:
            {
                'per_question_scores': [...],
                'overall_score': X,
                'total_points': Y,
                'earned_points': Z,
                'percentage': P,
                'grade': 'A'|'B'|'C'|'D'|'F',
                'summary': '...'
            }
        """
        logger.info(f"Evaluating interview with {len(questions)} questions")
        
        # Create answer lookup
        answer_map = {ans.get('question_id'): ans.get('answer_text', '') 
                     for ans in answers}
        
        # Evaluate each question
        per_question_scores = []
        total_earned = 0
        total_possible = 0
        
        for question in questions:
            question_id = question.get('id')
            student_answer = answer_map.get(question_id, '')
            
            if not student_answer:
                # No answer provided
                evaluation = {
                    'score': 0,
                    'max_score': question.get('points', 10),
                    'feedback': 'No answer provided.',
                    'key_points_covered': [],
                    'key_points_missed': question.get('correct_answer', []),
                }
            else:
                evaluation = self.evaluate_answer(question, student_answer)
            
            per_question_scores.append({
                'question_id': question_id,
                'question_text': question.get('text'),
                'student_answer': student_answer,
                **evaluation
            })
            
            total_earned += evaluation['score']
            total_possible += evaluation['max_score']
        
        # Calculate overall metrics
        percentage = (total_earned / total_possible * 100) if total_possible > 0 else 0
        
        # Assign grade
        if percentage >= 90:
            grade = 'A'
        elif percentage >= 80:
            grade = 'B'
        elif percentage >= 70:
            grade = 'C'
        elif percentage >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        # Generate summary
        summary = self._generate_summary(per_question_scores, percentage, grade)
        
        result = {
            'per_question_scores': per_question_scores,
            'overall_score': round(percentage, 2),
            'total_points': total_possible,
            'earned_points': round(total_earned, 2),
            'percentage': round(percentage, 2),
            'grade': grade,
            'summary': summary,
        }
        
        logger.info(f"Interview evaluation complete. Score: {percentage:.1f}% (Grade: {grade})")
        
        return result
    
    def _generate_summary(self, per_question_scores: List[Dict], 
                         percentage: float, grade: str) -> str:
        """Generate human-readable summary of interview performance"""
        total_questions = len(per_question_scores)
        questions_correct = sum(1 for q in per_question_scores 
                               if q['score'] >= q['max_score'] * 0.7)
        
        strengths = []
        weaknesses = []
        
        for q in per_question_scores:
            skill = q.get('skill_tested', 'General')
            if q['score'] >= q['max_score'] * 0.8:
                strengths.append(skill)
            elif q['score'] < q['max_score'] * 0.5:
                weaknesses.append(skill)
        
        summary = f"Interview Performance: {grade} ({percentage:.1f}%)\n\n"
        summary += f"Answered {questions_correct} out of {total_questions} questions well.\n\n"
        
        if strengths:
            summary += f"Strengths: {', '.join(set(strengths))}\n"
        
        if weaknesses:
            summary += f"Areas for Improvement: {', '.join(set(weaknesses))}\n"
        
        if percentage >= 80:
            summary += "\nExcellent performance! Strong candidate for the position."
        elif percentage >= 60:
            summary += "\nGood performance with room for improvement in some areas."
        else:
            summary += "\nNeeds significant improvement. Consider additional training."
        
        return summary


# Singleton instance
interview_agent = InterviewAgent()


# Convenience functions
def generate_interview_questions(job_data: Dict, student_data: Dict) -> Dict:
    """Generate interview questions"""
    return interview_agent.generate_interview_questions(job_data, student_data)


def evaluate_interview(questions: List[Dict], answers: List[Dict]) -> Dict:
    """Evaluate complete interview"""
    return interview_agent.evaluate_interview(questions, answers)


def evaluate_answer(question: Dict, student_answer: str) -> Dict:
    """Evaluate single answer"""
    return interview_agent.evaluate_answer(question, student_answer)
