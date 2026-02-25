from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import University, Opportunity, UserOpportunity, Application, OpportunityAlert


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_ivy_league', 'last_scraped', 'active')
    list_filter = ('is_ivy_league', 'active')
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'website', 'opportunities_url', 'logo', 'description')
        }),
        ('Status', {
            'fields': ('is_ivy_league', 'active', 'last_scraped')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'university', 'opportunity_type', 'domain', 'deadline', 'is_active')
    list_filter = ('opportunity_type', 'domain', 'university', 'is_active', 'is_remote')
    search_fields = ('title', 'description', 'university__name')
    readonly_fields = ('views_count', 'applications_count', 'saved_count', 'created_at', 'updated_at', 'source_hash')
    date_hierarchy = 'deadline'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'opportunity_type', 'domain', 'university')
        }),
        ('Dates & Location', {
            'fields': ('deadline', 'start_date', 'end_date', 'location', 'is_remote')
        }),
        ('Compensation', {
            'fields': ('is_paid', 'stipend')
        }),
        ('Links', {
            'fields': ('external_url', 'application_url', 'source_url')
        }),
        ('Criteria', {
            'fields': ('eligibility_criteria', 'benefits', 'requirements', 'tags')
        }),
        ('Metadata', {
            'fields': ('source_id', 'source_hash', 'is_active', 'is_featured', 
                      'views_count', 'applications_count', 'saved_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_active', 'mark_inactive', 'mark_featured']
    
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
    mark_active.short_description = "Mark selected as active"
    
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
    mark_inactive.short_description = "Mark selected as inactive"
    
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)
    mark_featured.short_description = "Mark selected as featured"


@admin.register(UserOpportunity)
class UserOpportunityAdmin(admin.ModelAdmin):
    list_display = ('user', 'opportunity', 'status', 'applied_date', 'reminder_date')
    list_filter = ('status',)
    search_fields = ('user__username', 'opportunity__title')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'opportunity', 'status', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'opportunity__title')
    readonly_fields = ('submitted_at', 'updated_at')


@admin.register(OpportunityAlert)
class OpportunityAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'keywords', 'frequency', 'is_active')
    list_filter = ('frequency', 'is_active')
    search_fields = ('user__username', 'keywords')