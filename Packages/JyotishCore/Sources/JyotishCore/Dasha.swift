import Foundation

/// Vimshottari year selection is independent of the annual Mudda convention.
/// The supplied PL9 settings select a 365.25-day year and degree-based balance.
public enum VimshottariYearConvention: String, Codable, Sendable {
    case gregorianMean
    case julian

    public var daysPerYear: Double {
        switch self {
        case .gregorianMean: return 365.2425
        case .julian: return 365.25
        }
    }
}

/// Civil duration used to turn the traditional 360 Mudda parts into dates.
/// The supplied PL9 annual report is consistent with a fixed Gregorian year,
/// rather than the varying interval between successive astronomical returns.
public enum MuddaYearConvention: String, Codable, Sendable {
    case solarReturnInterval
    case fixedGregorianYear
}

public struct DashaPeriod: Codable, Equatable, Sendable {
    public let lord: String
    public let start: Date
    public let end: Date

    public init(lord: String, start: Date, end: Date) {
        self.lord = lord
        self.start = start
        self.end = end
    }

    public func contains(_ date: Date) -> Bool { start <= date && date < end }
}

/// The Python-compatible default year is 365.2425 days; callers can select
/// 365.25 days. The full first mahadasha is retained even before birth.
public enum Dasha {
    public static let daysPerYear = 365.2425
    public static let lordOrder = ["Ketu", "Venera", "Sunce", "Mjesec", "Mars", "Rahu", "Jupiter", "Saturn", "Merkur"]
    public static let lordYears: [String: Double] = [
        "Ketu": 7, "Venera": 20, "Sunce": 6, "Mjesec": 10, "Mars": 7,
        "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Merkur": 17
    ]
    public static let muddaLordOrder = ["Sunce", "Mjesec", "Mars", "Rahu", "Jupiter", "Saturn", "Merkur", "Ketu", "Venera"]

    private static func order(from lord: String) throws -> [String] {
        guard let index = lordOrder.firstIndex(of: lord) else {
            throw NatalCalculationError.unknownLord(lord)
        }
        return Array(lordOrder[index...]) + Array(lordOrder[..<index])
    }

    // Python timedelta rounds each duration to the nearest microsecond.
    private static func add(_ seconds: Double, to date: Date) -> Date {
        date.addingTimeInterval((seconds * 1_000_000).rounded(.toNearestOrEven) / 1_000_000)
    }

    public static func mahadashas(moonLongitude: Double, birthDate: Date,
                                  yearsToCover: Double = 120,
                                  yearConvention: VimshottariYearConvention = .gregorianMean) throws -> [DashaPeriod] {
        guard birthDate.timeIntervalSince1970.isFinite, yearsToCover.isFinite,
              yearsToCover > 0, yearsToCover <= 10_000 else {
            throw NatalCalculationError.invalidPeriod
        }
        let nakshatra = try Nakshatra.at(longitude: moonLongitude)
        let rotated = try order(from: nakshatra.lord)
        let elapsedYears = lordYears[nakshatra.lord]! * nakshatra.fractionElapsed
        let yearDays = yearConvention.daysPerYear
        var cursor = add(-elapsedYears * yearDays * 86400, to: birthDate)
        let horizon = add(yearsToCover * yearDays * 86400, to: birthDate)
        var periods: [DashaPeriod] = []
        var index = 0
        while cursor < horizon {
            let lord = rotated[index % rotated.count]
            let end = add(lordYears[lord]! * yearDays * 86400, to: cursor)
            periods.append(DashaPeriod(lord: lord, start: cursor, end: end))
            cursor = end
            index += 1
        }
        return periods
    }

    public static func subperiods(parent: DashaPeriod) throws -> [DashaPeriod] {
        guard parent.start.timeIntervalSince1970.isFinite,
              parent.end.timeIntervalSince1970.isFinite, parent.end > parent.start else {
            throw NatalCalculationError.invalidPeriod
        }
        let rotated = try order(from: parent.lord)
        let duration = parent.end.timeIntervalSince(parent.start)
        var cursor = parent.start
        var periods: [DashaPeriod] = []
        for (index, lord) in rotated.enumerated() {
            let end = index == rotated.count - 1 ? parent.end
                : add(duration * (lordYears[lord]! / 120), to: cursor)
            periods.append(DashaPeriod(lord: lord, start: cursor, end: end))
            cursor = end
        }
        return periods
    }

    public static func current(in periods: [DashaPeriod], at date: Date) throws -> DashaPeriod {
        guard let period = periods.first(where: { $0.contains(date) }) else {
            throw NatalCalculationError.outsideDashaRange
        }
        return period
    }

