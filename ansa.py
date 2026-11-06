"""Filtro per il feed di ANSA Valle d'Aosta.

ANSA a volte pubblica la stessa notizia due volte con link diversi (ad esempio una copia
nella sezione /consiglio/ e una nella sezione generale) e lo stesso titolo o quasi.
Qui si tiene la prima e si scartano le altre.
"""
import re, time
from difflib import SequenceMatcher

FEED = "https://www.ansa.it/valledaosta/notizie/valledaosta_rss.xml"
ORE = 12            # per quante ore ricordare i titoli già pubblicati (copie arrivano solitamente a pochi minuti di distanza)
SOGLIA = 0.85       # quanto devono somigliarsi due titoli per essere la stessa notizia


def _norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


def _simili(a, b):
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio() >= SOGLIA


def filtra(entries, state):
    """Restituisce le voci del feed senza i doppioni; quelli scartati vengono segnati come visti."""
    ora = time.time()
    recenti = [r for r in state.get("ansa_recenti", []) if ora - r[1] < ORE * 3600]
    state["ansa_recenti"] = recenti
    tenute, nuovi_titoli = [], []
  
    for e in entries:  # il feed va dalla più recente alla più vecchia
        link, titolo = e.get("link"), e.get("title", "")
        if not link or link in state["seen"]:
            tenute.append(e)
            continue
        if any(_simili(titolo, t) for t, _ in recenti) or any(_simili(titolo, t) for t in nuovi_titoli):
            print("ANSA, doppione saltato:", titolo)
            state["seen"].append(link)
            continue
        nuovi_titoli.append(titolo)
        tenute.append(e)
    return tenute


def registra(state, e):
    """Da chiamare dopo aver pubblicato (o registrato al primo avvio) una notizia ANSA."""
    state.setdefault("ansa_recenti", []).append([e.get("title", ""), time.time()])
    state["ansa_recenti"] = state["ansa_recenti"][-500:]
