"""
Osnovni tekstualni izvještaj sinastrije (Faza 1 + Faza 2 + Faza 3).

Struktura je podskup pune izvještajne strukture iz specifikacije
(prediktivna sinastrija - tranziti/dashe/Varshaphala - dolazi u Fazi 4).
Faza 1+2+3 pokriva: osnovni podaci, metodologija (aktivne postavke),
kućni overlay, Graha Drishti, konjunkcije, nakšatra sinastrija, Ashtakoota,
Kuja Dosha, ključni signifikatori (7. kuća, DK/AK, UL/A7), D9 sinastrija,
kategorijsko bodovanje, zaključak.

Jasno se razlikuje: (1) čisti izračun (brojevi, znakovi, kuće), (2)
tradicionalno Jyotish pravilo (npr. "7. kuća = partnerstvo"), (3)
interpretacija (core/synastry/interpretation.py) - odjeljci su tako i
naslovljeni.

Faza 2/3 argumenti su OPCIONALNI (None) radi unatrag kompatibilnosti -
izvještaj i dalje radi i bez njih (samo preskače te odjeljke).
"""

from typing import List, Optional

from core.constants import RASHI
from core.natal import NatalContext
from core.synastry.config import SynastryConfig
from core.synastry.models import (
    ConjunctionContact, GrahaDrishtiContact, HouseOverlayRow,
    NakshatraSynastryResult, AshtakootaResult, KujaDoshaComparison, RelationshipSignificatorsResult,
    VargaSynastryResult, SynastryScoreResult,
)

VERSION = "1.3.0-ispravci-logike"


def _format_overlay_section(rows: List[HouseOverlayRow], source: str, target: str) -> List[str]:
    lines = [f"### Planeti osobe {source} u karti osobe {target}", ""]
    for r in rows:
        marker = " ★" if r.is_significant_house else ""
        bhava_note = f" (Bhava Chalit: {r.bhava_chalit_house}. kuća)" if r.bhava_chalit_house else ""
        lines.append(
            f"- {r.planet}: {r.sign}, {r.whole_sign_house}. kuća{marker}{bhava_note} - "
            f"{r.nakshatra} pada {r.pada}, dispozitor {r.sign_lord}, dostojanstvo: {r.dignity}. "
            f"Odnos s vladarom kuće ({r.target_house_lord}): {r.target_house_lord_relation}."
        )
    lines.append("")
    lines.append("★ = kuća iz posebno naglašenog skupa (1,2,4,5,7,8,9,10,11,12).")
    lines.append("")
    return lines


def _format_drishti_section(contacts: List[GrahaDrishtiContact]) -> List[str]:
    if not contacts:
        return ["_Nema aktivnih Graha Drishti kontakata unutar ovog izbora._", ""]
    lines = []
    for c in contacts:
        lines.append(f"- {c.detailed_interpretation}")
    lines.append("")
    return lines


def _format_conjunction_section(contacts: List[ConjunctionContact]) -> List[str]:
    if not contacts:
        return ["_Nema konjunkcija unutar konfiguriranih orbisa._", ""]
    lines = []
    for c in contacts:
        lines.append(f"- {c.detailed_interpretation}")
    lines.append("")
    return lines


def _format_nakshatra_section(result: NakshatraSynastryResult) -> List[str]:
    lines = []
    for label, profiles in (("A", result.profiles_a), ("B", result.profiles_b)):
        lines.append(f"### Osoba {label}")
        for prof in profiles.values():
            lines.append(
                f"- {prof.point_label} ({prof.planet_or_point}): {prof.nakshatra} pada {prof.pada}, "
                f"vladar {prof.nakshatra_lord}, devata {prof.devata}, Gana {prof.gana}, "
                f"Yoni {prof.yoni} ({prof.yoni_gender}), Nadi {prof.nadi}, D9 znak pade {prof.navamsha_sign} "
                f"({prof.pada_element})."
            )
    lines.append("")
    lines.append("**Unakrsne veze:**")
    if result.cross_links:
        for link in result.cross_links:
            lines.append(f"- {link.source_label} — {link.target_label}: {link.detail}")
    else:
        lines.append("_Nema pronađenih izravnih veza unutar ovog izbora točaka._")
    lines.append("")
    lines.append("**Ponovljeni obrasci (ista nakšatra kroz više točaka):**")
    if result.repeated_themes:
        for theme in result.repeated_themes:
            lines.append(f"- {theme.nakshatra}: {', '.join(theme.points_involved)} - {theme.note}")
    else:
        lines.append("_Nije pronađena nakšatra koja se ponavlja kroz više ključnih točaka._")
    lines.append("")
    return lines


