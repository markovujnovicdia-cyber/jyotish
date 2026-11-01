import Foundation

public struct GulikaResult: Codable, Sendable {
    public let longitude: Double
    public let isDayBirth: Bool
    public let segmentNumber: Int
    /// Monday = 0 … Sunday = 6, matching Python datetime.weekday().
    public let weekdayForLord: Int
    public let periodStart: Date
    public let mandiLongitude: Double?
    /// Fixed ghatika method retained separately from the seasonal Gulika method.
    public let mandiGhatikas: Double?
}

public struct NatalSpecialPoints: Codable, Sendable {
    public let arudhaSign: Int
    public let upapadaSign: Int
    public let darapadaSign: Int
    public let bhriguBinduLongitude: Double
    public let gulika: GulikaResult?
    /// Polar-night / unavailable horizon-event failures remain visible as data.
    public let gulikaError: String?
}

/// Mathematical ports of OriginalPython/core/special_points.py; no meanings or
/// astrological interpretations are included in the native model.
public enum SpecialPoints {
    public static func arudha(houseSign: Int, positions: [String: PlanetPosition]) throws -> Int {
        let sign = NatalMath.modulo(houseSign, 12)
        let lord = Astro.signLords[sign]
        guard let lordPosition = positions[lord] else {
            throw NatalCalculationError.missingPlanet(lord)
        }
        guard lordPosition.longitude.isFinite else { throw NatalCalculationError.nonFiniteLongitude }
        let distance = NatalMath.modulo(lordPosition.signIndex - sign, 12)
        var result = (lordPosition.signIndex + distance) % 12
        if result == sign { result = (sign + 9) % 12 }
        else if result == (sign + 6) % 12 { result = (sign + 3) % 12 }
        return result
    }

    /// Preserve the Python FORWARD Rahu-to-Moon arc. Its introductory docstring
    /// calls this the shorter arc, but the implemented formula is the forward arc.
    public static func bhriguBindu(moonLongitude: Double, rahuLongitude: Double) throws -> Double {
        let moon = try NatalMath.longitude(moonLongitude)
        let rahu = try NatalMath.longitude(rahuLongitude)
        return Astro.normalize(rahu + Astro.normalize(moon - rahu) / 2)
    }

    public static func compute(chart: Chart, localDate: String, latitude: Double,
                                longitude: Double) throws -> NatalSpecialPoints {
        guard let moon = chart.positions["Mjesec"] else {
            throw NatalCalculationError.missingPlanet("Mjesec")
        }
        guard let rahu = chart.positions["Rahu"] else {
            throw NatalCalculationError.missingPlanet("Rahu")
        }
        let al = try arudha(houseSign: chart.ascendantSign, positions: chart.positions)
        let ul = try arudha(houseSign: (chart.ascendantSign + 11) % 12, positions: chart.positions)
        let a7 = try arudha(houseSign: (chart.ascendantSign + 6) % 12, positions: chart.positions)
        let bp = try bhriguBindu(moonLongitude: moon.longitude, rahuLongitude: rahu.longitude)
        do {
            let result = try gulika(julianDay: chart.julianDay, localDate: localDate,
                                    latitude: latitude, longitude: longitude)
            return NatalSpecialPoints(arudhaSign: al, upapadaSign: ul, darapadaSign: a7,
                                      bhriguBinduLongitude: bp, gulika: result, gulikaError: nil)
        } catch {
            return NatalSpecialPoints(arudhaSign: al, upapadaSign: ul, darapadaSign: a7,
                                      bhriguBinduLongitude: bp, gulika: nil,
                                      gulikaError: error.localizedDescription)
        }
    }

    private static func weekday(localDate: String) throws -> Int {
        let parts = localDate.split(separator: "-")
        guard parts.count == 3, let year = Int(parts[0]), let month = Int(parts[1]),
              let day = Int(parts[2]) else { throw NatalCalculationError.invalidDate }
        let components = DateComponents(year: year, month: month, day: day)
        let calendar = NatalMath.utcCalendar
        guard let date = calendar.date(from: components),
              calendar.component(.year, from: date) == year,
              calendar.component(.month, from: date) == month,
              calendar.component(.day, from: date) == day else { throw NatalCalculationError.invalidDate }
        // Foundation: Sunday 1; Python: Monday 0.
        return (calendar.component(.weekday, from: date) + 5) % 7
    }

    private static func minuteDate(julianDay: Double) -> Date {
        let date = Ephemeris.date(julianDay: julianDay)
        return Date(timeIntervalSince1970: floor(date.timeIntervalSince1970 / 60) * 60)
    }

