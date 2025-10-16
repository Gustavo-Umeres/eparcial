from django.urls import path, include
from . import views

urlpatterns = [
    # URLs de la página principal y registro
    path('', views.home, name='home'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/company/', views.register_company, name='register_company'),

    # URLs del dashboard y autenticación
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accounts/', include('django.contrib.auth.urls')),

    # URLs para reclutadores
    path('jobs/create/', views.create_job_posting, name='create_job_posting'),
    path('jobs/', views.list_job_postings, name='list_jobs'),
    path('jobs/<int:job_id>/applications/', views.view_applications, name='view_applications'),
    path('jobs/edit/<int:job_id>/', views.edit_job_posting, name='edit_job_posting'),
    path('jobs/delete/<int:job_id>/', views.delete_job_posting, name='delete_job_posting'),
    
    # URLs de gestión de postulaciones
    path('received-applications/', views.received_applications, name='received_applications'),
    path('application/<int:application_id>/detail/', views.view_application_detail, name='view_application_detail'),
    path('application/<int:application_id>/<str:status>/', views.update_application_status, name='update_application_status'),
    
    # URLs para estudiantes
    path('my-applications/', views.my_applications, name='my_applications'),
    path('search-jobs/', views.search_jobs, name='search_jobs'),
    path('apply/<int:job_id>/', views.apply_to_job, name='apply_to_job'),
    path('application/delete/<int:application_id>/', views.delete_application, name='delete_application'),
]