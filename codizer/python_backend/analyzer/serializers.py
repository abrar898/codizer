from rest_framework import serializers
from .models import CodeAnalysis

class CodeAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeAnalysis
        fields = ['id', 'code', 'language', 'time_complexity', 'space_complexity', 'analysis_date']

class CodeAnalysisRequestSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    language = serializers.CharField(required=True) 