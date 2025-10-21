# ============================================
# students/urls.py
# ============================================

from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_etudiants, name='liste_etudiants'),
    path('ajouter/', views.ajouter_etudiant, name='ajouter_etudiant'),
    path('<str:matricule>/', views.detail_etudiant, name='detail_etudiant'),
    path('<str:matricule>/modifier/', views.modifier_etudiant, name='modifier_etudiant'),
    path('filieres/enspd/', views.liste_filieres, name='liste_filieres'),
    path('filieres/<str:code>/', views.detail_filiere, name='detail_filiere'),
]