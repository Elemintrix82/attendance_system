from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.http import HttpResponse
from datetime import datetime, timedelta
from students.models import Etudiant, Filiere  # ✅ Suppression de Niveau
from courses.models import Cours, SeanceCours
from attendance.models import Presence
from .models import RapportPresence


@login_required
def statistiques_globales(request):
    """Statistiques globales de présence"""
    
    # Statistiques générales
    total_etudiants = Etudiant.objects.filter(actif=True).count()
    total_cours = Cours.objects.filter(actif=True).count()
    total_seances = SeanceCours.objects.filter(presente=True).count()
    total_presences = Presence.objects.count()
    
    # Taux de présence global
    if total_presences > 0:
        presents = Presence.objects.filter(statut__in=['P', 'R', 'J']).count()
        taux_presence_global = round((presents / total_presences) * 100, 2)
    else:
        taux_presence_global = 0
    
    # Statistiques par filière (regroupées par spécialité + formation + niveau)
    stats_filieres = []
    for filiere in Filiere.objects.filter(actif=True):
        etudiants_filiere = Etudiant.objects.filter(filiere=filiere, actif=True)
        presences_filiere = Presence.objects.filter(etudiant__in=etudiants_filiere)
        
        total = presences_filiere.count()
        if total > 0:
            presents = presences_filiere.filter(statut__in=['P', 'R', 'J']).count()
            taux = round((presents / total) * 100, 2)
        else:
            taux = 0
        
        stats_filieres.append({
            'filiere': filiere,
            'nb_etudiants': etudiants_filiere.count(),
            'taux_presence': taux,
        })
    
    # ❌ SUPPRIMÉ : stats_niveaux (maintenant intégré dans stats_filieres)
    
    context = {
        'total_etudiants': total_etudiants,
        'total_cours': total_cours,
        'total_seances': total_seances,
        'total_presences': total_presences,
        'taux_presence_global': taux_presence_global,
        'stats_filieres': stats_filieres,
    }
    
    return render(request, 'statisticss/statistiques_globales.html', context)


@login_required
def statistiques_par_classe(request):
    """Statistiques de présence par classe (filière complète)"""
    
    filiere_id = request.GET.get('filiere')
    
    stats = []
    
    if filiere_id:
        # Filtrer par filière spécifique
        etudiants = Etudiant.objects.filter(
            filiere_id=filiere_id,
            actif=True
        )
        
        for etudiant in etudiants:
            presences = Presence.objects.filter(etudiant=etudiant)
            total = presences.count()
            
            if total > 0:
                presents = presences.filter(statut__in=['P', 'R', 'J']).count()
                absents = presences.filter(statut='A').count()
                retards = presences.filter(statut='R').count()
                taux = round((presents / total) * 100, 2)
            else:
                presents = absents = retards = 0
                taux = 0
            
            stats.append({
                'etudiant': etudiant,
                'total_seances': total,
                'presents': presents,
                'absents': absents,
                'retards': retards,
                'taux_presence': taux,
            })
    
    context = {
        'stats': stats,
        'filieres': Filiere.objects.filter(actif=True),
        'filiere_selectionnee': filiere_id,
    }
    
    return render(request, 'statisticss/statistiques_par_classe.html', context)


@login_required
def statistiques_par_etudiant(request, matricule):
    """Statistiques détaillées d'un étudiant"""
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    # Toutes les présences de l'étudiant
    presences = Presence.objects.filter(etudiant=etudiant).select_related('seance__cours')
    
    total_seances = presences.count()
    presents = presences.filter(statut__in=['P', 'R', 'J']).count()
    absents = presences.filter(statut='A').count()
    retards = presences.filter(statut='R').count()
    justifies = presences.filter(statut='J').count()
    
    taux_presence = etudiant.get_taux_presence()
    
    # Statistiques par cours
    stats_par_cours = []
    cours_suivis = Cours.objects.filter(
        filiere=etudiant.filiere,
        actif=True
    )
    
    for cours in cours_suivis:
        presences_cours = presences.filter(seance__cours=cours)
        total = presences_cours.count()
        
        if total > 0:
            presents_cours = presences_cours.filter(statut__in=['P', 'R', 'J']).count()
            taux_cours = round((presents_cours / total) * 100, 2)
        else:
            presents_cours = 0
            taux_cours = 0
        
        stats_par_cours.append({
            'cours': cours,
            'total': total,
            'presents': presents_cours,
            'taux': taux_cours,
        })
    
    # Évolution sur les 30 derniers jours
    date_debut = datetime.now().date() - timedelta(days=30)
    presences_recentes = presences.filter(seance__date__gte=date_debut).order_by('seance__date')
    
    context = {
        'etudiant': etudiant,
        'total_seances': total_seances,
        'presents': presents,
        'absents': absents,
        'retards': retards,
        'justifies': justifies,
        'taux_presence': taux_presence,
        'stats_par_cours': stats_par_cours,
        'presences_recentes': presences_recentes,
    }
    
    return render(request, 'statisticss/statistiques_par_etudiant.html', context)


