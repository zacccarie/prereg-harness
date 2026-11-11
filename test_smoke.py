#!/usr/bin/env python3
"""Smoke test : déroule le cycle complet + vérifie les gardes de la machine à états.

Isolé via PREREG_HOME (répertoire temporaire) pour ne rien écrire dans le repo.
Lance : python3 test_smoke.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREREG = HERE / "prereg.py"

FILLED = """# Carte de préenregistrement — happy

## Hypothèse (1 phrase)
La fenêtre de gain s'effondre sur une cloche commune en π_match.

## Ce qui confirme
Spread des positions de pic ≤ 0.05 sur 3 échelles.

## Ce qui tue (seuils chiffrés)
Spread > 0.10 ou pente ≤ 0 sur 3 échelles ; p > 0.05.

## Pourquoi c'est intéressant
Rend ρ(X,M) adimensionné et pré-mesurable avant tout entraînement.

## Application concrète si vrai
Prédire la fenêtre de gain sans lancer la grille complète.

## Définitions gelées
π_match = log10(τ_X/τ_M) ; κ = I/H ; fenêtre = pic ± 1 décade.

## Échelles (règle de la pente : lister ≥3 échelles)
- n = 80
- n = 320
- n = 640
"""


def run(home, *args, expect=0):
    env = dict(os.environ, PREREG_HOME=str(home))
    r = subprocess.run(
        [sys.executable, str(PREREG), *args],
        capture_output=True, text=True, env=env,
    )
    assert r.returncode == expect, (
        f"`prereg {' '.join(args)}` code={r.returncode} attendu={expect}\n"
        f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    )
    return r


def fill(home, slug, content):
    (Path(home) / "cards" / f"{slug}.md").write_text(content, encoding="utf-8")


def state_of(home, slug):
    s = json.loads((Path(home) / ".prereg" / "state.json").read_text(encoding="utf-8"))
    return s["cards"][slug]["state"]


def main():
    with tempfile.TemporaryDirectory() as home:
        # 1. Cycle complet draft → frozen → gated → running → logged
        run(home, "new", "happy")
        assert state_of(home, "happy") == "draft"
        fill(home, "happy", FILLED)
        run(home, "freeze", "happy")
        assert state_of(home, "happy") == "frozen"
        run(home, "verify", "happy")
        run(home, "gate", "happy", "--result", "pass", "--note", "témoin positif vu")
        assert state_of(home, "happy") == "gated"
        run(home, "run", "happy")
        assert state_of(home, "happy") == "running"
        r = run(home, "log", "happy",
                "--outcome", "solide", "--x", "RFF", "--m", "ridge",
                "--regime", "n=80..640", "--metrique", "κ=I/H",
                "--verdict", "collapse π*≈0", "--pi", "-0.026")
        assert state_of(home, "happy") == "logged"
        # le tuple a bien été écrit
        atlas = json.loads((Path(home) / "atlas.json").read_text(encoding="utf-8"))
        assert len(atlas) == 1, atlas
        t = atlas[0]
        for k in ("id", "p", "x", "m", "r", "o", "v", "k", "s", "frozenHash", "date"):
            assert k in t, f"clé manquante dans le tuple : {k}"
        assert t["x"] == "RFF" and t["o"] == "solide" and t["s"] == "happy"
        assert t["p"] == "-0.026" and t["k"] == "κ=I/H"
        print("OK  cycle complet + tuple écrit (toutes les clés présentes)")

        # 2. freeze refusé si champs vides (carte fraîche non remplie)
        run(home, "new", "empty")
        r = run(home, "freeze", "empty", expect=1)
        assert "freeze refusé" in r.stderr, r.stderr
        print("OK  freeze refusé sur carte non remplie")

        # 3. run AVANT gate → bloqué (contrôle positif requis)
        run(home, "new", "nogate")
        fill(home, "nogate", FILLED)
        run(home, "freeze", "nogate")
        r = run(home, "run", "nogate", expect=1)
        assert "contrôle positif requis" in r.stderr, r.stderr
        print("OK  run bloqué sans gate (contrôle positif requis)")

        # 4. gate fail → stopped, et run reste bloqué
        run(home, "new", "gatefail")
        fill(home, "gatefail", FILLED)
        run(home, "freeze", "gatefail")
        run(home, "gate", "gatefail", "--result", "fail", "--note", "rien sur le témoin")
        assert state_of(home, "gatefail") == "stopped"
        r = run(home, "run", "gatefail", expect=1)
        assert "ÉCHEC" in r.stderr or "bloquée" in r.stderr, r.stderr
        print("OK  gate fail → stopped, run bloqué")

        # 5. tamper détecté : on modifie la carte gelée
        run(home, "new", "tamper")
        fill(home, "tamper", FILLED)
        run(home, "freeze", "tamper")
        run(home, "verify", "tamper")  # encore intacte
        fill(home, "tamper", FILLED + "\n<!-- ligne ajoutée après gel -->\n")
        r = run(home, "verify", "tamper", expect=1)
        assert "TAMPERED" in r.stderr, r.stderr
        print("OK  tamper détecté (verify exit 1)")

        # 6. gate impossible sur draft (pédagogie de la machine à états)
        run(home, "new", "draftgate")
        r = run(home, "gate", "draftgate", "--result", "pass", expect=1)
        assert "GELÉE" in r.stderr or "draft" in r.stderr, r.stderr
        print("OK  gate refusé sur draft")

        # 7. status liste toutes les cartes
        r = run(home, "status")
        slugs = ("happy", "empty", "nogate", "gatefail", "tamper", "draftgate")
        for slug in slugs:
            assert slug in r.stdout, r.stdout
        print(f"OK  status liste les {len(slugs)} cartes")

        # 8. fichier de carte supprimé → erreur propre, pas de traceback
        os.remove(os.path.join(home, "cards", "tamper.md"))
        r = run(home, "verify", "tamper", expect=1)
        assert "disparu" in r.stderr and "Traceback" not in r.stderr, r.stderr
        print("OK  fichier disparu → erreur propre (pas de traceback)")

    print("\nALL GREEN — machine à états + intégrité + atlas vérifiés")


if __name__ == "__main__":
    main()
