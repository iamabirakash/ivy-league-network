import numpy as np
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from apps.accounts.models import User, StudentAchievement
from apps.opportunities.models import UserOpportunity
import logging
import re

logger = logging.getLogger(__name__)

class InCoScoreCalculator:
    """
    Intelligent Competency Score Calculator
    """
    
    def __init__(self):
        # Weights for different components
        self.weights = {
            'academic': 0.25,
            'research': 0.20,
            'projects': 0.15,
            'hackathons': 0.15,
            'internships': 0.15,
            'certifications': 0.10,
        }
        
        # Decay factor for older achievements
        self.time_decay = 0.95  # 5% decay per month
        
    def calculate_score(self, user_id):
        """Calculate InCoScore for a user"""
        try:
            user = User.objects.get(id=user_id)
            
            scores = {
                'academic': self._calculate_academic_score(user),
                'research': self._calculate_research_score(user),
                'projects': self._calculate_projects_score(user),
                'hackathons': self._calculate_hackathon_score(user),
                'internships': self._calculate_internship_score(user),
                'certifications': self._calculate_certification_score(user),
            }
            
            logger.debug(f"Scores for {user.username}: {scores}")
            
            # Apply weights
            total_score = sum(
                scores[key] * self.weights[key] 
                for key in scores
            )
            
            # Apply time decay for older activities
            account_age_days = (timezone.now() - user.date_joined).days
            if account_age_days > 365:
                decay_factor = self.time_decay ** (account_age_days / 30)  # Monthly decay
                total_score *= decay_factor
            
            # Normalize to 0-100 scale
            normalized_score = min(100, max(0, total_score * 10))
            
            # Update user's score
            user.incoscore = round(normalized_score, 2)
            user.save()
            
            logger.info(f"Calculated InCoScore for {user.username}: {user.incoscore}")
            return user.incoscore
            
        except Exception as e:
            logger.error(f"Error calculating score for user {user_id}: {str(e)}")
            return 0
    
    def _calculate_academic_score(self, user):
        """Calculate academic performance score"""
        score = 0
        
        # GPA contribution
        if user.gpa:
            # Scale GPA to 0-10 (assuming 4.0 scale)
            gpa_score = (user.gpa / 4.0) * 10
            score += gpa_score * 0.4
        
        # Course completion (if tracking courses)
        completed_courses = getattr(user, 'completed_courses', [])
        course_score = min(10, len(completed_courses) / 3)  # 3 courses = 1 point
        score += course_score * 0.3
        
        # Academic awards
        academic_awards = StudentAchievement.objects.filter(
            user=user,
            achievement_type='certification',
            verified=True
        ).count()
        score += min(10, academic_awards * 2) * 0.3
        
        return score
    
    def _calculate_research_score(self, user):
        """Calculate research contribution score"""
        score = 0
        
        # Research papers
        papers = StudentAchievement.objects.filter(
            user=user,
            achievement_type='research',
            verified=True
        )
        
        for paper in papers:
            # Points based on venue quality
            venue_score = self._get_venue_score(paper.organization)
            paper_age = (timezone.now().date() - paper.date_achieved).days
            
            # Apply time decay
            decay = self.time_decay ** (paper_age / 30)
            score += venue_score * decay
        
        return min(10, score)
    
    def _calculate_projects_score(self, user):
        """Calculate project experience score"""
        score = 0
        
        projects = StudentAchievement.objects.filter(
            user=user,
            achievement_type='project',
            verified=True
        )
        
        for project in projects:
            # Complexity score based on description length and keywords
            complexity = self._assess_project_complexity(project.description)
            score += complexity
        
        # GitHub contributions if linked
        if user.github_url:
            # Would integrate with GitHub API
            github_score = self._fetch_github_stats(user.github_url)
            score += github_score * 0.3
        
        return min(10, score)
    
    def _calculate_hackathon_score(self, user):
        """Calculate hackathon participation and wins"""
        score = 0
        
        hackathons = StudentAchievement.objects.filter(
            user=user,
            achievement_type='hackathon',
            verified=True
        )
        
        for hackathon in hackathons:
            # Base participation points
            base_points = 2
            
            # Check if it was a win (based on title/description)
            if any(word in hackathon.title.lower() for word in ['win', 'winner', '1st', 'first', 'champion']):
                base_points *= 3
            elif any(word in hackathon.title.lower() for word in ['runner', '2nd', 'second', 'finalist']):
                base_points *= 2
            
            # Apply time decay
            hackathon_age = (timezone.now().date() - hackathon.date_achieved).days
            decay = self.time_decay ** (hackathon_age / 30)
            
            score += base_points * decay
        
        return min(10, score)
    
    def _calculate_internship_score(self, user):
        """Calculate internship experience score"""
        score = 0
        
        internships = StudentAchievement.objects.filter(
            user=user,
            achievement_type='internship',
            verified=True
        )
        
        for internship in internships:
            # Base points for internship
            base_points = 3
            
            # Bonus for prestigious companies
            if self._is_prestigious_company(internship.organization):
                base_points *= 1.5
            
            # Duration bonus (if duration mentioned in description)
            duration = self._extract_duration(internship.description)
            if duration:
                duration_bonus = min(3, duration / 30)  # 1 point per month, max 3
                base_points += duration_bonus
            
            # Apply time decay
            internship_age = (timezone.now().date() - internship.date_achieved).days
            decay = self.time_decay ** (internship_age / 30)
            
            score += base_points * decay
        
        return min(10, score)
    
    def _calculate_certification_score(self, user):
        """Calculate certification score"""
        score = 0
        
        certifications = StudentAchievement.objects.filter(
            user=user,
            achievement_type='certification',
            verified=True
        )
        
        for cert in certifications:
            # Points based on certification difficulty/relevance
            difficulty_score = self._get_certification_difficulty(cert.title, cert.organization)
            
            # Apply time decay
            cert_age = (timezone.now().date() - cert.date_achieved).days
            decay = self.time_decay ** (cert_age / 30)
            
            score += difficulty_score * decay
        
        return min(10, score)
    
    def _get_venue_score(self, organization):
        """Get score based on research venue prestige"""
        prestigious_venues = [
            'nature', 'science', 'cell', 'ieee', 'acm', 'neurips', 'icml',
            'iclr', 'cvpr', 'acl', 'naacl', 'emnlp', 'kdd', 'sigmod',
            'vldb', 'osdi', 'sosp', 'pldi', 'popl', 'fse', 'icse'
        ]
        
        org_lower = organization.lower()
        for venue in prestigious_venues:
            if venue in org_lower:
                return 8  # High prestige
        
        return 4  # Regular venue
    
    def _assess_project_complexity(self, description):
        """Assess project complexity based on description"""
        complexity_score = 2  # Base score
        
        # Keywords indicating complexity
        advanced_keywords = [
            'machine learning', 'deep learning', 'neural network', 'ai',
            'distributed', 'scalable', 'optimization', 'algorithm',
            'framework', 'architecture', 'pipeline', 'real-time',
            'full-stack', 'microservices', 'kubernetes', 'docker',
            'tensorflow', 'pytorch', 'keras', 'transformers'
        ]
        
        description_lower = description.lower()
        for keyword in advanced_keywords:
            if keyword in description_lower:
                complexity_score += 1
        
        # Length indicates detail/complexity
        word_count = len(description.split())
        if word_count > 100:
            complexity_score += 2
        elif word_count > 50:
            complexity_score += 1
        
        return min(8, complexity_score)
    
    def _fetch_github_stats(self, github_url):
        """Fetch GitHub statistics (placeholder for API integration)"""
        # This would integrate with GitHub API in production
        # For now, return a placeholder score
        return 2
    
    def _is_prestigious_company(self, organization):
        """Check if company is prestigious"""
        prestigious_companies = [
            'google', 'microsoft', 'amazon', 'meta', 'facebook', 'apple',
            'netflix', 'uber', 'airbnb', 'linkedin', 'twitter', 'salesforce',
            'oracle', 'ibm', 'intel', 'nvidia', 'amd', 'qualcomm',
            'goldman sachs', 'jpmorgan', 'morgan stanley', 'blackrock',
            'mckinsey', 'boston consulting group', 'bain', 'deloitte',
            'pwc', 'ey', 'kpmg', 'spacex', 'tesla', 'openai', 'deepmind'
        ]
        
        org_lower = organization.lower()
        for company in prestigious_companies:
            if company in org_lower:
                return True
        
        return False
    
    def _extract_duration(self, text):
        """Extract duration in days from text"""
        # Look for patterns like "3 months", "6 weeks", etc.
        patterns = [
            (r'(\d+)\s*(month|months)', 30),  # months to days multiplier
            (r'(\d+)\s*(week|weeks)', 7),      # weeks to days multiplier
            (r'(\d+)\s*(day|days)', 1),        # days multiplier
            (r'(\d+)\s*(year|years)', 365),    # years to days multiplier
        ]
        
        text_lower = text.lower()
        for pattern, multiplier in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1)) * multiplier
        
        return 0
    
    def _get_certification_difficulty(self, title, organization):
        """Get difficulty score for certification"""
        difficult_certs = [
            'aws certified', 'google cloud', 'azure', 'ccie', 'ccnp',
            'cissp', 'cism', 'pmp', 'pgmp', 'cfa', 'frm', 'caia',
            'series 7', 'series 63', 'actuarial', 'soa', 'cas'
        ]
        
        text = f"{title} {organization}".lower()
        for cert in difficult_certs:
            if cert in text:
                return 6  # Difficult certification
        
        return 3  # Regular certification


def calculate_bulk_scores():
    """Calculate scores for all users"""
    users = User.objects.all()
    calculator = InCoScoreCalculator()
    
    for user in users:
        calculator.calculate_score(user.id)
    
    logger.info(f"Updated scores for {users.count()} users")