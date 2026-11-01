"""
Tekstualni sloj (hrvatski) za sinastrijske kontakte - odvojen od izračuna
(core/synastry/overlays.py, graha_drishti.py, conjunctions.py) po uzoru na
zahtjev da se jasno razlikuje "čisti izračun" od "interpretacije".

Ton namjerno izbjegava apsolutne tvrdnje ("sigurno će...", "ovo znači da
će...") - koristi formulacije poput "naglašava", "podržava mogućnost",
"sam po sebi nije dovoljan" (vidi specifikacija, poglavlje 7).

Planeti poput Saturna, Rahua, Ketua i Marsa namjerno imaju VIŠE mogućih
izraza iste simbolike umjesto jedne fiksne "dobro/loše" oznake - vidi
PLANET_NATURE_NOTES.

ISPRAVAK (dva odvojena bivša problema):

1. Terminologija "partnerska 7. kuća" (spec 6): puni (7.) Graha Drishti se
   ranije UVIJEK opisivao kao "prema partnerskoj (7.) kući", iako to samo
   znači da je META aspekta sedmi ZNAK brojan OD planeta koji baca aspekt -
   to NIJE isto što i "pogađa natalnu 7. kuću druge osobe" (ta bi tvrdnja
   zahtijevala da aspektirani planet stvarno LEŽI u natalnoj 7. kući cilja).
   graha_drishti_interpretation() sada razlikuje ta dva ("puni opozicijski
   Graha Drishti - cilj je sedmi znak od planeta" nasuprot "kontakt dodatno
   aktivira natalnu 7. kuću osobe X", potonje SAMO kad je stvarno točno).

2. Paušalno tumačenje osi 3./10., 4./8., 5./9. (spec 7): ranije je SVAKI
   aspekt na toj udaljenosti dobivao FIKSAN tekst ("5./9. = sklad",
   "3./10. = obveza/pritisak", "4./8. = intimnost") bez obzira na to KOJI
   su planeti uključeni. interpret_cross_chart_contact() niže gradi
   tumačenje iz funkcionalne prirode oba planeta (core.planet_strength.
   compute_functional_nature), dostojanstva i D9 potvrde - "jaka" tvrdnja
   (npr. "izrazita intimnost") dopuštena je SAMO uz d9_confirmation=True
   (dodatni, neovisan sloj), inače tekst ostaje u "blagoj/mješovitoj" formi.
"""

from typing import List, Optional

from core.houses import whole_sign_house
from core.natal import NatalContext
from core.planet_strength import compute_dignity, compute_functional_nature
from core.synastry.deduplication import key_from_drishti_contact
from core.synastry.models import ConjunctionContact, GrahaDrishtiContact, VargaSynastryResult

CAUTION_LINE = (
    "Ovaj pokazatelj sam po sebi nije dovoljan za zaključak - za potvrdu "
    "treba promatrati više slojeva (overlay, aspekte, nakšatre, dashe) zajedno."
)

# --- Priroda planeta - VIŠE mogućih izraza, ne jedna fiksna ocjena ---
PLANET_NATURE_NOTES = {
    "Saturn": (
        "Saturn u sinastriji može naglasiti stabilnost, obvezu i trajnost, ali i "
        "strah, blokadu ili osjećaj udaljenosti - koji se izraz aktivira ovisi o "
        "ostatku karte i o vrsti odnosa."
    ),
    "Rahu": (
        "Rahu može naglasiti snažnu privlačnost, opsesivnost, ubrzavanje ili "
        "projekciju (vidjeti u drugome ono što se traži) - a ne nužno stabilnu, "
        "smirenu vezu."
    ),
    "Ketu": (
        "Ketu može naglasiti osjećaj prijašnje povezanosti, ali i odvajanje, "
        "nejasnoću ili nezainteresiranost - ponekad i duhovnu, manje osobnu "
        "dimenziju veze."
    ),
    "Mars": (
        "Mars može naglasiti privlačnost, inicijativu i energiju, ali i sukob "
        "ili nestrpljivost - ovisno o kontekstu."
    ),
    "Jupiter": (
        "Jupiter može naglasiti podršku, rast i velikodušnost, ali i "
        "pretjerivanje ili moraliziranje."
    ),
    "Venera": (
        "Venera obično naglašava privlačnost, ugodu i vrijednosti koje se dijele "
        "u odnosu."
    ),
    "Mjesec": (
        "Mjesec naglašava emocionalnu razinu odnosa - osjećaj bliskosti, "
        "svakodnevne navike i potrebu za sigurnošću."
    ),
    "Sunce": (
        "Sunce naglašava temu identiteta i priznanja u odnosu - koliko se "
        "netko osjeća viđenim i podržanim u svom smjeru."
    ),
    "Merkur": (
        "Merkur naglašava komunikaciju, razmjenu ideja i način na koji dvoje "
        "ljudi razgovaraju i razumiju jedno drugo."
    ),
}

