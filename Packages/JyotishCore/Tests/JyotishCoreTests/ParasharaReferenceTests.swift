import Foundation
import XCTest
@testable import JyotishCore

/// The expected pair lists are transcribed from the user's three-page PL9
/// "Marko / Tajika Yogas" PDF, not generated from Jyotish or OriginalPython.
/// The user identified the report as annual, 27 December 2026. The birth input
/// below comes from the earlier application screenshot, not from that PDF.
/// This validates those pair lists for that input; it does not establish all
/// sixteen yoga predicates, PL9 defaults, or planetary-position parity.
final class ParasharaReferenceTests: XCTestCase {
    private func pair(_ a: String, _ b: String) -> String {
        [a, b].sorted().joined(separator: "/")
    }

    private func pairs(_ relations: [TajikaRelation]) -> Set<String> {
        Set(relations.map { pair($0.planetA, $0.planetB) })
    }

    func testAnnual2026PairListsMatchSuppliedParasharaReport() throws {
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let zone = try XCTUnwrap(TimeZone(identifier: "Europe/Zagreb"))
        let annual = try Annual.calculate(
            birthDate: birth, latitude: 45.45, longitude: 16.0 + 22.0 / 60.0,
            year: 2026, birthTimeZone: zone,
            tajikaConvention: .longitudeBothOrbs
        )
        XCTAssertEqual(BirthMoment.localDateString(annual.returnDate, zoneID: zone.identifier), "2026-12-27")

        let applying: Set<String> = [
            pair("Merkur", "Sunce"), pair("Merkur", "Mars"),
            pair("Merkur", "Saturn"), pair("Sunce", "Mars"),
            pair("Sunce", "Saturn"), pair("Mjesec", "Jupiter")
        ]
        let separating: Set<String> = [
            pair("Mjesec", "Venera"), pair("Merkur", "Jupiter"),
            pair("Sunce", "Jupiter")
        ]
        XCTAssertEqual(annual.ithasala.count, 6)
        XCTAssertEqual(annual.isarapha.count, 3)
        XCTAssertEqual(pairs(annual.ithasala), applying)
        XCTAssertEqual(pairs(annual.isarapha), separating)
        XCTAssertTrue(annual.ithasala.allSatisfy { $0.withinOrb && $0.isApplying })
        XCTAssertTrue(annual.isarapha.allSatisfy { $0.withinOrb && $0.isSeparating })
    }

    func testOutOfSignConjunctionAndDefaultLegacyConvention() throws {
        // Synthetic adjacent signs: the conjunction must not disappear at 30°.
        let moon = PlanetPosition(name: "Mjesec", longitude: 29, speed: 13)
        let jupiter = PlanetPosition(name: "Jupiter", longitude: 31, speed: 0.08)
        let result = try Tajika.analyze(moon, jupiter, aspectConvention: .longitudeBothOrbs)
        XCTAssertEqual(result.aspect, "konjunkcija")
        XCTAssertEqual(result.orbDifference, 2, accuracy: 1e-12)
        XCTAssertTrue(result.withinOrb && result.isApplying)
        XCTAssertFalse(result.isExact || result.isSeparating)
        XCTAssertNil(try Tajika.analyze(moon, jupiter).aspect)
        XCTAssertNil(try Tajika.analyze(moon, jupiter, aspectConvention: .legacySignBased).aspect)
    }

    func testCircularConjunctionRetrogradeStationaryAndExactCases() throws {
        let jupiter = PlanetPosition(name: "Jupiter", longitude: 1, speed: 0)
        let forward = PlanetPosition(name: "Mjesec", longitude: 359, speed: 13)
        let backward = PlanetPosition(name: "Mjesec", longitude: 359, speed: -1)
        let stationary = PlanetPosition(name: "Mjesec", longitude: 359, speed: 0)
        for (moon, applying, separating) in [(forward, true, false), (backward, false, true), (stationary, false, false)] {
            for (a, b) in [(moon, jupiter), (jupiter, moon)] {
                let result = try Tajika.analyze(a, b, aspectConvention: .longitudeBothOrbs)
                XCTAssertEqual(result.aspect, "konjunkcija")
                XCTAssertEqual(result.orbDifference, 2, accuracy: 1e-12)
                XCTAssertTrue(result.withinOrb)
                XCTAssertFalse(result.isExact)
                XCTAssertEqual(result.isApplying, applying)
                XCTAssertEqual(result.isSeparating, separating)
            }
        }
        let exact = try Tajika.analyze(
            PlanetPosition(name: "Mjesec", longitude: 1, speed: 13), jupiter,
            aspectConvention: .longitudeBothOrbs
        )
        XCTAssertTrue(exact.withinOrb && exact.isExact)
        XCTAssertFalse(exact.isApplying || exact.isSeparating)
    }

