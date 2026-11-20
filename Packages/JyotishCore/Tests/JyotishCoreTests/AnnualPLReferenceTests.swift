import Foundation
import XCTest
@testable import JyotishCore

/// Numerical inputs transcribed from the user's PL9 "Varshaphala 2026–2027"
/// PDF; expected Sahams come from the separately supplied Sahams screenshot.
/// Neither the expected longitudes nor the ascendant are fitted to our output.
final class AnnualPLReferenceTests: XCTestCase {
    private func dms(_ sign: Int, _ degree: Int, _ minute: Int, _ second: Int) -> Double {
        Double(sign * 30 + degree) + Double(minute) / 60 + Double(second) / 3600
    }

    private var referencePositions: [String: PlanetPosition] {
        let values: [(String, Double, Double)] = [
            ("Sunce", dms(8, 11, 16, 27), dms(0, 1, 1, 7)),
            ("Mjesec", dms(3, 26, 27, 48), dms(0, 14, 33, 1)),
            ("Mars", dms(4, 14, 58, 27), dms(0, 0, 9, 52)),
            ("Merkur", dms(8, 8, 9, 9), dms(0, 1, 34, 51)),
            ("Jupiter", dms(4, 2, 27, 27), -dms(0, 0, 2, 46)),
            ("Venera", dms(6, 24, 37, 21), dms(0, 0, 57, 40)),
            ("Saturn", dms(11, 13, 56, 11), dms(0, 0, 1, 46))
        ]
        return Dictionary(uniqueKeysWithValues: values.map { name, longitude, speed in
            (name, PlanetPosition(name: name, longitude: longitude, speed: speed))
        })
    }

    func testThirteenSahamsMatchExternalReportFromItsOwnRoundedInputs() throws {
        let result = try Sahams.calculate(
            ascendant: dms(8, 12, 15, 23), positions: referencePositions,
            isDay: true, convention: .tajikaRoga
        )
        let expected: [String: Double] = [
            "Punya": dms(3, 27, 26, 44), "Vidya": dms(1, 27, 4, 2),
            "Yasha": dms(9, 17, 16, 6), "Mitra": dms(7, 29, 38, 3),
            "Putra": dms(9, 18, 15, 2), "Karma": dms(4, 19, 4, 41),
            "Roga": dms(3, 29, 43, 46), "Matri": dms(5, 14, 5, 50),
            "Pitri": dms(11, 14, 55, 7), "Bandhu": dms(1, 23, 56, 44),
            "Bhratri": dms(2, 0, 46, 39), "Rajya": dms(11, 14, 55, 7),
            "Sastra": dms(1, 26, 40, 25)
        ]
        XCTAssertEqual(expected.count, 13)
        for (name, longitude) in expected {
            // Each displayed angle is rounded to one arcsecond. Three
            // independent operands plus the expected display allow 2″.
            // Mitra expands through Punya to five independent operands,
            // allowing 3″. The largest observed residual is Mitra's 1″.
            let roundingBudget = (name == "Mitra" ? 3.0 : 2.0) / 3600
            let actual = try XCTUnwrap(result[name])
            XCTAssertEqual(Astro.signedDifference(actual - longitude), 0,
                           accuracy: roundingBudget, name)
        }
    }

    func testSevenClassicalLongitudesAtComputedReturnMatchPDFWithinOneArcsecond() throws {
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let zone = try XCTUnwrap(TimeZone(identifier: "Europe/Zagreb"))
        let annual = try Annual.calculate(
            birthDate: birth, latitude: 45.45, longitude: 16.0 + 22.0 / 60.0,
            year: 2026, birthTimeZone: zone
        )
        for (name, expected) in referencePositions {
            let actual = try XCTUnwrap(annual.chart.positions[name])
            XCTAssertEqual(Astro.signedDifference(actual.longitude - expected.longitude), 0,
                           accuracy: 1.0 / 3600, name)
            XCTAssertEqual(actual.isRetrograde, expected.isRetrograde, name)
            XCTAssertEqual(actual.speed, expected.speed, accuracy: 1.0 / 3600, name + "/speed")
        }
        // This deliberately makes no parity assertion about the PDF's
        // 06:43:23 UTC return timestamp or ascendant, which still differ.
        // The explicit alternate node convention is tested separately in
        // NodePLReferenceTests; no time/angle offset is fitted here.
    }

    func testConfirmedBirthZoneUsesUTCPlusOneWithNoDST() throws {
        let wall = try XCTUnwrap(BirthMoment.calendar.date(from: DateComponents(
            year: 1976, month: 12, day: 26, hour: 11, minute: 55, second: 0
        )))
        let candidates = try BirthMoment.candidates(wallClock: wall, zoneID: "Europe/Zagreb")
        let expected = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        XCTAssertEqual(candidates, [expected])
        let zone = try XCTUnwrap(TimeZone(identifier: "Europe/Zagreb"))
        XCTAssertEqual(zone.secondsFromGMT(for: expected), 3600)
        XCTAssertFalse(zone.isDaylightSavingTime(for: expected))
    }

    func testFifteenFullyCalculatedSahamsAgainstConfirmedPLReference() throws {
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let zone = try XCTUnwrap(TimeZone(identifier: "Europe/Zagreb"))
        let annual = try Annual.calculate(
            birthDate: birth, latitude: 45.45, longitude: 16.0 + 22.0 / 60.0,
            year: 2026, birthTimeZone: zone, tajikaConvention: .longitudeBothOrbs,
            muddaYearConvention: .fixedGregorianYear, sahamsConvention: .tajikaSripati,
            nodeConvention: .meanTropicalTrueAyanamsa, timeConvention: .historical2019Forecast
        )
        let expected: [String: Double] = [
            "Punya": dms(3, 27, 26, 44), "Vidya": dms(1, 27, 4, 2),
            "Yasha": dms(9, 17, 16, 6), "Mitra": dms(7, 29, 38, 3),
            "Putra": dms(9, 18, 15, 2), "Karma": dms(4, 19, 4, 41),
            "Roga": dms(3, 29, 43, 46), "Matri": dms(5, 14, 5, 50),
            "Pitri": dms(11, 14, 55, 7), "Bandhu": dms(1, 23, 56, 44),
            "Bhratri": dms(2, 0, 46, 39), "Rajya": dms(11, 14, 55, 7),
            "Sastra": dms(1, 26, 40, 25), "Artha": dms(6, 20, 10, 12),
            "Paradesa": dms(5, 2, 25, 33)
        ]
        XCTAssertEqual(expected.count, 15)
        for (name, longitude) in expected {
            let actual = try XCTUnwrap(annual.sahams[name])
            // 10″ is a separate end-to-end budget: the reference return is
            // printed only to one second (~15″/s for local angles). The
            // ~2.3″ ascendant-model residual remains documented. The stricter
            // direct-formula checks above retain their 2″/3″ budgets.
            XCTAssertEqual(Astro.signedDifference(actual - longitude), 0,
                           accuracy: 10.0 / 3600, name)
        }
    }

}
