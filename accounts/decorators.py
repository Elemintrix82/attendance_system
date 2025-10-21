from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_ou_scolarite_required(view_func):
    """
    Décorateur pour restreindre l'accès aux admins et scolarité uniquement
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profil'):
            messages.error(request, 'Vous n\'avez pas les permissions nécessaires.')
            return redirect('dashboard')
        
        if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
            messages.error(request, 'Accès refusé. Cette page est réservée aux administrateurs et à la scolarité.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def enseignant_required(view_func):
    """
    Décorateur pour restreindre l'accès aux enseignants uniquement
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profil'):
            messages.error(request, 'Vous n\'avez pas les permissions nécessaires.')
            return redirect('dashboard')
        
        if not request.user.profil.est_enseignant():
            messages.error(request, 'Accès refusé. Cette page est réservée aux enseignants.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def enseignant_owns_cours(view_func):
    """
    Décorateur pour vérifier qu'un enseignant accède uniquement à SES cours
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Si admin ou scolarité, accès total
        if request.user.profil.est_admin() or request.user.profil.est_scolarite():
            return view_func(request, *args, **kwargs)
        
        # Si enseignant, vérifier qu'il accède à SON cours
        if request.user.profil.est_enseignant():
            if hasattr(request.user, 'enseignant'):
                # Récupérer l'ID du cours depuis les kwargs
                code_cours = kwargs.get('code_cours') or kwargs.get('code')
                seance_id = kwargs.get('seance_id')
                
                if code_cours:
                    from courses.models import Cours
                    try:
                        cours = Cours.objects.get(code=code_cours)
                        if cours.enseignant != request.user.enseignant:
                            messages.error(request, 'Vous n\'avez pas accès à ce cours.')
                            return redirect('dashboard')
                    except Cours.DoesNotExist:
                        pass
                
                if seance_id:
                    from courses.models import SeanceCours
                    try:
                        seance = SeanceCours.objects.get(id=seance_id)
                        if seance.cours.enseignant != request.user.enseignant:
                            messages.error(request, 'Vous n\'avez pas accès à cette séance.')
                            return redirect('dashboard')
                    except SeanceCours.DoesNotExist:
                        pass
        
        return view_func(request, *args, **kwargs)
    return wrapper