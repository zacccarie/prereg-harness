# Carte de préenregistrement — nca-aligned-perturbation

_Projet : `claude-code-projects/nca-stability`. Gelée par Claude le 23/10/2026 à la demande de Zac (« lance le test décisif, carte prereg d'abord »), avant tout calcul de ce test._

## Hypothèse (1 phrase)
L'offset mesuré entre la croissance de perturbation et le certificat spectral (g_emp < log|λ1|, −0,021 en moyenne sur la trajectoire) vient de l'excitation non générique (mécanisme b) : une perturbation alignée sur le vecteur de Ritz dominant croît à log|λ1| dans le rollout stochastique réel, l'écart aléatoire − aligné s'éteint en 1/T, et ni la contraction non linéaire (a) ni le masque stochastique (c) ne sont nécessaires pour l'expliquer.

## Ce qui confirme
Porte franchie (voir Définitions), puis, sur le rollout STO à eps = 1e-3 :
- C1 : |médiane Δ_al| ≤ 0,005 à T = 45 et à T = 135.
- C2 : gain d'alignement G = g_al − g_rand ≥ +0,010 à T = 45, IC95 bootstrap sur les modèles strictement > 0.
- C3 : part expliquée f = G / (−Δ_rand) ≥ 0,7 à T = 45.
- C4 (pente) : pente de log G contre log T sur T ∈ {15, 45, 135} dans [−1,3 ; −0,7] (écart en 1/T, signature d'un défaut de projection initial et non d'un taux).
Lecture si C1-C4 tiennent : « |λ1| prédit la croissance dans la direction critique ; une perturbation générique la sous-estime d'un terme log|c1|/T ».

## Ce qui tue (seuils chiffrés)
- Porte G1 (instrument) : |médiane Δ_al,DET| > 0,005 à T = 45 et eps = 1e-3, ou résidu de Ritz médian > 0,10 → arrêt, l'instrument est faux, aucune grille.
- Porte G2 (phénomène) : médiane Δ_rand,STO > −0,010 à T = 45 et eps = 1e-2 → l'offset n'existe pas à ce budget, rien à expliquer, arrêt.
- K1 (b mort) : G(T = 45, eps = 1e-3) médian < +0,003 ou IC95 contenant 0 → l'alignement ne change rien, l'offset n'est pas un défaut de projection.
- K2 (mécanisme c, masque stochastique) : porte G1 passée mais médiane Δ_al,STO ≤ −0,010 à T = 45 et eps = 1e-3 → le jacobien de la carte moyenne ne gouverne pas le produit de jacobiens aléatoires ; le certificat doit être l'exposant de Lyapunov du produit stochastique, pas |λ1|.
- K3 (mécanisme a, non linéaire) : Δ_al,STO(eps = 1e-1) ≤ Δ_al,STO(eps = 1e-3) − 0,010 à T = 45 → la contraction non linéaire contribue hors du régime linéaire (n'invalide pas b en régime linéaire, borne sa portée).
- Mixte : 0,3 < f < 0,7 → issue « niche », b partiel ; f ≤ 0,3 → b mineur, issue « réfuté » pour b.
- Pente : pente de log G hors de [−1,3 ; −0,7] alors que C2 tient → G n'est pas un terme de projection ; issue « ouvert ».
- Moins de 6 modèles valides → aucun claim, issue « null ».

## Pourquoi c'est intéressant
Tranche entre trois lectures du même offset. Si b, le spectre intrinsèque prédit la croissance absolue dans la bonne direction et seule l'excitation est relationnelle : contre-exemple partiel et bien délimité à la loi « l'intrinsèque ne prédit pas le relationnel ». Si c, le bon certificat dépend du bruit de mise à jour du substrat, ce qui répond à la question ouverte du projet (bassin intrinsèque à la règle ou relationnel au bruit). Si a, la portée du certificat s'arrête au régime linéaire. Les trois issues produisent un énoncé publiable.

## Application concrète si vrai
Une fonction déployable checkpoint → (|λ1|, v1, croissance pire cas) : test de stress d'un NCA en quelques secondes par injection le long de v1 au lieu de longs rollouts censurés, et un dommage adversarial dirigé (v1) pour l'entraînement à la régénération à la place du dommage aléatoire.

## Définitions gelées
- Modèles : `GrowingNca` (16 canaux, 128 cachés, updateRate 0,5, gain 1), cibles {disk, ring, cross, square, blob} × graines {0, 1}, taille 28, `trainNca` par défaut à 1 200 itérations, MPS. Valide si fraction vivante > 0,05 et perte finale < 0,05 ; les invalides sont loggés et exclus.
- État d'ancrage x* : graine poussée 96 pas stochastiques puis 64 pas de la carte déterministe (espérance du masque). Résidu de point fixe r_fp = RMS(F_det(x*) − x*) / RMS(x*) relevé, non filtrant.
- Spectre : Arnoldi matrix-free (jvp) sur F_det en x*, 48 modes. λ1 = valeur de Ritz de module maximal, v1 = vecteur de Ritz associé (partie réelle si complexe). Résidu de Ritz = ‖J v1 − λ1 v1‖ / ‖v1‖ sur le vecteur complexe. ℓ = log|λ1|.
- Perturbations : δ0 = eps · σ(x*) · u, u de RMS 1 sur les 16 canaux ; u_al = ±v1 normalisé (signe alterné entre sondes), u_rand = gaussienne normalisée. 8 sondes par (modèle, condition, eps).
- Rollouts : DET = carte déterministe ; STO = masques stochastiques partagés entre copie de base et copie perturbée (CRN), et la même séquence de masques sert à la sonde alignée et à la sonde aléatoire de même indice (appariement).
- Croissance : d_t = RMS(xp − xb) sur tous les canaux ; g(T) = log(d_T / d_0) / T, lu à T ∈ {15, 45, 135} sur un même rollout de 135 pas. Sonde non finie = exclue et comptée.
- Écarts : Δ = g − ℓ ; G = g_al − g_rand ; f = G / (−Δ_rand).
- Agrégation : médiane sur les 8 sondes par modèle, puis médiane sur les modèles valides ; IC95 par bootstrap des modèles (2 000 rééchantillonnages, graine 0).

## Échelles (règle de la pente : lister ≥3 échelles)
- Horizon T : 15, 45, 135 pas (log-espacés ×3).
- Amplitude eps : 1e-3, 1e-2, 1e-1 (linéaire → non linéaire).
- Modèles : 5 cibles × 2 graines = 10 NCA entraînés.
