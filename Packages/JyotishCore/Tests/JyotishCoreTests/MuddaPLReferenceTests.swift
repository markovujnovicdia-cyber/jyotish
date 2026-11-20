import Foundation
import XCTest
@testable import JyotishCore

final class MuddaPLReferenceTests: XCTestCase {
    private func date(_ value: String) throws -> Date {
        try XCTUnwrap(ISO8601DateFormatter().date(from: value))
    }

    private func chart() throws -> (AnnualResult, Double) {
        let birth = try date("1976-12-26T10:55:00Z")
        let natal = try Ephemeris.chart(date: birth, latitude: 45.45, longitude: 16.0 + 22.0 / 60.0)
        let annual = try Annual.calculate(birthDate: birth, latitude: 45.45, longitude: 16.0 + 22.0 / 60.0,
                                         year: 2026, birthTimeZone: TimeZone(identifier: "Europe/Zagreb")!)
        return (annual, try XCTUnwrap(natal.positions["Mjesec"]?.longitude))
    }

    // Manually transcribed from the user's PL9 screenshots. Dates are printed
    // with a fixed +01:00 offset, including summer dates; they are not Zagreb
    // wall times during DST. Values are only minute precision. The remaining
    // <=90-second mismatch is recorded, not claimed to be exact PL9 parity.
    func testFixedYearMajorBoundariesAgainstMinutePrecisionPL9Report() throws {
        let (annual, moon) = try chart()
        let periods = try Dasha.mudda(natalMoonLongitude: moon, completedYears: 50,
                                      start: annual.returnDate, end: annual.nextReturnDate,
                                      yearConvention: .fixedGregorianYear)
        let expected = [
            ("Sunce", "2026-12-27T07:43:00+01:00"),
            ("Mjesec", "2027-01-14T11:37:00+01:00"),
            ("Mars", "2027-02-13T22:06:00+01:00"),
            ("Rahu", "2027-03-07T05:27:00+01:00"),
            ("Jupiter", "2027-05-01T00:19:00+01:00"),
            ("Saturn", "2027-06-18T17:06:00+01:00"),
            ("Merkur", "2027-08-15T13:01:00+01:00"),
            ("Ketu", "2027-10-06T06:50:00+01:00")
        ]
        XCTAssertEqual(periods.count, 10)
        for (actual, reference) in zip(periods, expected) {
            XCTAssertEqual(actual.lord, reference.0)
            XCTAssertEqual(actual.start.timeIntervalSince1970,
                           try date(reference.1).timeIntervalSince1970, accuracy: 90, reference.0)
        }
        XCTAssertEqual(try XCTUnwrap(periods.last).end.timeIntervalSince(annual.returnDate) / 86400,
                       365.2425, accuracy: 1e-8)
        XCTAssertNotEqual(periods.last?.end, annual.nextReturnDate)
    }

    func testFirstSubperiodPreservesMoonBalanceInsteadOfRescaling() throws {
        let (annual, moon) = try chart()
        let parent = try XCTUnwrap(Dasha.mudda(natalMoonLongitude: moon, completedYears: 50,
                                              start: annual.returnDate, yearConvention: .fixedGregorianYear).first)
        let children = try Dasha.muddaSubperiods(parent: parent, natalMoonLongitude: moon,
                                                annualStart: annual.returnDate,
                                                yearConvention: .fixedGregorianYear)
        let expected = [
            ("Sunce", "2026-12-27T07:43:00+01:00"),
            ("Mjesec", "2026-12-28T03:15:00+01:00"),
            ("Mars", "2026-12-29T15:46:00+01:00"),
            ("Rahu", "2026-12-30T17:20:00+01:00"),
            ("Jupiter", "2027-01-02T11:05:00+01:00")
        ]
        XCTAssertEqual(children.count, 9)
        for (actual, reference) in zip(children, expected) {
            XCTAssertEqual(actual.lord, reference.0)
            XCTAssertEqual(actual.start.timeIntervalSince1970,
                           try date(reference.1).timeIntervalSince1970, accuracy: 90, reference.0)
        }
        XCTAssertEqual(children.first?.start, parent.start)
        XCTAssertEqual(children.last?.end, parent.end)
        let rescaled = try Dasha.subperiods(parent: parent)
        XCTAssertGreaterThan(rescaled[1].start.timeIntervalSince(children[1].start), 2 * 3600)
    }

    func testBalancedChildrenClipElapsedAndFinalTruncatedPeriods() throws {
        let start = try date("2026-01-01T00:00:00Z")
        let moon = Nakshatra.arc * 0.75
        let periods = try Dasha.mudda(natalMoonLongitude: moon, completedYears: 29,
                                      start: start, yearConvention: .fixedGregorianYear)
        for parent in periods {
            let children = try Dasha.muddaSubperiods(parent: parent, natalMoonLongitude: moon,
                                                    annualStart: start, yearConvention: .fixedGregorianYear)
            XCTAssertFalse(children.isEmpty)
            XCTAssertEqual(children.first?.start, parent.start)
            XCTAssertEqual(children.last?.end, parent.end)
            XCTAssertTrue(children.allSatisfy { $0.end > $0.start })
            for (left, right) in zip(children, children.dropFirst()) {
                XCTAssertEqual(left.end, right.start)
            }
        }
        let first = try XCTUnwrap(periods.first)
        let firstChildren = try Dasha.muddaSubperiods(parent: first, natalMoonLongitude: moon,
                                                     annualStart: start, yearConvention: .fixedGregorianYear)
        XCTAssertLessThan(firstChildren.count, 9)
    }

    func testMonthlyReturnInstantsAgainstFixedOffsetPL9Display() throws {
        let (annual, _) = try chart()
        let birth = try date("1976-12-26T10:55:00Z")
        let sun = try Ephemeris.sunLongitude(julianDay: Ephemeris.julianDay(date: birth))
        let months = try Annual.masa(natalSunLongitude: sun, annualJulianDay: annual.chart.julianDay,
                                    latitude: 45.45, longitude: 16.0 + 22.0 / 60.0)
        let expected = [
            "2026-12-27T07:43:00+01:00", "2027-01-25T18:35:00+01:00",
            "2027-02-24T09:56:00+01:00", "2027-03-26T10:51:00+01:00",
            "2027-04-26T00:04:00+01:00", "2027-05-27T01:05:00+01:00",
            "2027-06-27T10:02:00+01:00", "2027-07-28T20:46:00+01:00",
            "2027-08-29T02:34:00+01:00"
        ]
        XCTAssertEqual(months.count, 12)
        for (actual, reference) in zip(months, expected) {
            XCTAssertEqual(actual.returnDate.timeIntervalSince1970,
                           try date(reference).timeIntervalSince1970, accuracy: 90,
                           "Month \(actual.monthNumber)")
        }
    }

    func testInvalidMuddaSubperiodInputThrows() throws {
        let start = try date("2026-01-01T00:00:00Z")
        XCTAssertThrowsError(try Dasha.muddaSubperiods(
            parent: DashaPeriod(lord: "Unknown", start: start, end: start.addingTimeInterval(100)),
            natalMoonLongitude: 0, annualStart: start))
        XCTAssertThrowsError(try Dasha.muddaSubperiods(
            parent: DashaPeriod(lord: "Sunce", start: start, end: start.addingTimeInterval(100)),
            natalMoonLongitude: .nan, annualStart: start))
    }
}
