from django.urls import path
from . import views

urlpatterns = [
    # Étudiants
    path('', views.liste_etudiants, name='liste_etudiants'),
    path('ajouter/', views.ajouter_etudiant, name='ajouter_etudiant'),
    path('<str:matricule>/', views.detail_etudiant, name='detail_etudiant'),
    path('<str:matricule>/modifier/', views.modifier_etudiant, name='modifier_etudiant'),
    path('<str:matricule>/supprimer/', views.supprimer_etudiant, name='supprimer_etudiant'),
    
    # Filières
    path('filieres/enspd/', views.liste_filieres, name='liste_filieres'),
    path('filieres/ajouter/', views.ajouter_filiere, name='ajouter_filiere'),
    path('filieres/<str:code>/', views.detail_filiere, name='detail_filiere'),
    path('filieres/<str:code>/modifier/', views.modifier_filiere, name='modifier_filiere'),
    path('filieres/<str:code>/supprimer/', views.supprimer_filiere, name='supprimer_filiere'),
    
    # Horaires supplémentaires
    path('filieres/<str:code>/horaire/ajouter/', views.ajouter_horaire_supplementaire, name='ajouter_horaire_supplementaire'),
    path('horaires/<int:horaire_id>/supprimer/', views.supprimer_horaire_supplementaire, name='supprimer_horaire_supplementaire'),
    
        # ============================================
    # GÉNÉRATION MATRICULES DÉPARTEMENT
    # ============================================
    
    # Générer le matricule pour un étudiant
    path('etudiants/<str:matricule>/generer-matricule/', 
         views.generer_matricule_etudiant, 
         name='generer_matricule_etudiant'),
    
    # Générer les matricules en masse
    path('etudiants/generer-matricules-masse/', 
         views.generer_matricules_masse, 
         name='generer_matricules_masse'),
    
    # AJAX pour génération rapide
    path('etudiants/<str:matricule>/generer-matricule-ajax/', 
         views.generer_matricule_ajax, 
         name='generer_matricule_ajax'),
]