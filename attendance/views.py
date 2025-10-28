from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from .models import Presence, Justificatif
from students.models import Etudiant, Filiere
from courses.models import SeanceCours, Cours
from teachers.models import Enseignant


# ============================================
# CONFIGURATION DES FILIÈRES
# ============================================

CONFIGURATION_FILIERES = {
    'FI': {  # Formation Initiale
        'nom': 'Formation Initiale',
        'specialites': {
            'GLO': {
                'nom': 'Génie Logistique',
                'niveaux': ['N3', 'N4', 'N5']
            },
            'GRT': {
                'nom': 'Génie des Réseaux et Télécommunications',
                'niveaux': ['N3', 'N4', 'N5']
            }
        }
    },
    'FA': {  # Formation en Alternance
        'nom': 'Formation en Alternance',
        'specialites': {
            'GLO': {
                'nom': 'Génie Logistique',
                'niveaux': ['N3', 'N4', 'N5']
            },
            'GRT': {
                'nom': 'Génie des Réseaux et Télécommunications',
                'niveaux': ['N3', 'N4', 'N5']
            }
        }
    },
    'MP': {  # Master Professionnel
        'nom': 'Master Professionnel',
        'specialites': {
            'CSCD': {
                'nom': 'Cyber-Sécurité et Cryptographie Digitale',
                'niveaux': ['N4', 'N5']
            },
            'SSI': {
                'nom': 'Systèmes et Sécurité Informatique',
                'niveaux': ['N4', 'N5']
            },
            'GLO': {
                'nom': 'Génie Logistique',
                'niveaux': ['N4', 'N5']
            },
            'GRT': {
                'nom': 'Génie des Réseaux et Télécommunications',
                'niveaux': ['N4', 'N5']
            },
            'GI': {
                'nom': 'Génie Informatique et Télécommunication',
                'niveaux': ['N4', 'N5']
            }
        }
    }
}


@login_required
def navigation_presences(request):
    """
    Vue pour naviguer par filière avec système en cascade
    """
    # Récupérer les sélections actuelles
    formation_selected = request.GET.get('formation', '')
    specialite_selected = request.GET.get('specialite', '')
    niveau_selected = request.GET.get('niveau', '')
    
    # Liste des formations disponibles
    formations = [(code, config['nom']) for code, config in CONFIGURATION_FILIERES.items()]
    
    # Spécialités disponibles selon la formation choisie
    specialites = []
    if formation_selected and formation_selected in CONFIGURATION_FILIERES:
        specialites = [
            (code, spec['nom']) 
            for code, spec in CONFIGURATION_FILIERES[formation_selected]['specialites'].items()
        ]
    
    # Niveaux disponibles selon la formation et spécialité choisies
    niveaux = []
    if formation_selected and specialite_selected:
        if (formation_selected in CONFIGURATION_FILIERES and 
            specialite_selected in CONFIGURATION_FILIERES[formation_selected]['specialites']):
            niveaux_codes = CONFIGURATION_FILIERES[formation_selected]['specialites'][specialite_selected]['niveaux']
            # Convertir en tuples (code, label)
            niveaux = [
                (niveau, f"Niveau {niveau[1]}")  # N3 → Niveau 3
                for niveau in niveaux_codes
            ]
    
    context = {
        'formations': formations,
        'specialites': specialites,
        'niveaux': niveaux,
        'formation_selected': formation_selected,
        'specialite_selected': specialite_selected,
        'niveau_selected': niveau_selected,
    }
    
    return render(request, 'attendance/navigation_presences.html', context)


@login_required
def get_specialites_ajax(request):
    """
    API AJAX pour récupérer les spécialités en fonction de la formation
    """
    formation = request.GET.get('formation', '')
    
    if formation and formation in CONFIGURATION_FILIERES:
        specialites = [
            {'code': code, 'nom': spec['nom']}
            for code, spec in CONFIGURATION_FILIERES[formation]['specialites'].items()
        ]
        return JsonResponse({'success': True, 'specialites': specialites})
    
    return JsonResponse({'success': False, 'specialites': []})


