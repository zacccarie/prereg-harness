# prereg-harness

Le process de recherche préenregistré de Zac, packagé en CLI (Python 3, stdlib uniquement). Une machine à états force l'ordre `draft → frozen → gated(pass) → running → logged` ; sauter une étape échoue avec un message qui explique *pourquoi*.

## Philosophie — pourquoi chaque gate existe

1. **`freeze` (hypothèse gelée avant calcul)** — sceller les 5 champs + définitions + seuils chiffrés AVANT de calculer empêche d'inventer le critère de victoire après avoir vu la courbe. Les seuils gelés ont tué une fausse histoire EMC à 3 graines.
2. **`verify` (sha256)** — re-hashe la carte ; toute édition post-gel ressort en `TAMPERED`. L'intégrité est mécanique, pas une promesse.
3. **`gate` (contrôle positif obligatoire)** — interdit la grille tant que l'effet n'est pas visible sur un cas témoin où il DOIT apparaître. Le contrôle positif a évité 8 min de grille aveugle sur CKA (l'effet était sous le bruit de graine, gain ×1.07).
4. **`run` puis `log`** — la grille n'est autorisée que sur `gate=pass`, et chaque résultat part dans `atlas.json` sous forme de tuple `(X × M × régime → outcome)`, compatible avec le rho-atlas. Le cimetière de falsifications est la donnée.

## Usage

```bash
python3 prereg.py new <slug>                # crée cards/<slug>.md (état draft)
# remplir les 5 champs + Définitions gelées + ≥3 Échelles (règle de la pente)
python3 prereg.py freeze <slug>             # sha256 + timestamp UTC ; refuse si incomplet
python3 prereg.py verify <slug>             # TAMPERED (exit 1) si la carte a bougé
python3 prereg.py gate <slug> --result pass|fail --note '...'   # contrôle positif
python3 prereg.py run <slug>                # autorise la grille (si gate=pass)
python3 prereg.py log <slug> --outcome solide|niche|réfuté|artefact|null|ouvert \
    --x '...' --m '...' --regime '...' --metrique '...' --verdict '...' [--pi <val>]
python3 prereg.py status                    # tableau des cartes + états + dates
```

## Fichiers produits

- `cards/<slug>.md` — la carte préenregistrée (template à 5 champs).
- `.prereg/state.json` — états et hashes de gel.
- `atlas.json` — tuples loggés `{id, p, x, m, r, o, v, k, s, frozenHash, date}`.

Racine surchargeable via la variable d'environnement `PREREG_HOME`.

## Test

```bash
python3 test_smoke.py    # déroule le cycle + vérifie tamper / gate-fail / log
```
