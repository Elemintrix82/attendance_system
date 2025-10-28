from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from .models import Etudiant, Filiere, HoraireSupplementaire
from attendance.models import Presence
from django.http import JsonResponse
from django.db import transaction

from datetime import datetime, timedelta
import json


# ============================================
# GESTION DES ÉTUDIANTS
# ============================================

@login_required
def liste_etudiants(request):
    """Liste de tous les étudiants avec recherche et filtres"""
    etudiants = Etudiant.objects.filter(actif=True).select_related('filiere')
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        etudiants = etudiants.filter(
            Q(matricule__icontains=search_query) |
            Q(matricule_departement__icontains=search_query) |
            Q(nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filtres
    filiere_id = request.GET.get('filiere')
    if filiere_id:
        etudiants = etudiants.filter(filiere_id=filiere_id)
    
    specialite = request.GET.get('specialite')
    if specialite:
        etudiants = etudiants.filter(filiere__specialite=specialite)
    
    formation = request.GET.get('formation')
    if formation:
        etudiants = etudiants.filter(filiere__formation=formation)
    
    niveau = request.GET.get('niveau')
    if niveau:
        etudiants = etudiants.filter(filiere__niveau=niveau)
    
    # Pagination
    paginator = Paginator(etudiants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filieres': Filiere.objects.filter(actif=True).order_by('specialite', 'formation', 'niveau'),
        'specialites': Filiere.SPECIALITES,
        'formations': Filiere.FORMATIONS,
        'niveaux': Filiere.NIVEAUX,
        'search_query': search_query,
        'total_etudiants': etudiants.count(),
    }
    
    return render(request, 'students/liste_etudiants.html', context)


@login_required
def detail_etudiant(request, matricule):
    """Détail d'un étudiant avec statistiques complètes et graphiques"""
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    # Récupérer toutes les présences de l'étudiant
    presences = Presence.objects.filter(etudiant=etudiant).select_related('seance__cours')
    
    # === STATISTIQUES GLOBALES ===
    total_seances = presences.count()
    presents = presences.filter(statut__in=['P', 'R']).count()
    absents = presences.filter(statut='A').count()
    retards = presences.filter(statut='R').count()
    justifies = presences.filter(statut='J').count()
    
    taux_presence = round((presents / total_seances * 100), 2) if total_seances > 0 else 0
    
    # === STATISTIQUES PAR COURS ===
    stats_par_cours = []
    cours_labels = []
    cours_presents = []
    cours_absents = []
    cours_colors = []
    
    presences_par_cours = presences.values('seance__cours__code', 'seance__cours__intitule').annotate(
        total=Count('id'),
        presents=Count('id', filter=Q(statut__in=['P', 'R'])),
        absents=Count('id', filter=Q(statut='A')),
        retards=Count('id', filter=Q(statut='R'))
    ).order_by('-total')
    
    for cours_stat in presences_par_cours:
        code = cours_stat['seance__cours__code']
        intitule = cours_stat['seance__cours__intitule']
        total = cours_stat['total']
        presents_count = cours_stat['presents']
        absents_count = cours_stat['absents']
        retards_count = cours_stat['retards']
        taux = round((presents_count / total * 100), 2) if total > 0 else 0
        
        # Code couleur selon le taux
        if taux >= 90:
            color = '#28a745'  # Vert
            badge_class = 'success'
        elif taux >= 70:
            color = '#ffc107'  # Jaune/Orange
            badge_class = 'warning'
        else:
            color = '#dc3545'  # Rouge
            badge_class = 'danger'
        
        stats_par_cours.append({
            'code': code,
            'intitule': intitule[:30] + '...' if len(intitule) > 30 else intitule,
            'total': total,
            'presents': presents_count,
            'absents': absents_count,
            'retards': retards_count,
            'taux': taux,
            'badge_class': badge_class,
            'color': color
        })
        
        cours_labels.append(f"{code}")
        cours_presents.append(presents_count)
        cours_absents.append(absents_count)
        cours_colors.append(color)
    
    # === STATISTIQUES PAR MOIS (6 derniers mois) ===
    mois_labels = []
    mois_taux = []
    mois_colors = []
    
    for i in range(5, -1, -1):
        date_debut = datetime.now() - timedelta(days=30*i)
        date_fin = datetime.now() - timedelta(days=30*(i-1)) if i > 0 else datetime.now()
        
        presences_mois = presences.filter(
            seance__date__gte=date_debut.date(),
            seance__date__lte=date_fin.date()
        )
        
        total_mois = presences_mois.count()
        presents_mois = presences_mois.filter(statut__in=['P', 'R']).count()
        taux_mois = round((presents_mois / total_mois * 100), 2) if total_mois > 0 else 0
        
        # Code couleur
        if taux_mois >= 90:
            color = 'rgba(40, 167, 69, 0.8)'  # Vert
        elif taux_mois >= 70:
            color = 'rgba(255, 193, 7, 0.8)'  # Jaune
        else:
            color = 'rgba(220, 53, 69, 0.8)'  # Rouge
        
        mois_labels.append(date_debut.strftime('%b %Y'))
        mois_taux.append(taux_mois)
        mois_colors.append(color)
    
    # === STATISTIQUES PAR SEMAINE (8 dernières semaines) ===
    semaine_labels = []
    semaine_taux = []
    semaine_colors = []
    
    for i in range(7, -1, -1):
        date_debut = datetime.now() - timedelta(weeks=i)
        date_fin = datetime.now() - timedelta(weeks=i-1) if i > 0 else datetime.now()
        
        presences_semaine = presences.filter(
            seance__date__gte=date_debut.date(),
            seance__date__lte=date_fin.date()
        )
        
        total_semaine = presences_semaine.count()
        presents_semaine = presences_semaine.filter(statut__in=['P', 'R']).count()
        taux_semaine = round((presents_semaine / total_semaine * 100), 2) if total_semaine > 0 else 0
        
        # Code couleur
        if taux_semaine >= 90:
            color = 'rgba(40, 167, 69, 0.8)'
        elif taux_semaine >= 70:
            color = 'rgba(255, 193, 7, 0.8)'
        else:
            color = 'rgba(220, 53, 69, 0.8)'
        
        semaine_labels.append(f"S{date_debut.isocalendar()[1]}")
        semaine_taux.append(taux_semaine)
        semaine_colors.append(color)
    
    # === STATISTIQUES PAR SEMESTRE ===
    semestre_labels = []
    semestre_taux = []
    semestre_colors = []
    
    for semestre in range(1, 9):  # 8 semestres
        presences_semestre = presences.filter(seance__cours__semestre=semestre)
        total_sem = presences_semestre.count()
        presents_sem = presences_semestre.filter(statut__in=['P', 'R']).count()
        taux_sem = round((presents_sem / total_sem * 100), 2) if total_sem > 0 else 0
        
        if total_sem > 0:  # Seulement si l'étudiant a des cours ce semestre
            # Code couleur
            if taux_sem >= 90:
                color = 'rgba(40, 167, 69, 0.8)'
            elif taux_sem >= 70:
                color = 'rgba(255, 193, 7, 0.8)'
            else:
                color = 'rgba(220, 53, 69, 0.8)'
            
            semestre_labels.append(f"Semestre {semestre}")
            semestre_taux.append(taux_sem)
            semestre_colors.append(color)
    
    # === STATISTIQUES PAR ANNÉE ACADÉMIQUE ===
    annees = presences.values_list('seance__cours__annee_academique', flat=True).distinct().order_by('seance__cours__annee_academique')
    annee_labels = []
    annee_taux = []
    annee_colors = []
    
    for annee in annees:
        presences_annee = presences.filter(seance__cours__annee_academique=annee)
        total_annee = presences_annee.count()
        presents_annee = presences_annee.filter(statut__in=['P', 'R']).count()
        taux_annee = round((presents_annee / total_annee * 100), 2) if total_annee > 0 else 0
        
        # Code couleur
        if taux_annee >= 90:
            color = 'rgba(40, 167, 69, 0.8)'
        elif taux_annee >= 70:
            color = 'rgba(255, 193, 7, 0.8)'
        else:
            color = 'rgba(220, 53, 69, 0.8)'
        
        annee_labels.append(annee)
        annee_taux.append(taux_annee)
        annee_colors.append(color)
    
    # === FILTRES POUR L'HISTORIQUE ===
    presences_historique = presences.order_by('-seance__date')
    
    # Filtre par cours
    cours_filtre = request.GET.get('cours_filtre')
    if cours_filtre:
        presences_historique = presences_historique.filter(seance__cours__code=cours_filtre)
    
    # Filtre par type de séance
    type_filtre = request.GET.get('type_filtre')
    if type_filtre:
        presences_historique = presences_historique.filter(seance__type_seance=type_filtre)
    
    # Filtre par statut
    statut_filtre = request.GET.get('statut_filtre')
    if statut_filtre:
        presences_historique = presences_historique.filter(statut=statut_filtre)
    
    # Liste des cours pour le filtre
    cours_liste = presences.values_list('seance__cours__code', 'seance__cours__intitule').distinct().order_by('seance__cours__code')
    
    # Pagination pour l'historique
    paginator = Paginator(presences_historique, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'etudiant': etudiant,
        'total_seances': total_seances,
        'presents': presents,
        'absents': absents,
        'retards': retards,
        'justifies': justifies,
        'taux_presence': taux_presence,
        'stats_par_cours': stats_par_cours,
        'page_obj': page_obj,
        
        # Liste pour les filtres
        'cours_liste': cours_liste,
        'cours_filtre': cours_filtre,
        'type_filtre': type_filtre,
        'statut_filtre': statut_filtre,
        'types_seance': [
            ('CM', 'Cours Magistral'),
            ('TD', 'Travaux Dirigés'),
            ('TP', 'Travaux Pratiques'),
            ('EXAM', 'Examen'),
            ('CONTROLE', 'Contrôle Continu'),
        ],
        'statuts': [
            ('P', 'Présent'),
            ('A', 'Absent'),
            ('R', 'Retard'),
            ('J', 'Justifié'),
        ],
        
        # Données pour les graphiques (JSON pour Chart.js)
        'cours_labels_json': json.dumps(cours_labels),
        'cours_presents_json': json.dumps(cours_presents),
        'cours_absents_json': json.dumps(cours_absents),
        'cours_colors_json': json.dumps(cours_colors),
        
        'mois_labels_json': json.dumps(mois_labels),
        'mois_taux_json': json.dumps(mois_taux),
        'mois_colors_json': json.dumps(mois_colors),
        
        'semaine_labels_json': json.dumps(semaine_labels),
        'semaine_taux_json': json.dumps(semaine_taux),
        'semaine_colors_json': json.dumps(semaine_colors),
        
        'semestre_labels_json': json.dumps(semestre_labels),
        'semestre_taux_json': json.dumps(semestre_taux),
        'semestre_colors_json': json.dumps(semestre_colors),
        
        'annee_labels_json': json.dumps(annee_labels),
        'annee_taux_json': json.dumps(annee_taux),
        'annee_colors_json': json.dumps(annee_colors),
    }
    
    return render(request, 'students/detail_etudiant.html', context)


@login_required
def ajouter_etudiant(request):
    """Ajouter un nouvel étudiant"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_etudiants')
    
    if request.method == 'POST':
        try:
            etudiant = Etudiant.objects.create(
                matricule=request.POST.get('matricule'),
                nom=request.POST.get('nom'),
                prenom=request.POST.get('prenom'),
                email=request.POST.get('email'),
                telephone=request.POST.get('telephone'),
                filiere_id=request.POST.get('filiere'),
                sexe=request.POST.get('sexe'),
                date_naissance=request.POST.get('date_naissance') or None,
                lieu_naissance=request.POST.get('lieu_naissance'),
                adresse=request.POST.get('adresse'),
            )
            
            if 'photo' in request.FILES:
                etudiant.photo = request.FILES['photo']
                etudiant.save()
            
            messages.success(request, f'✅ Étudiant {etudiant.nom_complet()} ajouté avec succès.')
            return redirect('detail_etudiant', matricule=etudiant.matricule)
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de l\'ajout : {str(e)}')
    
    context = {
        'filieres': Filiere.objects.filter(actif=True).order_by('specialite', 'formation', 'niveau'),
    }
    
    return render(request, 'students/ajouter_etudiant.html', context)


@login_required
def modifier_etudiant(request, matricule):
    """Modifier un étudiant"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_etudiants')
    
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    if request.method == 'POST':
        try:
            etudiant.nom = request.POST.get('nom')
            etudiant.prenom = request.POST.get('prenom')
            etudiant.email = request.POST.get('email')
            etudiant.telephone = request.POST.get('telephone')
            etudiant.filiere_id = request.POST.get('filiere')
            etudiant.sexe = request.POST.get('sexe')
            etudiant.date_naissance = request.POST.get('date_naissance') or None
            etudiant.lieu_naissance = request.POST.get('lieu_naissance')
            etudiant.adresse = request.POST.get('adresse')
            
            if 'photo' in request.FILES:
                etudiant.photo = request.FILES['photo']
            
            etudiant.save()
            
            messages.success(request, f'✅ Étudiant {etudiant.nom_complet()} modifié avec succès.')
            return redirect('detail_etudiant', matricule=etudiant.matricule)
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de la modification : {str(e)}')
    
    context = {
        'etudiant': etudiant,
        'filieres': Filiere.objects.filter(actif=True).order_by('specialite', 'formation', 'niveau'),
    }
    
    return render(request, 'students/modifier_etudiant.html', context)


@login_required
def supprimer_etudiant(request, matricule):
    """Supprimer un étudiant"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_etudiants')
    
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    if request.method == 'POST':
        try:
            nom_complet = etudiant.nom_complet()
            etudiant.delete()
            
            messages.success(request, f'✅ L\'étudiant {nom_complet} a été supprimé avec succès.')
            return redirect('liste_etudiants')
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de la suppression : {str(e)}')
            return redirect('detail_etudiant', matricule=matricule)
    
    return redirect('detail_etudiant', matricule=matricule)


@login_required
def generer_matricule_etudiant(request, matricule):
    """Générer ou régénérer le matricule département pour un étudiant"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_etudiants')
    
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    if request.method == 'POST':
        try:
            # Générer le nouveau matricule
            nouveau_matricule = etudiant.generer_matricule_departement()
            
            # Vérifier qu'il est unique
            if Etudiant.objects.filter(matricule_departement=nouveau_matricule).exclude(id=etudiant.id).exists():
                messages.error(request, f'❌ Erreur : Le matricule {nouveau_matricule} existe déjà.')
                return redirect('detail_etudiant', matricule=matricule)
            
            # Sauvegarder
            ancien_matricule = etudiant.matricule_departement
            etudiant.matricule_departement = nouveau_matricule
            etudiant.save()
            
            if ancien_matricule:
                messages.success(request, f'✅ Matricule mis à jour : {ancien_matricule} → {nouveau_matricule}')
            else:
                messages.success(request, f'✅ Matricule généré : {nouveau_matricule}')
            
            return redirect('detail_etudiant', matricule=matricule)
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de la génération : {str(e)}')
            return redirect('detail_etudiant', matricule=matricule)
    
    return redirect('detail_etudiant', matricule=matricule)


@login_required
def generer_matricules_masse(request):
    """Générer les matricules département pour tous les étudiants qui n'en ont pas"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_etudiants')
    
    if request.method == 'POST':
        try:
            # Récupérer tous les étudiants sans matricule département
            etudiants_sans_matricule = Etudiant.objects.filter(
                matricule_departement__isnull=True
            ).select_related('filiere')
            
            count = etudiants_sans_matricule.count()
            
            if count == 0:
                messages.info(request, 'ℹ️ Tous les étudiants ont déjà un matricule département.')
                return redirect('liste_etudiants')
            
            # Générer les matricules
            succes = 0
            erreurs = 0
            
            with transaction.atomic():
                for etudiant in etudiants_sans_matricule:
                    try:
                        etudiant.matricule_departement = etudiant.generer_matricule_departement()
                        etudiant.save()
                        succes += 1
                    except Exception as e:
                        erreurs += 1
                        print(f"Erreur pour {etudiant.matricule}: {e}")
            
            if erreurs == 0:
                messages.success(request, f'✅ {succes} matricules générés avec succès.')
            else:
                messages.warning(request, f'⚠️ {succes} matricules générés, {erreurs} erreurs.')
            
            return redirect('liste_etudiants')
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de la génération en masse : {str(e)}')
            return redirect('liste_etudiants')
    
    # Afficher la page de confirmation
    etudiants_sans_matricule = Etudiant.objects.filter(
        matricule_departement__isnull=True
    ).select_related('filiere')
    
    context = {
        'etudiants_sans_matricule': etudiants_sans_matricule,
        'count': etudiants_sans_matricule.count(),
    }
    
    return render(request, 'students/generer_matricules_masse.html', context)


@login_required
def generer_matricule_ajax(request, matricule):
    """Générer le matricule via AJAX (pour bouton rapide)"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        return JsonResponse({'success': False, 'message': 'Accès refusé'}, status=403)
    
    etudiant = get_object_or_404(Etudiant, matricule=matricule)
    
    try:
        nouveau_matricule = etudiant.generer_matricule_departement()
        
        # Vérifier unicité
        if Etudiant.objects.filter(matricule_departement=nouveau_matricule).exclude(id=etudiant.id).exists():
            return JsonResponse({
                'success': False,
                'message': f'Le matricule {nouveau_matricule} existe déjà'
            }, status=400)
        
        ancien_matricule = etudiant.matricule_departement
        etudiant.matricule_departement = nouveau_matricule
        etudiant.save()
        
        return JsonResponse({
            'success': True,
            'matricule': nouveau_matricule,
            'ancien_matricule': ancien_matricule,
            'message': f'Matricule généré : {nouveau_matricule}'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ============================================
# GESTION DES FILIÈRES
# ============================================

@login_required
def liste_filieres(request):
    """Liste des filières avec filtres"""
    filieres = Filiere.objects.filter(actif=True).annotate(
        nb_etudiants=Count('etudiants', filter=Q(etudiants__actif=True))
    )
    
    # Filtres
    specialite = request.GET.get('specialite')
    if specialite:
        filieres = filieres.filter(specialite=specialite)
    
    formation = request.GET.get('formation')
    if formation:
        filieres = filieres.filter(formation=formation)
    
    niveau = request.GET.get('niveau')
    if niveau:
        filieres = filieres.filter(niveau=niveau)
    
    # Ordre
    filieres = filieres.order_by('specialite', 'formation', 'niveau')
    
    # Statistiques globales
    total_filieres = filieres.count()
    total_etudiants = sum(f.nb_etudiants for f in filieres)
    
    context = {
        'filieres': filieres,
        'specialites': Filiere.SPECIALITES,
        'formations': Filiere.FORMATIONS,
        'niveaux': Filiere.NIVEAUX,
        'total_filieres': total_filieres,
        'total_etudiants': total_etudiants,
    }
    
    return render(request, 'students/liste_filieres.html', context)


@login_required
def detail_filiere(request, code):
    """Détail d'une filière avec ses étudiants et horaires"""
    filiere = get_object_or_404(Filiere, code=code)
    
    # Étudiants de cette filière
    etudiants = Etudiant.objects.filter(filiere=filiere, actif=True)
    
    # Horaires supplémentaires
    horaires_supp = HoraireSupplementaire.objects.filter(
        filiere=filiere, actif=True
    ).select_related('salle')
    
    # Pagination
    paginator = Paginator(etudiants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'filiere': filiere,
        'page_obj': page_obj,
        'total_etudiants': etudiants.count(),
        'horaires_supp': horaires_supp,
    }
    
    return render(request, 'students/detail_filiere.html', context)


@login_required
def ajouter_filiere(request):
    """Ajouter une nouvelle filière"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_filieres')
    
    if request.method == 'POST':
        try:
            from courses.models import Salle
            
            filiere = Filiere.objects.create(
                specialite=request.POST.get('specialite'),
                formation=request.POST.get('formation'),
                niveau=request.POST.get('niveau'),
                jour_semaine=request.POST.get('jour_semaine') or None,
                heure_debut=request.POST.get('heure_debut') or None,
                heure_fin=request.POST.get('heure_fin') or None,
                salle_principale_id=request.POST.get('salle_principale') or None,
                description=request.POST.get('description'),
            )
            
            messages.success(request, f'✅ Filière {filiere.nom_complet()} ajoutée avec succès.')
            return redirect('detail_filiere', code=filiere.code)
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de l\'ajout : {str(e)}')
    
    from courses.models import Salle
    
    context = {
        'specialites': Filiere.SPECIALITES,
        'formations': Filiere.FORMATIONS,
        'niveaux': Filiere.NIVEAUX,
        'jours': Filiere.JOURS_SEMAINE,
        'salles': Salle.objects.filter(disponible=True),
    }
    
    return render(request, 'students/ajouter_filiere.html', context)


@login_required
def modifier_filiere(request, code):
    """Modifier une filière"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_filieres')
    
    filiere = get_object_or_404(Filiere, code=code)
    
    if request.method == 'POST':
        try:
            filiere.specialite = request.POST.get('specialite')
            filiere.formation = request.POST.get('formation')
            filiere.niveau = request.POST.get('niveau')
            filiere.jour_semaine = request.POST.get('jour_semaine') or None
            filiere.heure_debut = request.POST.get('heure_debut') or None
            filiere.heure_fin = request.POST.get('heure_fin') or None
            filiere.salle_principale_id = request.POST.get('salle_principale') or None
            filiere.description = request.POST.get('description')
            
            # Régénérer le code si les infos de base changent
            old_code = filiere.code
            filiere.code = filiere.nom_court()
            filiere.save()
            
            messages.success(request, f'✅ Filière {filiere.nom_complet()} modifiée avec succès.')
            return redirect('detail_filiere', code=filiere.code)
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de la modification : {str(e)}')
    
    from courses.models import Salle
    
    context = {
        'filiere': filiere,
        'specialites': Filiere.SPECIALITES,
        'formations': Filiere.FORMATIONS,
        'niveaux': Filiere.NIVEAUX,
        'jours': Filiere.JOURS_SEMAINE,
        'salles': Salle.objects.filter(disponible=True),
    }
    
    return render(request, 'students/modifier_filiere.html', context)


@login_required
def supprimer_filiere(request, code):
    """Supprimer une filière"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_filieres')
    
    filiere = get_object_or_404(Filiere, code=code)
    
    if request.method == 'POST':
        try:
            nom_filiere = filiere.nom_complet()
            filiere.delete()
            
            messages.success(request, f'✅ La filière {nom_filiere} a été supprimée avec succès.')
            return redirect('liste_filieres')
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de la suppression : {str(e)}')
            return redirect('detail_filiere', code=code)
    
    return redirect('detail_filiere', code=code)


# ============================================
# GESTION DES HORAIRES SUPPLÉMENTAIRES
# ============================================

@login_required
def ajouter_horaire_supplementaire(request, code):
    """Ajouter un horaire supplémentaire à une filière"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_filieres')
    
    filiere = get_object_or_404(Filiere, code=code)
    
    if request.method == 'POST':
        try:
            from courses.models import Salle
            
            horaire = HoraireSupplementaire.objects.create(
                filiere=filiere,
                jour_semaine=request.POST.get('jour_semaine'),
                heure_debut=request.POST.get('heure_debut'),
                heure_fin=request.POST.get('heure_fin'),
                salle_id=request.POST.get('salle') or None,
                remarque=request.POST.get('remarque'),
            )
            
            messages.success(request, f'✅ Horaire supplémentaire ajouté pour {filiere.nom_complet()}.')
            return redirect('detail_filiere', code=filiere.code)
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de l\'ajout : {str(e)}')
    
    from courses.models import Salle
    
    context = {
        'filiere': filiere,
        'jours': HoraireSupplementaire.JOURS_SEMAINE,
        'salles': Salle.objects.filter(disponible=True),
    }
    
    return render(request, 'students/ajouter_horaire_supplementaire.html', context)


@login_required
def supprimer_horaire_supplementaire(request, horaire_id):
    """Supprimer un horaire supplémentaire"""
    
    if not (request.user.profil.est_admin() or request.user.profil.est_scolarite()):
        messages.error(request, "⛔ Accès refusé.")
        return redirect('liste_filieres')
    
    horaire = get_object_or_404(HoraireSupplementaire, id=horaire_id)
    code_filiere = horaire.filiere.code
    
    if request.method == 'POST':
        try:
            horaire.delete()
            messages.success(request, f'✅ Horaire supplémentaire supprimé avec succès.')
            return redirect('detail_filiere', code=code_filiere)
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de la suppression : {str(e)}')
            return redirect('detail_filiere', code=code_filiere)
    
    return redirect('detail_filiere', code=code_filiere)

