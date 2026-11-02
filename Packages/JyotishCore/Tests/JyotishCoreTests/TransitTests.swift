import XCTest
@testable import JyotishCore

final class TransitTests: XCTestCase {
    func testAllRowsMatchUnmodifiedPythonAcrossDatesAndSignBoundaries() throws {
        let url = try XCTUnwrap(Bundle.module.url(forResource: "TransitReference", withExtension: "json"))
        let fixture = try JSONDecoder().decode(Fixture.self, from: Data(contentsOf: url))
        XCTAssertEqual(fixture.cases.count, 65)
        for example in fixture.cases {
            let positions = example.positions.map { name, value in
                (name, PlanetPosition(name: name, longitude: value.longitude, speed: value.speed))
            }
            let rows = try Transits.calculate(positions: Dictionary(uniqueKeysWithValues: positions),
                                              natalAscendantLongitude: example.ascendant,
                                              natalMoonLongitude: example.moon)
            XCTAssertEqual(rows.map(\.planet), Astro.planetOrder)
            for row in rows {
                let expected = try XCTUnwrap(example.expected[row.planet])
                XCTAssertEqual(row.sign, expected.sign)
                XCTAssertEqual(row.longitude, expected.longitude, accuracy: 1e-10)
                XCTAssertEqual(row.degreeInSign, expected.degree_in_sign, accuracy: 1e-10)
                XCTAssertEqual(row.houseFromAscendant, expected.house_from_ascendant)
                XCTAssertEqual(row.houseFromMoon, expected.house_from_moon)
                XCTAssertEqual(row.isRetrograde, expected.is_retrograde)
                XCTAssertEqual(row.highlighted, expected.highlighted)
            }
        }
    }

    func testChartComparisonUsesNatalMoonAndNatalAscendantNotTransitAscendant() throws {
        let natal = try Ephemeris.chart(date: Ephemeris.date(julianDay: 2451545), latitude: 45.44, longitude: 16.28)
        let transit = try Ephemeris.chart(date: Ephemeris.date(julianDay: 2461346.5), latitude: -33.86, longitude: 151.21)
        let rows = try Transits.calculate(natal: natal, transit: transit)
        let moon = try XCTUnwrap(natal.positions["Mjesec"])
        for row in rows {
            let position = try XCTUnwrap(transit.positions[row.planet])
            XCTAssertEqual(row.houseFromAscendant, Astro.house(sign: position.signIndex, ascendantSign: natal.ascendantSign))
            XCTAssertEqual(row.houseFromMoon, Astro.house(sign: position.signIndex, ascendantSign: moon.signIndex))
        }
        XCTAssertNotEqual(natal.ascendantSign, transit.ascendantSign)
    }

    func testInvalidMissingAndMalformedPositionsAreRejected() throws {
        let positions = try Ephemeris.positions(julianDay: 2451545)
        for bad in [Double.nan, .infinity, -.infinity] {
            XCTAssertThrowsError(try Transits.calculate(positions: positions, natalAscendantLongitude: bad, natalMoonLongitude: 0))
            XCTAssertThrowsError(try Transits.calculate(positions: positions, natalAscendantLongitude: 0, natalMoonLongitude: bad))
            var malformed = positions
            malformed["Mars"] = PlanetPosition(name: "Mars", longitude: bad, speed: 1)
            XCTAssertThrowsError(try Transits.calculate(positions: malformed, natalAscendantLongitude: 0, natalMoonLongitude: 0))
            malformed["Mars"] = PlanetPosition(name: "Mars", longitude: 10, speed: bad)
            XCTAssertThrowsError(try Transits.calculate(positions: malformed, natalAscendantLongitude: 0, natalMoonLongitude: 0))
        }
        var missing = positions
        missing.removeValue(forKey: "Mjesec")
        XCTAssertThrowsError(try Transits.calculate(positions: missing, natalAscendantLongitude: 0, natalMoonLongitude: 0))
        missing["Mjesec"] = PlanetPosition(name: "Unexpected", longitude: 10, speed: 1)
        XCTAssertThrowsError(try Transits.calculate(positions: missing, natalAscendantLongitude: 0, natalMoonLongitude: 0))
        let badChart = Chart(julianDay: 2451545, ascendantLongitude: .nan, positions: positions)
        let chart = Chart(julianDay: 2451545, ascendantLongitude: 10, positions: positions)
        XCTAssertThrowsError(try Transits.calculate(natal: badChart, transit: chart))
    }

    private struct Fixture: Decodable { let cases: [Example] }
    private struct Example: Decodable {
        let ascendant: Double
        let moon: Double
        let positions: [String: Position]
        let expected: [String: Expected]
    }
    private struct Position: Decodable { let longitude: Double; let speed: Double }
    private struct Expected: Decodable {
        let sign: String
        let degree_in_sign: Double
        let longitude: Double
        let house_from_ascendant: Int
        let house_from_moon: Int
        let is_retrograde: Bool
        let highlighted: Bool
    }
}
