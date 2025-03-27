from rest_framework import serializers
from .models import ActivityLog

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = [
            'id', 
            'username',
            'phone'  
            'action_type', 
            'description', 
            'timestamp', 
            'ip_address'
        ]