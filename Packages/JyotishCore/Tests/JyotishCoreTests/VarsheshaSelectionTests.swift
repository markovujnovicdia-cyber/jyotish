import Foundation
import XCTest
@testable import JyotishCore

final class VarsheshaSelectionTests: XCTestCase {
    private func syntheticChart(ascendant: Double, overrides: [String: Double]) -> Chart {
        let positions = Dictionary(uniqueKeysWithValues: Tajika.planets.map { name in
            (name, PlanetPosition(name: name, longitude: overrides[name] ?? 340, speed: 1))
        })
        return Chart(julianDay: 2451545, ascendantLongitude: ascendant, positions: positions)
    }

    func testReferenceChartExplainsTheDifferentYearLordEligibilityPolicies() throws {
        // The date/place identify the supplied annual chart, but its PDF does
        // not explicitly print a year lord. Jupiter below is the result of the
        // sign-aspect election rule, not an asserted external PL9 year-lord value.
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let latitude = 45.45
        let longitude = 16.0 + 22.0 / 60.0
        let annual = try Annual.calculate(
            birthDate: birth, latitude: latitude, longitude: longitude, year: 2026,
            birthTimeZone: try XCTUnwrap(TimeZone(identifier: "Europe/Zagreb")),
            timeConvention: .historical2019Forecast
        )
        let natal = try Ephemeris.chart(date: birth, latitude: latitude, longitude: longitude)
        let legacy = try Varsheshwara.calculate(
            natalAscendantSign: natal.ascendantSign, munthaSign: annual.munthaSignIndex,
            chart: annual.chart, isDaytime: annual.isDay
        )
        let signBased = try Varsheshwara.calculate(
            natalAscendantSign: natal.ascendantSign, munthaSign: annual.munthaSignIndex,
            chart: annual.chart, isDaytime: annual.isDay, convention: .signAspect
        )
        XCTAssertEqual(legacy.candidates.count, 5)
        XCTAssertEqual(signBased.candidates.count, 5)
        XCTAssertEqual(legacy.winner?.planet, "Saturn")
        XCTAssertEqual(signBased.winner?.planet, "Jupiter")
        let legacyJupiter = try XCTUnwrap(legacy.candidates.first(where: { $0.planet == "Jupiter" }))
        let signJupiter = try XCTUnwrap(signBased.candidates.first(where: { $0.planet == "Jupiter" }))
        XCTAssertFalse(legacyJupiter.aspectsAscendant)
        XCTAssertTrue(signJupiter.aspectsAscendant)
        XCTAssertEqual(signJupiter.bala, legacyJupiter.bala)
        XCTAssertEqual(signJupiter.strengthScore, legacyJupiter.strengthScore)
    }

    func testSignAspectsQualifyBeyondDegreeOrbsAndNonAspectsDoNot() throws {
        let chart = syntheticChart(ascendant: 252, overrides: [
            "Jupiter": 122, // Leo→Sagittarius trine, residual 10° exceeds Jupiter's 9°.
            "Venera": 204, // Libra→Sagittarius sextile, residual 12° exceeds Venus's 7°.
            "Merkur": 270 // Capricorn is adjacent to Sagittarius, with no Tajika sign aspect.
        ])
        let definitions = [("Trine", "Jupiter"), ("Sextile", "Venera"), ("Non-aspect", "Merkur")]
        let legacy = try Varsheshwara.evaluate(definitions: definitions, chart: chart, convention: .legacyOrb)
        let signBased = try Varsheshwara.evaluate(definitions: definitions, chart: chart, convention: .signAspect)
        XCTAssertEqual(legacy.candidates.map(\.aspectsAscendant), [false, false, false])
        XCTAssertNil(legacy.winner)
        XCTAssertEqual(signBased.candidates.map(\.aspectsAscendant), [true, true, false])
        XCTAssertNotNil(signBased.winner)
    }

    func testSignElectionRanksUnroundedStrengthInsteadOfDisplayTies() throws {
        // Both qualify under either aspect rule. The existing five-component
        // formulas give Sun 10.833333… and Mercury 10.834722…; both display 10.83.
        // A display tie must not discard Mercury's larger unrounded strength.
        let chart = syntheticChart(ascendant: 0.6, overrides: ["Sunce": 70, "Merkur": 247.45])
        let definitions = [("First", "Sunce"), ("Second", "Merkur")]
        let legacy = try Varsheshwara.evaluate(definitions: definitions, chart: chart, convention: .legacyOrb)
        let signBased = try Varsheshwara.evaluate(definitions: definitions, chart: chart, convention: .signAspect)
        XCTAssertTrue(signBased.candidates.allSatisfy(\.aspectsAscendant))
        XCTAssertEqual(signBased.candidates.map(\.strengthScore), [10.83, 10.83])
        XCTAssertGreaterThan(signBased.candidates[1].bala.total, signBased.candidates[0].bala.total)
        XCTAssertEqual(legacy.winner?.planet, "Sunce")
        XCTAssertEqual(signBased.winner?.planet, "Merkur")
    }

    func testSharedElectionRejectsMissingOrUnsupportedCandidates() throws {
        let chart = syntheticChart(ascendant: 0, overrides: [:])
        XCTAssertThrowsError(try Varsheshwara.evaluate(
            definitions: [("Unsupported", "Rahu")], chart: chart, convention: .signAspect
        ))
        let incomplete = Chart(julianDay: 2451545, ascendantLongitude: 0, positions: [:])
        XCTAssertThrowsError(try Varsheshwara.evaluate(
            definitions: [("Missing", "Jupiter")], chart: incomplete, convention: .signAspect
        ))
    }
}
