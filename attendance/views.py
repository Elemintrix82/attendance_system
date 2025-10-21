from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Presence, Justificatif
from courses.models import SeanceCours, Cours
from students.models import Etudiant


@login_required
def prendre_presence(request, seance_id):
    """Prendre la présence pour une séance"""
    seance = get_object_or_404(
        SeanceCours.objects.select_related('cours', 'cours__filiere', 'cours__niveau', 'salle'),
        id=seance_id
    )
    
    # Vérifier les permissions pour les enseignants
    if request.user.profil.est_enseignant():
        try:
            enseignant = request.user.enseignant
            if seance.cours.enseignant != enseignant:
                messages.error(request, "⛔ Vous n'avez pas accès à cette séance.")
                return redirect('dashboard')
        except:
            messages.error(request, "⛔ Accès refusé.")
            return redirect('dashboard')
    
    # Récupérer tous les étudiants de cette filière et niveau
    etudiants = Etudiant.objects.filter(
        filiere=seance.cours.filiere,
        niveau=seance.cours.niveau,
        actif=True
    ).order_by('nom', 'prenom')
    
    if request.method == 'POST':
        # Traiter la soumission du formulaire de présence
        count = 0
        for etudiant in etudiants:
            statut = request.POST.get(f'presence_{etudiant.id}')
            heure_arrivee = request.POST.get(f'heure_{etudiant.id}') or None
            remarque = request.POST.get(f'remarque_{etudiant.id}', '')
            
            if statut:
                # Créer ou mettre à jour la présence
                presence, created = Presence.objects.update_or_create(
                    etudiant=etudiant,
                    seance=seance,
                    defaults={
                        'statut': statut,
                        'heure_arrivee': heure_arrivee,
                        'remarque': remarque,
                        'saisi_par': request.user,
                    }
                )
                count += 1
        
        # Marquer la séance comme présence effectuée
        seance.presente = True
        seance.save()
        
        messages.success(request, f'✅ Présence enregistrée avec succès pour {count} étudiant(s).')
        return redirect('detail_seance', seance_id=seance.id)
    
    # Récupérer les présences existantes et créer une liste d'étudiants avec leurs données
    presences_dict = {}
    for presence in Presence.objects.filter(seance=seance):
        presences_dict[presence.etudiant.id] = {
            'statut': presence.statut,
            'heure_arrivee': presence.heure_arrivee,
            'remarque': presence.remarque,
        }
    
    # Enrichir les étudiants avec les données de présence
    etudiants_list = []
    for etudiant in etudiants:
        etudiant_data = {
            'obj': etudiant,
            'presence': presences_dict.get(etudiant.id, None)
        }
        etudiants_list.append(etudiant_data)
    
    context = {
        'seance': seance,
        'etudiants': etudiants,
        'etudiants_data': etudiants_list,  # Liste enrichie
        'statuts': Presence.STATUTS,
    }
    
    return render(request, 'attendance/prendre_presence.html', context)


@login_required
def liste_presences(request):
    """Liste des présences avec filtres"""
    presences = Presence.objects.all().select_related(
        'etudiant', 'seance__cours', 'saisi_par'
    ).order_by('-seance__date')
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        presences = presences.filter(
            Q(etudiant__matricule__icontains=search_query) |
            Q(etudiant__nom__icontains=search_query) |
            Q(etudiant__prenom__icontains=search_query)
        )
    
    # Filtre par statut
    statut = request.GET.get('statut')
    if statut:
        presences = presences.filter(statut=statut)
    
    # Filtre par date
    date = request.GET.get('date')
    if date:
        presences = presences.filter(seance__date=date)
    
    # Filtre par cours
    cours_code = request.GET.get('cours')
    if cours_code:
        presences = presences.filter(seance__cours__code=cours_code)
    
    # Pagination
    paginator = Paginator(presences, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'statuts': Presence.STATUTS,
        'cours_list': Cours.objects.filter(actif=True),
        'search_query': search_query,
        'total_presences': presences.count(),
    }
    
    return render(request, 'attendance/liste_presences.html', context)


