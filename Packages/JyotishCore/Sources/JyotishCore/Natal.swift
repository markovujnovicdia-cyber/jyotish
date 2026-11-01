import Foundation

public enum NatalCalculationError: Error, LocalizedError, Equatable {
    case nonFiniteLongitude
    case invalidPeriod
    case unknownLord(String)
    case missingPlanet(String)
    case invalidDate
    case outsideDashaRange

    public var errorDescription: String? {
        switch self {
        case .nonFiniteLongitude: return "Dužina mora biti konačan broj."
        case .invalidPeriod: return "Nevaljan vremenski raspon."
        case .unknownLord(let name): return "Nepoznat vladar: \(name)."
        case .missingPlanet(let name): return "Nedostaje položaj planeta: \(name)."
        case .invalidDate: return "Nevaljan datum."
        case .outsideDashaRange: return "Datum je izvan izračunatog raspona daša."
        }
    }
}

/// Helpers preserve Python's modulo and floating floor-division conventions,
/// including the representable-value behavior at nakshatra boundaries.
enum NatalMath {
    static func modulo(_ value: Int, _ divisor: Int) -> Int {
        let result = value % divisor
        return result < 0 ? result + divisor : result
    }

    static func longitude(_ value: Double) throws -> Double {
        guard value.isFinite else { throw NatalCalculationError.nonFiniteLongitude }
        return Astro.normalize(value)
    }

    // CPython _float_div_mod: floor(a / b) alone differs at e.g. 40 // (360/27).
    static func pythonFloorDivision(_ numerator: Double, _ denominator: Double) -> Int {
        var remainder = numerator.truncatingRemainder(dividingBy: denominator)
        var quotient = (numerator - remainder) / denominator
        if remainder != 0, (denominator < 0) != (remainder < 0) {
            remainder += denominator
            quotient -= 1
        }
        guard quotient != 0 else { return 0 }
        var result = floor(quotient)
        if quotient - result > 0.5 { result += 1 }
        return Int(result)
    }

    static var utcCalendar: Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(secondsFromGMT: 0)!
        return calendar
    }
}

public struct NakshatraInfo: Codable, Equatable, Sendable {
    public let name: String
    public let index: Int
    public let pada: Int
    public let lord: String
    public let fractionElapsed: Double
}

public enum Nakshatra {
    public static let arc = 360.0 / 27.0
    public static let padaArc = arc / 4.0
    public static let names = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
        "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]

    /// Exact port of OriginalPython/core/nakshatra.py; names use its spelling.
    public static func at(longitude: Double) throws -> NakshatraInfo {
        let value = try NatalMath.longitude(longitude)
        let index = NatalMath.pythonFloorDivision(value, arc)
        let position = value - Double(index) * arc
        let pada = NatalMath.pythonFloorDivision(position, padaArc) + 1
        return NakshatraInfo(name: names[index], index: index, pada: pada,
                             lord: Dasha.lordOrder[index % 9], fractionElapsed: position / arc)
    }
}

/// All divisional charts present in OriginalPython/core/varga.py.
public enum Varga: Int, CaseIterable, Codable, Identifiable, Sendable {
    case d1 = 1, d7 = 7, d9 = 9, d10 = 10, d12 = 12
    public var id: Int { rawValue }
    public var label: String {
        switch self {
        case .d1: return "D1 · Rāśi"
        case .d7: return "D7 · Saptamsha"
        case .d9: return "D9 · Navamsha"
        case .d10: return "D10 · Dashamsha"
        case .d12: return "D12 · Dvadashamsha"
        }
    }

    public func signIndex(longitude: Double) throws -> Int {
        let value = try NatalMath.longitude(longitude)
        let sign = Int(value / 30)
        let degree = value - Double(sign) * 30
        switch self {
        case .d1: return sign
        case .d9: return Int(value / (30.0 / 9.0)) % 12
        case .d7:
            let start = sign % 2 == 0 ? sign : (sign + 6) % 12
            return (start + Int(degree / (30.0 / 7.0))) % 12
        case .d10:
            let start = sign % 2 == 0 ? sign : (sign + 8) % 12
            return (start + Int(degree / 3)) % 12
        case .d12: return (sign + Int(degree / 2.5)) % 12
        }
    }

    public func positions(chart: Chart) throws -> [String: Int] {
        try chart.positions.mapValues { try signIndex(longitude: $0.longitude) }
    }

    public func ascendantSign(chart: Chart) throws -> Int {
        try signIndex(longitude: chart.ascendantLongitude)
    }
}

public struct NatalResult: Codable, Sendable {
    public let chart: Chart
    public let specialPoints: NatalSpecialPoints
}

public enum Natal {
    /// localDate is the civil birth date (yyyy-MM-dd) in the person's chosen
    /// timezone, as used by the Python Gulika weekday convention.
    public static func compute(date: Date, localDate: String, latitude: Double,
                               longitude: Double) throws -> NatalResult {
        let chart = try Ephemeris.chart(date: date, latitude: latitude, longitude: longitude)
        let points = try SpecialPoints.compute(chart: chart, localDate: localDate,
                                               latitude: latitude, longitude: longitude)
        return NatalResult(chart: chart, specialPoints: points)
    }
}
