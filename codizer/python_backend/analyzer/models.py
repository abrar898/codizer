from django.db import models

# Create your models here.

class CodeAnalysis(models.Model):
    code = models.TextField()
    language = models.CharField(max_length=50)
    time_complexity = models.CharField(max_length=50)
    space_complexity = models.CharField(max_length=50)
    analysis_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis of {self.language} code on {self.analysis_date}"
