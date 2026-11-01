import Foundation
import CSwissEphemeris

public enum Astro {
    public static let signs = ["Ovan", "Bik", "Blizanci", "Rak", "Lav", "Djevica", "Vaga", "Škorpion", "Strijelac", "Jarac", "Vodenjak", "Ribe"]
    public static let planetOrder = ["Sunce", "Mjesec", "Mars", "Merkur", "Jupiter", "Venera", "Saturn", "Rahu", "Ketu"]
    public static let signLords = ["Mars", "Venera", "Merkur", "Mjesec", "Sunce", "Merkur", "Venera", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
    public static func normalize(_ value: Double) -> Double {
        let result = value.truncatingRemainder(dividingBy: 360)
        let wrapped = result < 0 ? result + 360 : result
        // Negative subnormal inputs can round up to exactly 360 on addition.
        // Keep the canonical half-open interval safe for sign array indexing.
        return wrapped >= 360 ? 0 : wrapped
    }
    public static func signedDifference(_ value: Double) -> Double { normalize(value + 180) - 180 }
    public static func house(sign: Int, ascendantSign: Int) -> Int { ((sign - ascendantSign) % 12 + 12) % 12 + 1 }
}

public struct PlanetPosition: Codable, Equatable, Sendable {
    public let name: String
    public let longitude: Double
    public let speed: Double
    public var isRetrograde: Bool { speed < 0 }
    public var signIndex: Int { Int(longitude / 30) }
    public var sign: String { Astro.signs[signIndex] }
    public var degree: Double { longitude.truncatingRemainder(dividingBy: 30) }
    public init(name: String, longitude: Double, speed: Double) {
        self.name = name
        self.longitude = Astro.normalize(longitude)
        self.speed = speed
    }
}

public struct Chart: Codable, Sendable {
    public let julianDay: Double
    public let ascendantLongitude: Double
    public let positions: [String: PlanetPosition]
    public var ascendantSign: Int { Int(ascendantLongitude / 30) }
    public init(julianDay: Double, ascendantLongitude: Double, positions: [String: PlanetPosition]) {
        self.julianDay = julianDay
        self.ascendantLongitude = Astro.normalize(ascendantLongitude)
        self.positions = positions
    }
}

public enum EphemerisError: Error, LocalizedError {
    case invalidCoordinates, unsupportedDate, missingResources, calculation(String), unavailableHorizon
    case resourcePathTooLong, resourcePreparation(String), conflictingResourceOverride
    public var errorDescription: String? {
        switch self {
        case .invalidCoordinates: return "Koordinate moraju biti konačne: širina između −90° i 90°, dužina od −180° do 180°."
        case .unsupportedDate: return "Ugrađene efemeride podržavaju datume od 1800. do 2399. godine."
        case .missingResources: return "Ugrađene Swiss Ephemeris datoteke nisu pronađene."
        case .resourcePathTooLong: return "Putanja efemerida je preduga za Swiss Ephemeris, a kratka lokalna mapa nije dostupna."
        case .resourcePreparation(let reason): return "Lokalne efemeride nije moguće pripremiti: \(reason)"
        case .conflictingResourceOverride: return "Varijabla SE_EPHE_PATH nadjačava ugrađene efemeride. Uklonite je iz postavki pokretanja aplikacije."
        case .calculation(let reason): return "Izračun efemerida nije uspio: \(reason)"
        case .unavailableHorizon: return "Izlazak ili zalazak Sunca nije dostupan za ovu lokaciju i datum."
        }
    }
}

/// Swiss Ephemeris owns process-global state. Every C entry is serialized and its
/// resource path/Lahiri mode restored under the same lock. No network is used.
public enum Ephemeris {
    private static let lock = NSRecursiveLock()
    private static let resources = EphemerisResources()
    private static let codes: [(String, Int32)] = [
        ("Sunce", 0), ("Mjesec", 1), ("Mars", 4), ("Merkur", 2),
        ("Jupiter", 5), ("Venera", 3), ("Saturn", 6), ("Rahu", 10)
    ]
    public static var version: String {
        lock.lock(); defer { lock.unlock() }
        return String(cString: jy_version())
    }
    public static let backendDescription = "Swiss Ephemeris · ugrađene efemeride · Lahiri · mean Rahu · Whole Sign"
    public static var licenseNotice: String {
        guard let directory = Bundle.module.url(forResource: "Licenses", withExtension: nil),
              let notice = try? String(contentsOf: directory.appendingPathComponent("Swiss-Ephemeris-NOTICE.txt"), encoding: .utf8),
              let agpl = try? String(contentsOf: directory.appendingPathComponent("AGPL-3.0.txt"), encoding: .utf8) else {
            return "Swiss Ephemeris: GNU AGPL v3 ili Professional License. Licencni tekstovi nisu pronađeni u paketu aplikacije."
        }
        return notice + "\n\n" + agpl
    }
    public static func julianDay(date: Date) -> Double { date.timeIntervalSince1970 / 86400 + 2440587.5 }
    public static func date(julianDay: Double) -> Date { Date(timeIntervalSince1970: (julianDay - 2440587.5) * 86400) }