def _format_ashtakoota_section(result: AshtakootaResult) -> List[str]:
    lines = [
        f"Nakšatra Mjeseca: A = {result.person_a_moon_nakshatra}, B = {result.person_b_moon_nakshatra}.",
        "",
    ]
    for k in result.kutas:
        lines.append(f"- **{k.name}**: {k.points:.1f}/{k.max_points:.0f} - {k.rule_used} _{k.interpretation}_")
    lines.append("")
    lines.append(f"**Ukupno: {result.total_points:.1f} / {result.max_points:.0f}**")
    lines.append(
        "_36 bodova NIJE konačna presuda o odnosu - riječ je samo o jednom tradicionalnom sloju "
        "(temeljenom isključivo na Mjesecu)._"
    )
    if result.cancellations:
        lines.append("")
        lines.append("**Tradicionalne iznimke/poništenja:**")
        for c in result.cancellations:
            lines.append(f"- {c}")
    lines.append("")
    return lines


def _format_kuja_dosha_section(comparison: KujaDoshaComparison) -> List[str]:
    lines = []
    for assessment in (comparison.person_a, comparison.person_b):
        lines.append(f"**Osoba {assessment.person_label}: {assessment.severity}** (indeks {assessment.severity_score:.0f}/100)")
        for r in assessment.reasons:
            lines.append(f"- {r}")
        for c in assessment.possible_cancellations:
            lines.append(f"- _Moguće poništenje:_ {c}")
    lines.append("")
    lines.append(comparison.balancing_note)
    lines.append("")
    return lines


def _format_significators_section(result: RelationshipSignificatorsResult) -> List[str]:
    lines = []
    for label, profile in (("A", result.profile_a), ("B", result.profile_b)):
        lines.append(f"### Osoba {label}")
        lines.append(
            f"- 7. kuća: {profile.seventh_house_sign} (planeti: {', '.join(profile.seventh_house_planets) or '-'}), "
            f"vladar {profile.seventh_lord} ({profile.seventh_lord_sign}, {profile.seventh_lord_house}. kuća)"
        )
        lines.append(f"- Venera: {profile.venus_sign} ({profile.venus_house}. kuća) · Mars: {profile.mars_sign} ({profile.mars_house}. kuća)")
        lines.append(f"- Jupiter: {profile.jupiter_sign} ({profile.jupiter_house}. kuća) · Mjesec: {profile.moon_sign} ({profile.moon_house}. kuća)")
        lines.append(f"- Atmakaraka: {profile.atmakaraka_planet} · Darakaraka: {profile.darakaraka_planet}")
        lines.append(f"- Arudha Lagna: {profile.arudha_lagna_sign}")
        lines.append(
            f"- Upapada Lagna (UL): {profile.upapada_lagna_sign} ({profile.upapada_house}. kuća), "
            f"vladar {profile.upapada_lord}, planeti: {', '.join(profile.upapada_planets) or '-'}"
        )
        lines.append(f"- 2. od UL: {profile.second_from_upapada_sign} · 8. od UL: {profile.eighth_from_upapada_sign}")
        lines.append(f"- Darapada (A7): {profile.darapada_sign} ({profile.darapada_house}. kuća)")
    lines.append("")
    lines.append("**Unakrsne veze:**")
    if result.cross_notes:
        for note in result.cross_notes:
            lines.append(f"- {note}")
    else:
        lines.append("_Nema pronađenih posebnih unakrsnih veza unutar ovog izbora._")
    lines.append("")
    return lines


def _format_navamsha_section(result: VargaSynastryResult) -> List[str]:
    lines = [
        f"Ascendent D9: A = {result.ascendant_sign_a}, B = {result.ascendant_sign_b}.",
        f"7. kuća D9: A = {result.seventh_sign_a} (vladar {result.seventh_lord_a}), "
        f"B = {result.seventh_sign_b} (vladar {result.seventh_lord_b}).",
        "",
    ]
    for label, points in (("A", result.key_points_a), ("B", result.key_points_b)):
        lines.append(f"Ključne točke D9 (osoba {label}): " + ", ".join(f"{k}={v}" for k, v in points.items()))
    lines.append("")
    for title, rows in (
        ("Planeti A u D9 kući osobe B", result.overlay_a_to_b),
        ("Planeti B u D9 kući osobe A", result.overlay_b_to_a),
    ):
        lines.append(f"**{title}:**")
        for r in rows:
            marker = " ★" if r.is_significant_house else ""
            lines.append(f"- {r.planet}: {r.varga_sign}, {r.house}. kuća{marker}")
    lines.append("")
    lines.append("**Ponovljeni obrasci (D1 ↔ D9):**")
    if result.repeated_pattern_notes:
        for n in result.repeated_pattern_notes:
            lines.append(f"- {n}")
    else:
        lines.append("_Nije pronađen par planeta povezan istovremeno u D1 i D9._")
    lines.append("")
    return lines


def _format_scoring_section(result: SynastryScoreResult) -> List[str]:
    """
    ISPRAVAK (spec 13): rezultat se prikazuje kao CIJELI broj (ne .1f) -
    model nije dovoljno precizan da opravda decimalu (Ashtakoota je jedina
    iznimka, vidi _format_ashtakoota_section). Uz rezultat se sada prikazuje
    i pouzdanost, broj neovisnih slojeva, potvrde/kontradikcije te odvojeno
    pozitivan/izazovan podrezultat (spec 10.10/13).
    """
    lines = []
    for category, cat_score in result.categories.items():
        lines.append(
            f"- **{category}: {round(cat_score.score)}/100** "
            f"(pozitivno {round(cat_score.positive_score)}, izazovno {round(cat_score.challenge_score)}; "
            f"pouzdanost: {cat_score.confidence}, neovisnih slojeva: {cat_score.independent_layers}, "
            f"potvrda: {cat_score.confirmations}, kontradikcija: {cat_score.contradictions_count})"
        )
        if cat_score.top_positive_notes:
            lines.append(f"  - Najvažniji pozitivni pokazatelji: {'; '.join(cat_score.top_positive_notes)}")
        if cat_score.top_challenge_notes:
            lines.append(f"  - Najvažniji izazovi: {'; '.join(cat_score.top_challenge_notes)}")
        for f in cat_score.factors:
            lines.append(f"  - {f.description} (doprinos {f.contribution:+.1f}, sloj: {f.layer})")
    if result.not_available:
        lines.append("")
        lines.append(f"_Nije dostupno (dolazi u Fazi 4): {', '.join(result.not_available)}_")
    lines.append("")
    lines.append(
        "_Kategorije su nezavisne procjene, ne zbrajaju se u jedan 'ukupni' rezultat. Dvostruko "
        "brojanje iste veze (konjunkcija + ista nakšatra + kućni overlay, ili višestruke uloge "
        "istog planeta) je spriječeno, a rezultati iznad 80/90 zahtijevaju dovoljno neovisnih "
        "slojeva potvrde - vidi core/synastry/scoring.py._"
    )
    lines.append("")
    return lines


def _score_bucket(score: float) -> str:
    if score >= 75:
        return "visok"
    if score >= 58:
        return "srednje-visok"
    if score >= 42:
        return "srednji"
    if score >= 25:
        return "srednje-nizak"
    return "nizak"


def build_relationship_summary(
    person_a_name: str, person_b_name: str,
    relationship_profile,   # core.synastry.relationship_profiles.RelationshipProfile, optional
    score_result: Optional[SynastryScoreResult],
    kuja_comparison: Optional[KujaDoshaComparison],
    ashtakoota_result: Optional[AshtakootaResult],
    navamsha_result: Optional[VargaSynastryResult],
) -> List[str]:
    """
    Strukturiran završni sažetak (spec 14) - zamjenjuje bivši flat
    "Zaključak" koji je samo nabrajao ŠTO izvještaj sadrži. Kad rezultati
    bodovanja/Kuja Dosha/Ashtakoote/D9 nisu dostupni (Faza 1 poziv bez tih
    argumenata), vraća se na kraći, opisni oblik - izvještaj i dalje radi
    bez tih odjeljaka.
    """
    lines: List[str] = []
    if score_result is None:
        lines.append(
            "Ovaj izvještaj daje programski izveden pregled kućnog overlaya, Graha Drishtija i "
            "konjunkcija. Ne uključuje kategorijsko bodovanje, Ashtakootu, Kuja Doshu ni D9 "
            "sinastriju u ovom pozivu. Nijedan pojedinačni pokazatelj ovdje ne treba čitati kao "
            "samostalnu presudu o odnosu; riječ je o slojevima koje treba promatrati zajedno."
        )
        return lines

    cats = score_result.categories
    if relationship_profile is not None:
        lines.append(f"**1. Osnovna priroda odnosa.** {relationship_profile.framing_note}")
    else:
        lines.append(
            "**1. Osnovna priroda odnosa.** Sinastrija je promatrana bez posebnog naglaska vrste "
            "odnosa - prikazan je ravnomjeran pregled svih kategorija."
        )

    # Overlay opis je oblika "{planet} ({source_person}) u {kuća}. kući osobe {target_person}"
    # (core/synastry/scoring.py:_collect_overlay_signals) - "(A) u" znači planet OSOBE A pada u
    # kartu osobe B, "(B) u" obrnuto.
    top_overlay = [f for cat in cats.values() for f in cat.factors if f.layer == "overlay" and f.polarity == "positive"]
    top_overlay.sort(key=lambda f: -f.contribution)
    a_to_b = [f for f in top_overlay if "(A) u" in f.description][:2]
    b_to_a = [f for f in top_overlay if "(B) u" in f.description][:2]
    lines.append(
        "**2. Što osoba A aktivira kod osobe B.** "
        + ("; ".join(f.description for f in a_to_b) if a_to_b else "Nema izraženog jednosmjernog kućnog naglaska (A→B).")
    )
    lines.append(
        "**3. Što osoba B aktivira kod osobe A.** "
        + ("; ".join(f.description for f in b_to_a) if b_to_a else "Nema izraženog jednosmjernog kućnog naglaska (B→A).")
    )

    emo = cats.get("Emocionalna povezanost")
    lines.append(
        f"**4. Najveće emocionalne poveznice** (rezultat: {_score_bucket(emo.score)}, {round(emo.score)}/100). "
        + ("; ".join(emo.top_positive_notes) if emo and emo.top_positive_notes else "Nema izrazito dominantnog pojedinačnog nalaza.")
    )

    attr = cats.get("Privlačnost i kemija")
    lines.append(
        f"**5. Najveća privlačnost** (rezultat: {_score_bucket(attr.score)}, {round(attr.score)}/100). "
        + ("; ".join(attr.top_positive_notes) if attr and attr.top_positive_notes else "Nema izrazito dominantnog pojedinačnog nalaza.")
    )

    stab = cats.get("Stabilnost")
    practical = cats.get("Praktična kompatibilnost")
    stabilizers = (stab.top_positive_notes if stab else []) + (practical.top_positive_notes if practical else [])
    lines.append(
        f"**6. Najveći stabilizatori** (Stabilnost: {round(stab.score) if stab else '-'}/100, "
        f"Praktična kompatibilnost: {round(practical.score) if practical else '-'}/100). "
        + ("; ".join(stabilizers[:3]) if stabilizers else "Nema izrazito dominantnog stabilizirajućeg nalaza.")
    )

    conflict = cats.get("Konflikt i pritisak")
    lines.append(
        f"**7. Najveći konflikti i blokade** (rezultat: {_score_bucket(conflict.score)}, {round(conflict.score)}/100). "
        + ("; ".join(conflict.top_challenge_notes) if conflict and conflict.top_challenge_notes else "Nema izrazito dominantnog konfliktnog nalaza.")
    )
    if kuja_comparison is not None and kuja_comparison.mutual_balancing:
        lines.append(f"   _Kuja Dosha napomena:_ {kuja_comparison.balancing_note}")

    if navamsha_result is not None:
        if navamsha_result.repeated_pattern_notes:
            lines.append(
                "**8. D9 potvrda.** D9 (Navamsha) potvrđuje da barem dio ovih tema NIJE površan - "
                "ponovljeno je u obje karte: " + "; ".join(navamsha_result.repeated_pattern_notes[:3])
            )
        else:
            lines.append(
                "**8. D9 potvrda.** D9 (Navamsha) ovdje NE potvrđuje snažne ponovljene obrasce iz D1 - "
                "to ne znači da je veza površna, samo da ovaj DODATNI sloj potvrde nedostaje."
            )
    else:
        lines.append("**8. D9 potvrda.** D9 (Navamsha) sinastrija nije uključena u ovaj izračun.")

    lines.append(
        f"**9. Praktična održivost** (rezultat: {_score_bucket(practical.score) if practical else 'nepoznato'}, "
        f"{round(practical.score) if practical else '-'}/100). Praktična kompatibilnost promatra svakodnevnu "
        "funkcionalnost odnosa, neovisno o intenzitetu privlačnosti ili karmičke povezanosti - visok intenzitet "
        "NE jamči visoku praktičnu održivost, niti obrnuto."
    )

    marriage = cats.get("Bračni potencijal")
    if marriage is not None:
        if marriage.score >= 80 and marriage.independent_layers < 4:
            marriage_note = (
                f"Bračni potencijal postoji ({round(marriage.score)}/100), ALI je uvjetovan - nema (još) "
                "dovoljno neovisnih slojeva potvrde da bi se prikazao kao gotovo siguran."
            )
        else:
            marriage_note = f"Bračni potencijal: {round(marriage.score)}/100 (pouzdanost: {marriage.confidence})."
        lines.append(f"   _Bračni potencijal:_ {marriage_note}")

    lines.append(
        "**10. Ograničenje.** Sinastrija pokazuje strukturni POTENCIJAL i teme odnosa - NE govori što "
        "bilo koja od osoba TRENUTNO želi, koliko su spremne za odnos, ili jesu li trenutno slobodne."
    )
    lines.append(
        "**11. Vremenska napomena.** Ovaj izvještaj je natalna (statička) sinastrija - za pitanje "
        "\"kada\" (hoće li se odnos aktivirati, produbiti ili zakomplicirati u određenom razdoblju) "
        "potrebno je zasebno analizirati Vimshottari Dashu, tranzite i Varshaphalu (godišnju kartu) "
        "obiju osoba."
    )
    return lines


def build_basic_report(
    person_a_name: str, person_a_birth: str,
    person_b_name: str, person_b_birth: str,
    ctx_a: NatalContext, ctx_b: NatalContext,
    relationship_type: str,
    config: SynastryConfig,
    overlay_a_to_b: List[HouseOverlayRow],
    overlay_b_to_a: List[HouseOverlayRow],
    mutual_notes: List[str],
    drishti_a_to_b: List[GrahaDrishtiContact],
    drishti_b_to_a: List[GrahaDrishtiContact],
    conjunctions: List[ConjunctionContact],
    nakshatra_result: Optional[NakshatraSynastryResult] = None,
    ashtakoota_result: Optional[AshtakootaResult] = None,
    kuja_comparison: Optional[KujaDoshaComparison] = None,
    significators_result: Optional[RelationshipSignificatorsResult] = None,
    navamsha_result: Optional[VargaSynastryResult] = None,
    score_result: Optional[SynastryScoreResult] = None,
    relationship_profile=None,   # core.synastry.relationship_profiles.RelationshipProfile, opcionalno
) -> str:
    lines: List[str] = []
    lines.append(f"# SINASTRIJA - {person_a_name} i {person_b_name}")
    lines.append("")
    lines.append("## 1. Osnovni podaci")
    lines.append(f"- Osoba A: {person_a_name}, {person_a_birth}")
    lines.append(f"- Osoba B: {person_b_name}, {person_b_birth}")
    lines.append(f"- Vrsta odnosa (utječe na naglasak tumačenja, ne na astronomski izračun): {relationship_type}")
    lines.append(
        f"- Ascendent A: {RASHI[ctx_a.ascendant_sign_index]} · Ascendent B: {RASHI[ctx_b.ascendant_sign_index]}"
    )
    lines.append("")

    lines.append("## 2. Metodologija i aktivne postavke")
    lines.append(
        "Svi izračuni koriste isti astronomski temelj kao natalna karta u ovoj aplikaciji: "
        "sideralni zodijak, Lahiri ayanamsha, Mean Node za Rahu/Ketu, Whole Sign kuće "
        "(uz Bhava Chalit kao dodatni prikaz)."
    )
    for k, v in config.settings_summary().items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## 3. Kućni overlay (D1)")
    lines.append(
        "**Tradicionalno pravilo:** planet koji pada u kuću druge osobe unosi svoju temu u "
        "TO područje života te osobe - smjer je važan (A→B nije isto što i B→A)."
    )
    lines.append("")
    lines.extend(_format_overlay_section(overlay_a_to_b, "A", "B"))
    lines.extend(_format_overlay_section(overlay_b_to_a, "B", "A"))

    lines.append("### Uzajamni (ponavljajući) obrasci")
    if mutual_notes:
        for n in mutual_notes:
            lines.append(f"- {n}")
    else:
        lines.append("_Nije pronađen izravan uzajamni obrazac istog planeta u oba smjera._")
    lines.append("")

    lines.append("## 4. Graha Drishti (planetarni aspekti između karata)")
    lines.append(
        "**Tradicionalno pravilo (BPHS):** svih 7 klasičnih grahe baca puni aspekt na 7. kuću "
        "od sebe; Mars dodatno na 4./8., Jupiter na 5./9., Saturn na 3./10. (vidi core/aspects.py)."
    )
    lines.append("")
    lines.append(f"### {person_a_name} → {person_b_name}")
    lines.extend(_format_drishti_section(drishti_a_to_b))
    lines.append(f"### {person_b_name} → {person_a_name}")
    lines.extend(_format_drishti_section(drishti_b_to_a))

    lines.append("## 5. Stupanjske konjunkcije")
    lines.extend(_format_conjunction_section(conjunctions))

    section_num = 6
    if nakshatra_result is not None:
        lines.append(f"## {section_num}. Nakšatra sinastrija")
        lines.extend(_format_nakshatra_section(nakshatra_result))
        section_num += 1

    if ashtakoota_result is not None:
        lines.append(f"## {section_num}. Ashtakoota (Guna Milan)")
        lines.extend(_format_ashtakoota_section(ashtakoota_result))
        section_num += 1

    if kuja_comparison is not None:
        lines.append(f"## {section_num}. Kuja (Mangal) Dosha")
        lines.extend(_format_kuja_dosha_section(kuja_comparison))
        section_num += 1

    if significators_result is not None:
        lines.append(f"## {section_num}. Ključni signifikatori (7. kuća, DK/AK, UL, A7)")
        lines.extend(_format_significators_section(significators_result))
        section_num += 1

    if navamsha_result is not None:
        lines.append(f"## {section_num}. D9 (Navamsha) sinastrija")
        lines.extend(_format_navamsha_section(navamsha_result))
        section_num += 1

    if score_result is not None:
        lines.append(f"## {section_num}. Kategorijsko bodovanje")
        lines.extend(_format_scoring_section(score_result))
        section_num += 1

    lines.append(f"## {section_num}. Zaključak")
    section_num += 1
    lines.extend(build_relationship_summary(
        person_a_name, person_b_name, relationship_profile,
        score_result, kuja_comparison, ashtakoota_result, navamsha_result,
    ))
    lines.append("")

    lines.append(f"## {section_num}. Tehnički dodatak")
    lines.append(f"- Verzija algoritma (sinastrija): {VERSION}")
    lines.append(f"- Sustav kuća: Whole Sign (osnovni), Bhava Chalit (dodatni)")
    lines.append(f"- Ayanamsha: Lahiri · Čvorovi: Mean Node")
    lines.append(f"- Broj kućnih overlay redaka: {len(overlay_a_to_b) + len(overlay_b_to_a)}")
    lines.append(f"- Broj Graha Drishti kontakata: {len(drishti_a_to_b) + len(drishti_b_to_a)}")
    lines.append(f"- Broj konjunkcija: {len(conjunctions)}")
    if ashtakoota_result is not None:
        lines.append(f"- Ashtakoota ukupno: {ashtakoota_result.total_points:.1f}/{ashtakoota_result.max_points:.0f}")

    return "\n".join(lines)