    /// Exactly preserves the Python wrapper's sunrise search and minute-truncated
    /// horizon-event times, even though Swiss Ephemeris provides finer precision.
    public static func gulika(julianDay: Double, localDate: String, latitude: Double,
                               longitude: Double) throws -> GulikaResult {
        guard julianDay.isFinite else { throw NatalCalculationError.invalidDate }
        let weekday = try weekday(localDate: localDate)
        func rise(_ date: Double) throws -> Double {
            try Ephemeris.riseOrSet(julianDay: date, latitude: latitude,
                                    longitude: longitude, isRise: true)
        }
        func set(_ date: Double) throws -> Double {
            try Ephemeris.riseOrSet(julianDay: date, latitude: latitude,
                                    longitude: longitude, isRise: false)
        }
        let candidateSunrise = try rise(julianDay - 1.5)
        let candidateSunset = try set(candidateSunrise)
        let sunriseToday: Double
        let sunsetToday: Double
        let previousSunset: Double
        if candidateSunset < julianDay {
            sunriseToday = try rise(candidateSunset)
            sunsetToday = try set(sunriseToday)
            previousSunset = candidateSunset
        } else {
            sunriseToday = candidateSunrise
            sunsetToday = candidateSunset
            previousSunset = try set(candidateSunrise - 1.5)
        }
        let nextSunrise = try rise(sunsetToday)
        return try gulika(birthDate: minuteDate(julianDay: julianDay), weekday: weekday,
                           sunrise: minuteDate(julianDay: sunriseToday),
                           sunset: minuteDate(julianDay: sunsetToday),
                           previousSunset: minuteDate(julianDay: previousSunset),
                           nextSunrise: minuteDate(julianDay: nextSunrise)) { date in
            // Python utc_to_julian_day ignores datetime microseconds.
            let truncated = Date(timeIntervalSince1970: floor(date.timeIntervalSince1970))
            return try Ephemeris.ascendant(julianDay: Ephemeris.julianDay(date: truncated),
                                           latitude: latitude, longitude: longitude)
        }
    }

    /// Testable pure seasonal Gulika segmentation, with Mandi returned as a
    /// distinct fixed-ghatika alternative exactly as in the original wrapper.
    public static func gulika(birthDate: Date, weekday: Int, sunrise: Date, sunset: Date,
                               previousSunset: Date, nextSunrise: Date,
                               ascendantAt: (Date) throws -> Double) throws -> GulikaResult {
        guard (0...6).contains(weekday),
              [birthDate, sunrise, sunset, previousSunset, nextSunrise].allSatisfy({
                  $0.timeIntervalSince1970.isFinite
              }) else { throw NatalCalculationError.invalidDate }
        let isDay = sunrise <= birthDate && birthDate < sunset
        let periodStart: Date
        let periodEnd: Date
        let weekdayForLord: Int
        if isDay {
            periodStart = sunrise
            periodEnd = sunset
            weekdayForLord = weekday
        } else if birthDate >= sunset {
            periodStart = sunset
            periodEnd = nextSunrise
            weekdayForLord = weekday
        } else {
            periodStart = previousSunset
            periodEnd = sunrise
            weekdayForLord = NatalMath.modulo(weekday - 1, 7)
        }
        guard periodEnd > periodStart else { throw NatalCalculationError.invalidPeriod }
        let startLordIndex = (weekdayForLord + 1) % 7
        let sequenceStart = isDay ? startLordIndex : (startLordIndex + 4) % 7
        let segmentIndex = NatalMath.modulo(6 - sequenceStart, 7)
        let segmentStart = periodStart.addingTimeInterval(
            periodEnd.timeIntervalSince(periodStart) / 8 * Double(segmentIndex))
        let dayGhatikas = [22.0, 18, 14, 10, 6, 2, 26]
        let nightGhatikas = [6.0, 2, 26, 22, 18, 14, 10]
        let ghatikas = (isDay ? dayGhatikas : nightGhatikas)[weekdayForLord]
        let mandiDate = periodStart.addingTimeInterval(ghatikas * 24 * 60)
        return GulikaResult(longitude: try ascendantAt(segmentStart), isDayBirth: isDay,
                            segmentNumber: segmentIndex + 1, weekdayForLord: weekdayForLord,
                            periodStart: periodStart, mandiLongitude: try ascendantAt(mandiDate),
                            mandiGhatikas: ghatikas)
    }
}
