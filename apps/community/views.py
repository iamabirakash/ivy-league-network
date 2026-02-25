from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Post, Comment, Group
from .forms import PostForm, CommentForm, GroupForm


class PostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'community/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Post.objects.all().order_by('-created_at')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )
        return queryset


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'community/post_detail.html'
    context_object_name = 'post'
    
    def get_object(self):
        obj = super().get_object()
        obj.views += 1
        obj.save()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all().order_by('created_at')
        context['comment_form'] = CommentForm()
        return context


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect('community:post_detail', pk=post.id)
    else:
        form = PostForm()
    return render(request, 'community/create_post.html', {'form': form})


@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('community:post_detail', pk=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'community/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, user=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('community:post_list')
    return render(request, 'community/delete_post.html', {'post': post})


@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect('community:post_detail', pk=pk)


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            messages.success(request, 'Comment added successfully!')
    return redirect('community:post_detail', pk=pk)


class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'community/group_list.html'
    context_object_name = 'groups'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Group.objects.all().order_by('name')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = 'community/group_detail.html'
    context_object_name = 'group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        context['posts'] = Post.objects.filter(group=group).order_by('-created_at')[:10]
        context['is_member'] = self.request.user in group.members.all()
        return context


@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            group.members.add(request.user)  # Creator automatically joins
            messages.success(request, 'Group created successfully!')
            return redirect('community:group_detail', pk=group.id)
    else:
        form = GroupForm()
    return render(request, 'community/create_group.html', {'form': form})


@login_required
def join_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group.members.add(request.user)
    messages.success(request, f'You joined {group.name}!')
    return redirect('community:group_detail', pk=pk)


@login_required
def leave_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group.members.remove(request.user)
    messages.success(request, f'You left {group.name}')
    return redirect('community:group_detail', pk=pk)