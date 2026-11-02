import Foundation

public enum TransitError: LocalizedError {
    case missingPlanet(String)
    case invalidPosition(String)
    case invalidReference

    public var errorDescription: String? {
        switch self {
        case .missingPlanet(let name): return "Nedostaje položaj planeta \(name) za usporedbu tranzita."
        case .invalidPosition(let name): return "Nevaljan položaj ili brzina planeta \(name)."
        case .invalidReference: return "Natalna lagna i Mjesec moraju imati konačne dužine."
        }
    }
}

/// Numerical rows from OriginalPython/core/transits.py. No interpretations are
/// attached to the highlighted planets or either house reference.
public struct TransitRow: Codable, Equatable, Sendable, Identifiable {
    public let planet: String
    public let sign: String
    public let degreeInSign: Double
    public let longitude: Double
    public let houseFromAscendant: Int
    public let houseFromMoon: Int
    public let isRetrograde: Bool
    public let highlighted: Bool
    public var id: String { planet }
}

public enum Transits {
    public static let highlightedPlanets = ["Saturn", "Jupiter", "Rahu", "Ketu", "Mars"]

    public static func calculate(natal: Chart, transit: Chart) throws -> [TransitRow] {
        // The comparison UI also displays natal positions, so validate both
        // dictionaries before any sign-index conversion can reach Int(NaN).
        try validate(natal.positions)
        return try calculate(positions: transit.positions,
                             natalAscendantLongitude: natal.ascendantLongitude,
                             natalMoonLongitude: natal.positions["Mjesec"]!.longitude)
    }

    public static func calculate(positions: [String: PlanetPosition],
                                 natalAscendantLongitude: Double,
                                 natalMoonLongitude: Double) throws -> [TransitRow] {
        guard natalAscendantLongitude.isFinite, natalMoonLongitude.isFinite else {
            throw TransitError.invalidReference
        }
        try validate(positions)
        let ascendantSign = Int(Astro.normalize(natalAscendantLongitude) / 30)
        let moonSign = Int(Astro.normalize(natalMoonLongitude) / 30)
        return Astro.planetOrder.map { name in
            let position = positions[name]!
            return TransitRow(planet: name, sign: position.sign, degreeInSign: position.degree,
                              longitude: position.longitude,
                              houseFromAscendant: Astro.house(sign: position.signIndex, ascendantSign: ascendantSign),
                              houseFromMoon: Astro.house(sign: position.signIndex, ascendantSign: moonSign),
                              isRetrograde: position.isRetrograde,
                              highlighted: highlightedPlanets.contains(name))
        }
    }

    private static func validate(_ positions: [String: PlanetPosition]) throws {
        for name in Astro.planetOrder {
            guard let position = positions[name] else { throw TransitError.missingPlanet(name) }
            guard position.name == name, position.longitude.isFinite, position.speed.isFinite,
                  position.longitude >= 0, position.longitude < 360 else {
                throw TransitError.invalidPosition(name)
            }
        }
    }
}
