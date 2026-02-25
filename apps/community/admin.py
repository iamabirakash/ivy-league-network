from django.contrib import admin
from .models import Group, Post, Comment


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "created_by", "is_private", "created_at")
    list_filter = ("domain", "is_private")
    search_fields = ("name", "description", "created_by__username")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "group", "views", "created_at")
    list_filter = ("group", "created_at")
    search_fields = ("title", "content", "user__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "user__username", "post__title")
