import Foundation
import XCTest
@testable import JyotishCore

final class AshtakavargaTests: XCTestCase {
    private struct Fixture: Decodable {
        let cases: [Reference]
        let kakshya: [KakshyaReference]
    }
    private struct ChartInput: Decodable {
        let unix: Double, latitude: Double, longitude: Double
    }
    private struct Reference: Decodable {
        let label: String
        let sourceSigns: [String: Int]
        let bhinna: [String: [Int]]
        let sarva: [Int]
        let activated: [String: [[Bool]]]
        let chartInput: ChartInput?
    }
    private struct KakshyaReference: Decodable {
        let degree: Double
        let lord: String
    }

    private func fixture() throws -> Fixture {
        let path = try XCTUnwrap(Bundle.module.url(forResource: "AshtakavargaReference", withExtension: "json"))
        return try JSONDecoder().decode(Fixture.self, from: Data(contentsOf: path))
    }

    func testEveryBhinnaCellAndSarvaSignAgainstUnmodifiedPython() throws {
        let references = try fixture().cases
        XCTAssertEqual(references.count, 64)
        for reference in references {
            let result = try Ashtakavarga.calculate(sourceSigns: reference.sourceSigns)
            XCTAssertEqual(result.bhinna, reference.bhinna, reference.label)
            XCTAssertEqual(result.sarva, reference.sarva, reference.label)
            XCTAssertEqual(result.sourceSigns, reference.sourceSigns, reference.label)
            XCTAssertEqual(result.total, 337, reference.label)
            for planet in Ashtakavarga.planetOrder {
                let row = try XCTUnwrap(result.bhinna[planet])
                XCTAssertEqual(row.count, 12)
                XCTAssertEqual(row.reduce(0, +), Ashtakavarga.totalBindus[planet], reference.label + planet)
                XCTAssertTrue(row.allSatisfy { (0...8).contains($0) })
            }
            for sign in 0..<12 {
                XCTAssertEqual(result.sarva[sign], Ashtakavarga.planetOrder.reduce(0) { $0 + result.bhinna[$1]![sign] })
            }
        }
    }

    func testActualNatalChartsUseSameEightSourcesAndExcludeNodes() throws {
        let references = try fixture().cases.filter { $0.chartInput != nil }
        XCTAssertEqual(references.count, 4)
        for reference in references {
            let input = try XCTUnwrap(reference.chartInput)
            let chart = try Ephemeris.chart(date: Date(timeIntervalSince1970: input.unix),
                                            latitude: input.latitude, longitude: input.longitude)
            let result = try Ashtakavarga.calculate(chart: chart)
            XCTAssertEqual(result.bhinna, reference.bhinna, reference.label)
            XCTAssertEqual(result.sarva, reference.sarva, reference.label)
            XCTAssertEqual(result.sourceSigns.count, 8)
            XCTAssertNil(result.bhinna["Rahu"])
            XCTAssertNil(result.bhinna["Ketu"])
            var onlyClassical = chart.positions
            onlyClassical.removeValue(forKey: "Rahu")
            onlyClassical.removeValue(forKey: "Ketu")
            let withoutNodes = Chart(julianDay: chart.julianDay, ascendantLongitude: chart.ascendantLongitude,
                                     positions: onlyClassical)
            XCTAssertEqual(try Ashtakavarga.calculate(chart: withoutNodes), result)
        }
    }

    func testKakshyaLordsAndAllContributorActivationsAgainstPython() throws {
        let fixture = try fixture()
        for reference in fixture.kakshya {
            XCTAssertEqual(try Ashtakavarga.kakshyaLord(degreeInSign: reference.degree), reference.lord)
        }
        for reference in fixture.cases {
            for planet in Ashtakavarga.planetOrder {
                let expected = try XCTUnwrap(reference.activated[planet])
                for sign in 0..<12 {
                    for (index, lord) in Ashtakavarga.kakshyaOrder.enumerated() {
                        XCTAssertEqual(try Ashtakavarga.isKakshyaActivated(planet: planet, signIndex: sign,
                            kakshyaLord: lord, sourceSigns: reference.sourceSigns), expected[sign][index],
                            reference.label + "/" + planet + "/" + String(sign) + "/" + lord)
                    }
                }
            }
        }
    }

    func testInvalidSourcesPlanetsAndDegreesAreRejected() throws {
        let sources = try XCTUnwrap(fixture().cases.first).sourceSigns
        var missing = sources
        missing.removeValue(forKey: "Lagna")
        XCTAssertThrowsError(try Ashtakavarga.calculate(sourceSigns: missing))
        for invalid in [-1, 12, Int.max, Int.min] {
            var malformed = sources
            malformed["Sunce"] = invalid
            XCTAssertThrowsError(try Ashtakavarga.calculate(sourceSigns: malformed))
        }
        XCTAssertThrowsError(try Ashtakavarga.isKakshyaActivated(planet: "Rahu", signIndex: 0,
            kakshyaLord: "Lagna", sourceSigns: sources))
        XCTAssertThrowsError(try Ashtakavarga.isKakshyaActivated(planet: "Sunce", signIndex: 12,
            kakshyaLord: "Lagna", sourceSigns: sources))
        XCTAssertThrowsError(try Ashtakavarga.isKakshyaActivated(planet: "Sunce", signIndex: 0,
            kakshyaLord: "Rahu", sourceSigns: sources))
        for invalid in [Double.nan, .infinity, -.infinity, -1, 30.001] {
            XCTAssertThrowsError(try Ashtakavarga.kakshyaLord(degreeInSign: invalid))
        }
        let positions = Dictionary(uniqueKeysWithValues: Ashtakavarga.planetOrder.map {
            ($0, PlanetPosition(name: $0, longitude: 0, speed: 0))
        })
        let malformedChart = Chart(julianDay: 2451545, ascendantLongitude: .nan, positions: positions)
        XCTAssertThrowsError(try Ashtakavarga.calculate(chart: malformedChart))
        var malformedPositions = positions
        malformedPositions["Sunce"] = PlanetPosition(name: "Sunce", longitude: .nan, speed: 0)
        XCTAssertThrowsError(try Ashtakavarga.calculate(chart: Chart(julianDay: 2451545,
            ascendantLongitude: 0, positions: malformedPositions)))
    }
}
