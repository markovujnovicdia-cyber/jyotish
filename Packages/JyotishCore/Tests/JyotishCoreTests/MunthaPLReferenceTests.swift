import Foundation
import XCTest
@testable import JyotishCore

final class MunthaPLReferenceTests: XCTestCase {
    private func date(_ value: String) throws -> Date {
        try XCTUnwrap(ISO8601DateFormatter().date(from: value))
    }

    private func angle(_ sign: Int, _ degree: Int, _ minute: Int, _ second: Int) -> Double {
        Double(sign * 30 + degree) + Double(minute) / 60 + Double(second) / 3600
    }

    func testAnnualMunthaPreservesNatalDegreeAndCompletedYearCount() throws {
        let natal = angle(11, 16, 30, 55)
        XCTAssertEqual(try Muntha.annualLongitude(natalAscendant: natal, completedYears: 0), natal, accuracy: 1e-12)
        XCTAssertEqual(try Muntha.annualLongitude(natalAscendant: natal, completedYears: 50), angle(1, 16, 30, 55), accuracy: 1e-12)
        XCTAssertEqual(try Muntha.annualLongitude(natalAscendant: natal, completedYears: 51), angle(2, 16, 30, 55), accuracy: 1e-12)
        XCTAssertEqual(try Muntha.annualLongitude(natalAscendant: natal, completedYears: 12), natal, accuracy: 1e-12)
        XCTAssertEqual(try Muntha.annualLongitude(natalAscendant: 359.9, completedYears: 1), 29.9, accuracy: 1e-12)
        XCTAssertEqual(try Muntha.annualLongitude(natalAscendant: natal, completedYears: Int.max),
                       Astro.normalize(natal + Double(Int.max % 12) * 30), accuracy: 1e-12)
    }

    func testProgressionMatchesSixVisibleMonthlyReferenceDegrees() throws {
        // The external monthly report prints Taurus 16:30:57 at its first
        // chart, 2″ beyond the annual count from its printed natal ascendant.
        // Use that independently supplied annual starting longitude here to
        // test progression only; do not hide that baseline discrepancy with
        // a fitted offset in the annual formula or ephemeris.
        let annualBase = angle(1, 16, 30, 57)
        let start = try date("2026-12-27T07:43:23+01:00")
        let references: [(String, Double)] = [
            ("2026-12-27T07:43:23+01:00", angle(1, 16, 30, 57)),
            ("2027-01-25T18:35:00+01:00", angle(1, 18, 56, 6)),
            ("2027-02-24T09:56:00+01:00", angle(1, 21, 22, 10)),
            ("2027-03-26T10:51:00+01:00", angle(1, 23, 50, 12)),
            ("2027-04-26T00:04:00+01:00", angle(1, 26, 20, 45)),
            ("2027-05-27T01:05:00+01:00", angle(1, 28, 53, 44))
        ]
        for (timestamp, expected) in references {
            let actual = try Muntha.progressedLongitude(annualLongitude: annualBase, annualStart: start, at: date(timestamp))
            // Monthly timestamps are displayed to a minute (≤60 s, or
            // 0.206″ of Muntha). Two DMS displays add at most 1″ total.
            XCTAssertEqual(Astro.signedDifference(actual - expected), 0, accuracy: 1.25 / 3600, timestamp)
        }
    }

