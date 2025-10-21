# attendance_system/courses/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Cours, Salle, SeanceCours
from students.models import Filiere, Niveau
from teachers.models import Enseignant

# ============================================
# GESTION DES ASSIGNATIONS COURS ↔ ENSEIGNANT
# ============================================

@login_required
def gerer_assignations(request):
    """Page de gestion des assignations cours-enseignant"""
    
    # Vérification permissions (Admin et Scolarité uniquement)
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé. Seuls les administrateurs peuvent gérer les assignations.")
        return redirect('dashboard')
    
    # Récupération des filtres
    search_query = request.GET.get('search', '')
    filiere_id = request.GET.get('filiere', '')
    niveau_id = request.GET.get('niveau', '')
    semestre = request.GET.get('semestre', '')
    statut = request.GET.get('statut', '')  # 'assigne', 'non_assigne', 'tous'
    
    # Base queryset avec annotations
    cours_list = Cours.objects.select_related(
        'enseignant', 
        'filiere', 
        'niveau', 
        'salle'
    ).annotate(
        nombre_seances=Count('seances')
    ).filter(actif=True)
    
    # Appliquer les filtres
    if search_query:
        cours_list = cours_list.filter(
            Q(code__icontains=search_query) | 
            Q(intitule__icontains=search_query)
        )
    
    if filiere_id:
        cours_list = cours_list.filter(filiere_id=filiere_id)
    
    if niveau_id:
        cours_list = cours_list.filter(niveau_id=niveau_id)
    
    if semestre:
        cours_list = cours_list.filter(semestre=semestre)
    
    if statut == 'assigne':
        cours_list = cours_list.filter(enseignant__isnull=False)
    elif statut == 'non_assigne':
        cours_list = cours_list.filter(enseignant__isnull=True)
    
    # Ordre par défaut
    cours_list = cours_list.order_by('filiere', 'niveau', 'semestre', 'code')
    
    # Récupération des enseignants actifs
    enseignants = Enseignant.objects.filter(actif=True).select_related('user').order_by('nom', 'prenom')
    
    # Données pour les filtres
    filieres = Filiere.objects.all().order_by('code')
    niveaux = Niveau.objects.all().order_by('cycle', 'annee')
    
    # Statistiques
    total_cours = cours_list.count()
    cours_assignes = cours_list.filter(enseignant__isnull=False).count()
    cours_non_assignes = cours_list.filter(enseignant__isnull=True).count()
    taux_assignation = round((cours_assignes / total_cours * 100), 1) if total_cours > 0 else 0
    
    context = {
        'cours_list': cours_list,
        'enseignants': enseignants,
        'filieres': filieres,
        'niveaux': niveaux,
        'search_query': search_query,
        'filiere_id': filiere_id,
        'niveau_id': niveau_id,
        'semestre': semestre,
        'statut': statut,
        'total_cours': total_cours,
        'cours_assignes': cours_assignes,
        'cours_non_assignes': cours_non_assignes,
        'taux_assignation': taux_assignation,
    }
    
    return render(request, 'courses/gerer_assignations.html', context)


