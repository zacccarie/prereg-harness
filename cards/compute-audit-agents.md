# Carte de préenregistrement — compute-audit-agents

_État initial : draft. Geler (`prereg freeze compute-audit-agents`) une fois les 5 champs + définitions + ≥3 échelles remplis. Le gel fige l'hypothèse AVANT tout calcul._

_Brouillon rédigé par Claude le 2026-09-17. Zac doit le reformuler avec ses mots avant le gel (règle de la carte : s'il ne peut pas la reformuler, on ne lance pas)._

## Hypothèse (1 phrase)
Sur du trafic réel d'agents de code, une configuration choisie par rejeu (modèle × budget de raisonnement × contexte × escalade) coûte au moins 40 % de moins que la configuration de référence à qualité vérifiée égale, et cette économie tient quand l'échantillon grandit.

## Ce qui confirme
- Économie ≥ 40 % du coût effectif sur les 3 échelles d'échantillon, à taux de réussite des tests dans ±2 points de la référence.
- Intervalle bootstrap (1000 tirages) de l'économie de largeur < 15 points sur l'échelle la plus grande.
- Pente de l'économie ≥ 0 de l'échelle 1 à l'échelle 3 (l'effet ne fond pas quand on ajoute des tâches).

## Ce qui tue (seuils chiffrés)
- Économie < 40 % à qualité égale sur l'échelle la plus grande.
- Perte de qualité > 2 points de taux de réussite pour toute configuration retenue.
- Largeur d'intervalle bootstrap de l'économie > 15 points (l'effet est sous le bruit).
- Meilleure configuration = configuration de référence (rien à gagner).
- Pente de l'économie ≤ 0 sur les 3 échelles → archive sans nouvelle théorisation.

## Pourquoi c'est intéressant
Teste si la dépense d'agents est optimisable par MESURE sur trafic réel, pas par benchmark public. Décide entre produit, open source et abandon de l'idée « moteur de mesure coût-qualité » avant d'écrire le produit.

## Application concrète si vrai
Audit en mode ombre + simulateur par rejeu = levier commercial ; chiffre auditable pour un client pilote ; démo publique (engineering as marketing). Si faux : résultat négatif publiable sur l'optimisation d'agents de code.

## Définitions gelées
- Tâche = une session d'agent de code avec critère de réussite exécutable (suite de tests du dépôt ou test écrit avant la session). Sans critère exécutable, la tâche est exclue.
- Qualité = taux de tâches dont les tests passent. Vérificateur = exécution des tests, jamais un juge LLM.
- Coût effectif = tokens entrée / sortie / cache × tarifs API figés au 2026-09-17, plus temps de mur en annexe (non décisionnel).
- Configurations, fixées à 4 : (R) référence = configuration actuelle de Zac ; (A) petit modèle + escalade vers le gros sur échec des tests ; (B) budget de raisonnement réduit d'un cran ; (C) contexte élagué (pas de fichiers non touchés par la tâche).
- Rejeu = ré-exécution de chaque tâche dans chaque configuration, 3 répétitions par cellule pour estimer le bruit de génération.
- Économie = 1 − coût(config) / coût(R), calculée seulement sur les configurations à qualité dans ±2 points de R.
- Contrôle positif (gate obligatoire) : une configuration volontairement dégradée (modèle minuscule, contexte vide) doit faire chuter le taux de réussite d'au moins 20 points. Sinon le vérificateur est aveugle et la grille est interdite.
- Sources de trafic : sessions Claude Code de Zac + une équipe amie (à nommer avant le gel).

## Échelles (règle de la pente : lister ≥3 échelles)
- 30 tâches
- 100 tâches
- 300 tâches
Livrable = économie(échelle) avec intervalle, jamais un point.