# --- Kućni overlay - kratka napomena po kući (samo relevantne kuće) ---
HOUSE_OVERLAY_NOTES = {
    1: "identitet, prvi dojam i način na koji planet 'boji' cijelo prisustvo u životu druge osobe",
    2: "vrijednosti, resursi i obiteljski kontekst",
    4: "emocionalna sigurnost, dom i osjećaj 'temelja'",
    5: "romantika, kreativnost i zajedničko uživanje",
    7: "izravno partnerstvo - klasično najizravnija kuća za sinastriju",
    8: "intimnost, transformacija i dijeljeni resursi - može biti intenzivno u oba smjera",
    9: "zajednička vjerovanja, smisao i širenje horizonata",
    10: "javni život, status i kako odnos djeluje 'prema van'",
    11: "prijateljstvo, zajedničke želje i mreža oko odnosa",
    12: "povučenost, žrtva ili duhovna/nesvjesna povezanost - može biti i gubitak granica",
}

_AXIS_HOUSES = {4: (4, 8), 8: (4, 8), 5: (5, 9), 9: (5, 9), 3: (3, 10), 10: (3, 10)}
_AXIS_LABEL = {(4, 8): "4./8.", (5, 9): "5./9.", (3, 10): "3./10."}


def interpret_cross_chart_contact(
    source_planet: str, target_planet: str, drishti_type: str,
    source_functional_nature: str, target_functional_nature: str,
    activated_houses: List[int], dignity_context: str, d9_confirmation: bool,
) -> str:
    """
    Zamjenjuje paušalno ("5./9.=sklad", "3./10.=pritisak", "4./8.=intimnost")
    tumačenje osi 3./10., 4./8., 5./9. (spec 7). Tumačenje ovisi o
    funkcionalnoj prirodi OBA planeta (core.planet_strength.
    compute_functional_nature - "funkcionalni dobrotvor/zlotvor/mješovit" za
    DANI ascendent), dostojanstvu i D9 potvrdi - ne o samoj kućnoj
    udaljenosti.

    drishti_type: "7" | "4_8" | "5_9" | "3_10" (os aspekta).
    activated_houses: koje kuće (brojano od planeta koji baca aspekt) ova
        os aktivira - npr. [4, 8].
    d9_confirmation: je li ISTI par planeta potvrđen i u D9 (core.synastry.
        divisional_synastry) - "jaka" tvrdnja dopuštena je SAMO uz ovu
        dodatnu, neovisnu potvrdu (spec 7: "zahtjeva potvrdu kroz najmanje
        dva neovisna sloja").
    """
    both_benefic = "dobrotvor" in source_functional_nature and "dobrotvor" in target_functional_nature
    both_malefic = "zlotvor" in source_functional_nature and "zlotvor" in target_functional_nature
    mixed = not both_benefic and not both_malefic

    houses_str = "/".join(f"{h}." for h in activated_houses)

    if drishti_type == "3_10":
        base = (
            f"{source_planet}-{target_planet} kontakt na osi {houses_str} kuće aktivira temu truda, "
            f"inicijative ili osjećaja obveze"
        )
    elif drishti_type == "5_9":
        base = (
            f"{source_planet}-{target_planet} kontakt na osi {houses_str} kuće aktivira temu rasta, "
            f"učenja ili fascinacije"
        )
    elif drishti_type == "4_8":
        base = (
            f"{source_planet}-{target_planet} kontakt na osi {houses_str} kuće aktivira dublju, manje "
            f"vidljivu temu (emocionalna sigurnost/intimnost naspram transformacije i ranjivosti)"
        )
    else:
        base = f"{source_planet}-{target_planet} kontakt (Graha Drishti {drishti_type})"

    if both_benefic:
        lean = "priroda oba uključena planeta za ove karte naginje podržavajućem izrazu ove teme"
    elif both_malefic:
        lean = "priroda oba uključena planeta za ove karte naginje napetijem, zahtjevnijem izrazu ove teme"
    else:
        lean = "planeti nose MIJEŠANU (jedan podržavajući, jedan zahtjevniji) prirodu za ove karte, pa je izraz vjerojatno dvosmislen - i podrška i trvenje istovremeno"

    strength_word = "izraženo" if d9_confirmation else "moguće, ali NEPOTVRĐENO drugim slojem"
    parts = [
        f"{base.capitalize()}; {lean}.",
        f"Dostojanstvo: {dignity_context}.",
    ]
    if d9_confirmation:
        parts.append("Isti par je potvrđen i u D9 (Navamsha) - dodatan, neovisan sloj čini ovu temu vjerojatnijom, ne samo simboličkom.")
    else:
        parts.append(
            "Nema (još) potvrde u D9 ni drugom neovisnom sloju - ovaj nalaz sam po sebi treba čitati kao "
            f"{strength_word}, ne kao samostalan dokaz snažne bračne veze, izrazite intimnosti, stabilnosti, "
            "karmičke povezanosti ili snažnog konflikta."
        )
    return " ".join(parts)


