from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Profil, HistoriqueConnexion
from teachers.models import Enseignant


def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Enregistrer l'historique de connexion
            HistoriqueConnexion.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
            return redirect('dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """Tableau de bord principal"""
    context = {
        'user': request.user,
    }
    
    # Vérifier le rôle de l'utilisateur
    if hasattr(request.user, 'profil'):
        profil = request.user.profil
        
        if profil.est_admin() or profil.est_scolarite():
            # Dashboard pour admin/scolarité
            from students.models import Etudiant, Filiere
            from teachers.models import Enseignant
            from courses.models import Cours, SeanceCours
            from attendance.models import Presence
            from django.db.models import Count, Q
            
            context.update({
                'total_etudiants': Etudiant.objects.filter(actif=True).count(),
                'total_enseignants': Enseignant.objects.filter(actif=True).count(),
                'total_cours': Cours.objects.filter(actif=True).count(),
                'total_filieres': Filiere.objects.count(),
                'seances_aujourdhui': SeanceCours.objects.filter(
                    date=timezone.now().date()
                ).count(),
            })
            
            return render(request, 'accounts/dashboard_admin.html', context)
        
        elif profil.est_enseignant():
            # Dashboard pour enseignant - UNIQUEMENT SES COURS
            if hasattr(request.user, 'enseignant'):
                enseignant = request.user.enseignant
                from courses.models import Cours, SeanceCours
                
                # Uniquement les cours assignés à cet enseignant
                mes_cours = Cours.objects.filter(enseignant=enseignant, actif=True)
                
                # Uniquement les séances de SES cours
                seances_aujourdhui = SeanceCours.objects.filter(
                    cours__enseignant=enseignant,
                    date=timezone.now().date()
                )
                
                context.update({
                    'mes_cours': mes_cours,
                    'seances_aujourdhui': seances_aujourdhui,
                })
                
                return render(request, 'accounts/dashboard_enseignant.html', context)
    
    # Dashboard par défaut
    return render(request, 'accounts/dashboard.html', context)


@login_required
def register_enseignant(request):
    """Enregistrer un nouvel enseignant - RÉSERVÉ ADMIN/SCOLARITÉ"""
    
    # Vérification des permissions
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
            mot_de_passe = request.POST.get('mot_de_passe')
            
            # Vérifier si le matricule existe déjà
            if User.objects.filter(username=matricule).exists():
                messages.error(request, f'Un utilisateur avec le matricule {matricule} existe déjà.')
                return redirect('register_enseignant')
            
            # Créer le User
            user = User.objects.create_user(
                username=matricule,
                email=email,
                first_name=prenom,
                last_name=nom,
                password=mot_de_passe  # Mot de passe personnalisé
            )
            
            # Créer le Profil avec rôle ENSEIGNANT
            profil = Profil.objects.get(user=user)  # Créé automatiquement par signal
            profil.role = 'ENSEIGNANT'
            profil.telephone = telephone
            profil.actif = True
            profil.save()
            
            # Créer l'Enseignant
            enseignant = Enseignant.objects.create(
                user=user,
                matricule=matricule,
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                specialite=specialite,
                grade=grade,
                actif=True
            )
            
            messages.success(request, f'Enseignant {enseignant.nom_complet()} créé avec succès ! Matricule: {matricule}')
            return redirect('liste_enseignants')
        
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
    
    context = {
        'grades': Enseignant.GRADES,
    }
    
    return render(request, 'accounts/register_enseignant.html', context)


@login_required
def profil_view(request):
    """Vue du profil utilisateur"""
    if request.method == 'POST':
        # Mise à jour du profil
        if hasattr(request.user, 'profil'):
            profil = request.user.profil
            profil.telephone = request.POST.get('telephone', profil.telephone)
            profil.adresse = request.POST.get('adresse', profil.adresse)
            
            if 'photo' in request.FILES:
                profil.photo = request.FILES['photo']
            
            profil.save()
            messages.success(request, 'Profil mis à jour avec succès.')
        
        # Mise à jour des informations User
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()
        
        return redirect('profil')
    
    context = {
        'user': request.user,
    }
    return render(request, 'accounts/profil.html', context)


@login_required
def changer_mot_de_passe(request):
    """Vue pour changer le mot de passe"""
    if request.method == 'POST':
        ancien_mdp = request.POST.get('ancien_mdp')
        nouveau_mdp = request.POST.get('nouveau_mdp')
        confirmer_mdp = request.POST.get('confirmer_mdp')
        
        # Vérifier l'ancien mot de passe
        if not request.user.check_password(ancien_mdp):
            messages.error(request, 'Ancien mot de passe incorrect.')
            return redirect('changer_mot_de_passe')
        
        # Vérifier que les mots de passe correspondent
        if nouveau_mdp != confirmer_mdp:
            messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
            return redirect('changer_mot_de_passe')
        
        # Vérifier la longueur
        if len(nouveau_mdp) < 6:
            messages.error(request, 'Le mot de passe doit contenir au moins 6 caractères.')
            return redirect('changer_mot_de_passe')
        
        # Changer le mot de passe
        request.user.set_password(nouveau_mdp)
        request.user.save()
        
        # Réauthentifier l'utilisateur
        login(request, request.user)
        
        messages.success(request, 'Mot de passe changé avec succès.')
        return redirect('profil')
    
    return render(request, 'accounts/changer_mot_de_passe.html')