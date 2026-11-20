import Foundation
import XCTest
@testable import JyotishCore

final class NodePLReferenceTests: XCTestCase {
    private func date(_ text: String) throws -> Date {
        try XCTUnwrap(ISO8601DateFormatter().date(from: text))
    }

    func testMeanNodesAgainstTwoIndependentPL9Epochs() throws {
        // Transcribed from the natal screenshot and annual var.pdf. The annual
        // instant is the PDF's own printed time, not a fitted return timestamp.
        let references: [(String, Double)] = [
            ("1976-12-26T10:55:00Z", 180 + 6 + 38.0 / 60 + 18.0 / 3600),
            ("2026-12-27T06:43:23Z", 270 + 28 + 51.0 / 60 + 15.0 / 3600)
        ]
        for (instant, rahuReference) in references {
            let jd = Ephemeris.julianDay(date: try date(instant))
            let positions = try Ephemeris.positions(julianDay: jd, nodeConvention: .meanTropicalTrueAyanamsa)
            let rahu = try XCTUnwrap(positions["Rahu"])
            let ketu = try XCTUnwrap(positions["Ketu"])
            XCTAssertEqual(Astro.signedDifference(rahu.longitude - rahuReference), 0,
                           accuracy: 1.0 / 3600, instant)
            XCTAssertEqual(Astro.signedDifference(ketu.longitude - Astro.normalize(rahuReference + 180)), 0,
                           accuracy: 1.0 / 3600, instant)
            XCTAssertEqual(Astro.normalize(ketu.longitude - rahu.longitude), 180, accuracy: 1e-12)
            XCTAssertEqual(ketu.speed, rahu.speed)
            let legacy = try XCTUnwrap(Ephemeris.positions(julianDay: jd)["Rahu"])
            XCTAssertGreaterThan(abs(Astro.signedDifference(legacy.longitude - rahuReference)) * 3600, 5)
        }
    }

    func testAnnualMeanNodeSpeedAgainstPrintedPL9Speed() throws {
        // var.pdf prints −00:03:11 degrees/day for both nodes.
        let jd = Ephemeris.julianDay(date: try date("2026-12-27T06:43:23Z"))
        let positions = try Ephemeris.positions(julianDay: jd, nodeConvention: .meanTropicalTrueAyanamsa)
        let reference = -(3.0 / 60 + 11.0 / 3600)
        for name in ["Rahu", "Ketu"] {
            let position = try XCTUnwrap(positions[name])
            XCTAssertEqual(position.speed, reference, accuracy: 1.0 / 3600, name)
            XCTAssertTrue(position.isRetrograde)
        }
    }

    func testAlternateNodeConventionPreservesClassicalPlanetsAndAscendant() throws {
        for instant in ["1976-12-26T10:55:00Z", "2026-12-27T06:43:23Z"] {
            let at = try date(instant)
            let legacy = try Ephemeris.chart(date: at, latitude: 45.4881, longitude: 16.3745)
            let alternative = try Ephemeris.chart(date: at, latitude: 45.4881, longitude: 16.3745,
                                                   nodeConvention: .meanTropicalTrueAyanamsa)
            XCTAssertEqual(alternative.ascendantLongitude, legacy.ascendantLongitude)
            XCTAssertEqual(alternative.julianDay, legacy.julianDay)
            for name in Tajika.planets {
                XCTAssertEqual(alternative.positions[name], legacy.positions[name], name)
            }
        }
    }

    func testNodeSpeedAgreesWithNumericalDerivativeOfItsLongitude() throws {
        let step = 0.001 // days; a much shorter check than the bridge's one-day ayanamsha difference.
        for instant in ["1976-12-26T10:55:00Z", "2026-12-27T06:43:23Z"] {
            let jd = Ephemeris.julianDay(date: try date(instant))
            let center = try XCTUnwrap(Ephemeris.positions(julianDay: jd, nodeConvention: .meanTropicalTrueAyanamsa)["Rahu"])
            let before = try XCTUnwrap(Ephemeris.positions(julianDay: jd - step, nodeConvention: .meanTropicalTrueAyanamsa)["Rahu"])
            let after = try XCTUnwrap(Ephemeris.positions(julianDay: jd + step, nodeConvention: .meanTropicalTrueAyanamsa)["Rahu"])
            let derivative = Astro.signedDifference(after.longitude - before.longitude) / (2 * step)
            // Numerical differentiation permits 0.0036 arcsecond/day here;
            // this budget is separate from the printed report's precision.
            XCTAssertEqual(center.speed, derivative, accuracy: 1e-6, instant)
        }
    }

    func testInterleavingNodeConventionsDoesNotChangeLegacyResults() throws {
        let first = Ephemeris.julianDay(date: try date("1976-12-26T10:55:00Z"))
        let second = Ephemeris.julianDay(date: try date("2026-12-27T06:43:23Z"))
        let original = try Ephemeris.positions(julianDay: first)
        _ = try Ephemeris.positions(julianDay: second, nodeConvention: .meanTropicalTrueAyanamsa)
        let alternative = try Ephemeris.positions(julianDay: first, nodeConvention: .meanTropicalTrueAyanamsa)
        XCTAssertEqual(try Ephemeris.positions(julianDay: first), original)
        XCTAssertEqual(try Ephemeris.positions(julianDay: first, nodeConvention: .swissSidereal), original)
        XCTAssertEqual(try Ephemeris.positions(julianDay: first, nodeConvention: .meanTropicalTrueAyanamsa), alternative)
        XCTAssertNotEqual(alternative["Rahu"], original["Rahu"])
    }
}
