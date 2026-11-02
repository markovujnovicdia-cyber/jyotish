import Foundation

public enum AshtakavargaError: Error, LocalizedError, Equatable {
    case missingSource(String), invalidSign(String), invalidPlanet(String), invalidLongitude, invalidDegree
    public var errorDescription: String? {
        switch self {
        case .missingSource(let name): return "Nedostaje Ashtakavarga izvor: \(name)."
        case .invalidSign(let name): return "Indeks znaka izvora \(name) mora biti između 0 i 11."
        case .invalidPlanet(let name): return "Ashtakavarga se računa za sedam klasičnih planeta, bez \(name)."
        case .invalidLongitude: return "Ashtakavarga zahtijeva konačne dužine između 0° i 360°."
        case .invalidDegree: return "Stupanj za Kakshyu mora biti konačan broj između 0° i 30°."
        }
    }
}

/// Unreduced Bhinna/Sarva tables from the unchanged Python reference.
/// Every row is ordered by zodiac sign (0 = Aries), not by natal house.
public struct AshtakavargaResult: Codable, Equatable, Sendable {
    public let bhinna: [String: [Int]]
    public let sarva: [Int]
    public let sourceSigns: [String: Int]
    public var total: Int { sarva.reduce(0, +) }
}

/// Exact port of OriginalPython/core/ashtakavarga.py. No predictive labels or
/// reductions are applied. Rahu/Ketu are not scoring planets or contributors.
public enum Ashtakavarga {
    public static let planetOrder = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn"]
    public static let sourceOrder = planetOrder + ["Lagna"]
    public static let totalBindus = ["Sunce": 48, "Mjesec": 49, "Mars": 39, "Merkur": 54,
                                     "Jupiter": 56, "Venera": 52, "Saturn": 39]
    public static let kakshyaOrder = ["Saturn", "Jupiter", "Mars", "Sunce", "Venera", "Merkur", "Mjesec", "Lagna"]
    public static let kakshyaSpan = 30.0 / 8.0

