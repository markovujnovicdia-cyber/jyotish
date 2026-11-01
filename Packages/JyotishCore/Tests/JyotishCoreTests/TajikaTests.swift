import Foundation
import XCTest
@testable import JyotishCore

final class TajikaTests: XCTestCase {
    private struct Fixture: Decodable {
        let relations: [PairFixture]
        let strength: [StrengthFixture]
        let yogas: [YogaFixture]
        let candidates: [CandidateFixture]
    }
    private struct PairFixture: Decodable {
        let a: String, b: String
        let longitudeA: Double, longitudeB: Double, speedA: Double, speedB: Double
        let expected: ExpectedRelation
    }
    private struct ExpectedRelation: Decodable {
        let planetA: String, planetB: String, faster: String, slower: String
        let aspect: String?
        let orbDiff: Double, combinedOrb: Double, relativeSpeed: Double
        let withinOrb: Bool, isApplying: Bool, isExact: Bool, isSeparating: Bool
    }
    private struct StrengthFixture: Decodable {
        let planet: String
        let longitude: Double, total: Double
    }
    private struct PositionFixture: Decodable {
        let name: String
        let longitude: Double, speed: Double
        var position: PlanetPosition { PlanetPosition(name: name, longitude: longitude, speed: speed) }
    }
    private struct YogaFixture: Decodable {
        let lagnesha: String, karyesha: String
        let ascendantSign: Int
        let positions: [PositionFixture]
        let expected: [String: Bool]
        let global: [String: Bool]
    }
    private struct ExpectedCandidate: Decodable {
        let role: String, planet: String
        let strengthScore: Double
        let aspectsAscendant: Bool
    }
    private struct CandidateFixture: Decodable {
        let natalSign: Int, munthaSign: Int
        let ascendant: Double
        let isDay: Bool
        let positions: [PositionFixture]
        let expected: [ExpectedCandidate]
        let winnerRole: String?
    }

    private func fixture() throws -> Fixture {
        let url = try XCTUnwrap(Bundle.module.url(forResource: "TajikaReference", withExtension: "json"))
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try decoder.decode(Fixture.self, from: Data(contentsOf: url))
    }

    func testAspectsAgainstUnmodifiedPythonReference() throws {
        let fixtures = try fixture().relations
        XCTAssertEqual(fixtures.count, 120)
        for f in fixtures {
            let result = try Tajika.analyze(PlanetPosition(name: f.a, longitude: f.longitudeA, speed: f.speedA),
                                            PlanetPosition(name: f.b, longitude: f.longitudeB, speed: f.speedB))
            let e = f.expected
            XCTAssertEqual(result.planetA, e.planetA)
            XCTAssertEqual(result.planetB, e.planetB)
            XCTAssertEqual(result.faster, e.faster)
            XCTAssertEqual(result.slower, e.slower)
            XCTAssertEqual(result.aspect, e.aspect)
            XCTAssertEqual(result.orbDifference, e.orbDiff, accuracy: 1e-10)
            XCTAssertEqual(result.combinedOrb, e.combinedOrb, accuracy: 1e-10)
            XCTAssertEqual(result.relativeSpeed, e.relativeSpeed, accuracy: 1e-10)
            XCTAssertEqual(result.withinOrb, e.withinOrb)
            XCTAssertEqual(result.isApplying, e.isApplying)
            XCTAssertEqual(result.isExact, e.isExact)
            XCTAssertEqual(result.isSeparating, e.isSeparating)
        }
    }

    func testAllFiveBalaComponentsAgainstPythonTotals() throws {
        let fixtures = try fixture().strength
        XCTAssertEqual(fixtures.count, 504)
        for f in fixtures {
            let result = try Varsheshwara.bala(planet: f.planet, longitude: f.longitude)
            XCTAssertEqual(result.total, f.total, accuracy: 1e-10, "\(f.planet) at \(f.longitude)")
            XCTAssertTrue((0...30).contains(result.kshetra))
            XCTAssertTrue((0...20).contains(result.uchcha))
            XCTAssertTrue((0...15).contains(result.hadda))
            XCTAssertTrue((0...10).contains(result.drekkana))
            XCTAssertTrue((0...5).contains(result.navamsa))
        }
    }

