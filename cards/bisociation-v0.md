# Carte de préenregistrement — bisociation-v0

_État : draft. Dispositif complet dans `claude-code-projects/bisociation/CADRAGE.md` §4. À geler par Zac après relecture, une fois le corpus et les 90 problèmes hashés._

## Hypothèse (1 phrase)
À budget de tokens égal, l'opérateur de bisociation (abstraction du problème en schéma relationnel, récupération du schéma hors domaine à distance d, transposition, critique) résout davantage de problèmes de transfert inter-domaines que le best-of-N, le RAG plus-proches-voisins, le RAG aléatoire et le branchement sans corpus, et ce gain n'existe pas sur les problèmes intra-domaine.

## Ce qui confirme
Porte franchie (C4-oracle ≥ C0 + 25 pts sur T-trans), puis P1, P2 et P4 :
- P1 : schémas distincts C4 / C1 ≥ 1,3 à budget égal.
- P2 : réussite C4 ≥ max(C1, C2, C3, C5) + 10 pts sur T-trans.
- P4 : (C4 − C1) sur T-trans ≥ (C4 − C1) sur T-intra + 8 pts.
P3 (bande 10-50 % > bande 0-1 %) confirme la lecture « distance contrôlée » sans être requise.

## Ce qui tue (seuils chiffrés)
- Porte : C4-oracle < C0 + 25 pts sur T-trans → arrêt, aucune grille.
- P1 : rapport de schémas distincts C4 / C1 ≤ 1,1 aux trois budgets.
- P2 : écart C4 − max(autres) ≤ 3 pts, ou C3 (aléatoire) ≥ C4 → le mécanisme est la perturbation, pas le pont.
- P3 : réussite bande 0-1 % ≥ bande 10-50 %.
- P4 : gain intra ≥ gain trans.
- Pente : si C1 rattrape C4 à 16B, issue notée « niche » (raccourci de calcul), pas « solide ».
- Accord juge-humain < 0,8 sur l'audit de 20 % → interprétation suspendue.

## Pourquoi c'est intéressant
Tranche entre deux thèses : l'association à distance structurée élargit l'espace d'options d'un LLM, ou tout gain apparent n'est que du calcul ou de la perturbation déguisés. C3 (documents aléatoires) et C1 (best-of-N à budget égal) sont là pour tuer les deux explications triviales.

## Application concrète si vrai
Un opérateur « bisocier » branché dans les workflows d'agents de ce poste (idéation, débogage en impasse), déclenché par le méta-contrôleur de blocage en V1 ; ouverture du niveau B (cross-attention par bande de distance) seulement après.

## Définitions gelées
- T-trans : 60 problèmes, solution = mécanisme d'un document du corpus d'un autre domaine ; recouvrement de lemmes problème/source < 10 % ; classiques publiés exclus.
- T-intra : 30 problèmes, solution dans le domaine du problème.
- Filtre de plafond : problème retiré si C0 le résout > 40 % sur 20 tirages.
- Corpus : ~2 000 résumés Wikipédia de mécanismes, ≥ 12 domaines, liste hashée avant gel.
- Budget B : tokens totaux par problème de C0 ; toutes les conditions ramenées à B, 4B, 16B.
- Conditions : C0 un tirage T=0,7 ; C1 best-of-N + même critique ; C2 RAG kNN sur texte du problème ; C3 RAG aléatoire ; C4 bisociation ; C5 branchement cadres hétérogènes sans corpus ; C4-oracle source exacte fournie.
- Distance : rang cosinus schéma ↔ document dans l'embedding fixé avant gel, en quantiles.
- Réussite : solution retenue instancie le mécanisme cible, juge d'une autre famille que le générateur, grille écrite avant gel, audit humain 20 %.
- Schémas distincts : étiquettes de mécanisme par le juge sur 20 tirages.
- Pont énonçable : la réponse nomme la relation commune source/cible, mesuré avant et après la critique.

## Échelles (règle de la pente : lister ≥3 échelles)
- Distance : bandes de quantiles 0-1 %, 1-10 %, 10-50 %, 50-90 %.
- Budget : B, 4B, 16B.
- Graines d'échantillonnage : 5 par cellule.
