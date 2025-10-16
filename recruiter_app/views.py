from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory

# Importaciones de modelos y formularios
from .models import JobPosting, Question, Application, Answer, CustomUser, QuestionOption
from .forms import JobPostingForm, QuestionForm, ApplicationForm, StudentRegistrationForm, CompanyRegistrationForm, AnswerForm

# Formset para la creación y edición de ofertas
QuestionFormSet = modelformset_factory(Question, form=QuestionForm, extra=1, can_delete=True)

def home(request):
    """Renderiza la página de inicio."""
    return render(request, 'recruiter_app/home.html')

# ---
# Autenticación y Registro de Usuarios
# ---

def register_student(request):
    """Maneja el formulario de registro para estudiantes."""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.is_company = False
            new_user.save()
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    return render(request, 'recruiter_app/register_student.html', {'form': form})

def register_company(request):
    """Maneja el formulario de registro para empresas."""
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.is_company = True
            new_user.save()
            return redirect('login')
    else:
        form = CompanyRegistrationForm()
    return render(request, 'recruiter_app/register_company.html', {'form': form})

@login_required
def dashboard(request):
    """Renderiza el dashboard del usuario según su rol."""
    return render(request, 'recruiter_app/dashboard.html')

# ---
# Gestión de Ofertas de Empleo (Reclutadores)
# ---

@login_required
def create_job_posting(request):
    """Permite a los reclutadores crear una nueva oferta con preguntas dinámicas."""
    if request.method == 'POST':
        job_form = JobPostingForm(request.POST)
        question_formset = QuestionFormSet(request.POST, prefix='questions')
        
        if job_form.is_valid() and question_formset.is_valid():
            job = job_form.save(commit=False)
            job.recruiter = request.user
            job.save()
            
            for form_q in question_formset:
                if form_q.is_valid() and form_q.cleaned_data:
                    question = form_q.save(commit=False)
                    question.job_posting = job
                    question.save()

                    if question.question_type == 'closed':
                        options_text = request.POST.get(f'options_for_{form_q.prefix}', '')
                        if options_text:
                            for option_text in options_text.split('||'):
                                QuestionOption.objects.create(question=question, text=option_text.strip())
            return redirect('list_jobs')
    else:
        job_form = JobPostingForm()
        question_formset = QuestionFormSet(queryset=Question.objects.none(), prefix='questions')

    context = {
        'job_form': job_form,
        'question_formset': question_formset,
    }
    return render(request, 'recruiter_app/create_job.html', context)

@login_required
def list_job_postings(request):
    """Muestra una lista de ofertas creadas por el usuario actual."""
    jobs = JobPosting.objects.filter(recruiter=request.user)
    return render(request, 'recruiter_app/list_jobs.html', {'jobs': jobs})

@login_required
def edit_job_posting(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id, recruiter=request.user)
    if request.method == 'POST':
        job_form = JobPostingForm(request.POST, instance=job)
        question_formset = QuestionFormSet(request.POST, prefix='questions', queryset=job.questions.all())

        if job_form.is_valid() and question_formset.is_valid():
            job_form.save()
            
            for form_q in question_formset:
                if form_q.is_valid() and form_q.cleaned_data:
                    question = form_q.save(commit=False)
                    question.job_posting = job
                    question.save()

                    if question.question_type == 'closed':
                        options_text = request.POST.get(f'options_for_{form_q.prefix}', '')
                        if options_text:
                            question.options.all().delete()
                            for option_text in options_text.split('||'):
                                QuestionOption.objects.create(question=question, text=option_text.strip())

            messages.success(request, 'La oferta se ha actualizado correctamente.')
            return redirect('list_jobs')
    else:
        job_form = JobPostingForm(instance=job)
        question_formset = QuestionFormSet(prefix='questions', queryset=job.questions.all())

    context = {
        'job_form': job_form,
        'question_formset': question_formset,
        'job': job
    }
    return render(request, 'recruiter_app/edit_job.html', context)


@login_required
def delete_job_posting(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id, recruiter=request.user)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'La oferta se ha eliminado correctamente.')
        return redirect('list_jobs')
    
    context = {'job': job}
    return render(request, 'recruiter_app/delete_job.html', context)

