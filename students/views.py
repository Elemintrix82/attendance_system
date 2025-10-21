from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Etudiant, Filiere, Niveau
from attendance.models import Presence


@login_required
def liste_etudiants(request):
    """Liste de tous les étudiants avec recherche et filtres"""
    etudiants = Etudiant.objects.filter(actif=True).select_related('filiere', 'niveau')
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        etudiants = etudiants.filter(
            Q(matricule__icontains=search_query) |
            Q(nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filtres
    filiere_id = request.GET.get('filiere')
    if filiere_id:
        etudiants = etudiants.filter(filiere_id=filiere_id)
    
    niveau_id = request.GET.get('niveau')
    if niveau_id:
        etudiants = etudiants.filter(niveau_id=niveau_id)
    
    # Pagination
    paginator = Paginator(etudiants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filieres': Filiere.objects.all(),
        'niveaux': Niveau.objects.all(),
        'search_query': search_query,
        'total_etudiants': etudiants.count(),
    }
    
    return render(request, 'students/liste_etudiants.html', context)


@login_required
def detail_etudiant(request, matricule):
    """Détail d'un étudiant avec ses présences"""
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    # Récupérer les présences
    presences = Presence.objects.filter(etudiant=etudiant).select_related(
        'seance__cours'
    ).order_by('-seance__date')
    
    # Statistiques de présence
    total_seances = presences.count()
    presents = presences.filter(statut__in=['P', 'R', 'J']).count()
    absents = presences.filter(statut='A').count()
    retards = presences.filter(statut='R').count()
    
    taux_presence = etudiant.get_taux_presence()
    
    # Pagination des présences
    paginator = Paginator(presences, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'etudiant': etudiant,
        'page_obj': page_obj,
        'total_seances': total_seances,
        'presents': presents,
        'absents': absents,
        'retards': retards,
        'taux_presence': taux_presence,
    }
    
    return render(request, 'students/detail_etudiant.html', context)


@login_required
def ajouter_etudiant(request):
    """Ajouter un nouvel étudiant"""
    if request.method == 'POST':
        try:
            etudiant = Etudiant.objects.create(
                matricule=request.POST.get('matricule'),
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom'),
                email=request.POST.get('email'),
                telephone=request.POST.get('telephone'),
                filiere_id=request.POST.get('filiere'),
                niveau_id=request.POST.get('niveau'),
                sexe=request.POST.get('sexe'),
                date_naissance=request.POST.get('date_naissance') or None,
                lieu_naissance=request.POST.get('lieu_naissance'),
                adresse=request.POST.get('adresse'),
            )
            
            if 'photo' in request.FILES:
                etudiant.photo = request.FILES['photo']
                etudiant.save()
            
            messages.success(request, f'Étudiant {etudiant.nom_complet()} ajouté avec succès.')
            return redirect('detail_etudiant', matricule=etudiant.matricule)
        
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout : {str(e)}')
    
    context = {
        'filieres': Filiere.objects.all(),
        'niveaux': Niveau.objects.all(),
    }
    
    return render(request, 'students/ajouter_etudiant.html', context)


@login_required
def modifier_etudiant(request, matricule):
    """Modifier un étudiant"""
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    if request.method == 'POST':
        try:
            etudiant.nom = request.POST.get('nom')
            etudiant.prenom = request.POST.get('prenom')
            etudiant.email = request.POST.get('email')
            etudiant.telephone = request.POST.get('telephone')
            etudiant.filiere_id = request.POST.get('filiere')
            etudiant.niveau_id = request.POST.get('niveau')
            etudiant.sexe = request.POST.get('sexe')
            etudiant.date_naissance = request.POST.get('date_naissance') or None
            etudiant.lieu_naissance = request.POST.get('lieu_naissance')
            etudiant.adresse = request.POST.get('adresse')
            
            if 'photo' in request.FILES:
                etudiant.photo = request.FILES['photo']
            
            etudiant.save()
            
            messages.success(request, f'Étudiant {etudiant.nom_complet()} modifié avec succès.')
            return redirect('detail_etudiant', matricule=etudiant.matricule)
        
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    context = {
        'etudiant': etudiant,
        'filieres': Filiere.objects.all(),
        'niveaux': Niveau.objects.all(),
    }
    
    return render(request, 'students/modifier_etudiant.html', context)


@login_required
def liste_filieres(request):
    """Liste des filières"""
    filieres = Filiere.objects.annotate(
        nb_etudiants=Count('etudiants', filter=Q(etudiants__actif=True))
    )
    
    context = {
        'filieres': filieres,
    }
    
    return render(request, 'students/liste_filieres.html', context)


@login_required
def detail_filiere(request, code):
    """Détail d'une filière avec ses étudiants"""
    filiere = get_object_or_404(Filiere, code=code)
    etudiants = Etudiant.objects.filter(filiere=filiere, actif=True).select_related('niveau')
    
    # Pagination
    paginator = Paginator(etudiants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'filiere': filiere,
        'page_obj': page_obj,
        'total_etudiants': etudiants.count(),
    }
    
    return render(request, 'students/detail_filiere.html', context)