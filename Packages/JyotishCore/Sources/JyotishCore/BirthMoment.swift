import Foundation

public enum BirthMomentError: LocalizedError, Equatable {
    case message(String)
    public var errorDescription: String? {
        switch self { case .message(let text): return text }
    }
}

/// A DatePicker displays a neutral UTC wall clock; resolve it explicitly in the
/// selected IANA zone. This avoids interpreting birth time in the device zone.
public enum BirthMoment {
    public static let utc = TimeZone(secondsFromGMT: 0)!
    public static var calendar: Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = utc
        return calendar
    }
    public static let supportedDates: ClosedRange<Date> = {
        let start = calendar.date(from: DateComponents(year: 1800, month: 1, day: 1))!
        let end = calendar.date(from: DateComponents(year: 2399, month: 1, day: 1))!.addingTimeInterval(-1)
        return start...end
    }()
    public static let defaultWallClock = calendar.date(from: DateComponents(year: 2000, month: 1, day: 1, hour: 12))!

    public static func wallClock(from instant: Date, zoneID: String) -> Date {
        var local = calendar
        local.timeZone = TimeZone(identifier: zoneID) ?? utc
        let components = local.dateComponents([.year, .month, .day, .hour, .minute, .second], from: instant)
        return calendar.date(from: components) ?? instant
    }

    /// Returns zero candidates for a skipped clock time, two for a repeated time.
    public static func candidates(wallClock: Date, zoneID: String) throws -> [Date] {
        guard wallClock.timeIntervalSince1970.isFinite else { throw BirthMomentError.message("Nevaljan trenutak rođenja.") }
        guard let zone = TimeZone(identifier: zoneID) else {
            throw BirthMomentError.message("Nepoznata vremenska zona. Koristite IANA naziv, npr. Europe/Zagreb.")
        }
        let fields: Set<Calendar.Component> = [.year, .month, .day, .hour, .minute, .second]
        let wanted = calendar.dateComponents(fields, from: wallClock)
        var local = calendar
        local.timeZone = zone
        let offsets = Set((-36...36).map { zone.secondsFromGMT(for: wallClock.addingTimeInterval(Double($0) * 3600)) })
        let values = offsets.map { wallClock.addingTimeInterval(-Double($0)) }.filter { instant in
            let got = local.dateComponents(fields, from: instant)
            return got.year == wanted.year && got.month == wanted.month && got.day == wanted.day && got.hour == wanted.hour && got.minute == wanted.minute && got.second == wanted.second
        }
        return Array(Set(values)).sorted()
    }

    public static func localDateString(_ date: Date, zoneID: String) -> String {
        let format = DateFormatter()
        format.locale = Locale(identifier: "en_US_POSIX")
        format.calendar = calendar
        format.timeZone = TimeZone(identifier: zoneID) ?? utc
        format.dateFormat = "yyyy-MM-dd"
        return format.string(from: date)
    }

    public static func display(_ date: Date, zoneID: String = "UTC", seconds: Bool = false) -> String {
        let format = DateFormatter()
        format.locale = Locale(identifier: "hr_HR")
        format.calendar = calendar
        format.timeZone = TimeZone(identifier: zoneID) ?? utc
        format.dateFormat = seconds ? "dd.MM.yyyy. HH:mm:ss" : "dd.MM.yyyy. HH:mm"
        return format.string(from: date)
    }
}