    private static func configure(julianDay: Double) throws {
        // Gregorian 1800-01-01 through 2400-01-01 (exclusive).
        guard julianDay.isFinite, julianDay >= 2378496.5, julianDay < 2597641.5 else { throw EphemerisError.unsupportedDate }
        guard let source = Bundle.module.url(forResource: "Ephemeris", withExtension: nil) else {
            throw EphemerisError.missingResources
        }
        let directory = try resources.directory(bundleDirectory: source)
        let status = directory.path.withCString { jy_set_path($0) }
        if status == -2 { throw EphemerisError.conflictingResourceOverride }
        guard status == 0 else { throw EphemerisError.resourcePathTooLong }
    }
    private static func coordinates(_ latitude: Double, _ longitude: Double) throws {
        guard latitude.isFinite, longitude.isFinite, latitude > -90, latitude < 90,
              longitude >= -180, longitude <= 180 else { throw EphemerisError.invalidCoordinates }
    }
    private static func values(julianDay: Double, body: Int32) throws -> [Double] {
        var output = [Double](repeating: 0, count: 6)
        var error = [CChar](repeating: 0, count: 256)
        let status = jy_calc(julianDay, body, &output, &error)
        guard status >= 0 else { throw EphemerisError.calculation(String(cString: error)) }
        // Never silently replace bundled Swiss data with Moshier/JPL results.
        guard status & 2 != 0 else { throw EphemerisError.calculation("Swiss datoteke nisu korištene: \(String(cString: error))") }
        guard output.allSatisfy(\.isFinite) else { throw EphemerisError.calculation("Nekonačan položaj") }
        return output
    }
    public static func positions(julianDay: Double) throws -> [String: PlanetPosition] {
        lock.lock(); defer { lock.unlock() }
        try configure(julianDay: julianDay)
        var result: [String: PlanetPosition] = [:]
        for (name, code) in codes {
            let output = try values(julianDay: julianDay, body: code)
            result[name] = PlanetPosition(name: name, longitude: output[0], speed: output[3])
        }
        if let rahu = result["Rahu"] {
            result["Ketu"] = PlanetPosition(name: "Ketu", longitude: rahu.longitude + 180, speed: rahu.speed)
        }
        return result
    }
    public static func ascendant(julianDay: Double, latitude: Double, longitude: Double) throws -> Double {
        lock.lock(); defer { lock.unlock() }
        try coordinates(latitude, longitude)
        try configure(julianDay: julianDay)
        var ascendant = 0.0
        guard jy_ascendant(julianDay, latitude, longitude, &ascendant) >= 0, ascendant.isFinite else {
            throw EphemerisError.calculation("Ascendent nije dostupan")
        }
        return Astro.normalize(ascendant)
    }
    public static func chart(date: Date, latitude: Double, longitude: Double) throws -> Chart {
        let jd = julianDay(date: date)
        return try Chart(julianDay: jd, ascendantLongitude: ascendant(julianDay: jd, latitude: latitude, longitude: longitude), positions: positions(julianDay: jd))
    }
    public static func sunLongitude(julianDay: Double) throws -> Double {
        lock.lock(); defer { lock.unlock() }
        try configure(julianDay: julianDay)
        return Astro.normalize(try values(julianDay: julianDay, body: 0)[0])
    }
    public static func isDaytime(julianDay: Double, latitude: Double, longitude: Double) throws -> Bool {
        lock.lock(); defer { lock.unlock() }
        try coordinates(latitude, longitude)
        try configure(julianDay: julianDay)
        var altitude = 0.0
        var error = [CChar](repeating: 0, count: 256)
        let status = jy_daytime(julianDay, latitude, longitude, &altitude, &error)
        guard status >= 0, status & 2 != 0, altitude.isFinite else {
            throw EphemerisError.calculation(String(cString: error))
        }
        return altitude >= 0
    }
    public static func riseOrSet(julianDay: Double, latitude: Double, longitude: Double, isRise: Bool) throws -> Double {
        lock.lock(); defer { lock.unlock() }
        try coordinates(latitude, longitude)
        try configure(julianDay: julianDay)
        var result = 0.0
        var error = [CChar](repeating: 0, count: 256)
        guard jy_rise_set(julianDay, latitude, longitude, isRise ? 1 : 0, &result, &error) >= 0, result.isFinite else {
            throw EphemerisError.unavailableHorizon
        }
        return result
    }
    public static func sunriseSunset(julianDay: Double, latitude: Double, longitude: Double) throws -> (sunrise: Double, sunset: Double) {
        try (riseOrSet(julianDay: julianDay - 0.5, latitude: latitude, longitude: longitude, isRise: true),
             riseOrSet(julianDay: julianDay - 0.5, latitude: latitude, longitude: longitude, isRise: false))
    }
}