@login_required
def statistiques_par_cours(request, code_cours):
    """Statistiques de présence pour un cours"""
    cours = get_object_or_404(Cours, code=code_cours)
    
    # Toutes les séances du cours
    seances = SeanceCours.objects.filter(cours=cours, presente=True).order_by('-date')
    
    # Statistiques globales du cours
    total_seances = seances.count()
    
    stats_seances = []
    for seance in seances:
        presences = Presence.objects.filter(seance=seance)
        total = presences.count()
        
        if total > 0:
            presents = presences.filter(statut__in=['P', 'R', 'J']).count()
            taux = round((presents / total) * 100, 2)
        else:
            presents = 0
            taux = 0
        
        stats_seances.append({
            'seance': seance,
            'total': total,
            'presents': presents,
            'taux': taux,
        })
    
    # Taux de présence moyen pour ce cours
    if stats_seances:
        taux_moyen = sum(s['taux'] for s in stats_seances) / len(stats_seances)
        taux_moyen = round(taux_moyen, 2)
    else:
        taux_moyen = 0
    
    context = {
        'cours': cours,
        'total_seances': total_seances,
        'stats_seances': stats_seances,
        'taux_moyen': taux_moyen,
    }
    
    return render(request, 'statisticss/statistiques_par_cours.html', context)


@login_required
def generer_rapport(request):
    """Générer un rapport de présence"""
    
    if request.method == 'POST':
        type_rapport = request.POST.get('type_rapport')
        format_fichier = request.POST.get('format_fichier', 'PDF')
        
        # Créer le rapport (pour l'instant, juste l'enregistrer)
        rapport = RapportPresence.objects.create(
            titre=f"Rapport {type_rapport} - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            type_rapport=type_rapport,
            format_fichier=format_fichier,
            genere_par=request.user,
        )
        
        # Appliquer les filtres selon le type
        if type_rapport == 'ETUDIANT':
            matricule = request.POST.get('etudiant_matricule')
            if matricule:
                rapport.etudiant = Etudiant.objects.get(matricule=matricule)
        
        elif type_rapport == 'COURS':
            code_cours = request.POST.get('cours_code')
            if code_cours:
                rapport.cours = Cours.objects.get(code=code_cours)
        
        elif type_rapport == 'FILIERE':
            filiere_id = request.POST.get('filiere')
            if filiere_id:
                rapport.filiere = Filiere.objects.get(id=filiere_id)
        
        # ❌ SUPPRIMÉ : type_rapport == 'NIVEAU'
        
        # Dates
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        
        if date_debut:
            rapport.date_debut = date_debut
        if date_fin:
            rapport.date_fin = date_fin
        
        rapport.save()
        
        messages.success(request, 'Rapport généré avec succès.')
        return redirect('liste_rapports')
    
    context = {
        'types_rapport': RapportPresence.TYPE_RAPPORT,
        'formats': RapportPresence.FORMAT_RAPPORT,
        'etudiants': Etudiant.objects.filter(actif=True),
        'cours': Cours.objects.filter(actif=True),
        'filieres': Filiere.objects.filter(actif=True),
    }
    
    return render(request, 'statisticss/generer_rapport.html', context)


@login_required
def liste_rapports(request):
    """Liste des rapports générés"""
    rapports = RapportPresence.objects.all().order_by('-date_generation')
    
    context = {
        'rapports': rapports,
    }
    
    return render(request, 'statisticss/liste_rapports.html', context)