    func testEndToEndMonthlyIncrementsMatchReferenceWithoutFittingNatalAscendant() throws {
        let birth = try date("1976-12-26T10:55:00Z")
        let zone = try XCTUnwrap(TimeZone(identifier: "Europe/Zagreb"))
        let natal = try Ephemeris.chart(date: birth, latitude: 45.45, longitude: 16 + 22.0 / 60,
                                         timeConvention: .historical2019Forecast)
        let annual = try Annual.calculate(birthDate: birth, latitude: 45.45, longitude: 16 + 22.0 / 60,
                                            year: 2026, birthTimeZone: zone, timeConvention: .historical2019Forecast)
        let sun = try XCTUnwrap(natal.positions["Sunce"]?.longitude)
        let months = try Annual.masa(natalSunLongitude: sun, annualJulianDay: annual.chart.julianDay,
                                       latitude: 45.45, longitude: 16 + 22.0 / 60,
                                       timeConvention: .historical2019Forecast)
        let base = try Muntha.annualLongitude(natalAscendant: natal.ascendantLongitude, completedYears: 50)
        let externalIncrementsArcseconds = [0.0, 8709, 17473, 26355, 35388, 44567]
        let externalLongitudes = [
            angle(1, 16, 30, 57), angle(1, 18, 56, 6), angle(1, 21, 22, 10),
            angle(1, 23, 50, 12), angle(1, 26, 20, 45), angle(1, 28, 53, 44)
        ]
        XCTAssertEqual(months.count, 12)
        for (index, month) in months.prefix(6).enumerated() {
            let advanced = try Muntha.progressedLongitude(annualLongitude: base, annualStart: annual.returnDate, at: month.returnDate)
            let increment = Astro.normalize(advanced - base) * 3600
            // Each external displayed degree is rounded to 1″. Comparing
            // two such displays permits 1″ for the measured increment.
            XCTAssertEqual(increment, externalIncrementsArcseconds[index], accuracy: 1, "Month \(month.monthNumber)")
            // The independently computed natal ascendant is 3.69″ below
            // its printed PL value, whose annual starting degree itself
            // differs from the monthly report's starting degree by 2″.
            // Keep the resulting ~5.7″ baseline discrepancy explicit:
            // absolute parity is established only to 10″, not to 1″.
            XCTAssertEqual(Astro.signedDifference(advanced - externalLongitudes[index]), 0,
                           accuracy: 10.0 / 3600, "Absolute month \(month.monthNumber)")
        }
    }

    func testProgressionCrossesSignsAndAcceptsExplicitYearLength() throws {
        let start = try date("2026-01-01T00:00:00Z")
        let oneJulianYear = start.addingTimeInterval(365.25 * 86400)
        XCTAssertEqual(try Muntha.progressedLongitude(annualLongitude: 350, annualStart: start, at: oneJulianYear), 20, accuracy: 1e-10)
        XCTAssertEqual(try Muntha.progressedLongitude(annualLongitude: 29, annualStart: start, at: start.addingTimeInterval(365.25 * 86400 / 12)), 31.5, accuracy: 1e-10)
        XCTAssertEqual(try Muntha.progressedLongitude(annualLongitude: 350, annualStart: start, at: start), 350, accuracy: 1e-12)
        let endOfOtherYear = start.addingTimeInterval(365.2425 * 86400)
        XCTAssertEqual(try Muntha.progressedLongitude(annualLongitude: 350, annualStart: start, at: endOfOtherYear, daysPerYear: 365.2425), 20, accuracy: 1e-10)
    }

    func testInvalidInputsThrow() throws {
        let start = try date("2026-01-01T00:00:00Z")
        XCTAssertThrowsError(try Muntha.annualLongitude(natalAscendant: .nan, completedYears: 50))
        XCTAssertThrowsError(try Muntha.annualLongitude(natalAscendant: 30, completedYears: -1))
        XCTAssertThrowsError(try Muntha.progressedLongitude(annualLongitude: .infinity, annualStart: start, at: start))
        XCTAssertThrowsError(try Muntha.progressedLongitude(annualLongitude: 30, annualStart: start, at: start.addingTimeInterval(-1)))
        XCTAssertThrowsError(try Muntha.progressedLongitude(annualLongitude: 30, annualStart: start, at: Date(timeIntervalSince1970: .infinity)))
        for yearLength in [0.0, -365.25, .nan, .infinity] {
            XCTAssertThrowsError(try Muntha.progressedLongitude(annualLongitude: 30, annualStart: start, at: start, daysPerYear: yearLength))
        }
    }
}