@login_required
def get_niveaux_ajax(request):
    """
    API AJAX pour récupérer les niveaux en fonction de la formation et spécialité
    """
    formation = request.GET.get('formation', '')
    specialite = request.GET.get('specialite', '')
    
    if (formation and specialite and 
        formation in CONFIGURATION_FILIERES and 
        specialite in CONFIGURATION_FILIERES[formation]['specialites']):
        
        niveaux_codes = CONFIGURATION_FILIERES[formation]['specialites'][specialite]['niveaux']
        niveaux = [
            {'code': niveau, 'nom': f"Niveau {niveau[1]}"}
            for niveau in niveaux_codes
        ]
        return JsonResponse({'success': True, 'niveaux': niveaux})
    
    return JsonResponse({'success': False, 'niveaux': []})


@login_required
def presences_par_filiere(request):
    """
    Affiche les présences filtrées par filière complète
    """
    # Récupérer les paramètres de filière
    formation = request.GET.get('formation', '')
    specialite = request.GET.get('specialite', '')
    niveau_param = request.GET.get('niveau', '')
    
    # ✅ Gérer le niveau correctement (avec ou sans "N")
    if niveau_param:
        if not niveau_param.startswith('N'):
            niveau = f"N{niveau_param}"
        else:
            niveau = niveau_param
    else:
        niveau = ''
    
    # Vérifier que tous les paramètres sont présents
    if not all([formation, specialite, niveau]):
        messages.warning(request, "⚠️ Veuillez sélectionner une formation, une spécialité et un niveau.")
        return redirect('navigation_presences')
    
    # Rechercher la filière correspondante
    try:
        filiere = Filiere.objects.get(
            formation=formation,
            specialite=specialite,
            niveau=niveau
        )
    except Filiere.DoesNotExist:
        # ✅ Si la filière n'existe pas, proposer de la créer
        messages.error(request, f"❌ Aucune filière trouvée pour {formation}-{specialite}-{niveau}")
        
        context = {
            'formation': formation,
            'specialite': specialite,
            'niveau': niveau,
            'filiere_inexistante': True,
        }
        return render(request, 'attendance/filiere_inexistante.html', context)
    
    # Vérifier s'il y a des étudiants dans cette filière
    etudiants = Etudiant.objects.filter(filiere=filiere, actif=True)
    total_etudiants = etudiants.count()
    
    if total_etudiants == 0:
        # ✅ Aucun étudiant dans cette filière
        messages.warning(request, f"⚠️ Aucun étudiant enregistré dans la filière {filiere.nom_complet()}")
        
        context = {
            'filiere': filiere,
            'formation': formation,
            'specialite': specialite,
            'niveau': niveau,
            'aucun_etudiant': True,
        }
        return render(request, 'attendance/presences_par_filiere.html', context)
    
    # Récupérer les présences pour cette filière
    presences = Presence.objects.filter(
        etudiant__filiere=filiere
    ).select_related(
        'etudiant',
        'seance__cours',
        'seance__salle'
    ).order_by('-seance__date', 'etudiant__nom')
    
    # Filtres supplémentaires
    search_query = request.GET.get('search', '')
    statut_filtre = request.GET.get('statut', '')
    date_filtre = request.GET.get('date', '')
    cours_filtre = request.GET.get('cours', '')
    
    # Appliquer les filtres
    if search_query:
        presences = presences.filter(
            Q(etudiant__matricule__icontains=search_query) |
            Q(etudiant__nom__icontains=search_query) |
            Q(etudiant__prenom__icontains=search_query)
        )
    
    if statut_filtre:
        presences = presences.filter(statut=statut_filtre)
    
    if date_filtre:
        presences = presences.filter(seance__date=date_filtre)
    
    if cours_filtre:
        presences = presences.filter(seance__cours__code=cours_filtre)
    
    # Statistiques
    total_presences = presences.count()
    stats = {
        'presents': presences.filter(statut='P').count(),
        'absents': presences.filter(statut='A').count(),
        'retards': presences.filter(statut='R').count(),
        'justifies': presences.filter(statut='J').count(),
    }
    
    # Liste des cours pour le filtre
    cours_list = Cours.objects.filter(filiere=filiere, actif=True)
    
    # Pagination
    paginator = Paginator(presences, 50)  # 50 résultats par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Choix de statuts pour le formulaire
    statuts = Presence.STATUTS
    
    context = {
        'filiere': filiere,
        'formation': formation,
        'specialite': specialite,
        'niveau': niveau,
        'page_obj': page_obj,
        'total_presences': total_presences,
        'total_etudiants': total_etudiants,
        'stats': stats,
        'cours_list': cours_list,
        'statuts': statuts,
        'search_query': search_query,
        'statut_filtre': statut_filtre,
        'date_filtre': date_filtre,
        'cours_filtre': cours_filtre,
        'aucun_etudiant': False,
    }
    
    return render(request, 'attendance/presences_par_filiere.html', context)


