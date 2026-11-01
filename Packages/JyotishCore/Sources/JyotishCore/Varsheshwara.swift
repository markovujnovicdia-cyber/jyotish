import Foundation

/// Numerical dignity helpers only. Interpretive planet labels are not generated.
enum PlanetDignity {
    static let friends: [String: Set<String>] = [
        "Sunce": ["Mjesec", "Mars", "Jupiter"], "Mjesec": ["Sunce", "Merkur"],
        "Mars": ["Sunce", "Mjesec", "Jupiter"], "Merkur": ["Sunce", "Venera"],
        "Jupiter": ["Sunce", "Mjesec", "Mars"], "Venera": ["Merkur", "Saturn"],
        "Saturn": ["Merkur", "Venera"]
    ]
    static let enemies: [String: Set<String>] = [
        "Sunce": ["Venera", "Saturn"], "Mjesec": [], "Mars": ["Merkur"], "Merkur": ["Mjesec"],
        "Jupiter": ["Merkur", "Venera"], "Venera": ["Sunce", "Mjesec"], "Saturn": ["Sunce", "Mjesec", "Mars"]
    ]
    static let exaltation: [String: (Int, Double)] = [
        "Sunce": (0, 10), "Mjesec": (1, 3), "Mars": (9, 28), "Merkur": (5, 15),
        "Jupiter": (3, 5), "Venera": (11, 27), "Saturn": (6, 20)
    ]
    static func classify(planet: String, signIndex: Int) -> String {
        guard let (exaltedSign, _) = exaltation[planet] else { return "neutralan" }
        if signIndex == exaltedSign { return "uzvišen" }
        if signIndex == (exaltedSign + 6) % 12 { return "pad" }
        let lord = Astro.signLords[signIndex]
        if lord == planet { return "vlastiti" }
        if friends[planet, default: []].contains(lord) { return "prijateljski" }
        if enemies[planet, default: []].contains(lord) { return "neprijateljski" }
        return "neutralan"
    }
    static func relationshipPoints(planet: String, lord: String, maximum: Double) -> Double {
        if planet == lord { return maximum }
        if friends[planet, default: []].contains(lord) { return maximum * 0.75 }
        if enemies[planet, default: []].contains(lord) { return maximum * 0.25 }
        return maximum * 0.5
    }
    static func uchcha(planet: String, longitude: Double) -> Double {
        guard let (sign, degree) = exaltation[planet] else { return 30 }
        let debilitated = Astro.normalize(Double(sign) * 30 + degree + 180)
        return abs(Astro.signedDifference(longitude - debilitated)) / 3
    }
}

public struct PanchaVargiyaBala: Codable, Equatable, Sendable {
    public let kshetra: Double
    public let uchcha: Double
    public let hadda: Double
    public let drekkana: Double
    public let navamsa: Double
    public var total: Double { (kshetra + uchcha + hadda + drekkana + navamsa) / 4 }
    /// This is the imported Python table, not an independently verified Tajika table.
    public var haddaConvention: String { "Egyptian terms; inherited Python convention" }
}

public struct VarsheshwaraCandidate: Codable, Equatable, Sendable, Identifiable {
    public let role: String
    public let planet: String
    public let strengthScore: Double
    public let aspectsAscendant: Bool
    public let bala: PanchaVargiyaBala
    public var id: String { role }
}

public struct VarsheshwaraResult: Codable, Equatable, Sendable {
    public let candidates: [VarsheshwaraCandidate]
    public let winner: VarsheshwaraCandidate?
    public var anyQualified: Bool { winner != nil }
}

public enum Varsheshwara {
    public static let triplicityDay = ["Sunce", "Venera", "Saturn", "Venera", "Jupiter", "Mjesec", "Merkur", "Mars", "Saturn", "Mars", "Jupiter", "Mjesec"]
    public static let triplicityNight = ["Jupiter", "Mjesec", "Merkur", "Mars", "Sunce", "Venera", "Saturn", "Venera", "Saturn", "Mars", "Jupiter", "Mjesec"]
    // Egyptian terms as supplied in the original Python source. No table substitution.
    private static let hadda: [[(Double, String)]] = [
        [(6,"Jupiter"),(12,"Venera"),(20,"Merkur"),(25,"Mars"),(30,"Saturn")],
        [(8,"Venera"),(15,"Merkur"),(22,"Jupiter"),(26,"Saturn"),(30,"Mars")],
        [(7,"Merkur"),(14,"Jupiter"),(21,"Venera"),(25,"Mars"),(30,"Saturn")],
        [(6,"Mars"),(13,"Venera"),(20,"Merkur"),(27,"Jupiter"),(30,"Saturn")],
        [(6,"Jupiter"),(11,"Venera"),(18,"Saturn"),(24,"Merkur"),(30,"Mars")],
        [(7,"Merkur"),(17,"Venera"),(21,"Jupiter"),(28,"Mars"),(30,"Saturn")],
        [(6,"Saturn"),(14,"Merkur"),(21,"Jupiter"),(28,"Venera"),(30,"Mars")],
        [(7,"Mars"),(11,"Venera"),(19,"Merkur"),(24,"Jupiter"),(30,"Saturn")],
        [(12,"Jupiter"),(17,"Venera"),(21,"Merkur"),(26,"Saturn"),(30,"Mars")],
        [(7,"Merkur"),(14,"Jupiter"),(22,"Venera"),(26,"Saturn"),(30,"Mars")],
        [(7,"Merkur"),(13,"Venera"),(20,"Jupiter"),(25,"Mars"),(30,"Saturn")],
        [(12,"Venera"),(16,"Jupiter"),(19,"Merkur"),(28,"Mars"),(30,"Saturn")]
    ]

