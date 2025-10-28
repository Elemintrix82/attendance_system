# ============================================
# teachers/urls.py
# ============================================

from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_enseignants, name='liste_enseignants'),
    path('ajouter/', views.ajouter_enseignant, name='ajouter_enseignant'),
    path('<str:matricule>/', views.detail_enseignant, name='detail_enseignant'),
    path('<str:matricule>/modifier/', views.modifier_enseignant, name='modifier_enseignant'),
    path('<str:matricule>/supprimer/', views.supprimer_enseignant, name='supprimer_enseignant'),  # ✅ NOUVEAU
    path('<str:matricule>/assigner-cours/', views.assigner_cours, name='assigner_cours'),
    path('<str:matricule>/reset-password/', views.reinitialiser_mot_de_passe_enseignant, name='reset_password_enseignant'),
]