    func testEveryPairAndGlobalYogaAgainstPython() throws {
        let fixtures = try fixture().yogas
        XCTAssertEqual(fixtures.count, 252)
        for f in fixtures {
            let positions = Dictionary(uniqueKeysWithValues: f.positions.map { ($0.name, $0.position) })
            let result = try Tajika.karyeshaYogas(lagnesha: f.lagnesha, karyesha: f.karyesha,
                                                 positions: positions, ascendantSign: f.ascendantSign)
            XCTAssertEqual(Dictionary(uniqueKeysWithValues: result.map { ($0.name, $0.found) }), f.expected,
                           "\(f.lagnesha)/\(f.karyesha), ascendant \(f.ascendantSign)")
            let global = try Tajika.globalYogas(positions: positions, ascendantSign: f.ascendantSign)
            XCTAssertEqual(Dictionary(uniqueKeysWithValues: global.map { ($0.name, $0.found) }), f.global)
        }
    }

    func testAllCandidatesAndElectionAgainstPython() throws {
        let fixtures = try fixture().candidates
        XCTAssertEqual(fixtures.count, 12)
        for f in fixtures {
            let positions = Dictionary(uniqueKeysWithValues: f.positions.map { ($0.name, $0.position) })
            let chart = Chart(julianDay: 2451545, ascendantLongitude: f.ascendant, positions: positions)
            let result = try Varsheshwara.calculate(natalAscendantSign: f.natalSign, munthaSign: f.munthaSign,
                                                    chart: chart, isDaytime: f.isDay)
            XCTAssertEqual(result.candidates.count, f.expected.count)
            for (candidate, expected) in zip(result.candidates, f.expected) {
                XCTAssertEqual(candidate.role, expected.role)
                XCTAssertEqual(candidate.planet, expected.planet)
                XCTAssertEqual(candidate.aspectsAscendant, expected.aspectsAscendant)
                XCTAssertEqual(candidate.strengthScore, expected.strengthScore, accuracy: 1e-12)
            }
            XCTAssertEqual(result.winner?.role, f.winnerRole)
        }
    }

    func testMirroredTrineExactAndNotApplyingOrSeparating() throws {
        let moon = PlanetPosition(name: "Mjesec", longitude: 125, speed: 13)
        let mars = PlanetPosition(name: "Mars", longitude: 5, speed: 0.5)
        for (a, b) in [(moon, mars), (mars, moon)] {
            let r = try Tajika.analyze(a, b)
            XCTAssertEqual(r.aspect, "trigon")
            XCTAssertEqual(r.orbDifference, 0, accuracy: 1e-12)
            XCTAssertTrue(r.isExact && r.withinOrb)
            XCTAssertFalse(r.isApplying || r.isSeparating)
        }
        XCTAssertTrue(try Tajika.ithasala(positions: [moon.name: moon, mars.name: mars]).isEmpty)
        XCTAssertTrue(try Tajika.isarapha(positions: [moon.name: moon, mars.name: mars]).isEmpty)
    }

    func testSignedAndStationarySpeeds() throws {
        let mercury = PlanetPosition(name: "Merkur", longitude: 5, speed: 1)
        let moon = PlanetPosition(name: "Mjesec", longitude: 0, speed: 13)
        XCTAssertTrue(try Tajika.analyze(moon, mercury).isApplying)
        XCTAssertTrue(try Tajika.analyze(PlanetPosition(name: "Mjesec", longitude: 0, speed: -1), mercury).isSeparating)
        let stationary = try Tajika.analyze(PlanetPosition(name: "Mjesec", longitude: 0, speed: 0),
                                            PlanetPosition(name: "Merkur", longitude: 5, speed: 0))
        XCTAssertFalse(stationary.isApplying || stationary.isSeparating)
    }

    func testNoUnqualifiedYearLordIsInvented() throws {
        let positions = Dictionary(uniqueKeysWithValues: Tajika.planets.map {
            ($0, PlanetPosition(name: $0, longitude: 340, speed: 1))
        })
        let result = try Varsheshwara.calculate(natalAscendantSign: 0, munthaSign: 0,
                                                chart: Chart(julianDay: 2451545, ascendantLongitude: 22, positions: positions),
                                                isDaytime: true)
        XCTAssertNil(result.winner)
        XCTAssertFalse(result.anyQualified)
        XCTAssertTrue(result.candidates.allSatisfy { !$0.aspectsAscendant })
    }

    func testMissingOrUnsupportedPlanetsThrow() throws {
        XCTAssertThrowsError(try Tajika.analyze(PlanetPosition(name: "Rahu", longitude: 0, speed: -0.05),
                                                PlanetPosition(name: "Mars", longitude: 0, speed: 1)))
        XCTAssertThrowsError(try Tajika.karyeshaYogas(lagnesha: "Mars", karyesha: "Venera", positions: [:], ascendantSign: 0))
        XCTAssertThrowsError(try Varsheshwara.bala(planet: "Mars", longitude: .nan))
    }
}