@login_required
def prendre_presence(request, seance_id):
    """
    Prendre la présence pour une séance donnée
    """
    seance = get_object_or_404(SeanceCours, id=seance_id)
    
    # Récupérer tous les étudiants de la filière du cours
    etudiants = Etudiant.objects.filter(
        filiere=seance.cours.filiere,
        actif=True
    ).order_by('nom', 'prenom')
    
    if request.method == 'POST':
        # Traiter les présences
        count = 0
        for etudiant in etudiants:
            statut = request.POST.get(f'presence_{etudiant.id}')
            heure_arrivee = request.POST.get(f'heure_{etudiant.id}')
            remarque = request.POST.get(f'remarque_{etudiant.id}')
            
            if statut:
                # Créer ou mettre à jour la présence
                presence, created = Presence.objects.update_or_create(
                    etudiant=etudiant,
                    seance=seance,
                    defaults={
                        'statut': statut,
                        'heure_arrivee': heure_arrivee if heure_arrivee else None,
                        'remarque': remarque,
                        'saisi_par': request.user,
                    }
                )
                count += 1
        
        # Marquer la séance comme "présence effectuée"
        seance.presente = True
        seance.save()
        
        messages.success(request, f"✅ Présence enregistrée pour {count} étudiant(s)")
        return redirect('dashboard')
    
    # Pour l'affichage, créer une liste avec les présences existantes
    etudiants_data = []
    for etudiant in etudiants:
        presence = Presence.objects.filter(
            etudiant=etudiant,
            seance=seance
        ).first()
        etudiants_data.append({
            'obj': etudiant,
            'presence': presence
        })
    
    context = {
        'seance': seance,
        'etudiants': etudiants,
        'etudiants_data': etudiants_data,
    }
    
    return render(request, 'attendance/prendre_presence.html', context)


@login_required
def modifier_presence(request, presence_id):
    """
    Modifier une présence existante
    """
    presence = get_object_or_404(Presence, id=presence_id)
    
    # Vérifier les permissions
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "❌ Vous n'avez pas la permission de modifier les présences.")
        return redirect('liste_presences')
    
    if request.method == 'POST':
        statut = request.POST.get('statut')
        heure_arrivee = request.POST.get('heure_arrivee')
        remarque = request.POST.get('remarque')
        justification = request.FILES.get('justification')
        
        # Mise à jour
        presence.statut = statut
        presence.heure_arrivee = heure_arrivee if heure_arrivee else None
        presence.remarque = remarque
        
        if justification:
            presence.justification = justification
        
        presence.save()
        
        messages.success(request, "✅ Présence modifiée avec succès")
        return redirect('liste_presences')
    
    # Choix de statuts
    statuts = Presence.STATUTS
    
    context = {
        'presence': presence,
        'statuts': statuts,
    }
    
    return render(request, 'attendance/modifier_presence.html', context)


@login_required
def liste_presences(request):
    """
    Liste globale de toutes les présences (avec filtres)
    """
    presences = Presence.objects.select_related(
        'etudiant',
        'seance__cours',
        'seance__salle'
    ).order_by('-seance__date', 'etudiant__nom')
    
    # Filtres
    search_query = request.GET.get('search', '')
    statut_filtre = request.GET.get('statut', '')
    date_filtre = request.GET.get('date', '')
    cours_filtre = request.GET.get('cours', '')
    
    if search_query:
        presences = presences.filter(
            Q(etudiant__matricule__icontains=search_query) |
            Q(etudiant__nom__icontains=search_query) |
            Q(etudiant__prenom__icontains=search_query)
        )
    
    if statut_filtre:
        presences = presences.filter(statut=statut_filtre)
    
    if date_filtre:
        presences = presences.filter(seance__date=date_filtre)
    
    if cours_filtre:
        presences = presences.filter(seance__cours__code=cours_filtre)
    
    # Pagination
    paginator = Paginator(presences, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Liste des cours pour le filtre
    cours_list = Cours.objects.filter(actif=True)
    
    # Choix de statuts
    statuts = Presence.STATUTS
    
    context = {
        'page_obj': page_obj,
        'total_presences': presences.count(),
        'cours_list': cours_list,
        'statuts': statuts,
        'search_query': search_query,
    }
    
    return render(request, 'attendance/liste_presences.html', context)


@login_required
def detail_presence(request, presence_id):
    """Voir le détail d'une présence"""
    presence = get_object_or_404(Presence, id=presence_id)
    context = {'presence': presence}
    return render(request, 'attendance/detail_presence.html', context)


@login_required
def supprimer_presence(request, presence_id):
    """Supprimer une présence"""
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "❌ Permission refusée")
        return redirect('liste_presences')
    
    presence = get_object_or_404(Presence, id=presence_id)
    
    if request.method == 'POST':
        etudiant_nom = presence.etudiant.nom_complet
        cours = presence.seance.cours.code
        presence.delete()
        messages.success(request, f"✅ Présence de {etudiant_nom} ({cours}) supprimée")
        return redirect('liste_presences')
    
    return redirect('liste_presences')


