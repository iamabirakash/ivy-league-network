from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Opportunity, UserOpportunity, University, OpportunityAlert, Application
from .forms import OpportunityAlertForm, ApplicationForm
from apps.accounts.models import User
import logging

logger = logging.getLogger(__name__)


class OpportunityListView(LoginRequiredMixin, ListView):
    model = Opportunity
    template_name = 'opportunities/list.html'
    context_object_name = 'opportunities'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Opportunity.objects.filter(
            is_active=True,
            deadline__gte=timezone.now()
        ).select_related('university')
        
        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(university__name__icontains=search)
            )
        
        # Filters
        domain = self.request.GET.get('domain', '')
        if domain:
            queryset = queryset.filter(domain=domain)
        
        opp_type = self.request.GET.get('type', '')
        if opp_type:
            queryset = queryset.filter(opportunity_type=opp_type)
        
        university = self.request.GET.get('university', '')
        if university:
            queryset = queryset.filter(university_id=university)
        
        # Sort
        sort = self.request.GET.get('sort', '-created_at')
        allowed_sorts = {'-created_at', 'created_at', 'deadline', '-deadline', '-views_count', 'views_count'}
        queryset = queryset.order_by(sort if sort in allowed_sorts else '-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['universities'] = University.objects.filter(active=True)
        context['domains'] = Opportunity.DOMAIN_CHOICES
        context['opportunity_types'] = Opportunity.OPPORTUNITY_TYPES
        
        # Get saved opportunities for current user
        saved_opps = UserOpportunity.objects.filter(
            user=self.request.user,
            status='saved'
        ).values_list('opportunity_id', flat=True)
        context['saved_opps'] = list(saved_opps)
        
        return context


class OpportunityDetailView(LoginRequiredMixin, DetailView):
    model = Opportunity
    template_name = 'opportunities/detail.html'
    context_object_name = 'opportunity'
    
    def get_object(self):
        obj = super().get_object()
        # Increment view count
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        opportunity = self.object
        
        # Check if user has saved/applied
        user_opp = UserOpportunity.objects.filter(
            user=self.request.user,
            opportunity=opportunity
        ).first()
        context['user_opportunity'] = user_opp
        context["application_form"] = ApplicationForm()
        
        # Similar opportunities
        context['similar'] = Opportunity.objects.filter(
            domain=opportunity.domain,
            is_active=True
        ).exclude(id=opportunity.id)[:5]
        context["recommended_students"] = _get_recommended_students(opportunity)
        
        return context


def _build_recommendation_queryset(user):
    queryset = Opportunity.objects.filter(
        is_active=True,
        deadline__gte=timezone.now(),
    )
    interests = user.interests or []
    skills = user.skills or []

    if interests or skills:
        filters = Q()
        for item in interests:
            token = str(item).strip().lower()
            if not token:
                continue
            filters |= Q(domain=token) | Q(tags__icontains=token) | Q(title__icontains=token)
        for item in skills:
            token = str(item).strip().lower()
            if not token:
                continue
            filters |= Q(tags__icontains=token) | Q(description__icontains=token)
        queryset = queryset.filter(filters)

    return queryset.order_by("-is_featured", "deadline", "-created_at")


def _get_recommended_students(opportunity, limit=5):
    domains = [opportunity.domain] if opportunity.domain else []
    tags = [str(tag).strip().lower() for tag in (opportunity.tags or []) if str(tag).strip()]

    students = User.objects.filter(is_active=True, user_type="student")
    profile_filter = Q()
    for token in domains + tags:
        profile_filter |= Q(interests__icontains=token) | Q(skills__icontains=token)

    if profile_filter:
        students = students.filter(profile_filter)
    return students.order_by("-incoscore")[:limit]


@login_required
def save_opportunity(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk)
    
    user_opp, created = UserOpportunity.objects.get_or_create(
        user=request.user,
        opportunity=opportunity,
        defaults={'status': 'saved'}
    )
    
    if not created:
        if user_opp.status == 'saved':
            user_opp.delete()
            opportunity.saved_count = max(0, opportunity.saved_count - 1)
            opportunity.save(update_fields=["saved_count"])
            messages.success(request, 'Opportunity removed from saved.')
        else:
            user_opp.status = 'saved'
            user_opp.save()
            messages.success(request, 'Opportunity saved!')
    else:
        # Increment saved count
        opportunity.saved_count += 1
        opportunity.save(update_fields=['saved_count'])
        messages.success(request, 'Opportunity saved!')
    
    return redirect('opportunities:detail', pk=pk)


@login_required
def dashboard(request):
    # User's opportunities stats
    saved_count = UserOpportunity.objects.filter(
        user=request.user,
        status='saved'
    ).count()
    
    applied_count = UserOpportunity.objects.filter(
        user=request.user,
        status='applied'
    ).count()
    
    accepted_count = UserOpportunity.objects.filter(
        user=request.user,
        status='accepted'
    ).count()
    
    # Recent opportunities
    recent_opps = Opportunity.objects.filter(
        is_active=True
    ).order_by('-created_at')[:10]
    
    # Recommended opportunities (based on user interests)
    recommended = _build_recommendation_queryset(request.user)[:10]
    
    # Upcoming deadlines
    deadlines = UserOpportunity.objects.filter(
        user=request.user,
        status='saved',
        opportunity__deadline__gte=timezone.now()
    ).select_related('opportunity').order_by('opportunity__deadline')[:5]
    
    context = {
        'saved_count': saved_count,
        'applied_count': applied_count,
        'accepted_count': accepted_count,
        'recent_opps': recent_opps,
        'recommended': recommended,
        'deadlines': deadlines,
    }
    
    return render(request, 'opportunities/dashboard.html', context)


@login_required
def apply_opportunity(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk, is_active=True)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.opportunity = opportunity
            application.status = "applied"
            application.save()

            user_opp, _ = UserOpportunity.objects.get_or_create(
                user=request.user,
                opportunity=opportunity,
                defaults={"status": "applied", "applied_date": timezone.now()},
            )
            if user_opp.status != "applied":
                user_opp.status = "applied"
            user_opp.applied_date = timezone.now()
            user_opp.application_data = application.submitted_data
            user_opp.save(update_fields=["status", "applied_date", "application_data", "updated_at"])

            opportunity.applications_count += 1
            opportunity.save(update_fields=["applications_count"])

            messages.success(request, "Application submitted successfully.")
            return redirect("opportunities:detail", pk=opportunity.pk)
    else:
        initial_data = {
            "full_name": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
            "university": request.user.university,
            "major": request.user.major,
            "skills": request.user.skills or [],
            "interests": request.user.interests or [],
        }
        form = ApplicationForm(initial={"submitted_data": initial_data})

    return render(
        request,
        "opportunities/apply.html",
        {
            "opportunity": opportunity,
            "form": form,
        },
    )


@login_required
def alerts(request):
    if request.method == 'POST':
        form = OpportunityAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
            messages.success(request, 'Alert created successfully!')
            return redirect('opportunities:alerts')
    else:
        form = OpportunityAlertForm()
    
    user_alerts = OpportunityAlert.objects.filter(user=request.user)
    
    context = {
        'form': form,
        'alerts': user_alerts,
    }
    return render(request, 'opportunities/alerts.html', context)


@login_required
def delete_alert(request, pk):
    alert = get_object_or_404(OpportunityAlert, pk=pk, user=request.user)
    alert.delete()
    messages.success(request, 'Alert deleted successfully!')
    return redirect('opportunities:alerts')
