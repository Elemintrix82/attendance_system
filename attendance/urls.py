# ============================================
# attendance/urls.py
# ============================================

from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_presences, name='liste_presences'),
    # path('prendre/<int:seance_id>/', views.prendre_presence, name='prendre_presence'),
    # path('<int:presence_id>/modifier/', views.modifier_presence, name='modifier_presence'),
    path('prendre/<int:seance_id>/', views.prendre_presence, name='prendre_presence'),
    path('modifier/<int:presence_id>/', views.modifier_presence, name='modifier_presence'),
    path('justificatifs/', views.liste_justificatifs, name='liste_justificatifs'),
    path('justificatifs/<int:justificatif_id>/', views.detail_justificatif, name='detail_justificatif'),
    path('justificatifs/<int:justificatif_id>/valider/', views.valider_justificatif, name='valider_justificatif'),
    path('justificatifs/<int:justificatif_id>/refuser/', views.refuser_justificatif, name='refuser_justificatif'),
    path('justificatifs/ajouter/<str:matricule>/', views.ajouter_justificatif, name='ajouter_justificatif'),
]