@login_required
def modifier_presence(request, presence_id):
    """Modifier une présence"""
    presence = get_object_or_404(Presence, id=presence_id)
    
    if request.method == 'POST':
        try:
            presence.statut = request.POST.get('statut')
            presence.heure_arrivee = request.POST.get('heure_arrivee') or None
            presence.remarque = request.POST.get('remarque', '')
            
            if 'justification' in request.FILES:
                presence.justification = request.FILES['justification']
            
            presence.save()
            
            messages.success(request, 'Présence modifiée avec succès.')
            return redirect('liste_presences')
        
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    context = {
        'presence': presence,
        'statuts': Presence.STATUTS,
    }
    
    return render(request, 'attendance/modifier_presence.html', context)


@login_required
def liste_justificatifs(request):
    """Liste des justificatifs"""
    justificatifs = Justificatif.objects.all().select_related('etudiant').order_by('-date_soumission')
    
    # Filtre par validation
    valide = request.GET.get('valide')
    if valide == 'true':
        justificatifs = justificatifs.filter(valide=True)
    elif valide == 'false':
        justificatifs = justificatifs.filter(valide=False)
    
    # Filtre par type
    type_justificatif = request.GET.get('type')
    if type_justificatif:
        justificatifs = justificatifs.filter(type_justificatif=type_justificatif)
    
    # Pagination
    paginator = Paginator(justificatifs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'types_justificatif': Justificatif.TYPE_JUSTIFICATIF,
        'total_justificatifs': justificatifs.count(),
    }
    
    return render(request, 'attendance/liste_justificatifs.html', context)


@login_required
def detail_justificatif(request, justificatif_id):
    """Détail d'un justificatif"""
    justificatif = get_object_or_404(Justificatif, id=justificatif_id)
    
    context = {
        'justificatif': justificatif,
    }
    
    return render(request, 'attendance/detail_justificatif.html', context)


@login_required
def valider_justificatif(request, justificatif_id):
    """Valider un justificatif"""
    justificatif = get_object_or_404(Justificatif, id=justificatif_id)
    
    if request.method == 'POST':
        justificatif.valide = True
        justificatif.valide_par = request.user
        justificatif.date_validation = timezone.now()
        justificatif.remarque_validation = request.POST.get('remarque_validation', '')
        justificatif.save()
        
        messages.success(request, 'Justificatif validé avec succès.')
        return redirect('detail_justificatif', justificatif_id=justificatif.id)
    
    return redirect('detail_justificatif', justificatif_id=justificatif.id)


@login_required
def refuser_justificatif(request, justificatif_id):
    """Refuser un justificatif"""
    justificatif = get_object_or_404(Justificatif, id=justificatif_id)
    
    if request.method == 'POST':
        justificatif.valide = False
        justificatif.valide_par = request.user
        justificatif.date_validation = timezone.now()
        justificatif.remarque_validation = request.POST.get('remarque_validation', '')
        justificatif.save()
        
        messages.success(request, 'Justificatif refusé.')
        return redirect('detail_justificatif', justificatif_id=justificatif.id)
    
    return redirect('detail_justificatif', justificatif_id=justificatif.id)


@login_required
def ajouter_justificatif(request, matricule):
    """Ajouter un justificatif pour un étudiant"""
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    if request.method == 'POST':
        try:
            justificatif = Justificatif.objects.create(
                etudiant=etudiant,
                type_justificatif=request.POST.get('type_justificatif'),
                motif=request.POST.get('motif'),
                date_debut=request.POST.get('date_debut'),
                date_fin=request.POST.get('date_fin'),
                fichier=request.FILES.get('fichier'),
            )
            
            messages.success(request, f'Justificatif ajouté avec succès pour {etudiant.nom_complet()}.')
            return redirect('detail_justificatif', justificatif_id=justificatif.id)
        
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout : {str(e)}')
    
    context = {
        'etudiant': etudiant,
        'types_justificatif': Justificatif.TYPE_JUSTIFICATIF,
    }
    
    return render(request, 'attendance/ajouter_justificatif.html', context)