def graha_drishti_interpretation(
    contact: GrahaDrishtiContact,
    ctx_a: Optional[NatalContext] = None, ctx_b: Optional[NatalContext] = None,
    functional_nature_source: str = "", functional_nature_target: str = "",
    dignity_context: str = "", d9_confirmation: bool = False,
) -> GrahaDrishtiContact:
    dist = contact.house_distance

    seventh_house_note = ""
    if dist == 7:
        nature = "puni opozicijski Graha Drishti - cilj je sedmi znak brojan OD planeta koji baca aspekt"
        target_ctx = ctx_b if contact.target_person == "B" else ctx_a if contact.target_person == "A" else None
        if target_ctx is not None and contact.to_planet != "Lagna" and contact.to_planet in target_ctx.positions:
            to_house_in_own_chart = whole_sign_house(
                target_ctx.positions[contact.to_planet].sign_index, target_ctx.ascendant_sign_index,
            )
            if to_house_in_own_chart == 7:
                seventh_house_note = (
                    f" Ovaj kontakt DODATNO aktivira natalnu 7. kuću osobe {contact.target_person} "
                    f"(jer je {contact.to_planet} u toj karti stvarno posjednut u 7. kući, ne samo meta "
                    f"aspekta) - ovo je dodatna, provjerena okolnost, ne automatska posljedica svakog "
                    f"punog aspekta."
                )
    elif dist in _AXIS_HOUSES:
        axis = _AXIS_HOUSES[dist]
        axis_label = _AXIS_LABEL[axis]
        nature = interpret_cross_chart_contact(
            source_planet=contact.from_planet, target_planet=contact.to_planet,
            drishti_type={( 4, 8): "4_8", (5, 9): "5_9", (3, 10): "3_10"}[axis],
            source_functional_nature=functional_nature_source or "nepoznata funkcionalna priroda",
            target_functional_nature=functional_nature_target or "nepoznata funkcionalna priroda",
            activated_houses=list(axis), dignity_context=dignity_context or "nije procijenjeno",
            d9_confirmation=d9_confirmation,
        )
    else:
        nature = "dodatni Drishti"

    planet_note = PLANET_NATURE_NOTES.get(contact.from_planet, "")

    short = (
        f"{contact.from_planet} ({contact.source_person}) aspektira {contact.to_planet} "
        f"({contact.target_person}) - {contact.house_distance}. kuća, {contact.strength_label}."
    )
    detailed_parts = [
        short,
        (nature[0].upper() + nature[1:] if dist in _AXIS_HOUSES else nature.capitalize()) + ("." if dist not in _AXIS_HOUSES else ""),
    ]
    if seventh_house_note:
        detailed_parts.append(seventh_house_note.strip())
    if contact.from_planet_houses_own_chart:
        houses_str = ", ".join(f"{h}." for h in contact.from_planet_houses_own_chart)
        detailed_parts.append(
            f"{contact.from_planet} u vlastitoj karti ({contact.source_person}) vlada kućom/kućama {houses_str}, "
            f"pa taj aspekt djelomično nosi i te teme."
        )
    if planet_note:
        detailed_parts.append(planet_note)
    detailed_parts.append(CAUTION_LINE)

    contact.short_interpretation = short
    contact.detailed_interpretation = " ".join(detailed_parts)
    return contact


def enrich_graha_drishti_contacts(
    contacts: List[GrahaDrishtiContact],
    ctx_a: Optional[NatalContext] = None, ctx_b: Optional[NatalContext] = None,
) -> List[GrahaDrishtiContact]:
    """
    ctx_a/ctx_b su OPCIONALNI (zadano None) - bez njih se i dalje ispravno
    obrađuju puni (7.) aspekti (samo bez dodatne "aktivira natalnu 7. kuću"
    provjere) i osi 3./10., 4./8., 5./9. (bez funkcionalne prirode/D9
    potvrde - vidi core/synastry/report.py za punu obogaćenu putanju koja
    IH prosljeđuje).
    """
    return [graha_drishti_interpretation(c, ctx_a, ctx_b) for c in contacts]


