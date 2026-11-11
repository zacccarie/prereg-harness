#!/usr/bin/env python3
"""prereg-harness — process de recherche préenregistré en CLI (stdlib only).

Machine à états imposée : draft → frozen → gated(pass) → running → logged.
Toute tentative de saut d'étape échoue avec un message qui explique POURQUOI.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Racine surchargée par PREREG_HOME (utile pour les tests isolés)
ROOT = Path(os.environ.get("PREREG_HOME") or Path(__file__).resolve().parent)
CARDS_DIR = ROOT / "cards"
STATE_DIR = ROOT / ".prereg"
STATE_FILE = STATE_DIR / "state.json"
ATLAS_FILE = ROOT / "atlas.json"

PLACEHOLDER = "À REMPLIR"

# Sections requises (le titre réel peut être plus long ; on matche sur le préfixe)
REQUIRED_SECTIONS = [
    "Hypothèse (1 phrase)",
    "Ce qui confirme",
    "Ce qui tue (seuils chiffrés)",
    "Pourquoi c'est intéressant",
    "Application concrète si vrai",
    "Définitions gelées",
    "Échelles",
]

OUTCOMES = ["solide", "niche", "réfuté", "artefact", "null", "ouvert"]

TEMPLATE = """# Carte de préenregistrement — {slug}

_État initial : draft. Geler (`prereg freeze {slug}`) une fois les 5 champs + définitions + ≥3 échelles remplis. Le gel fige l'hypothèse AVANT tout calcul._

## Hypothèse (1 phrase)
{ph}

## Ce qui confirme
{ph}

## Ce qui tue (seuils chiffrés)
{ph} — donner les nombres (ex : spread > 0.10, pente ≤ 0 sur 3 échelles, p > 0.05)

## Pourquoi c'est intéressant
{ph}

## Application concrète si vrai
{ph}

## Définitions gelées
{ph} — variables, métriques, fenêtres, figées AVANT tout calcul

