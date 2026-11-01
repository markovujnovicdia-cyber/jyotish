import Foundation

/// Twenty numeric saham longitudes, translated from `core/sahams.py`.
/// Vivaha/Putra retain the source's fixed day/night convention and +30° arc correction.
public enum Sahams {
    public static let order = ["Punya", "Vidya", "Yasha", "Mitra", "Vivaha", "Preeti", "Putra", "Karma", "Vyapara", "Artha", "Labha", "Roga", "Matri", "Pitri", "Bandhu", "Bhratri", "Rajya", "Sastra", "Sraddha", "Paradesa"]

    public static func arc(_ a: Double, _ b: Double, _ c: Double) -> Double {
        let arc = Astro.normalize(a - b)
        let correction = Astro.normalize(c - b) <= arc ? 0.0 : 30.0
        return Astro.normalize(a - b + c + correction)
    }

    public static func calculate(ascendant: Double, positions: [String: PlanetPosition], isDay: Bool) throws -> [String: Double] {
        for name in ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"] {
            guard let position = positions[name], position.longitude.isFinite else {
                throw AnnualError.missingPlanet(name)
            }
        }
        guard ascendant.isFinite else { throw AnnualError.invalidInput("Ascendent mora biti konačan broj.") }
        let asc = Astro.normalize(ascendant)
        let su = positions["Sunce"]!.longitude
        let mo = positions["Mjesec"]!.longitude
        let ma = positions["Mars"]!.longitude
        let me = positions["Merkur"]!.longitude
        let ju = positions["Jupiter"]!.longitude
        let ve = positions["Venera"]!.longitude
        let sa = positions["Saturn"]!.longitude
        func calc(_ a: Double, _ b: Double, _ c: Double? = nil, reverse: Bool = true) -> Double {
            if reverse && !isDay { return arc(b, a, c ?? asc) }
            return arc(a, b, c ?? asc)
        }
        func house(_ number: Int) -> Double { Astro.normalize(asc + Double(30 * (number - 1))) }
        func lord(_ number: Int) -> Double { positions[Astro.signLords[Int(house(number) / 30)]]!.longitude }
        let punya = calc(mo, su)
        let sastra = calc(ju, sa, me)
        return [
            "Punya": punya, "Vidya": calc(su, mo), "Yasha": calc(ju, punya),
            "Mitra": calc(ju, punya, ve), "Vivaha": calc(ve, sa, reverse: false),
            "Preeti": calc(sastra, punya), "Putra": calc(ju, mo, reverse: false),
            "Karma": calc(ma, me), "Vyapara": calc(ma, sa, reverse: false),
            "Artha": calc(house(2), lord(2), reverse: false),
            "Labha": calc(house(11), lord(11), reverse: false), "Roga": calc(asc, mo),
            "Matri": calc(mo, ve), "Pitri": calc(sa, su), "Bandhu": calc(me, mo),
            "Bhratri": calc(ju, sa, reverse: false), "Rajya": calc(sa, su),
            "Sastra": sastra, "Sraddha": calc(ve, ma),
            "Paradesa": calc(house(9), lord(9), reverse: false)
        ]
    }
}
