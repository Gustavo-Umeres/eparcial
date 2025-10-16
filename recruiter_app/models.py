from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado para diferenciar entre empresas y estudiantes.
    La propiedad 'is_company' se usará para mostrar diferentes menús y opciones.
    """
    is_company = models.BooleanField(default=False)

class JobPosting(models.Model):
    """
    Modelo para la publicación de ofertas de empleo.
    """
    recruiter = models.ForeignKey('recruiter_app.CustomUser', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    min_education = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    """
    Modelo para preguntas personalizadas en una oferta de empleo.
    """
    QUESTION_TYPES = (
        ('open', 'Respuesta Abierta'),
        ('closed', 'Respuesta Cerrada'),
    )
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)

    def __str__(self):
        return self.text

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text
    
    
class Application(models.Model):
    """
    Modelo para la postulación de un estudiante a una oferta de empleo.
    """
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey('recruiter_app.CustomUser', on_delete=models.CASCADE, related_name='my_applications')
    cv = models.FileField(upload_to='cvs/')
    status = models.CharField(max_length=20, choices=[('pending', 'Pendiente'), ('accepted', 'Aceptado'), ('rejected', 'Rechazado')], default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Postulación para {self.job_posting.title} de {self.applicant.username}'

class Answer(models.Model):
    """
    Modelo para las respuestas de un estudiante a las preguntas de una oferta.
    """
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()

    def __str__(self):
        return f'Respuesta a {self.question.text} por {self.application.applicant.username}'