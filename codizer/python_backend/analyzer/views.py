from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CodeAnalysis
from .serializers import CodeAnalysisSerializer, CodeAnalysisRequestSerializer
from .complexity_analyzer import ComplexityAnalyzer

# Initialize the analyzer
complexity_analyzer = ComplexityAnalyzer()

@api_view(['POST'])
def analyze_code(request):
    """
    Analyze code for time and space complexity
    """
    serializer = CodeAnalysisRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        code = serializer.validated_data['code']
        language = serializer.validated_data['language']
        
        # Analyze the code
        result = complexity_analyzer.analyze_code(code, language)
        
        # Save to database
        analysis = CodeAnalysis(
            code=code,
            language=language,
            time_complexity=result['time_complexity'],
            space_complexity=result['space_complexity']
        )
        analysis.save()
        
        # Return the result
        return Response({
            'time_complexity': result['time_complexity'],
            'space_complexity': result['space_complexity']
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_analysis_history(request):
    """
    Get the analysis history
    """
    analyses = CodeAnalysis.objects.all().order_by('-analysis_date')[:20]  # Get the last 20 analyses
    serializer = CodeAnalysisSerializer(analyses, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
