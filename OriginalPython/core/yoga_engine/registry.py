"""
Yoga Registry (zahtjev #28) - centralni katalog svih yoga. Nova yoga se
dodaje pozivom @register(definition) iznad funkcije pravila u
core/yoga_engine/rules/*.py - NIŠTA se ne mijenja u ovom modulu niti u UI-u.

Svaka funkcija pravila ima potpis:
    def rule(chart: ChartContext) -> List[YogaResult]

Vraća listu jer neke yoge imaju više pojavnica u istoj karti (Parivartana -
svaka zamjena zasebno, Dhana yoga - svaka kombinacija zasebno). Za obične
"singleton" yoge (Gaja Kesari, Ruchaka...) lista ima točno 1 element, čak i
kad present=False (to je bitno za Debug mod, #25 - "nije prisutna" je i
dalje rezultat, ne izostanak rezultata).
"""

from dataclasses import dataclass
from typing import Callable, Dict, List

from core.yoga_engine.context import ChartContext
from core.yoga_engine.models import YogaDefinition, YogaResult

RuleFunc = Callable[[ChartContext], List[YogaResult]]


@dataclass
class RegisteredYoga:
    definition: YogaDefinition
    rule: RuleFunc


YOGA_REGISTRY: Dict[str, RegisteredYoga] = {}

# Definicije yoga za koje NAMJERNO (zahtjev #29) nije implementirano pravilo
# jer se klasični izvori razlikuju ili mi definicija nije dovoljno sigurna
# iz sjećanja da bih je proglasio "provjerenom" - vidi requires_source_review
# i review_note na svakoj. NE ulaze u YOGA_REGISTRY (nema rule funkcije),
# ali ulaze u katalošku tablicu (core/yoga_engine/catalog.py) da korisnik
# vidi da su namjerno preskočene, ne zaboravljene.
PENDING_REVIEW: List[YogaDefinition] = []


def select_from_group(group_fn: RuleFunc, yoga_id: str) -> RuleFunc:
    """
    Omotač za pravila koja računaju VIŠE povezanih yoga u jednom prolazu
    (dijele istu skupu provjeru, npr. Sunapha/Anapha/Durudhara ili
    Vesi/Vosi/Ubhayachari) - SVAKI registrirani id smije vratiti SAMO svoj
    vlastiti rezultat, inače bi run_all_yogas dodao cijelu grupu jednom PO
    SVAKOM id-u iz te grupe (duplikati - vidi napomenu u core/yoga_engine/
    rules/nabhasa.py gdje je ovaj obrazac prvo uočen i ispravljen).
    """
    def wrapper(chart: ChartContext) -> List[YogaResult]:
        return [r for r in group_fn(chart) if r.id == yoga_id]
    return wrapper


def register(definition: YogaDefinition):
    def decorator(fn: RuleFunc) -> RuleFunc:
        if definition.id in YOGA_REGISTRY:
            raise ValueError(f"Yoga id '{definition.id}' je već registrirana (duplikat).")
        YOGA_REGISTRY[definition.id] = RegisteredYoga(definition=definition, rule=fn)
        return fn
    return decorator


def mark_pending_review(definition: YogaDefinition) -> None:
    """Registrira yogu u katalog BEZ pravila - vidi PENDING_REVIEW gore."""
    definition.implemented = False
    definition.requires_source_review = True
    PENDING_REVIEW.append(definition)


def _load_all_rule_modules() -> None:
    """Uvozi sve core/yoga_engine/rules/*.py module - svaki se sam registrira preko @register."""
    from core.yoga_engine.rules import (  # noqa: F401
        mahapurusha, chandra, surya, nabhasa, raja, dhana,
        neecha_bhanga, viparita_raja, parivartana, special, negative,
    )


_load_all_rule_modules()


def run_all_yogas(chart: ChartContext) -> List[YogaResult]:
    """Pokreće SVA registrirana pravila nad zadanom kartom, vraća spljoštenu listu rezultata."""
    results: List[YogaResult] = []
    for entry in YOGA_REGISTRY.values():
        results.extend(entry.rule(chart))
    return results


def run_yoga(yoga_id: str, chart: ChartContext) -> List[YogaResult]:
    return YOGA_REGISTRY[yoga_id].rule(chart)
