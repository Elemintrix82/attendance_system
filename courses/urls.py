# ============================================
# courses/urls.py
# ============================================

from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_cours, name='liste_cours'),
    path('ajouter/', views.ajouter_cours, name='ajouter_cours'),
    path('<str:code>/', views.detail_cours, name='detail_cours'),
    path('<str:code>/modifier/', views.modifier_cours, name='modifier_cours'),
    path('<str:code_cours>/seance/ajouter/', views.ajouter_seance, name='ajouter_seance'),
    path('salles/enspd/', views.liste_salles, name='liste_salles'),
    path('seances/enspd/', views.liste_seances, name='liste_seances'),
    path('seances/<int:seance_id>/', views.detail_seance, name='detail_seance'),
    path('assignations/gerer/', views.gerer_assignations, name='gerer_assignations'),
    path('assignations/assigner/<str:code_cours>/', views.assigner_enseignant_cours, name='assigner_enseignant_cours'),
]