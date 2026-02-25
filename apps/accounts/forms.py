from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, StudentAchievement
import ast
import json
import re


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
    skills = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter skills separated by commas'}),
    )
    interests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter interests separated by commas'}),
    )

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'profile_picture', 'bio',
            'university', 'graduation_year', 'major', 'gpa', 'skills',
            'interests', 'resume', 'linkedin_url', 'github_url', 'portfolio_url'
        )
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def _normalize_list(self, value):
        """Normalize list-like JSON/string values into a clean list of strings."""
        current = value

        # Unwrap nested serialized strings a few times.
        for _ in range(5):
            if isinstance(current, str):
                text = current.strip()
                if not text:
                    return []
                parsed = None
                try:
                    parsed = json.loads(text)
                except Exception:
                    try:
                        parsed = ast.literal_eval(text)
                    except Exception:
                        parsed = None
                if parsed is None:
                    current = [text]
                    break
                current = parsed
            else:
                break

        if isinstance(current, (tuple, set)):
            current = list(current)
        if not isinstance(current, list):
            current = [current] if current not in (None, "") else []

        result = []
        for item in current:
            if isinstance(item, (list, tuple, set)):
                result.extend(self._normalize_list(list(item)))
                continue
            text = str(item).strip()
            if not text or text in {"[]", "['']", '[""]'}:
                continue
            # Ignore strings that are effectively only punctuation/brackets.
            if not re.sub(r"[\[\]\(\)\{\}'\"\\,]", "", text).strip():
                continue
            # If list items are themselves serialized, try one more normalize pass.
            if (text.startswith("[") and text.endswith("]")) or (text.startswith("{") and text.endswith("}")):
                nested = self._normalize_list(text)
                if nested:
                    result.extend(nested)
                    continue
                # If nested parsing yields nothing, treat as junk.
                continue
            result.append(text)

        # De-duplicate while preserving order.
        seen = set()
        deduped = []
        for item in result:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['skills'].initial = ', '.join(self._normalize_list(self.instance.skills))
            self.fields['interests'].initial = ', '.join(self._normalize_list(self.instance.interests))
    
    def clean_skills(self):
        skills = self.cleaned_data.get('skills', '')
        return self._normalize_list([s.strip() for s in skills.split(',') if s.strip()])
    
    def clean_interests(self):
        interests = self.cleaned_data.get('interests', '')
        return self._normalize_list([i.strip() for i in interests.split(',') if i.strip()])


class StudentAchievementForm(forms.ModelForm):
    class Meta:
        model = StudentAchievement
        fields = ('achievement_type', 'title', 'description', 'organization', 
                 'date_achieved', 'certificate_url', 'proof_file')
        widgets = {
            'achievement_type': forms.Select(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
            'title': forms.TextInput(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
            'organization': forms.TextInput(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
            'certificate_url': forms.URLInput(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
            'proof_file': forms.ClearableFileInput(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
            'date_achieved': forms.DateInput(attrs={'type': 'date', 'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
        }