# ============================================
# JUSTIFICATIFS - VERSION AMÉLIORÉE
# ============================================

@login_required
def liste_justificatifs(request):
    """Liste des justificatifs d'absence avec statistiques complètes"""
    
    # Récupérer tous les justificatifs
    justificatifs = Justificatif.objects.select_related(
        'etudiant__filiere', 'valide_par'
    ).order_by('-date_soumission')
    
    # 🔍 FILTRES
    statut_filtre = request.GET.get('statut', '')
    type_filtre = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    # Appliquer les filtres
    if statut_filtre == 'valide':
        justificatifs = justificatifs.filter(valide=True)
    elif statut_filtre == 'non_valide':
        justificatifs = justificatifs.filter(valide=False)
    
    if type_filtre:
        justificatifs = justificatifs.filter(type_justificatif=type_filtre)
    
    if search_query:
        justificatifs = justificatifs.filter(
            Q(etudiant__matricule__icontains=search_query) |
            Q(etudiant__nom__icontains=search_query) |
            Q(etudiant__prenom__icontains=search_query)
        )
    
    # 📊 STATISTIQUES (sur la liste COMPLÈTE, pas filtrée)
    tous_justificatifs = Justificatif.objects.all()
    total_justificatifs = tous_justificatifs.count()
    validated_count = tous_justificatifs.filter(valide=True).count()
    pending_count = tous_justificatifs.filter(valide=False).count()
    
    # 📄 PAGINATION
    paginator = Paginator(justificatifs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 📦 CONTEXTE
    context = {
        'page_obj': page_obj,
        'types': Justificatif.TYPES_JUSTIFICATIF,
        'total_justificatifs': total_justificatifs,
        'validated_count': validated_count,
        'pending_count': pending_count,
        # Pour les filtres (affichage)
        'search_query': search_query,
        'statut_filtre': statut_filtre,
        'type_filtre': type_filtre,
    }
    
    return render(request, 'attendance/liste_justificatifs.html', context)


@login_required
def detail_justificatif(request, justificatif_id):
    """Détail d'un justificatif avec présences concernées"""
    justificatif = get_object_or_404(Justificatif, id=justificatif_id)
    
    # 🆕 Récupérer les présences concernées par ce justificatif
    presences_concernees = justificatif.presences_concernees()
    
    # Séparer en présences liées et non liées
    presences_liees = presences_concernees.filter(justificatif_formel=justificatif)
    presences_non_liees = presences_concernees.exclude(justificatif_formel=justificatif)
    
    context = {
        'justificatif': justificatif,
        'presences_concernees': presences_concernees,
        'presences_liees': presences_liees,
        'presences_non_liees': presences_non_liees,
        'nb_presences_concernees': presences_concernees.count(),
        'nb_presences_liees': presences_liees.count(),
    }
    
    return render(request, 'attendance/detail_justificatif.html', context)


@login_required
def valider_justificatif(request, justificatif_id):
    """Valider un justificatif et l'appliquer automatiquement aux présences"""
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "❌ Permission refusée")
        return redirect('liste_justificatifs')
    
    justificatif = get_object_or_404(Justificatif, id=justificatif_id)
    
    if request.method == 'POST':
        # Validation du justificatif
        justificatif.valide = True
        justificatif.valide_par = request.user
        justificatif.date_validation = timezone.now()
        justificatif.remarque_validation = request.POST.get('remarque', '')
        justificatif.save()
        
        # 🆕 Appliquer automatiquement aux présences
        nb_presences = justificatif.appliquer_aux_presences()
        
        messages.success(
            request, 
            f"✅ Justificatif validé et appliqué à {nb_presences} présence(s)"
        )
        return redirect('detail_justificatif', justificatif_id=justificatif.id)
    
    # Prévisualiser les présences qui seront affectées
    presences_concernees = justificatif.presences_concernees()
    presences_absentes = presences_concernees.filter(statut='A')
    
    context = {
        'justificatif': justificatif,
        'presences_concernees': presences_concernees,
        'presences_absentes': presences_absentes,
        'nb_a_justifier': presences_absentes.count(),
    }
    
    return render(request, 'attendance/valider_justificatif.html', context)


