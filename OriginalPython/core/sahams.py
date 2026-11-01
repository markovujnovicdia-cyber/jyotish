"""PVR Narasimha Rao, Vedic Astrology: An Integrated Approach, §28.8,
Table 74, pp. 382–384. Uses day/night reversal and the 30° arc correction.
House longitudes use the ascendant degree in each whole-sign house.
Legacy tajika functions remain available to older report modules.
This project uses the fixed day/night Vivaha and Putra variant (Neelakanthi);
other schools reverse them at night. Correction +30° is retained here.
Do not mix this with uncorrected legacy formulas.
"""
from core.constants import RASHI_LORD, RASHI

SAHAM_INFO = {
 'Punya':('PuS','Sreća i zaštita'), 'Vidya':('ViS','Obrazovanje'),
 'Yasha':('YaS','Ugled'), 'Mitra':('MiS','Prijateljstvo'),
 'Vivaha':('VvS','Brak i partnerstvo'), 'Preeti':('PrS','Ljubav i privrženost'),
 'Putra':('PtS','Djeca'), 'Karma':('KaS','Rad i djelovanje'),
 'Vyapara':('VyS','Poslovanje'), 'Artha':('ArS','Novac'),
 'Labha':('LaS','Dobitci'), 'Roga':('RoS','Zdravlje / bolest'),
 'Matri':('MtS','Majka'), 'Pitri':('PiS','Otac'),
 'Bandhu':('BaS','Rođaci'), 'Bhratri':('BhS','Braća i sestre'),
 'Rajya':('RjS','Položaj i vlast'), 'Sastra':('SsS','Znanost'),
 'Sraddha':('SrS','Predanost'), 'Paradesa':('PaS','Inozemstvo'),
}

def saham_arc(a,b,c):
    arc=(a-b)%360
    correction=0 if (c-b)%360 <= arc else 30
    return (a-b+c+correction)%360

def compute_sahams(asc, positions, is_day):
    v={k:p.longitude for k,p in positions.items()}
    def calc(a,b,c=asc,reverse=True):
        if reverse and not is_day: a,b=b,a
        return saham_arc(a,b,c)
    house=lambda n:(asc+30*(n-1))%360
    lord=lambda n:v[RASHI_LORD[RASHI[int(house(n)//30)]]]
    su,mo,ma,me,ju,ve,sa=[v[k] for k in ['Sunce','Mjesec','Mars','Merkur','Jupiter','Venera','Saturn']]
    punya=calc(mo,su);sastra=calc(ju,sa,me)
    return {'Punya':punya,'Vidya':calc(su,mo),'Yasha':calc(ju,punya),
      'Mitra':calc(ju,punya,ve),'Vivaha':calc(ve,sa,reverse=False),'Preeti':calc(sastra,punya),
      'Putra':calc(ju,mo,reverse=False),'Karma':calc(ma,me),'Vyapara':calc(ma,sa,reverse=False),
      'Artha':calc(house(2),lord(2),reverse=False),'Labha':calc(house(11),lord(11),reverse=False),
      'Roga':calc(asc,mo),'Matri':calc(mo,ve),'Pitri':calc(sa,su),'Bandhu':calc(me,mo),
      'Bhratri':calc(ju,sa,reverse=False),'Rajya':calc(sa,su),'Sastra':sastra,
      'Sraddha':calc(ve,ma),'Paradesa':calc(house(9),lord(9),reverse=False)}

def is_daytime(jd, latitude, longitude):
    import swisseph as swe
    solar=swe.calc_ut(jd,swe.SUN)[0]
    return swe.azalt(jd,swe.ECL2HOR,(longitude,latitude,0),0,15,solar[:3])[1] >= 0
