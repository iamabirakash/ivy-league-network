from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Post, Comment, Group

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'incoscore']


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'content', 'likes_count', 'created_at', 'updated_at']
    
    def get_likes_count(self, obj):
        return obj.likes.count()


class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'user', 'group', 'title', 'content', 'likes_count', 
                  'comments_count', 'views', 'created_at', 'updated_at']
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_likes_count(self, obj):
        return obj.likes.count()


class GroupSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'domain', 'created_by', 
                  'members_count', 'posts_count', 'is_private', 'created_at']
    
    def get_members_count(self, obj):
        return obj.members.count()
    
    def get_posts_count(self, obj):
        return obj.posts.count()