import Foundation

/// Full Muntha longitude. The annual position preserves the natal ascendant's
/// degree; elapsed-time progression is separate from the annual sign count.
public enum Muntha {
    /// A conventional Julian year. The supplied PL9 monthly example is
    /// consistent with 30 degrees per 365.25 days to its displayed precision.
    /// This is deliberately independent of the selected dasha year length.
    public static let julianYearDays = 365.25

    public static func annualLongitude(natalAscendant: Double, completedYears: Int) throws -> Double {
        guard natalAscendant.isFinite, completedYears >= 0 else {
            throw AnnualError.invalidInput("Muntha zahtijeva konačan natalni ascendent i nenegativan broj navršenih godina.")
        }
        // Reduce the integer first, avoiding overflow for arbitrary callers.
        return Astro.normalize(Astro.normalize(natalAscendant) + Double(completedYears % 12) * 30)
    }

    /// Continuous progression from the annual Muntha at the solar return.
    /// Supply an explicit year length when comparing another convention.
    /// The result can cross signs and zero degrees without losing its degree.
    public static func progressedLongitude(annualLongitude: Double, annualStart: Date, at date: Date,
                                            daysPerYear: Double = julianYearDays) throws -> Double {
        let elapsedSeconds = date.timeIntervalSince(annualStart)
        guard annualLongitude.isFinite, annualStart.timeIntervalSince1970.isFinite,
              date.timeIntervalSince1970.isFinite, elapsedSeconds.isFinite, elapsedSeconds >= 0,
              daysPerYear.isFinite, daysPerYear > 0 else {
            throw AnnualError.invalidInput("Nevaljani podaci za napredovanje Munthe.")
        }
        let progression = (elapsedSeconds / 86400) / daysPerYear * 30
        guard progression.isFinite else {
            throw AnnualError.invalidInput("Napredovanje Munthe izlazi iz numeričkog raspona.")
        }
        return Astro.normalize(Astro.normalize(annualLongitude) + progression)
    }
}