@login_required
def assigner_enseignant_cours(request, code_cours):
    """Assigner ou retirer un enseignant d'un cours (AJAX)"""
    
    # Vérification permissions
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        return JsonResponse({
            'success': False, 
            'message': '⛔ Accès refusé.'
        }, status=403)
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'message': '❌ Méthode non autorisée.'
        }, status=405)
    
    try:
        # Récupérer le cours
        cours = get_object_or_404(Cours, code=code_cours)
        
        # Récupérer l'action
        action = request.POST.get('action')  # 'assigner' ou 'retirer'
        
        if action == 'retirer':
            # Retirer l'enseignant
            ancien_enseignant = cours.enseignant
            if ancien_enseignant:
                cours.enseignant = None
                cours.save()
                
                messages.success(
                    request, 
                    f"✅ L'enseignant {ancien_enseignant.nom_complet()} a été retiré du cours {cours.code}."
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f"Enseignant retiré avec succès.",
                    'action': 'retirer',
                    'cours_code': cours.code
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': "⚠️ Ce cours n'a pas d'enseignant assigné."
                })
        
        elif action == 'assigner':
            # Assigner un nouvel enseignant
            enseignant_id = request.POST.get('enseignant_id')
            
            if not enseignant_id:
                return JsonResponse({
                    'success': False,
                    'message': '⚠️ Veuillez sélectionner un enseignant.'
                })
            
            enseignant = get_object_or_404(Enseignant, id=enseignant_id, actif=True)
            
            # Vérifier si le cours avait déjà un enseignant
            ancien_enseignant = cours.enseignant
            
            # Assigner le nouvel enseignant
            cours.enseignant = enseignant
            cours.save()
            
            if ancien_enseignant:
                messages.success(
                    request,
                    f"✅ Le cours {cours.code} a été réassigné de {ancien_enseignant.nom_complet()} à {enseignant.nom_complet()}."
                )
                message_type = 'reassigne'
            else:
                messages.success(
                    request,
                    f"✅ Le cours {cours.code} a été assigné à {enseignant.nom_complet()}."
                )
                message_type = 'assigne'
            
            return JsonResponse({
                'success': True,
                'message': f"Cours assigné avec succès à {enseignant.nom_complet()}.",
                'action': 'assigner',
                'cours_code': cours.code,
                'enseignant_nom': enseignant.nom_complet(),
                'message_type': message_type
            })
        
        else:
            return JsonResponse({
                'success': False,
                'message': '❌ Action non reconnue.'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'❌ Erreur : {str(e)}'
        }, status=500)
        
        
        
@login_required
def liste_cours(request):
    """Liste de tous les cours avec recherche et filtres"""
    cours = Cours.objects.filter(actif=True).select_related('filiere', 'niveau', 'enseignant', 'salle')
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        cours = cours.filter(
            Q(code__icontains=search_query) |
            Q(intitule__icontains=search_query) |
            Q(enseignant__nom__icontains=search_query) |
            Q(enseignant__prenom__icontains=search_query)
        )
    
    # Filtres
    filiere_id = request.GET.get('filiere')
    if filiere_id:
        cours = cours.filter(filiere_id=filiere_id)
    
    niveau_id = request.GET.get('niveau')
    if niveau_id:
        cours = cours.filter(niveau_id=niveau_id)
    
    semestre = request.GET.get('semestre')
    if semestre:
        cours = cours.filter(semestre=semestre)
    
    # Pagination
    paginator = Paginator(cours, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filieres': Filiere.objects.all(),
        'niveaux': Niveau.objects.all(),
        'search_query': search_query,
        'total_cours': cours.count(),
    }
    
    return render(request, 'courses/liste_cours.html', context)


@login_required
def detail_cours(request, code):
    """Détail d'un cours avec ses séances"""
    cours = get_object_or_404(Cours, code=code)
    
    # Récupérer les séances
    seances = SeanceCours.objects.filter(cours=cours).select_related('salle').order_by('-date')
    
    # Pagination
    paginator = Paginator(seances, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'cours': cours,
        'page_obj': page_obj,
        'total_seances': seances.count(),
    }
    
    return render(request, 'courses/detail_cours.html', context)


@login_required
def ajouter_cours(request):
    """Ajouter un nouveau cours"""
    if request.method == 'POST':
        try:
            cours = Cours.objects.create(
                code=request.POST.get('code'),
                intitule=request.POST.get('intitule'),
                description=request.POST.get('description'),
                filiere_id=request.POST.get('filiere'),
                niveau_id=request.POST.get('niveau'),
                enseignant_id=request.POST.get('enseignant') or None,
                salle_id=request.POST.get('salle') or None,
                semestre=request.POST.get('semestre'),
                annee_academique=request.POST.get('annee_academique'),
                jour_semaine=request.POST.get('jour_semaine'),
                heure_debut=request.POST.get('heure_debut') or None,
                heure_fin=request.POST.get('heure_fin') or None,
                credits=request.POST.get('credits', 3),
                coefficient=request.POST.get('coefficient', 1.0),
                volume_horaire_cm=request.POST.get('volume_horaire_cm', 0),
                volume_horaire_td=request.POST.get('volume_horaire_td', 0),
                volume_horaire_tp=request.POST.get('volume_horaire_tp', 0),
            )
            
            messages.success(request, f'Cours {cours.code} - {cours.intitule} ajouté avec succès.')
            return redirect('detail_cours', code=cours.code)
        
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout : {str(e)}')
    
    context = {
        'filieres': Filiere.objects.all(),
        'niveaux': Niveau.objects.all(),
        'enseignants': Enseignant.objects.filter(actif=True),
        'salles': Salle.objects.filter(disponible=True),
        'jours_semaine': Cours.JOURS_SEMAINE,
        'semestres': Cours.SEMESTRES,
    }
    
    return render(request, 'courses/ajouter_cours.html', context)


