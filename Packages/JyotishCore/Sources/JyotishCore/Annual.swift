import Foundation

public enum AnnualError: LocalizedError, Equatable {
    case invalidInput(String)
    case missingPlanet(String)
    case unbracketedSolarReturn
    public var errorDescription: String? {
        switch self {
        case .invalidInput(let message): return message
        case .missingPlanet(let name): return "Nedostaje položaj planeta: \(name)."
        case .unbracketedSolarReturn: return "Solarni povratak nije pronađen unutar provjerenog raspona."
        }
    }
}

public struct AnnualResult: Sendable {
    public let year: Int
    public let returnDate: Date
    public let nextReturnDate: Date
    public let completedYears: Int
    public var lifeYear: Int { completedYears + 1 }
    public let chart: Chart
    public let munthaSignIndex: Int
    public var munthaSign: String { Astro.signs[munthaSignIndex] }
    public let isDay: Bool
    public let sahams: [String: Double]
    public let muddaDasha: [DashaPeriod]
    public let arudhaSign: Int
    public let bhriguBinduLongitude: Double
    public let gulika: GulikaResult?
    public let gulikaError: String?
    public let ithasala: [TajikaRelation]
    public let isarapha: [TajikaRelation]
    public let varsheshwara: VarsheshwaraResult
}

public struct MasaResult: Sendable, Identifiable {
    public let monthNumber: Int
    public var id: Int { monthNumber }
    /// Exact UTC return instant. Python truncated this display value to a minute.
    public let returnDate: Date
    public let chart: Chart
    public let arudhaSign: Int
    public let bhriguBinduLongitude: Double
    public let gulika: GulikaResult?
    public let gulikaError: String?
}

