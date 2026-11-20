import Foundation
import XCTest
@testable import JyotishCore

final class SripatiPLReferenceTests: XCTestCase {
    private func dms(_ sign: Int, _ degree: Int, _ minute: Int, _ second: Int) -> Double {
        Double(sign * 30 + degree) + Double(minute) / 60 + Double(second) / 3600
    }

    private var referencePositions: [String: PlanetPosition] {
        let longitudes: [String: Double] = [
            "Sunce": dms(8, 11, 16, 27), "Mjesec": dms(3, 26, 27, 48),
            "Mars": dms(4, 14, 58, 27), "Merkur": dms(8, 8, 9, 9),
            "Jupiter": dms(4, 2, 27, 27), "Venera": dms(6, 24, 37, 21),
            "Saturn": dms(11, 13, 56, 11)
        ]
        return Dictionary(uniqueKeysWithValues: longitudes.map { name, longitude in
            (name, PlanetPosition(name: name, longitude: longitude, speed: 1))
        })
    }

    func testArthaAndParadesaMatchPLReportUsingItsPrintedReturnTime() throws {
        // Source: the user's PL9 annual PDF prints 27 December 2026,
        // 07:43:23 CET in Sisak. Coordinates were explicitly supplied as
        // 45N27'00", 16E22'00"; none are inferred from the expected Sahams.
        let date = try XCTUnwrap(ISO8601DateFormatter().date(from: "2026-12-27T06:43:23Z"))
        let cusps = try Ephemeris.sripatiCusps(
            julianDay: Ephemeris.julianDay(date: date),
            latitude: 45.45, longitude: 16 + 22.0 / 60
        )
        let result = try Sahams.calculate(
            ascendant: dms(8, 12, 15, 23), positions: referencePositions,
            isDay: true, convention: .tajikaSripati, houseCusps: cusps
        )
        // The report rounds UTC to 1 second. The relevant Sripati cusp
        // rates here are below 16 arcseconds/second, so ±0.5 s allows 8″.
        // The two displayed DMS operands add at most another 1″, plus
        // 0.5″ for the expected displayed result: a conservative 10″ total.
        // Actual residuals are −0.93″ and +2.37″; the tolerance is not an
        // adjustment of the computed longitude or solar-return timestamp.
        let roundingBudget = 10.0 / 3600
        XCTAssertEqual(Astro.signedDifference(try XCTUnwrap(result["Artha"]) - dms(6, 20, 10, 12)),
                       0, accuracy: roundingBudget)
        XCTAssertEqual(Astro.signedDifference(try XCTUnwrap(result["Paradesa"]) - dms(5, 2, 25, 33)),
                       0, accuracy: roundingBudget)
    }

    func testHouseLongitudesUseSripatiButLordsUseWholeSignHouses() throws {
        let ascendant = 252.25 // Sagittarius; whole-sign ninth house is Leo.
        var cusps = (0..<12).map { Astro.normalize(ascendant + Double($0) * 30) }
        cusps[1] = 291.85
        cusps[8] = 151.4 // Virgo; its Mercury lord must not replace Leo's Sun.
        var positions = referencePositions
        positions["Sunce"] = PlanetPosition(name: "Sunce", longitude: 250, speed: 1)
        positions["Merkur"] = PlanetPosition(name: "Merkur", longitude: 20, speed: 1)
        positions["Saturn"] = PlanetPosition(name: "Saturn", longitude: 344, speed: 1)
        let result = try Sahams.calculate(
            ascendant: ascendant, positions: positions, isDay: true,
            convention: .tajikaSripati, houseCusps: cusps
        )
        // House 2 − Saturn + Asc; house 9 − Sun + Asc. Both directed
        // arcs contain the ascendant and therefore need no 30° addition.
        XCTAssertEqual(try XCTUnwrap(result["Artha"]), 200.1, accuracy: 1e-10)
        XCTAssertEqual(try XCTUnwrap(result["Paradesa"]), 153.65, accuracy: 1e-10)
    }

    func testSripatiSahamModeRejectsMissingOrMalformedCusps() throws {
        let ascendant = 252.25
        let valid = (0..<12).map { Astro.normalize(ascendant + Double($0) * 30) }
        XCTAssertThrowsError(try Sahams.calculate(
            ascendant: ascendant, positions: referencePositions, isDay: true,
            convention: .tajikaSripati
        ))
        var nonfinite = valid
        nonfinite[8] = .nan
        var infinite = valid
        infinite[1] = .infinity
        for invalid in [[], Array(valid.dropLast()), valid + [10], nonfinite, infinite] {
            XCTAssertThrowsError(try Sahams.calculate(
                ascendant: ascendant, positions: referencePositions, isDay: true,
                convention: .tajikaSripati, houseCusps: invalid
            ))
        }
    }

    func testSripatiHelperReturnsTwelveFiniteAnglesAndRejectsInvalidInputs() throws {
        let date = try XCTUnwrap(ISO8601DateFormatter().date(from: "2026-12-27T06:43:23Z"))
        let jd = Ephemeris.julianDay(date: date)
        let cusps = try Ephemeris.sripatiCusps(julianDay: jd, latitude: 45.45, longitude: 16 + 22.0 / 60)
        XCTAssertEqual(cusps.count, 12)
        XCTAssertTrue(cusps.allSatisfy { $0.isFinite && (0..<360).contains($0) })
        XCTAssertEqual(cusps[0], try Ephemeris.ascendant(julianDay: jd, latitude: 45.45, longitude: 16 + 22.0 / 60), accuracy: 1e-10)
        for index in 0..<6 {
            XCTAssertEqual(Astro.normalize(cusps[index + 6] - cusps[index]), 180, accuracy: 1e-10)
        }
        XCTAssertThrowsError(try Ephemeris.sripatiCusps(julianDay: .nan, latitude: 45.45, longitude: 16))
        XCTAssertThrowsError(try Ephemeris.sripatiCusps(julianDay: jd, latitude: 90, longitude: 16))
        XCTAssertThrowsError(try Ephemeris.sripatiCusps(julianDay: jd, latitude: 45.45, longitude: 181))
    }
}
