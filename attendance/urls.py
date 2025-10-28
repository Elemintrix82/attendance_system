# ============================================
# attendance/urls.py
# ============================================

from django.urls import path
from . import views

urlpatterns = [
    
    path('navigation/', views.navigation_presences, name='navigation_presences'),
    path('filiere/', views.presences_par_filiere, name='presences_par_filiere'),
    path('ajax/specialites/', views.get_specialites_ajax, name='get_specialites_ajax'),
    path('ajax/niveaux/', views.get_niveaux_ajax, name='get_niveaux_ajax'),
    path('par-filiere/', views.presences_par_filiere, name='presences_par_filiere'),
    
    # ============================================
    # PRÉSENCES - Actions
    # ============================================
    path('', views.liste_presences, name='liste_presences'),
    path('prendre/<int:seance_id>/', views.prendre_presence, name='prendre_presence'),
    path('modifier/<int:presence_id>/', views.modifier_presence, name='modifier_presence'),
    
    # ============================================
    # JUSTIFICATIFS
    # ============================================
    path('justificatifs/', views.liste_justificatifs, name='liste_justificatifs'),
    path('justificatifs/<int:justificatif_id>/', views.detail_justificatif, name='detail_justificatif'),
    path('justificatifs/<int:justificatif_id>/valider/', views.valider_justificatif, name='valider_justificatif'),
    path('justificatifs/<int:justificatif_id>/refuser/', views.refuser_justificatif, name='refuser_justificatif'),
    path('justificatifs/ajouter/<str:matricule>/', views.ajouter_justificatif, name='ajouter_justificatif'),
    
    # ============================================
    # API AJAX pour navigation dynamique
    # ============================================
    path('api/specialites/', views.get_specialites_ajax, name='get_specialites_ajax'),
    path('api/niveaux/', views.get_niveaux_ajax, name='get_niveaux_ajax'),
    
    # ============================================
    # JUSTIFICATIFS - GESTION MANUELLE (Nouveau)
    # ============================================
    # Appliquer un justificatif à une présence spécifique
    path('justificatifs/<int:justificatif_id>/appliquer/<int:presence_id>/', 
         views.appliquer_justificatif_manuel, 
         name='appliquer_justificatif_manuel'),
    
    # Retirer un justificatif d'une présence
    path('presences/<int:presence_id>/retirer-justificatif/', 
         views.retirer_justificatif_manuel, 
         name='retirer_justificatif_manuel'),
    
    path('justificatifs/nouveau/', 
     views.selectionner_etudiant_justificatif, 
     name='selectionner_etudiant_justificatif'),
    
    path('justificatifs/<int:justificatif_id>/modifier/', 
     views.modifier_justificatif, 
     name='modifier_justificatif'),

    path('justificatifs/<int:justificatif_id>/supprimer/', 
        views.supprimer_justificatif, 
        name='supprimer_justificatif'),

    # CRUD Présences
    path('<int:presence_id>/', 
        views.detail_presence, 
        name='detail_presence'),

    path('<int:presence_id>/supprimer/', 
        views.supprimer_presence, 
        name='supprimer_presence'),
]