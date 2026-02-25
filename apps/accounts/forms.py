from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, StudentAchievement


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'profile_picture', 'bio',
            'university', 'graduation_year', 'major', 'gpa', 'skills',
            'interests', 'resume', 'linkedin_url', 'github_url', 'portfolio_url'
        )
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter skills separated by commas'}),
            'interests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter interests separated by commas'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean_skills(self):
        skills = self.cleaned_data.get('skills')
        if skills and isinstance(skills, str):
            return [s.strip() for s in skills.split(',')]
        return skills
    
    def clean_interests(self):
        interests = self.cleaned_data.get('interests')
        if interests and isinstance(interests, str):
            return [i.strip() for i in interests.split(',')]
        return interests


class StudentAchievementForm(forms.ModelForm):
    class Meta:
        model = StudentAchievement
        fields = ('achievement_type', 'title', 'description', 'organization', 
                 'date_achieved', 'certificate_url', 'proof_file')
        widgets = {
            'date_achieved': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }