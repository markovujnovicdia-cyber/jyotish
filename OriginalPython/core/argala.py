"""
Argala (protočnost/uplitanje) i Virodhargala (blokada) - klasičan sustav
koji pokazuje "propušta li" kuća svoje obećanje van, ili je blokirana.

Provjereno protiv više neovisnih izvora (uključujući Sanjay Rath), svi se
slažu oko točnog uparivanja:
- Argala iz 2. kuće blokira 12. kuća
- Argala iz 4. kuće blokira 10. kuća
- Argala iz 11. kuće blokira 3. kuća
- Argala iz 5. kuće (sekundarna) blokira 9. kuća

Pravilo: ako planeta u argala-kući ima VIŠE (ili jednako) od planeta u
odgovarajućoj blokirajućoj kući, argala je AKTIVNA; inače je BLOKIRANA.
"""

from dataclasses import dataclass
from typing import Dict, List

_ARGALA_PAIRS = [(2, 12), (4, 10), (11, 3), (5, 9)]


@dataclass
class ArgalaSource:
    argala_house: int
    argala_count: int
    obstruction_house: int
    obstruction_count: int
    active: bool


def compute_argala(house_num: int, planet_count_by_house: Dict[int, int]) -> List[ArgalaSource]:
    """
    house_num: kuća o kojoj je riječ (1-12)
    planet_count_by_house: {broj_kuce: broj_planeta_u_njoj} (whole sign, od ascendenta)
    Vraća listu izvora argale (4 klasična para) s oznakom je li svaki aktivan.
    """
    results = []
    for argala_offset, block_offset in _ARGALA_PAIRS:
        argala_house = ((house_num - 1 + argala_offset - 1) % 12) + 1
        block_house = ((house_num - 1 + block_offset - 1) % 12) + 1

        argala_count = planet_count_by_house.get(argala_house, 0)
        block_count = planet_count_by_house.get(block_house, 0)

        active = argala_count > 0 and argala_count >= block_count

        results.append(ArgalaSource(
            argala_house=argala_house,
            argala_count=argala_count,
            obstruction_house=block_house,
            obstruction_count=block_count,
            active=active,
        ))
    return results


def count_active_argala(house_num: int, planet_count_by_house: Dict[int, int]) -> int:
    """Brz zbroj koliko od 4 moguća izvora argale je trenutno aktivno (za kompaktan prikaz)."""
    return sum(1 for a in compute_argala(house_num, planet_count_by_house) if a.active)