    func testOrbMustBeWithinBothIndividualDeeptamshas() throws {
        // Synthetic square residual 7.8°: inside the average Venus/Jupiter orb
        // of 8°, but outside Venus's individual 7° orb. No calculated longitude
        // from our annual output is used as an external positional fixture.
        let venus = PlanetPosition(name: "Venera", longitude: 10, speed: 1)
        let jupiter = PlanetPosition(name: "Jupiter", longitude: 92.2, speed: 0.08)
        let geometric = try Tajika.analyze(venus, jupiter, aspectConvention: .longitudeBothOrbs)
        let legacy = try Tajika.analyze(venus, jupiter, aspectConvention: .legacySignBased)
        XCTAssertEqual(geometric.aspect, "kvadrat")
        XCTAssertEqual(geometric.orbDifference, 7.8, accuracy: 1e-12)
        XCTAssertFalse(geometric.withinOrb)
        XCTAssertTrue(legacy.withinOrb)
        let positions = [venus.name: venus, jupiter.name: jupiter]
        XCTAssertTrue(try Tajika.ithasala(positions: positions, aspectConvention: .longitudeBothOrbs).isEmpty)
        XCTAssertTrue(try Tajika.isarapha(positions: positions, aspectConvention: .longitudeBothOrbs).isEmpty)
    }

    func testIndividualOrbBoundaryIsInclusive() throws {
        let venus = PlanetPosition(name: "Venera", longitude: 10, speed: 1)
        let onBoundary = PlanetPosition(name: "Jupiter", longitude: 93, speed: 0.08)
        let outside = PlanetPosition(name: "Jupiter", longitude: 92.9999, speed: 0.08)
        XCTAssertTrue(try Tajika.analyze(venus, onBoundary, aspectConvention: .longitudeBothOrbs).withinOrb)
        XCTAssertFalse(try Tajika.analyze(venus, outside, aspectConvention: .longitudeBothOrbs).withinOrb)
    }

    func testAllAspectOrientationsAreSymmetricWhenPairIsSwapped() throws {
        let moon = PlanetPosition(name: "Mjesec", longitude: 1, speed: 13)
        for longitude in [3.0, 59, 89, 119, 179, 243, 273, 303] {
            let mars = PlanetPosition(name: "Mars", longitude: longitude, speed: 0.5)
            let forward = try Tajika.analyze(moon, mars, aspectConvention: .longitudeBothOrbs)
            let swapped = try Tajika.analyze(mars, moon, aspectConvention: .longitudeBothOrbs)
            XCTAssertNotNil(forward.aspect)
            XCTAssertEqual(forward.aspect, swapped.aspect)
            XCTAssertEqual(forward.orbDifference, swapped.orbDifference, accuracy: 1e-12)
            XCTAssertEqual(forward.withinOrb, swapped.withinOrb)
            XCTAssertEqual(forward.isApplying, swapped.isApplying)
            XCTAssertEqual(forward.isSeparating, swapped.isSeparating)
            XCTAssertEqual(forward.isExact, swapped.isExact)
        }
    }

    func testAnnual2026ManauPairsMatchSuppliedParasharaReport() throws {
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let zone = try XCTUnwrap(TimeZone(identifier: "Europe/Zagreb"))
        let annual = try Annual.calculate(
            birthDate: birth, latitude: 45.45, longitude: 16.0 + 22.0 / 60.0,
            year: 2026, birthTimeZone: zone, tajikaConvention: .longitudeBothOrbs
        )
        var actual: Set<String> = []
        for relation in annual.ithasala {
            let yogas = try Tajika.karyeshaYogas(
                lagnesha: relation.planetA, karyesha: relation.planetB,
                positions: annual.chart.positions, ascendantSign: annual.chart.ascendantSign,
                speedConvention: .ephemeris, aspectConvention: .longitudeBothOrbs
            )
            if try XCTUnwrap(yogas.first(where: { $0.name == "Manau" })).found {
                actual.insert(pair(relation.planetA, relation.planetB))
            }
        }
        let expected: Set<String> = [
            pair("Merkur", "Sunce"), pair("Merkur", "Mars"),
            pair("Merkur", "Saturn"), pair("Sunce", "Mars"),
            pair("Sunce", "Saturn")
        ]
        XCTAssertEqual(actual, expected)
    }

