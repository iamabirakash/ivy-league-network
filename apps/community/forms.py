from django import forms
from .models import Post, Comment, Group


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'group']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
            'content': forms.Textarea(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy', 'rows': 5}),
            'group': forms.Select(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy', 'rows': 3}),
        }


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'domain']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
            'description': forms.Textarea(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy', 'rows': 4}),
            'domain': forms.Select(attrs={'class': 'w-full bg-cream border border-cream-dk rounded-lg px-4 py-2.5 text-sm text-navy'}),
        }
