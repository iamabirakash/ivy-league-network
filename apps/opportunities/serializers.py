from rest_framework import serializers
from .models import Opportunity, University, UserOpportunity
from django.utils import timezone

class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['id', 'name', 'code', 'logo', 'is_ivy_league']


class OpportunitySerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    university_id = serializers.IntegerField(write_only=True)
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Opportunity
        fields = '__all__'
    
    def get_time_remaining(self, obj):
        if obj.deadline:
            delta = obj.deadline - timezone.now()
            return delta.days
        return None


class UserOpportunitySerializer(serializers.ModelSerializer):
    opportunity = OpportunitySerializer(read_only=True)
    
    class Meta:
        model = UserOpportunity
        fields = ['id', 'opportunity', 'status', 'applied_date', 'notes', 'created_at']