## Échelles (règle de la pente : lister ≥3 échelles)
- {ph} (échelle 1)
- {ph} (échelle 2)
- {ph} (échelle 3)
"""


def fail(msg, code=1):
    print(f"erreur : {msg}", file=sys.stderr)
    sys.exit(code)


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def card_path(slug):
    return CARDS_DIR / f"{slug}.md"


def card_hash(slug):
    path = card_path(slug)
    if not path.exists():
        sys.exit(f"erreur : la carte '{slug}' est dans l'état mais son fichier a disparu ({path}) — désync état/disque")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"cards": {}}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_atlas():
    if ATLAS_FILE.exists():
        return json.loads(ATLAS_FILE.read_text(encoding="utf-8"))
    return []


def save_atlas(atlas):
    ATLAS_FILE.write_text(json.dumps(atlas, ensure_ascii=False, indent=2), encoding="utf-8")


def require_card(state, slug):
    card = state.get("cards", {}).get(slug)
    if card is None:
        fail(f"carte '{slug}' inconnue. Crée-la d'abord : prereg new {slug}")
    return card


def parse_sections(text):
    """Découpe un markdown en {titre: corps} sur les en-têtes `## `."""
    sections, current, buf = {}, None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current, buf = line[3:].strip(), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def validate_card(text):
    """Renvoie la liste des raisons qui empêchent le gel (vide = carte complète)."""
    sections = parse_sections(text)
    errors = []
    for req in REQUIRED_SECTIONS:
        match = next((t for t in sections if t.startswith(req)), None)
        if match is None:
            errors.append(f"section manquante : '{req}'")
            continue
        body = sections[match]
        if not body:
            errors.append(f"section vide : '{match}'")
        elif PLACEHOLDER in body:
            errors.append(f"placeholder non rempli dans '{match}'")
    # Règle de la pente : ≥3 échelles réellement renseignées
    ech = next((t for t in sections if t.startswith("Échelles")), None)
    if ech:
        bullets = [l for l in sections[ech].splitlines() if l.strip().startswith("-")]
        filled = [b for b in bullets if PLACEHOLDER not in b and b.strip(" -").strip()]
        if len(filled) < 3:
            errors.append(f"règle de la pente : {len(filled)} échelle(s) remplie(s), ≥3 requis")
    # Seuils chiffrés : la section kill doit contenir au moins un nombre
    kill = next((t for t in sections if t.startswith("Ce qui tue")), None)
    if kill and PLACEHOLDER not in sections[kill] and not any(c.isdigit() for c in sections[kill]):
        errors.append("'Ce qui tue' doit contenir des seuils chiffrés (aucun nombre détecté)")
    return errors


def cmd_new(args):
    slug = args.slug
    state = load_state()
    if slug in state["cards"]:
        fail(f"carte '{slug}' existe déjà (état : {state['cards'][slug]['state']})")
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    path = card_path(slug)
    if path.exists():
        fail(f"fichier {path} existe déjà — choisis un autre slug")
    path.write_text(TEMPLATE.format(slug=slug, ph=PLACEHOLDER), encoding="utf-8")
    state["cards"][slug] = {"state": "draft", "created": now_iso()}
    save_state(state)
    print(f"[draft] carte créée : {path}")
    print(f"Remplis les 5 champs + définitions + ≥3 échelles, puis : prereg freeze {slug}")


def cmd_freeze(args):
    slug = args.slug
    state = load_state()
    card = require_card(state, slug)
    if card["state"] != "draft":
        fail(f"freeze impossible depuis l'état '{card['state']}'. Le gel ne part que de 'draft' "
             "(on ne re-gèle pas une hypothèse déjà figée).")
    errors = validate_card(card_path(slug).read_text(encoding="utf-8"))
    if errors:
        print("freeze refusé — la carte n'est pas complète :", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        sys.exit(1)
    h = card_hash(slug)
    card["state"] = "frozen"
    card["frozenHash"] = h
    card["frozenAt"] = now_iso()
    save_state(state)
    print(f"[frozen] {slug} gelé à {card['frozenAt']}")
    print(f"  sha256 : {h}")
    print(f"Contrôle positif obligatoire : prereg gate {slug} --result pass|fail --note '...'")


def cmd_verify(args):
    slug = args.slug
    state = load_state()
    card = require_card(state, slug)
    if "frozenHash" not in card:
        fail(f"'{slug}' n'est pas gelée — rien à vérifier (prereg freeze {slug} d'abord).")
    current = card_hash(slug)
    if current != card["frozenHash"]:
        print(f"TAMPERED — la carte '{slug}' a été modifiée après le gel.", file=sys.stderr)
        print(f"  hash gelé   : {card['frozenHash']}", file=sys.stderr)
        print(f"  hash actuel : {current}", file=sys.stderr)
        sys.exit(1)
    print(f"OK — '{slug}' intacte depuis le gel ({card['frozenAt']}).")


def cmd_gate(args):
    slug = args.slug
    state = load_state()
    card = require_card(state, slug)
    if card["state"] != "frozen":
        if card["state"] == "draft":
            fail(f"gate impossible : '{slug}' est en draft. Le contrôle positif se fait sur une "
                 "carte GELÉE — sinon rien n'empêche d'ajuster l'hypothèse après avoir vu le "
                 f"résultat. Gèle d'abord : prereg freeze {slug}")
        fail(f"gate impossible depuis l'état '{card['state']}' : le contrôle positif s'enregistre "
             "une seule fois, juste après le gel.")
    if card_hash(slug) != card["frozenHash"]:
        fail("la carte a été modifiée après le gel (TAMPERED). Recommence proprement avant le contrôle.")
    card["gate"] = {"result": args.result, "note": args.note, "at": now_iso()}
    if args.result == "pass":
        card["state"] = "gated"
        save_state(state)
        print(f"[gated] contrôle positif PASS enregistré pour '{slug}'.")
        if args.note:
            print(f"  note : {args.note}")
        print(f"Grille autorisée : prereg run {slug}")
    else:
        card["state"] = "stopped"
        save_state(state)
        print(f"[stopped] contrôle positif FAIL pour '{slug}'.")
        if args.note:
            print(f"  note : {args.note}")
        print("Grille bloquée. Leçon : pas de grille tant que l'effet n'est pas visible sur un cas "
              "témoin où il DOIT apparaître.")


def cmd_run(args):
    slug = args.slug
    state = load_state()
    card = require_card(state, slug)
    if card["state"] == "stopped":
        fail("contrôle positif en ÉCHEC : grille bloquée. Revois l'instrumentation, re-crée une "
             "carte, et ne lance la grille qu'une fois l'effet visible sur le cas témoin.")
    gate = card.get("gate")
    if card["state"] != "gated" or not gate or gate.get("result") != "pass":
        fail(f"contrôle positif requis d'abord : lance `prereg gate {slug} --result pass` une fois "
             "l'effet vérifié sur un cas témoin. (le contrôle positif a évité 8 min de grille "
             "aveugle sur CKA — l'effet était sous le bruit de graine.)")
    card["state"] = "running"
    card["ranAt"] = now_iso()
    save_state(state)
    print(f"[running] grille autorisée pour '{slug}'. Calcule, puis logge le tuple : "
          f"prereg log {slug} --outcome ... --x ... --m ... --regime ... --metrique ... --verdict ...")


def cmd_log(args):
    slug = args.slug
    state = load_state()
    card = require_card(state, slug)
    if card["state"] not in ("running", "logged"):
        fail("log impossible : la grille n'a pas été autorisée. Enchaîne "
             f"freeze → gate --result pass → run avant de logger (état actuel : '{card['state']}').")
    if card_hash(slug) != card.get("frozenHash"):
        fail("TAMPERED : la carte a changé depuis le gel — un log doit référencer une hypothèse intacte.")
    atlas = load_atlas()
    entry = {
        "id": len(atlas) + 1,
        "p": args.pi,
        "x": args.x,
        "m": args.m,
        "r": args.regime,
        "o": args.outcome,
        "v": args.verdict,
        "k": args.metrique,
        "s": slug,
        "frozenHash": card["frozenHash"],
        "date": now_iso(),
    }
    atlas.append(entry)
    save_atlas(atlas)
    card["state"] = "logged"
    card["loggedAt"] = entry["date"]
    save_state(state)
    print(f"[logged] tuple #{entry['id']} → {ATLAS_FILE.name} : "
          f"{args.x} × {args.m} / {args.regime} → {args.outcome}")


def cmd_status(args):
    state = load_state()
    cards = state.get("cards", {})
    if not cards:
        print("aucune carte. Crée-en une : prereg new <slug>")
        return
    rows = []
    for slug, c in sorted(cards.items()):
        date = c.get("loggedAt") or c.get("ranAt") or c.get("frozenAt") or c.get("created") or ""
        gate = c.get("gate", {}).get("result", "-")
        rows.append((slug, c["state"], gate, date))
    w0 = max(4, *(len(r[0]) for r in rows))
    w1 = max(5, *(len(r[1]) for r in rows))
    w2 = max(4, *(len(str(r[2])) for r in rows))
    header = f"{'slug':<{w0}}  {'état':<{w1}}  {'gate':<{w2}}  date"
    print(header)
    print("-" * len(header))
    for slug, st, gate, date in rows:
        print(f"{slug:<{w0}}  {st:<{w1}}  {str(gate):<{w2}}  {date}")


def build_parser():
    p = argparse.ArgumentParser(
        prog="prereg",
        description="process de recherche préenregistré (draft→frozen→gated→running→logged)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pn = sub.add_parser("new", help="créer une carte (état draft)")
    pn.add_argument("slug")
    pn.set_defaults(func=cmd_new)

    pf = sub.add_parser("freeze", help="geler la carte (sha256 + timestamp UTC)")
    pf.add_argument("slug")
    pf.set_defaults(func=cmd_freeze)

    pv = sub.add_parser("verify", help="vérifier l'intégrité (TAMPERED si modifiée)")
    pv.add_argument("slug")
    pv.set_defaults(func=cmd_verify)

    pg = sub.add_parser("gate", help="enregistrer le contrôle positif")
    pg.add_argument("slug")
    pg.add_argument("--result", required=True, choices=["pass", "fail"])
    pg.add_argument("--note", default="")
    pg.set_defaults(func=cmd_gate)

    pr = sub.add_parser("run", help="autoriser la grille (si gate=pass)")
    pr.add_argument("slug")
    pr.set_defaults(func=cmd_run)

    pl = sub.add_parser("log", help="logger un tuple dans atlas.json")
    pl.add_argument("slug")
    pl.add_argument("--outcome", required=True, choices=OUTCOMES)
    pl.add_argument("--x", required=True)
    pl.add_argument("--m", required=True)
    pl.add_argument("--regime", required=True)
    pl.add_argument("--metrique", required=True)
    pl.add_argument("--verdict", required=True)
    pl.add_argument("--pi", default=None, help="valeur π optionnelle (log ratio adimensionné)")
    pl.set_defaults(func=cmd_log)

    ps = sub.add_parser("status", help="tableau des cartes et de leurs états")
    ps.set_defaults(func=cmd_status)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
