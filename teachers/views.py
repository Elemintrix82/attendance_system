from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Enseignant
from courses.models import Cours
from students.models import Filiere, Niveau


@login_required
def liste_enseignants(request):
    """Liste de tous les enseignants avec recherche et filtres"""
    enseignants = Enseignant.objects.filter(actif=True)
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        enseignants = enseignants.filter(
            Q(matricule__icontains=search_query) |
            Q(nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(specialite__icontains=search_query)
        )
    
    # Filtre par grade
    grade = request.GET.get('grade')
    if grade:
        enseignants = enseignants.filter(grade=grade)
    
    # Pagination
    paginator = Paginator(enseignants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'grades': Enseignant.GRADES,
        'search_query': search_query,
        'total_enseignants': enseignants.count(),
    }
    
    return render(request, 'teachers/liste_enseignants.html', context)


@login_required
def detail_enseignant(request, matricule):
    """Détail d'un enseignant avec ses cours"""
    enseignant = get_object_or_404(Enseignant, matricule=matricule)
    
    # Récupérer les cours de l'enseignant
    cours = Cours.objects.filter(enseignant=enseignant, actif=True).select_related(
        'filiere', 'niveau', 'salle'
    )
    
    context = {
        'enseignant': enseignant,
        'cours': cours,
        'total_cours': cours.count(),
    }
    
    return render(request, 'teachers/detail_enseignant.html', context)


@login_required
def assigner_cours(request, matricule):
    """Interface pour assigner des cours à un enseignant"""
    
    # Vérification des permissions
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    enseignant = get_object_or_404(Enseignant, matricule=matricule)
    
    # POST - Assigner/Retirer des cours
    if request.method == 'POST':
        action = request.POST.get('action')
        cours_id = request.POST.get('cours_id')
        
        if cours_id:
            try:
                cours = Cours.objects.get(id=cours_id)
                
                if action == 'assigner':
                    cours.enseignant = enseignant
                    cours.save()
                    messages.success(request, f'✅ Cours {cours.code} assigné à {enseignant.nom_complet()}')
                
                elif action == 'retirer':
                    cours.enseignant = None
                    cours.save()
                    messages.success(request, f'✅ Cours {cours.code} retiré de {enseignant.nom_complet()}')
            
            except Cours.DoesNotExist:
                messages.error(request, '❌ Cours introuvable')
        
        return redirect('assigner_cours', matricule=matricule)
    
    # GET - Afficher l'interface
    # Cours déjà assignés à cet enseignant
    cours_assignes = Cours.objects.filter(
        enseignant=enseignant, 
        actif=True
    ).select_related('filiere', 'niveau')
    
    # Cours disponibles (sans enseignant OU assignés à d'autres)
    tous_les_cours = Cours.objects.filter(actif=True).select_related('filiere', 'niveau', 'enseignant')
    
    # Filtres
    search_query = request.GET.get('search', '')
    filiere_id = request.GET.get('filiere')
    niveau_id = request.GET.get('niveau')
    
    cours_disponibles = tous_les_cours.exclude(enseignant=enseignant)
    
    if search_query:
        cours_disponibles = cours_disponibles.filter(
            Q(code__icontains=search_query) |
            Q(intitule__icontains=search_query)
        )
    
    if filiere_id:
        cours_disponibles = cours_disponibles.filter(filiere_id=filiere_id)
    
    if niveau_id:
        cours_disponibles = cours_disponibles.filter(niveau_id=niveau_id)
    
    context = {
        'enseignant': enseignant,
        'cours_assignes': cours_assignes,
        'cours_disponibles': cours_disponibles,
        'filieres': Filiere.objects.all(),
        'niveaux': Niveau.objects.all(),
        'search_query': search_query,
    }
    
    return render(request, 'teachers/assigner_cours.html', context)


@login_required
def ajouter_enseignant(request):
    """Ajouter un nouvel enseignant AVEC compte et permissions - VERSION FUSIONNÉE"""
    
    # Vérification des permissions - RÉSERVÉ ADMIN/SCOLARITÉ
    if not hasattr(request.user, 'profil'):
        messages.error(request, 'Erreur de profil utilisateur.')
        return redirect('dashboard')
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, 'Accès refusé. Seuls les administrateurs et la scolarité peuvent créer des enseignants.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            matricule = request.POST.get('matricule')
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            email = request.POST.get('email')
            telephone = request.POST.get('telephone')
            specialite = request.POST.get('specialite')
            grade = request.POST.get('grade')
            sexe = request.POST.get('sexe')
            date_naissance = request.POST.get('date_naissance') or None
            date_embauche = request.POST.get('date_embauche') or None
            adresse = request.POST.get('adresse')
            mot_de_passe = request.POST.get('mot_de_passe')
            
            # Vérifier si le matricule existe déjà
            if User.objects.filter(username=matricule).exists():
                messages.error(request, f'Un utilisateur avec le matricule {matricule} existe déjà.')
                return redirect('ajouter_enseignant')
            
            # Vérifier si l'email existe déjà
            if User.objects.filter(email=email).exists():
                messages.error(request, f'Un utilisateur avec l\'email {email} existe déjà.')
                return redirect('ajouter_enseignant')
            
            # 1. Créer le User Django
            user = User.objects.create_user(
                username=matricule,
                email=email,
                first_name=prenom,
                last_name=nom,
                password=mot_de_passe  # Mot de passe personnalisé
            )
            
            # 2. Configurer le Profil (créé automatiquement par le signal)
            profil = user.profil
            profil.role = 'ENSEIGNANT'  # Assigner le rôle ENSEIGNANT
            profil.telephone = telephone
            profil.adresse = adresse
            profil.actif = True
            profil.save()
            
            # 3. Créer l'Enseignant
            enseignant = Enseignant.objects.create(
                user=user,
                matricule=matricule,
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                specialite=specialite,
                grade=grade,
                sexe=sexe,
                date_naissance=date_naissance,
                date_embauche=date_embauche,
                adresse=adresse,
                actif=True
            )
            
            # Gérer la photo si uploadée
            if 'photo' in request.FILES:
                enseignant.photo = request.FILES['photo']
                enseignant.save()
            
            messages.success(
                request, 
                f'✅ Enseignant {enseignant.nom_complet()} créé avec succès ! '
                f'Il peut maintenant se connecter avec le matricule {matricule}.'
            )
            return redirect('detail_enseignant', matricule=enseignant.matricule)
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de la création : {str(e)}')
            # Si erreur, supprimer le User créé pour éviter les doublons
            if 'user' in locals():
                user.delete()
    
    context = {
        'grades': Enseignant.GRADES,
    }
    
    return render(request, 'teachers/ajouter_enseignant.html', context)


@login_required
def modifier_enseignant(request, matricule):
    """Modifier un enseignant"""
    
    # Vérification des permissions
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    enseignant = get_object_or_404(Enseignant, matricule=matricule)
    
    if request.method == 'POST':
        try:
            # Mise à jour des informations enseignant
            enseignant.nom = request.POST.get('nom')
            enseignant.prenom = request.POST.get('prenom')
            enseignant.email = request.POST.get('email')
            enseignant.telephone = request.POST.get('telephone')
            enseignant.specialite = request.POST.get('specialite')
            enseignant.grade = request.POST.get('grade')
            enseignant.sexe = request.POST.get('sexe')
            enseignant.date_naissance = request.POST.get('date_naissance') or None
            enseignant.date_embauche = request.POST.get('date_embauche') or None
            enseignant.adresse = request.POST.get('adresse')
            
            if 'photo' in request.FILES:
                enseignant.photo = request.FILES['photo']
            
            enseignant.save()
            
            # Mettre à jour le User aussi
            enseignant.user.first_name = enseignant.prenom
            enseignant.user.last_name = enseignant.nom
            enseignant.user.email = enseignant.email
            enseignant.user.save()
            
            # Mettre à jour le profil
            enseignant.user.profil.telephone = enseignant.telephone
            enseignant.user.profil.adresse = enseignant.adresse
            enseignant.user.profil.save()
            
            messages.success(request, f'✅ Enseignant {enseignant.nom_complet()} modifié avec succès.')
            return redirect('detail_enseignant', matricule=enseignant.matricule)
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de la modification : {str(e)}')
    
    context = {
        'enseignant': enseignant,
        'grades': Enseignant.GRADES,
    }
    
    return render(request, 'teachers/modifier_enseignant.html', context)


@login_required
def reinitialiser_mot_de_passe_enseignant(request, matricule):
    """Réinitialiser le mot de passe d'un enseignant - RÉSERVÉ ADMIN/SCOLARITÉ"""
    
    # Vérification des permissions
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    enseignant = get_object_or_404(Enseignant, matricule=matricule)
    
    if request.method == 'POST':
        nouveau_mdp = request.POST.get('nouveau_mdp')
        
        if nouveau_mdp and len(nouveau_mdp) >= 6:
            enseignant.user.set_password(nouveau_mdp)
            enseignant.user.save()
            
            messages.success(
                request, 
                f'✅ Mot de passe réinitialisé pour {enseignant.nom_complet()}. '
                f'Nouveau mot de passe : {nouveau_mdp}'
            )
        else:
            messages.error(request, '❌ Le mot de passe doit contenir au moins 6 caractères.')
    
    return redirect('detail_enseignant', matricule=matricule)