@login_required
def modifier_cours(request, code):
    """Modifier un cours"""
    cours = get_object_or_404(Cours, code=code)
    
    if request.method == 'POST':
        try:
            cours.intitule = request.POST.get('intitule')
            cours.description = request.POST.get('description')
            cours.filiere_id = request.POST.get('filiere')
            cours.niveau_id = request.POST.get('niveau')
            cours.enseignant_id = request.POST.get('enseignant') or None
            cours.salle_id = request.POST.get('salle') or None
            cours.semestre = request.POST.get('semestre')
            cours.annee_academique = request.POST.get('annee_academique')
            cours.jour_semaine = request.POST.get('jour_semaine')
            cours.heure_debut = request.POST.get('heure_debut') or None
            cours.heure_fin = request.POST.get('heure_fin') or None
            cours.credits = request.POST.get('credits', 3)
            cours.coefficient = request.POST.get('coefficient', 1.0)
            cours.volume_horaire_cm = request.POST.get('volume_horaire_cm', 0)
            cours.volume_horaire_td = request.POST.get('volume_horaire_td', 0)
            cours.volume_horaire_tp = request.POST.get('volume_horaire_tp', 0)
            
            cours.save()
            
            messages.success(request, f'Cours {cours.code} modifié avec succès.')
            return redirect('detail_cours', code=cours.code)
        
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    context = {
        'cours': cours,
        'filieres': Filiere.objects.all(),
        'niveaux': Niveau.objects.all(),
        'enseignants': Enseignant.objects.filter(actif=True),
        'salles': Salle.objects.filter(disponible=True),
        'jours_semaine': Cours.JOURS_SEMAINE,
        'semestres': Cours.SEMESTRES,
    }
    
    return render(request, 'courses/modifier_cours.html', context)


# ============================================
# VUES POUR LES SALLES
# ============================================

@login_required
def liste_salles(request):
    """Liste de toutes les salles"""
    
    # Filtres
    search_query = request.GET.get('search', '')
    type_salle = request.GET.get('type_salle', '')
    batiment = request.GET.get('batiment', '')
    
    # Base queryset
    salles = Salle.objects.all()
    
    # Appliquer les filtres
    if search_query:
        salles = salles.filter(
            Q(nom__icontains=search_query) | 
            Q(batiment__icontains=search_query)
        )
    
    if type_salle:
        salles = salles.filter(type_salle=type_salle)
    
    if batiment:
        salles = salles.filter(batiment__icontains=batiment)
    
    # Ordre
    salles = salles.order_by('batiment', 'nom')
    
    # Pagination
    paginator = Paginator(salles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_salles = salles.count()
    salles_disponibles = salles.filter(disponible=True).count()
    
    # Liste des bâtiments pour le filtre
    batiments = Salle.objects.values_list('batiment', flat=True).distinct().order_by('batiment')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'type_salle': type_salle,
        'batiment': batiment,
        'total_salles': total_salles,
        'salles_disponibles': salles_disponibles,
        'batiments': batiments,
        'types_salle': Salle.TYPES_SALLE,
    }
    
    return render(request, 'courses/liste_salles.html', context)


# ============================================
# VUES POUR LES SÉANCES
# ============================================