/// Annual and monthly return calculations, ported from the Python source.
/// Lahiri/mean-node ephemeris settings are fixed by `Ephemeris`.
public enum Annual {
    private static var utcCalendar: Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(secondsFromGMT: 0)!
        return calendar
    }

    /// Retains the Python ±3-day bisection when its endpoints bracket the root.
    /// If the day-28 guess excludes a late-month return, expands the *search*
    /// window; the solar longitude formula and angular tolerance are unchanged.
    public static func solarReturn(natalSunLongitude: Double, targetYear: Int, birthMonth: Int, birthDay: Int) throws -> Double {
        guard natalSunLongitude.isFinite, (1800...2399).contains(targetYear),
              (1...12).contains(birthMonth), (1...31).contains(birthDay) else {
            throw AnnualError.invalidInput("Datum ili dužina solarnog povratka izvan je podržanog raspona.")
        }
        let components = DateComponents(timeZone: TimeZone(secondsFromGMT: 0), year: targetYear, month: birthMonth, day: min(birthDay, 28), hour: 12)
        guard let guessDate = utcCalendar.date(from: components) else {
            throw AnnualError.invalidInput("Nevaljan datum solarnog povratka.")
        }
        return try findSolarLongitude(targetLongitude: Astro.normalize(natalSunLongitude), guess: Ephemeris.julianDay(date: guessDate), initialWindow: 3)
    }

    private static func findSolarLongitude(targetLongitude: Double, guess: Double, initialWindow: Double) throws -> Double {
        guard targetLongitude.isFinite, guess.isFinite else { throw AnnualError.invalidInput("Nevaljana dužina ili Julijanski dan.") }
        func difference(_ jd: Double) throws -> Double {
            Astro.signedDifference(try Ephemeris.sunLongitude(julianDay: jd) - targetLongitude)
        }
        // Clamp search probes to the bundled 1800..<2400 ephemeris range.
        let minimumJD = 2378496.5
        let maximumJD = 2597641.5.nextDown
        var low = max(minimumJD, guess - initialWindow)
        var high = min(maximumJD, guess + initialWindow)
        var dLow = try difference(low)
        var dHigh = try difference(high)
        if abs(dLow) < 1e-6 { return low }
        if abs(dHigh) < 1e-6 { return high }
        if !(dLow < 0 && dHigh > 0) {
            low = max(minimumJD, guess - 14)
            high = min(maximumJD, guess + 14)
            dLow = try difference(low)
            dHigh = try difference(high)
            guard dLow < 0 && dHigh > 0 else { throw AnnualError.unbracketedSolarReturn }
        }
        for _ in 0..<60 {
            let middle = (low + high) / 2
            let dMiddle = try difference(middle)
            if abs(dMiddle) < 1e-6 { return middle }
            if (dLow < 0) == (dMiddle < 0) {
                low = middle
                dLow = dMiddle
            } else {
                high = middle
            }
        }
        let answer = (low + high) / 2
        guard abs(try difference(answer)) < 1e-6 else { throw AnnualError.unbracketedSolarReturn }
        return answer
    }

    public static func muntha(natalAscendant: Double, completedYears: Int) -> Int {
        let sign = Int(Astro.normalize(natalAscendant) / 30)
        return ((sign + completedYears) % 12 + 12) % 12
    }

    public static func activeYear(birthDate: Date, latitude: Double, longitude: Double, referenceDate: Date, birthTimeZone: TimeZone = TimeZone(secondsFromGMT: 0)!) throws -> Int {
        guard birthDate.timeIntervalSince1970.isFinite, referenceDate.timeIntervalSince1970.isFinite,
              referenceDate >= birthDate else { throw AnnualError.invalidInput("Referentni datum mora biti nakon rođenja.") }
        let natal = try Ephemeris.chart(date: birthDate, latitude: latitude, longitude: longitude)
        guard let sun = natal.positions["Sunce"] else { throw AnnualError.missingPlanet("Sunce") }
        var birthCalendar = utcCalendar
        birthCalendar.timeZone = birthTimeZone
        let birth = birthCalendar.dateComponents([.year, .month, .day], from: birthDate)
        let year = utcCalendar.component(.year, from: referenceDate)
        let start = try solarReturn(natalSunLongitude: sun.longitude, targetYear: year, birthMonth: birth.month!, birthDay: birth.day!)
        return max(Ephemeris.julianDay(date: referenceDate) >= start ? year : year - 1, birth.year!)
    }

    public static func calculate(birthDate: Date, latitude: Double, longitude: Double, year: Int, birthTimeZone: TimeZone = TimeZone(secondsFromGMT: 0)!) throws -> AnnualResult {
        guard birthDate.timeIntervalSince1970.isFinite, (1800...2398).contains(year) else {
            throw AnnualError.invalidInput("Podržane godine Varshaphale su 1800–2398.")
        }
        var birthCalendar = utcCalendar
        birthCalendar.timeZone = birthTimeZone
        let birth = birthCalendar.dateComponents([.year, .month, .day], from: birthDate)
        guard let birthYear = birth.year, let month = birth.month, let day = birth.day, year >= birthYear else {
            throw AnnualError.invalidInput("Godina Varshaphale mora biti nakon godine rođenja.")
        }
        let natal = try Ephemeris.chart(date: birthDate, latitude: latitude, longitude: longitude)
        guard let sun = natal.positions["Sunce"], let moon = natal.positions["Mjesec"] else { throw AnnualError.missingPlanet("Sunce/Mjesec") }
        let jd = try solarReturn(natalSunLongitude: sun.longitude, targetYear: year, birthMonth: month, birthDay: day)
        let nextJD = try solarReturn(natalSunLongitude: sun.longitude, targetYear: year + 1, birthMonth: month, birthDay: day)
        let start = Ephemeris.date(julianDay: jd)
        let end = Ephemeris.date(julianDay: nextJD)
        let chart = try Ephemeris.chart(date: start, latitude: latitude, longitude: longitude)
        let age = year - birthYear
        let munthaSign = muntha(natalAscendant: natal.ascendantLongitude, completedYears: age)
        let isDay = try Ephemeris.isDaytime(julianDay: jd, latitude: latitude, longitude: longitude)
        let arudha = try SpecialPoints.arudha(houseSign: chart.ascendantSign, positions: chart.positions)
        let bhrigu = try SpecialPoints.bhriguBindu(moonLongitude: chart.positions["Mjesec"]!.longitude, rahuLongitude: chart.positions["Rahu"]!.longitude)
        let gulika = optionalGulika(julianDay: jd, date: start, latitude: latitude, longitude: longitude)
        return AnnualResult(
            year: year, returnDate: start, nextReturnDate: end, completedYears: age,
            chart: chart, munthaSignIndex: munthaSign, isDay: isDay,
            sahams: try Sahams.calculate(ascendant: chart.ascendantLongitude, positions: chart.positions, isDay: isDay),
            muddaDasha: try Dasha.mudda(natalMoonLongitude: moon.longitude, completedYears: age, start: start, end: end),
            arudhaSign: arudha, bhriguBinduLongitude: bhrigu, gulika: gulika.result, gulikaError: gulika.error,
            ithasala: try Tajika.ithasala(positions: chart.positions),
            isarapha: try Tajika.isarapha(positions: chart.positions),
            varsheshwara: try Varsheshwara.calculate(natalAscendantSign: natal.ascendantSign, munthaSign: munthaSign, chart: chart, isDaytime: isDay)
        )
    }

    public static func masa(natalSunLongitude: Double, annualJulianDay: Double, latitude: Double, longitude: Double) throws -> [MasaResult] {
        guard natalSunLongitude.isFinite, annualJulianDay.isFinite else { throw AnnualError.invalidInput("Nevaljani podaci Masa Praveše.") }
        return try (0..<12).map { index in
            let target = Astro.normalize(natalSunLongitude + Double(index) * 30)
            let jd: Double
            if index == 0 { jd = annualJulianDay }
            else { jd = try findSolarLongitude(targetLongitude: target, guess: annualJulianDay + Double(index) * (365.2425 / 12), initialWindow: 4) }
            let date = Ephemeris.date(julianDay: jd)
            let chart = try Ephemeris.chart(date: date, latitude: latitude, longitude: longitude)
            let gulika = optionalGulika(julianDay: jd, date: date, latitude: latitude, longitude: longitude)
            return MasaResult(
                monthNumber: index + 1, returnDate: date, chart: chart,
                arudhaSign: try SpecialPoints.arudha(houseSign: chart.ascendantSign, positions: chart.positions),
                bhriguBinduLongitude: try SpecialPoints.bhriguBindu(moonLongitude: chart.positions["Mjesec"]!.longitude, rahuLongitude: chart.positions["Rahu"]!.longitude),
                gulika: gulika.result, gulikaError: gulika.error
            )
        }
    }

    private static func optionalGulika(julianDay: Double, date: Date, latitude: Double, longitude: Double) -> (result: GulikaResult?, error: String?) {
        do {
            return (try SpecialPoints.gulika(julianDay: julianDay, localDate: dateString(date), latitude: latitude, longitude: longitude), nil)
        } catch { return (nil, error.localizedDescription) }
    }

    private static func dateString(_ date: Date) -> String {
        let parts = utcCalendar.dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", parts.year!, parts.month!, parts.day!)
    }
}
