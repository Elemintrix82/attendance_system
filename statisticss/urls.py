# ============================================
# statistics/urls.py
# ============================================

from django.urls import path
from . import views

urlpatterns = [
    path('', views.statistiques_globales, name='statistiques_globales'),
    path('par-classe/', views.statistiques_par_classe, name='statistiques_par_classe'),
    path('etudiant/<str:matricule>/', views.statistiques_par_etudiant, name='statistiques_par_etudiant'),
    path('cours/<str:code_cours>/', views.statistiques_par_cours, name='statistiques_par_cours'),
    path('rapports/', views.liste_rapports, name='liste_rapports'),
    path('rapports/generer/', views.generer_rapport, name='generer_rapport'),
]