    public static func bala(planet: String, longitude: Double) throws -> PanchaVargiyaBala {
        guard Tajika.planets.contains(planet) else { throw TajikaError.invalidPlanet(planet) }
        guard longitude.isFinite else { throw TajikaError.invalidCoordinate }
        let lon = Astro.normalize(longitude)
        let sign = Int(lon / 30), degree = lon.truncatingRemainder(dividingBy: 30)
        let kshetra = PlanetDignity.relationshipPoints(planet: planet, lord: Astro.signLords[sign], maximum: 30)
        let uchcha = PlanetDignity.uchcha(planet: planet, longitude: lon) / 3
        let haddaLord = hadda[sign].first { degree < $0.0 }?.1 ?? hadda[sign].last!.1
        let haddaPoints = PlanetDignity.relationshipPoints(planet: planet, lord: haddaLord, maximum: 15)
        let decan = min(Int(degree / 10), 2)
        let drekkanaLord = Astro.signLords[(sign + decan * 4) % 12]
        let drekkanaPoints = PlanetDignity.relationshipPoints(planet: planet, lord: drekkanaLord, maximum: 10)
        // Identical to core/varga.py's continuous Navamsha formula.
        let navamsaSign = Int(lon / (30.0 / 9.0)) % 12
        let navamsaPoints = PlanetDignity.relationshipPoints(planet: planet, lord: Astro.signLords[navamsaSign], maximum: 5)
        return PanchaVargiyaBala(kshetra: kshetra, uchcha: uchcha, hadda: haddaPoints,
                                drekkana: drekkanaPoints, navamsa: navamsaPoints)
    }

    public static func calculate(natalAscendantSign: Int, munthaSign: Int,
                                  chart: Chart, isDaytime: Bool) throws -> VarsheshwaraResult {
        guard chart.ascendantLongitude.isFinite, (0..<360).contains(chart.ascendantLongitude) else {
            throw TajikaError.invalidCoordinate
        }
        guard [natalAscendantSign, munthaSign, chart.ascendantSign].allSatisfy({ (0..<12).contains($0) }) else {
            throw TajikaError.invalidSign
        }
        for planet in Tajika.planets {
            guard let position = chart.positions[planet] else { throw TajikaError.missingPlanet(planet) }
            guard position.longitude.isFinite, (0..<360).contains(position.longitude) else { throw TajikaError.invalidCoordinate }
        }
        let dayPlanet = chart.positions[isDaytime ? "Sunce" : "Mjesec"]!
        let definitions = [
            ("Janma Lagna Pati", Astro.signLords[natalAscendantSign]),
            ("Muntha Pati", Astro.signLords[munthaSign]),
            ("Varsha Lagna Pati", Astro.signLords[chart.ascendantSign]),
            ("Dina-Ratri Pati", Astro.signLords[dayPlanet.signIndex]),
            ("Tri-Rashi Pati", (isDaytime ? triplicityDay : triplicityNight)[chart.ascendantSign])
        ]
        var candidates: [VarsheshwaraCandidate] = []
        for (role, planet) in definitions {
            let p = chart.positions[planet]!
            let strength = try bala(planet: planet, longitude: p.longitude)
            let aspect = Tajika.aspect(signA: p.signIndex, signB: chart.ascendantSign)
            let qualifies = aspect.map {
                abs(Tajika.residual(longitudeA: p.longitude, longitudeB: chart.ascendantLongitude, aspect: $0)) <= Tajika.deeptamsha[planet]!
            } ?? false
            // Decimal formatting preserves Python round(x, 2)'s treatment of the
            // actual binary Double; multiplying by 100 first can create false ties.
            let rounded = Double(String(format: "%.2f", locale: Locale(identifier: "en_US_POSIX"), strength.total))!
            candidates.append(VarsheshwaraCandidate(role: role, planet: planet, strengthScore: rounded,
                                                    aspectsAscendant: qualifies, bala: strength))
        }
        // Python max retains the first equally scored qualified candidate.
        var winner: VarsheshwaraCandidate?
        for c in candidates where c.aspectsAscendant {
            if winner == nil || c.strengthScore > winner!.strengthScore { winner = c }
        }
        return VarsheshwaraResult(candidates: candidates, winner: winner)
    }
}