    func testManauIncludesHostileSquareAndOppositionButNotTrine() throws {
        // Synthetic direct Mercury/Sun Ithasala with an independent malefic.
        var positions = Dictionary(uniqueKeysWithValues: [
            PlanetPosition(name: "Mjesec", longitude: 220, speed: 13),
            PlanetPosition(name: "Merkur", longitude: 10, speed: 1.2),
            PlanetPosition(name: "Venera", longitude: 255, speed: 1.18),
            PlanetPosition(name: "Sunce", longitude: 15, speed: 0.986),
            PlanetPosition(name: "Mars", longitude: 100, speed: 0.524),
            PlanetPosition(name: "Jupiter", longitude: 300, speed: 0.083),
            PlanetPosition(name: "Saturn", longitude: 200, speed: 0.034)
        ].map { ($0.name, $0) })
        for (longitude, expected) in [(100.0, true), (190.0, true), (130.0, false)] {
            positions["Mars"] = PlanetPosition(name: "Mars", longitude: longitude, speed: 0.524)
            let yogas = try Tajika.karyeshaYogas(
                lagnesha: "Merkur", karyesha: "Sunce", positions: positions,
                ascendantSign: 0, speedConvention: .ephemeris,
                aspectConvention: .longitudeBothOrbs
            )
            XCTAssertTrue(try XCTUnwrap(yogas.first(where: { $0.name == "Ithasala" })).found)
            XCTAssertEqual(try XCTUnwrap(yogas.first(where: { $0.name == "Manau" })).found, expected)
        }
    }

    func testManauDoesNotCountTheFasterMaleficsSelfAspect() throws {
        let positions = Dictionary(uniqueKeysWithValues: [
            PlanetPosition(name: "Mjesec", longitude: 220, speed: 13),
            PlanetPosition(name: "Merkur", longitude: 70, speed: 1.2),
            PlanetPosition(name: "Venera", longitude: 310, speed: 1.18),
            PlanetPosition(name: "Sunce", longitude: 170, speed: 0.986),
            PlanetPosition(name: "Mars", longitude: 10, speed: 0.524),
            PlanetPosition(name: "Jupiter", longitude: 15, speed: 0.083),
            PlanetPosition(name: "Saturn", longitude: 250, speed: 0.034)
        ].map { ($0.name, $0) })
        let yogas = try Tajika.karyeshaYogas(
            lagnesha: "Mars", karyesha: "Jupiter", positions: positions,
            ascendantSign: 0, speedConvention: .ephemeris,
            aspectConvention: .longitudeBothOrbs
        )
        XCTAssertTrue(try XCTUnwrap(yogas.first(where: { $0.name == "Ithasala" })).found)
        XCTAssertFalse(try XCTUnwrap(yogas.first(where: { $0.name == "Manau" })).found)
    }

    func testSevenClassicalNatalPlanetLongitudesAgainstSuppliedPL9Screenshot() throws {
        // Transcribed D:M:S, not regenerated from this application's ephemeris.
        // Planet longitudes do not depend on the still-unconfirmed Sisak coordinates.
        // The legacy node mode differs by about 8.75 arcseconds; the app's
        // alternate coordinate convention is separately checked against both
        // external epochs in NodePLReferenceTests, without a fitted offset.
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let chart = try Ephemeris.chart(date: birth, latitude: 45.45, longitude: 16.0 + 22.0 / 60.0)
        let expected: [(String, Int, Int, Int, Int)] = [
            ("Sunce", 8, 11, 16, 27), ("Mjesec", 10, 20, 4, 21),
            ("Mars", 8, 2, 18, 30), ("Merkur", 8, 29, 30, 45),
            ("Jupiter", 0, 28, 19, 6), ("Venera", 9, 26, 10, 11),
            ("Saturn", 3, 22, 35, 36)
        ]
        for (name, sign, degree, minute, second) in expected {
            let reference = Double(sign * 30 + degree) + Double(minute) / 60 + Double(second) / 3600
            let actual = try XCTUnwrap(chart.positions[name])
            XCTAssertEqual(Astro.signedDifference(actual.longitude - reference), 0,
                           accuracy: 1.0 / 3600, name)
        }
    }

}