@login_required
def liste_seances(request):
    """Liste de toutes les séances"""
    
    # Filtres
    search_query = request.GET.get('search', '')
    cours_id = request.GET.get('cours', '')
    type_seance = request.GET.get('type_seance', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    # Base queryset
    seances = SeanceCours.objects.select_related(
        'cours', 
        'cours__enseignant', 
        'cours__filiere',
        'cours__niveau',
        'salle'
    )
    
    # Filtrer par enseignant si c'est un enseignant connecté
    if request.user.profil.est_enseignant():
        try:
            enseignant = request.user.enseignant
            seances = seances.filter(cours__enseignant=enseignant)
        except:
            seances = seances.none()
    
    # Appliquer les filtres
    if search_query:
        seances = seances.filter(
            Q(cours__code__icontains=search_query) | 
            Q(cours__intitule__icontains=search_query)
        )
    
    if cours_id:
        seances = seances.filter(cours_id=cours_id)
    
    if type_seance:
        seances = seances.filter(type_seance=type_seance)
    
    if date_debut:
        seances = seances.filter(date__gte=date_debut)
    
    if date_fin:
        seances = seances.filter(date__lte=date_fin)
    
    # Ordre par date décroissante
    seances = seances.order_by('-date', '-heure_debut')
    
    # Pagination
    paginator = Paginator(seances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_seances = seances.count()
    seances_avec_presence = seances.filter(presente=True).count()
    seances_sans_presence = seances.filter(presente=False).count()
    
    # Liste des cours pour le filtre
    cours_list = Cours.objects.filter(actif=True).select_related('filiere', 'niveau').order_by('code')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'cours_id': cours_id,
        'type_seance': type_seance,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'total_seances': total_seances,
        'seances_avec_presence': seances_avec_presence,
        'seances_sans_presence': seances_sans_presence,
        'cours_list': cours_list,
        'types_seance': SeanceCours.TYPE_SEANCE,
    }
    
    return render(request, 'courses/liste_seances.html', context)


@login_required
def detail_seance(request, seance_id):
    """Détail d'une séance"""
    
    seance = get_object_or_404(
        SeanceCours.objects.select_related(
            'cours',
            'cours__enseignant',
            'cours__filiere',
            'cours__niveau',
            'salle'
        ),
        id=seance_id
    )
    
    # Vérifier les permissions pour les enseignants
    if request.user.profil.est_enseignant():
        try:
            enseignant = request.user.enseignant
            if seance.cours.enseignant != enseignant:
                messages.error(request, "⛔ Vous n'avez pas accès à cette séance.")
                return redirect('liste_seances')
        except:
            messages.error(request, "⛔ Accès refusé.")
            return redirect('liste_seances')
    
    # Récupérer les présences de cette séance
    from attendance.models import Presence
    presences = Presence.objects.filter(seance=seance).select_related('etudiant').order_by('etudiant__nom', 'etudiant__prenom')
    
    context = {
        'seance': seance,
        'presences': presences,
    }
    
    return render(request, 'courses/detail_seance.html', context)

@login_required
def ajouter_seance(request, code_cours):
    """Ajouter une nouvelle séance pour un cours"""
    cours = get_object_or_404(Cours, code=code_cours)
    
    if request.method == 'POST':
        try:
            seance = SeanceCours.objects.create(
                cours=cours,
                date=request.POST.get('date'),
                heure_debut=request.POST.get('heure_debut'),
                heure_fin=request.POST.get('heure_fin'),
                salle_id=request.POST.get('salle') or None,
                type_seance=request.POST.get('type_seance'),
                contenu=request.POST.get('contenu'),
            )
            
            messages.success(request, f'Séance ajoutée avec succès pour le cours {cours.code}.')
            return redirect('detail_seance', seance_id=seance.id)
        
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout : {str(e)}')
    
    context = {
        'cours': cours,
        'salles': Salle.objects.filter(disponible=True),
        'types_seance': SeanceCours.TYPE_SEANCE,
    }
    
    return render(request, 'courses/ajouter_seance.html', context)


@login_required
def detail_seance(request, seance_id):
    """Détail d'une séance"""
    seance = get_object_or_404(SeanceCours, id=seance_id)
    
    # Récupérer les présences pour cette séance
    from attendance.models import Presence
    presences = Presence.objects.filter(seance=seance).select_related('etudiant')
    
    # Statistiques
    total = presences.count()
    presents = presences.filter(statut__in=['P', 'R']).count()
    absents = presences.filter(statut='A').count()
    retards = presences.filter(statut='R').count()
    
    context = {
        'seance': seance,
        'presences': presences,
        'total': total,
        'presents': presents,
        'absents': absents,
        'retards': retards,
        'taux_presence': seance.get_taux_presence() if seance.presente else None,
    }
    
    return render(request, 'courses/detail_seance.html', context)