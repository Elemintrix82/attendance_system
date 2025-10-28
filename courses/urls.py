# ============================================
# courses/urls.py
# ============================================

from django.urls import path
from . import views

urlpatterns = [
    # Cours
    path('', views.liste_cours, name='liste_cours'),
    path('ajouter/', views.ajouter_cours, name='ajouter_cours'),
    path('<str:code>/', views.detail_cours, name='detail_cours'),
    path('<str:code>/modifier/', views.modifier_cours, name='modifier_cours'),
    path('<str:code>/supprimer/', views.supprimer_cours, name='supprimer_cours'),
    
    # Séances - URLs spécifiques en premier
    path('salles/enspd/', views.liste_salles, name='liste_salles'),
    path('salles/ajouter/', views.ajouter_salle, name='ajouter_salle'),
    path('salles/<int:salle_id>/', views.detail_salle, name='detail_salle'),
    path('salles/<int:salle_id>/modifier/', views.modifier_salle, name='modifier_salle'),
    path('salles/<int:salle_id>/supprimer/', views.supprimer_salle, name='supprimer_salle'),
    
    path('seances/enspd/', views.liste_seances, name='liste_seances'),
    path('seances/ajouter-global/', views.ajouter_seance_global, name='ajouter_seance_global'),
    path('seances/<int:seance_id>/', views.detail_seance, name='detail_seance'),
    path('seances/<int:seance_id>/modifier/', views.modifier_seance, name='modifier_seance'),
    path('seances/<int:seance_id>/supprimer/', views.supprimer_seance, name='supprimer_seance'),
    
    # Ajouter séance depuis un cours
    path('<str:code_cours>/seance/ajouter/', views.ajouter_seance, name='ajouter_seance'),
    
    # Assignations
    path('assignations/gerer/', views.gerer_assignations, name='gerer_assignations'),
    path('assignations/assigner/<str:code_cours>/', views.assigner_enseignant_cours, name='assigner_enseignant_cours'),
    
     # ============================================
    # HORAIRES DE COURS
    # ============================================
    path('<str:code_cours>/horaires/ajouter/', views.ajouter_horaire_cours, name='ajouter_horaire_cours'),
    path('horaires/<int:horaire_id>/modifier/', views.modifier_horaire_cours, name='modifier_horaire_cours'),
    path('horaires/<int:horaire_id>/supprimer/', views.supprimer_horaire_cours, name='supprimer_horaire_cours'),
]