@login_required
def refuser_justificatif(request, justificatif_id):
    """Refuser un justificatif et retirer des présences"""
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "❌ Permission refusée")
        return redirect('liste_justificatifs')
    
    justificatif = get_object_or_404(Justificatif, id=justificatif_id)
    
    if request.method == 'POST':
        # 🆕 Retirer le justificatif des présences d'abord
        nb_presences = justificatif.retirer_des_presences()
        
        # Refuser le justificatif
        justificatif.valide = False
        justificatif.valide_par = None
        justificatif.date_validation = None
        justificatif.remarque_validation = request.POST.get('remarque', '')
        justificatif.save()
        
        messages.warning(
            request, 
            f"⚠️ Justificatif refusé. {nb_presences} présence(s) remise(s) en 'Absent'"
        )
        return redirect('liste_justificatifs')
    
    # Prévisualiser les présences qui seront affectées
    presences_liees = Presence.objects.filter(justificatif_formel=justificatif)
    
    context = {
        'justificatif': justificatif,
        'presences_liees': presences_liees,
        'nb_a_retirer': presences_liees.count(),
    }
    
    return render(request, 'attendance/refuser_justificatif.html', context)


@login_required
def ajouter_justificatif(request, matricule):
    """Ajouter un justificatif pour un étudiant"""
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    if request.method == 'POST':
        type_justificatif = request.POST.get('type_justificatif')
        motif = request.POST.get('motif')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin') or None
        fichier = request.FILES.get('fichier')
        
        # Créer le justificatif
        justificatif = Justificatif.objects.create(
            etudiant=etudiant,
            type_justificatif=type_justificatif,
            motif=motif,
            date_debut=date_debut,
            date_fin=date_fin,
            fichier=fichier,
        )
        
        # 🆕 Optionnel : Appliquer automatiquement si l'utilisateur est admin
        if request.user.profil.est_admin() or request.user.profil.est_scolarite():
            auto_validate = request.POST.get('auto_validate', False)
            if auto_validate:
                justificatif.valide = True
                justificatif.valide_par = request.user
                justificatif.date_validation = timezone.now()
                justificatif.save()
                
                nb_presences = justificatif.appliquer_aux_presences()
                messages.success(
                    request, 
                    f"✅ Justificatif ajouté et validé. Appliqué à {nb_presences} présence(s)"
                )
            else:
                messages.success(request, "✅ Justificatif ajouté (en attente de validation)")
        else:
            messages.success(request, "✅ Justificatif soumis (en attente de validation)")
        
        return redirect('detail_etudiant', matricule=matricule)
    
    # 🆕 Récupérer les absences non justifiées de cet étudiant
    absences_non_justifiees = Presence.objects.filter(
        etudiant=etudiant,
        statut='A',
        justificatif_formel__isnull=True
    ).select_related('seance__cours').order_by('-seance__date')[:10]
    
    context = {
        'etudiant': etudiant,
        'types': Justificatif.TYPES_JUSTIFICATIF,
        'absences_non_justifiees': absences_non_justifiees,
    }
    
    return render(request, 'attendance/ajouter_justificatif.html', context)