    /// Ordered Maha, Antar, Pratyantar, Sookshma, Prana, with half-open boundaries.
    public static func currentFiveLevels(moonLongitude: Double, birthDate: Date,
                                          at date: Date,
                                          yearConvention: VimshottariYearConvention = .gregorianMean) throws -> [DashaPeriod] {
        guard date.timeIntervalSince1970.isFinite else { throw NatalCalculationError.invalidDate }
        let years = max(120, date.timeIntervalSince(birthDate) / (86400 * yearConvention.daysPerYear) + 1)
        let sequence = try mahadashas(moonLongitude: moonLongitude, birthDate: birthDate,
                                     yearsToCover: years, yearConvention: yearConvention)
        var parent = try current(in: sequence, at: date)
        var result = [parent]
        for _ in 0..<4 {
            parent = try current(in: subperiods(parent: parent), at: date)
            result.append(parent)
        }
        return result
    }

    public static func muddaStartingLord(natalMoonLongitude: Double, completedYears: Int) throws -> String {
        let nakshatraNumber = try Nakshatra.at(longitude: natalMoonLongitude).index + 1
        // Reduce separately to avoid arithmetic overflow for arbitrary caller integers.
        let remainder = NatalMath.modulo(NatalMath.modulo(completedYears, 9) + nakshatraNumber - 2, 9)
        return muddaLordOrder[NatalMath.modulo(remainder - 1, 9)]
    }

    /// Without end, preserve the legacy 360 civil-day convention. Supplying the
    /// next solar return proportionally scales the same 360 parts to that date.
    public static func mudda(natalMoonLongitude: Double, completedYears: Int,
                             start: Date, end: Date? = nil,
                             yearConvention: MuddaYearConvention = .solarReturnInterval) throws -> [DashaPeriod] {
        guard start.timeIntervalSince1970.isFinite,
              end == nil || (end!.timeIntervalSince1970.isFinite && end! > start) else {
            throw NatalCalculationError.invalidPeriod
        }
        let annualDays = muddaYearDays(start: start, end: end, convention: yearConvention)
        let scale = annualDays / 360
        let startingLord = try muddaStartingLord(natalMoonLongitude: natalMoonLongitude,
                                                 completedYears: completedYears)
        let remainingFraction = 1 - (try Nakshatra.at(longitude: natalMoonLongitude)).fractionElapsed
        let rotated = try order(from: startingLord)
        var periods: [DashaPeriod] = []
        var cursor = start
        var totalDays = 0.0
        var index = 0
        while totalDays < 360 - 1e-6 {
            let lord = rotated[index % rotated.count]
            let fullDays = lordYears[lord]! * 3
            var duration = index == 0 ? fullDays * remainingFraction : fullDays
            if totalDays + duration > 360 { duration = 360 - totalDays }
            let next = add(duration * scale * 86400, to: cursor)
            periods.append(DashaPeriod(lord: lord, start: cursor, end: next))
            cursor = next
            totalDays += duration
            index += 1
        }
        if yearConvention == .solarReturnInterval, let end, let last = periods.last {
            periods[periods.count - 1] = DashaPeriod(lord: last.lord, start: last.start, end: end)
        }
        return periods
    }

    /// Preserve the already-elapsed phase of the first major period instead of
    /// distributing nine new subperiods over its shortened visible balance.
    /// The final, truncated major period is likewise clipped without rescaling.
    public static func muddaSubperiods(parent: DashaPeriod, natalMoonLongitude: Double,
                                       annualStart: Date, annualEnd: Date? = nil,
                                       yearConvention: MuddaYearConvention = .solarReturnInterval) throws -> [DashaPeriod] {
        guard annualStart.timeIntervalSince1970.isFinite,
              annualEnd == nil || (annualEnd!.timeIntervalSince1970.isFinite && annualEnd! > annualStart),
              parent.start.timeIntervalSince1970.isFinite,
              parent.end.timeIntervalSince1970.isFinite,
              parent.start >= annualStart, parent.end > parent.start,
              let years = lordYears[parent.lord] else {
            throw NatalCalculationError.invalidPeriod
        }
        let phase = try Nakshatra.at(longitude: natalMoonLongitude).fractionElapsed
        let days = muddaYearDays(start: annualStart, end: annualEnd, convention: yearConvention)
        let fullSeconds = years * 3 * days / 360 * 86400
        let fullStart = parent.start == annualStart ? add(-fullSeconds * phase, to: annualStart) : parent.start
        let fullEnd = add(fullSeconds, to: fullStart)
        let full = DashaPeriod(lord: parent.lord, start: fullStart, end: fullEnd)
        return try subperiods(parent: full).compactMap { child in
            let start = max(parent.start, child.start)
            let end = min(parent.end, child.end)
            return end > start ? DashaPeriod(lord: child.lord, start: start, end: end) : nil
        }
    }

    private static func muddaYearDays(start: Date, end: Date?, convention: MuddaYearConvention) -> Double {
        switch convention {
        case .solarReturnInterval: return end.map { $0.timeIntervalSince(start) / 86400 } ?? 360
        case .fixedGregorianYear: return daysPerYear
        }
    }
}