def enrich_graha_drishti_contacts_with_axis_context(
    contacts: List[GrahaDrishtiContact], ctx_a: NatalContext, ctx_b: NatalContext,
    navamsha_result: Optional[VargaSynastryResult] = None,
) -> List[GrahaDrishtiContact]:
    """
    Puna obogaćena putanja (koristi je core/synastry/report.py) - za svaki
    kontakt na osi 3./10., 4./8., 5./9. izračuna funkcionalnu prirodu OBA
    planeta (u NJIHOVOJ vlastitoj karti), dostojanstvo planeta koji baca
    aspekt, i provjerava je li ISTI par potvrđen u D9 (navamsha_result.
    repeated_pattern_pair_keys) - sve ulazi u interpret_cross_chart_contact
    umjesto paušalnog teksta (spec 7).
    """
    confirmed_keys = set(navamsha_result.repeated_pattern_pair_keys) if navamsha_result is not None else set()
    enriched = []
    for c in contacts:
        source_ctx = ctx_a if c.source_person == "A" else ctx_b
        target_ctx = ctx_b if c.target_person == "B" else ctx_a
        functional_source = compute_functional_nature(c.from_planet, source_ctx.ascendant_sign_index)
        functional_target = (
            compute_functional_nature(c.to_planet, target_ctx.ascendant_sign_index)
            if c.to_planet in target_ctx.positions else "nepoznata funkcionalna priroda (posebna točka)"
        )
        dignity, _ = compute_dignity(c.from_planet, source_ctx.positions[c.from_planet].sign_index)
        d9_confirmation = key_from_drishti_contact(c) in confirmed_keys
        enriched.append(graha_drishti_interpretation(
            c, ctx_a, ctx_b,
            functional_nature_source=functional_source, functional_nature_target=functional_target,
            dignity_context=dignity, d9_confirmation=d9_confirmation,
        ))
    return enriched


def conjunction_interpretation(contact: ConjunctionContact) -> ConjunctionContact:
    exact_note = "egzaktna (unutar 1°) " if contact.is_exact else ""
    nak_note = ""
    if contact.same_pada:
        nak_note = " Isti su i u istoj nakšatri I istoj padi - vrlo uska, specifična veza."
    elif contact.same_nakshatra:
        nak_note = " U istoj su nakšatri (različita pada) - dijele širu simboličku temu."

    short = (
        f"{contact.person_a_object} (A) i {contact.person_b_object} (B) su u "
        f"{exact_note}konjunkciji ({contact.degree_distance:.1f}°, {contact.sign})."
    )

    detail_parts = [short + nak_note]

    flag_notes = []
    for flag in contact.special_flags:
        if flag == "Rahu/Ketu":
            flag_notes.append(
                "Uključenost čvora (Rahu/Ketu) obično pojačava intenzitet i osjećaj sudbinske "
                "privlačnosti - ali to sam po sebi nije dokaz ni pozitivnog ni negativnog ishoda."
            )
        elif flag == "Saturn":
            flag_notes.append(PLANET_NATURE_NOTES["Saturn"])
        elif flag == "Mjesec":
            flag_notes.append(PLANET_NATURE_NOTES["Mjesec"])
        elif flag == "Venera":
            flag_notes.append(PLANET_NATURE_NOTES["Venera"])
        elif flag == "Mars":
            flag_notes.append(PLANET_NATURE_NOTES["Mars"])
        elif flag.startswith("vladar 7. kuće"):
            which = "A" if "(A)" in flag else "B"
            flag_notes.append(
                f"Uključen je vladar 7. kuće osobe {which} - konjunkcija time izravnije "
                f"dotiče temu partnerstva u toj karti."
            )
        elif flag in ("Upapada Lagna (UL)", "Darapada (A7)"):
            flag_notes.append(
                f"Uključena je {flag} - klasična Jaimini točka za brak/partnerstva, pa "
                f"konjunkcija ovdje ima poseban naglasak na temu odnosa."
            )

    detail_parts.extend(flag_notes)
    detail_parts.append(CAUTION_LINE)

    contact.short_interpretation = short
    contact.detailed_interpretation = " ".join(detail_parts)
    return contact


def enrich_conjunction_contacts(contacts: List[ConjunctionContact]) -> List[ConjunctionContact]:
    return [conjunction_interpretation(c) for c in contacts]