@login_required
def appliquer_justificatif_manuel(request, justificatif_id, presence_id):
    """Lier manuellement un justificatif à une présence spécifique"""
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "❌ Permission refusée")
        return redirect('liste_justificatifs')
    
    justificatif = get_object_or_404(Justificatif, id=justificatif_id)
    presence = get_object_or_404(Presence, id=presence_id)
    
    # Vérifier que le justificatif est validé
    if not justificatif.valide:
        messages.error(request, "❌ Le justificatif doit d'abord être validé")
        return redirect('detail_justificatif', justificatif_id=justificatif.id)
    
    # Vérifier que c'est le même étudiant
    if presence.etudiant != justificatif.etudiant:
        messages.error(request, "❌ Le justificatif ne correspond pas à cet étudiant")
        return redirect('detail_justificatif', justificatif_id=justificatif.id)
    
    # Appliquer
    presence.statut = 'J'
    presence.justificatif_formel = justificatif
    presence.save()
    
    messages.success(request, "✅ Justificatif appliqué à cette présence")
    return redirect('detail_justificatif', justificatif_id=justificatif.id)


@login_required
def retirer_justificatif_manuel(request, presence_id):
    """Retirer manuellement un justificatif d'une présence"""
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "❌ Permission refusée")
        return redirect('liste_justificatifs')
    
    presence = get_object_or_404(Presence, id=presence_id)
    justificatif = presence.justificatif_formel
    
    if not justificatif:
        messages.error(request, "❌ Aucun justificatif lié à cette présence")
        return redirect('liste_presences')
    
    # Retirer
    presence.statut = 'A'
    presence.justificatif_formel = None
    presence.save()
    
    messages.success(request, "✅ Justificatif retiré de cette présence")
    return redirect('detail_justificatif', justificatif_id=justificatif.id)


@login_required
def modifier_justificatif(request, justificatif_id):
    """Modifier un justificatif existant"""
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "❌ Permission refusée")
        return redirect('liste_justificatifs')
    
    justificatif = get_object_or_404(Justificatif, id=justificatif_id)
    
    if request.method == 'POST':
        justificatif.type_justificatif = request.POST.get('type_justificatif')
        justificatif.motif = request.POST.get('motif')
        justificatif.date_debut = request.POST.get('date_debut')
        justificatif.date_fin = request.POST.get('date_fin') or None
        
        if 'fichier' in request.FILES:
            justificatif.fichier = request.FILES['fichier']
        
        justificatif.save()
        messages.success(request, "✅ Justificatif modifié avec succès")
        return redirect('detail_justificatif', justificatif_id=justificatif.id)
    
    context = {
        'justificatif': justificatif,
        'types': Justificatif.TYPES_JUSTIFICATIF,
    }
    return render(request, 'attendance/modifier_justificatif.html', context)


@login_required
def supprimer_justificatif(request, justificatif_id):
    """Supprimer un justificatif"""
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "❌ Permission refusée")
        return redirect('liste_justificatifs')
    
    justificatif = get_object_or_404(Justificatif, id=justificatif_id)
    
    if request.method == 'POST':
        etudiant_nom = justificatif.etudiant.nom_complet
        justificatif.delete()
        messages.success(request, f"✅ Justificatif de {etudiant_nom} supprimé")
        return redirect('liste_justificatifs')
    
    return redirect('detail_justificatif', justificatif_id=justificatif.id)


@login_required
def selectionner_etudiant_justificatif(request):
    """Page de sélection d'un étudiant pour ajouter un justificatif"""
    
    # Récupérer les paramètres de recherche
    search_query = request.GET.get('search', '')
    formation_filtre = request.GET.get('formation', '')
    niveau_filtre = request.GET.get('niveau', '')
    
    etudiants = None
    
    if search_query or formation_filtre or niveau_filtre:
        # Rechercher les étudiants
        etudiants = Etudiant.objects.filter(actif=True).select_related('filiere')
        
        if search_query:
            etudiants = etudiants.filter(
                Q(matricule__icontains=search_query) |
                Q(nom__icontains=search_query) |
                Q(prenom__icontains=search_query)
            )
        
        if formation_filtre:
            etudiants = etudiants.filter(filiere__formation=formation_filtre)
        
        if niveau_filtre:
            etudiants = etudiants.filter(filiere__niveau=niveau_filtre)
        
        etudiants = etudiants.order_by('nom', 'prenom')
    
    context = {
        'etudiants': etudiants,
        'search_query': search_query,
        'formation_filtre': formation_filtre,
        'niveau_filtre': niveau_filtre,
    }
    
    return render(request, 'attendance/selectionner_etudiant_justificatif.html', context)