@login_required
def received_applications(request):
    """Muestra todas las postulaciones recibidas por el reclutador."""
    user_jobs = request.user.jobposting_set.all()
    received_apps = Application.objects.filter(job_posting__in=user_jobs).order_by('-submitted_at')
    
    context = {
        'received_apps': received_apps,
    }
    return render(request, 'recruiter_app/received_applications.html', context)

@login_required
def view_applications(request, job_id):
    """Muestra todas las postulaciones para una oferta específica."""
    job = get_object_or_404(JobPosting, id=job_id, recruiter=request.user)
    applications = job.applications.all()
    return render(request, 'recruiter_app/applications.html', {'job': job, 'applications': applications})


@login_required
def view_application_detail(request, application_id):
    """Muestra los detalles completos de una sola postulación, a menos que ya haya sido aceptada o rechazada."""
    application = get_object_or_404(Application, id=application_id)
    
    # Lógica para verificar el estado de la postulación
    if application.status != 'pending':
        messages.warning(request, f'La postulación de {application.applicant.username} ya ha sido procesada.')
        return redirect('received_applications')
    
    answers = application.answers.all()
    context = {
        'application': application,
        'answers': answers,
    }
    return render(request, 'recruiter_app/application_detail.html', context)


@login_required
def update_application_status(request, application_id, status):
    """Actualiza el estado de una postulación (aceptada o rechazada)."""
    application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        if status in ['accepted', 'rejected']:
            application.status = status
            application.save()
            messages.success(request, f'Postulación {status} correctamente.')
            
            # --- CORRECCIÓN AQUÍ ---
            return redirect('received_applications') 
    
    return redirect('view_application_detail', application_id=application.id)

# ---
# Búsqueda de Empleo y Postulaciones (Estudiantes)
# ---

@login_required
def my_applications(request):
    """Muestra todas las postulaciones del usuario logeado."""
    my_apps = Application.objects.filter(applicant=request.user).order_by('-submitted_at')
    return render(request, 'recruiter_app/my_applications.html', {'my_apps': my_apps})

@login_required
def search_jobs(request):
    """Permite a los estudiantes buscar y filtrar ofertas."""
    query = request.GET.get('q')
    jobs = JobPosting.objects.all()

    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query))
    
    context = {
        'jobs': jobs,
        'query': query,
    }
    return render(request, 'recruiter_app/search_jobs.html', context)

@login_required
def apply_to_job(request, job_id):
    """Maneja el proceso de postulación a una oferta."""
    job = get_object_or_404(JobPosting, id=job_id)
    
    if request.method == 'POST':
        application_form = ApplicationForm(request.POST, request.FILES)
        
        if application_form.is_valid():
            application = application_form.save(commit=False)
            application.job_posting = job
            application.applicant = request.user
            application.save()
            
            # Procesar las respuestas de las preguntas
            for question in job.questions.all():
                # Use a single, consistent name for all answer fields
                answer_text = request.POST.get(f'answer_text_{question.id}', '')
                if answer_text:
                    Answer.objects.create(application=application, question=question, answer_text=answer_text)
            
            messages.success(request, 'Tu postulación se ha enviado correctamente.')
            return redirect('my_applications')
    else:
        application_form = ApplicationForm()
    
    questions = job.questions.all()
    
    context = {
        'job': job,
        'application_form': application_form,
        'questions': questions,
    }
    return render(request, 'recruiter_app/apply_to_job.html', context)
    """Maneja el proceso de postulación a una oferta."""
    job = get_object_or_404(JobPosting, id=job_id)
    
    if request.method == 'POST':
        application_form = ApplicationForm(request.POST, request.FILES)
        
        if application_form.is_valid():
            application = application_form.save(commit=False)
            application.job_posting = job
            application.applicant = request.user
            application.save()
            
            for question in job.questions.all():
                if question.question_type == 'open':
                    answer_text = request.POST.get(f'answer_text_open_{question.id}')
                    if answer_text:
                        Answer.objects.create(application=application, question=question, answer_text=answer_text)
                elif question.question_type == 'closed':
                    answer_text = request.POST.get(f'answer_text_closed_{question.id}')
                    if answer_text:
                        Answer.objects.create(application=application, question=question, answer_text=answer_text)
            
            return redirect('my_applications')
    else:
        application_form = ApplicationForm()
    
    questions = job.questions.all()
    
    context = {
        'job': job,
        'application_form': application_form,
        'questions': questions,
    }
    return render(request, 'recruiter_app/apply_to_job.html', context)