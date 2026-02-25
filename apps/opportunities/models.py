from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import URLValidator
import hashlib

User = get_user_model()


class University(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    website = models.URLField()
    opportunities_url = models.URLField()
    is_ivy_league = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='university_logos/', null=True, blank=True)
    description = models.TextField(blank=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Universities"


class Opportunity(models.Model):
    OPPORTUNITY_TYPES = (
        ('workshop', 'Workshop'),
        ('hackathon', 'Hackathon'),
        ('internship', 'Internship'),
        ('research', 'Research Position'),
        ('scholarship', 'Scholarship'),
        ('conference', 'Conference'),
        ('course', 'Course'),
        ('fellowship', 'Fellowship'),
        ('competition', 'Competition'),
        ('job', 'Job'),
    )
    
    DOMAIN_CHOICES = (
        ('ai', 'Artificial Intelligence'),
        ('ml', 'Machine Learning'),
        ('ds', 'Data Science'),
        ('cs', 'Computer Science'),
        ('ece', 'Electrical & Computer Engineering'),
        ('mech', 'Mechanical Engineering'),
        ('bio', 'Biomedical'),
        ('chem', 'Chemistry'),
        ('physics', 'Physics'),
        ('math', 'Mathematics'),
        ('business', 'Business'),
        ('law', 'Law'),
        ('medicine', 'Medicine'),
        ('humanities', 'Humanities'),
        ('arts', 'Arts'),
        ('social_sciences', 'Social Sciences'),
    )
    
    title = models.CharField(max_length=500)
    description = models.TextField()
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPES)
    domain = models.CharField(max_length=20, choices=DOMAIN_CHOICES, null=True, blank=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='opportunities')
    external_url = models.URLField()
    application_url = models.URLField(blank=True)
    deadline = models.DateTimeField()
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_remote = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    stipend = models.CharField(max_length=100, blank=True)
    eligibility_criteria = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    requirements = models.JSONField(default=list)
    tags = models.JSONField(default=list)
    
    # Metadata
    source_url = models.URLField()
    source_id = models.CharField(max_length=200, blank=True)
    source_hash = models.CharField(max_length=64, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)
    applications_count = models.IntegerField(default=0)
    saved_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.source_hash:
            # Create unique hash based on title and university
            hash_string = f"{self.title}{self.university_id}{self.external_url}"
            self.source_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.university.name}"
    
    class Meta:
        verbose_name_plural = "Opportunities"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['domain', '-created_at']),
            models.Index(fields=['deadline']),
            models.Index(fields=['university', 'opportunity_type']),
            models.Index(fields=['source_hash']),
        ]


class UserOpportunity(models.Model):
    STATUS_CHOICES = (
        ('saved', 'Saved'),
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('interview', 'Interview'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opportunities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='saved')
    applied_date = models.DateTimeField(null=True, blank=True)
    application_data = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    reminder_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'opportunity']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reminder_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.opportunity.title}"


class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    submitted_data = models.JSONField()
    resume_used = models.FileField(upload_to='applications/resumes/')
    cover_letter = models.FileField(upload_to='applications/cover_letters/', null=True, blank=True)
    additional_documents = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=UserOpportunity.STATUS_CHOICES, default='applied')
    confirmation_email = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.opportunity.title}"
    
    class Meta:
        ordering = ['-submitted_at']


class OpportunityAlert(models.Model):
    FREQUENCY_CHOICES = (
        ('instant', 'Instant'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    keywords = models.CharField(max_length=500)
    domains = models.JSONField(default=list)
    opportunity_types = models.JSONField(default=list)
    universities = models.JSONField(default=list)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.keywords}"