    private static let beneficPlaces: [String: [String: [Int]]] = [
        "Sunce": [
            "Sunce": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mjesec": [3, 6, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Merkur": [3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [5, 6, 9, 11],
            "Venera": [6, 7, 12],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
            "Lagna": [3, 4, 6, 10, 11, 12],
        ],
        "Mjesec": [
            "Sunce": [3, 6, 7, 8, 10, 11],
            "Mjesec": [1, 3, 6, 7, 10, 11],
            "Mars": [2, 3, 5, 6, 9, 10, 11],
            "Merkur": [1, 3, 4, 5, 7, 8, 10, 11],
            "Jupiter": [1, 4, 7, 8, 10, 11, 12],
            "Venera": [3, 4, 5, 7, 9, 10, 11],
            "Saturn": [3, 5, 6, 11],
            "Lagna": [3, 6, 10, 11],
        ],
        "Mars": [
            "Sunce": [3, 5, 6, 10, 11],
            "Mjesec": [3, 6, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Merkur": [3, 5, 6, 11],
            "Jupiter": [6, 10, 11, 12],
            "Venera": [6, 8, 11, 12],
            "Saturn": [1, 4, 7, 8, 9, 10, 11],
            "Lagna": [1, 3, 6, 10, 11],
        ],
        "Merkur": [
            "Sunce": [5, 6, 9, 11, 12],
            "Mjesec": [2, 4, 6, 8, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Merkur": [1, 3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [6, 8, 11, 12],
            "Venera": [1, 2, 3, 4, 5, 8, 9, 11],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
            "Lagna": [1, 2, 4, 6, 8, 10, 11],
        ],
        "Jupiter": [
            "Sunce": [1, 2, 3, 4, 7, 8, 9, 10, 11],
            "Mjesec": [2, 5, 7, 9, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Merkur": [1, 2, 4, 5, 6, 9, 10, 11],
            "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
            "Venera": [2, 5, 6, 9, 10, 11],
            "Saturn": [3, 5, 6, 12],
            "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11],
        ],
        "Venera": [
            "Sunce": [8, 11, 12],
            "Mjesec": [1, 2, 3, 4, 5, 8, 9, 11, 12],
            "Mars": [3, 5, 6, 9, 11, 12],
            "Merkur": [3, 5, 6, 9, 11],
            "Jupiter": [5, 8, 9, 10, 11],
            "Venera": [1, 2, 3, 4, 5, 8, 9, 10, 11],
            "Saturn": [3, 4, 5, 8, 9, 10, 11],
            "Lagna": [1, 2, 3, 4, 5, 8, 9, 11],
        ],
        "Saturn": [
            "Sunce": [1, 2, 4, 7, 8, 10, 11],
            "Mjesec": [3, 6, 11],
            "Mars": [3, 5, 6, 10, 11, 12],
            "Merkur": [6, 8, 9, 10, 11, 12],
            "Jupiter": [5, 6, 11, 12],
            "Venera": [6, 11, 12],
            "Saturn": [3, 5, 6, 11],
            "Lagna": [1, 3, 4, 6, 10, 11],
        ],
    ]

    private static func validatedSources(_ sourceSigns: [String: Int]) throws -> [String: Int] {
        var result: [String: Int] = [:]
        for name in sourceOrder {
            guard let sign = sourceSigns[name] else { throw AshtakavargaError.missingSource(name) }
            guard (0..<12).contains(sign) else { throw AshtakavargaError.invalidSign(name) }
            result[name] = sign
        }
        return result
    }

    public static func calculate(chart: Chart) throws -> AshtakavargaResult {
        guard chart.ascendantLongitude.isFinite, (0..<360).contains(chart.ascendantLongitude) else {
            throw AshtakavargaError.invalidLongitude
        }
        var sources = ["Lagna": Int(chart.ascendantLongitude / 30)]
        for name in planetOrder {
            guard let position = chart.positions[name] else { throw AshtakavargaError.missingSource(name) }
            guard position.longitude.isFinite, (0..<360).contains(position.longitude) else {
                throw AshtakavargaError.invalidLongitude
            }
            sources[name] = Int(position.longitude / 30)
        }
        return try calculate(sourceSigns: sources)
    }

    public static func calculate(sourceSigns: [String: Int]) throws -> AshtakavargaResult {
        let sources = try validatedSources(sourceSigns)
        var rows: [String: [Int]] = [:]
        var totals = [Int](repeating: 0, count: 12)
        for planet in planetOrder {
            var bindus = [Int](repeating: 0, count: 12)
            for source in sourceOrder {
                // Names come from our fixed table, never user-provided indices.
                for house in beneficPlaces[planet]![source]! {
                    let target = (sources[source]! + house - 1) % 12
                    bindus[target] += 1
                }
            }
            rows[planet] = bindus
            for sign in 0..<12 { totals[sign] += bindus[sign] }
        }
        return AshtakavargaResult(bhinna: rows, sarva: totals, sourceSigns: sources)
    }

    /// The source accepts the upper endpoint 30° and assigns the last Kakshya.
    /// Transit positions normally have degreeInSign in the half-open 0..<30 range.
    public static func kakshyaLord(degreeInSign: Double) throws -> String {
        guard degreeInSign.isFinite, (0...30).contains(degreeInSign) else {
            throw AshtakavargaError.invalidDegree
        }
        return kakshyaOrder[min(Int(degreeInSign / kakshyaSpan), 7)]
    }

    public static func isKakshyaActivated(planet: String, signIndex: Int, kakshyaLord: String,
                                         sourceSigns: [String: Int]) throws -> Bool {
        guard let table = beneficPlaces[planet] else { throw AshtakavargaError.invalidPlanet(planet) }
        guard (0..<12).contains(signIndex) else { throw AshtakavargaError.invalidSign(planet) }
        let sources = try validatedSources(sourceSigns)
        guard let offsets = table[kakshyaLord], let sourceSign = sources[kakshyaLord] else {
            throw AshtakavargaError.missingSource(kakshyaLord)
        }
        return offsets.contains { (sourceSign + $0 - 1) % 12 == signIndex }
    }
}
