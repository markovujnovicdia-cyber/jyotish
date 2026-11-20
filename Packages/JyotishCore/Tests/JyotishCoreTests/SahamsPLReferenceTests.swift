import Foundation
import XCTest
@testable import JyotishCore

final class SahamsPLReferenceTests: XCTestCase {
    private func positions(moon: Double = 40, saturn: Double = 70) -> [String: PlanetPosition] {
        let longitudes: [String: Double] = [
            "Sunce": 200, "Mjesec": moon, "Mars": 130, "Merkur": 250,
            "Jupiter": 100, "Venera": 300, "Saturn": saturn
        ]
        return Dictionary(uniqueKeysWithValues: longitudes.map { name, longitude in
            (name, PlanetPosition(name: name, longitude: longitude, speed: 1))
        })
    }

    func testRogaUsesSaturnAndReversesOperandsAtNight() throws {
        let source = positions()
        let day = try Sahams.calculate(ascendant: 10, positions: source, isDay: true, convention: .tajikaRoga)
        let night = try Sahams.calculate(ascendant: 10, positions: source, isDay: false, convention: .tajikaRoga)
        // Day: 70−40+10+30 = 70. Night: 40−70+10 wraps to 340;
        // the ascendant is inside that directed arc, so no 30° is added.
        XCTAssertEqual(try XCTUnwrap(day["Roga"]), 70, accuracy: 1e-10)
        XCTAssertEqual(try XCTUnwrap(night["Roga"]), 340, accuracy: 1e-10)
        let legacyDay = try Sahams.calculate(ascendant: 10, positions: source, isDay: true)
        let legacyNight = try Sahams.calculate(ascendant: 10, positions: source, isDay: false)
        XCTAssertEqual(try XCTUnwrap(legacyDay["Roga"]), 340, accuracy: 1e-10)
        XCTAssertEqual(try XCTUnwrap(legacyNight["Roga"]), 40, accuracy: 1e-10)
    }

    func testRogaArcCorrectionBoundaryAndCircularWrap() throws {
        // At the end of the directed Moon→Saturn arc no correction applies;
        // immediately outside it the inherited Tajika rule adds 30°.
        let boundary = try Sahams.calculate(ascendant: 70, positions: positions(), isDay: true, convention: .tajikaRoga)
        let outside = try Sahams.calculate(ascendant: 70.000001, positions: positions(), isDay: true, convention: .tajikaRoga)
        XCTAssertEqual(try XCTUnwrap(boundary["Roga"]), 100, accuracy: 1e-10)
        XCTAssertEqual(try XCTUnwrap(outside["Roga"]), 130.000001, accuracy: 1e-10)

        let source = positions(moon: 10, saturn: 350)
        let day = try Sahams.calculate(ascendant: 5, positions: source, isDay: true, convention: .tajikaRoga)
        let night = try Sahams.calculate(ascendant: 5, positions: source, isDay: false, convention: .tajikaRoga)
        XCTAssertEqual(try XCTUnwrap(day["Roga"]), 15, accuracy: 1e-10)
        XCTAssertEqual(try XCTUnwrap(night["Roga"]), 25, accuracy: 1e-10)
    }

    func testRogaConventionPreservesEveryOtherSahamAndLegacyDefault() throws {
        for isDay in [true, false] {
            for ascendant in [10.0, 100.0, 250.0, 359.0] {
                let original = try Sahams.calculate(ascendant: ascendant, positions: positions(), isDay: isDay)
                let explicitLegacy = try Sahams.calculate(ascendant: ascendant, positions: positions(), isDay: isDay, convention: .legacyPython)
                let corrected = try Sahams.calculate(ascendant: ascendant, positions: positions(), isDay: isDay, convention: .tajikaRoga)
                XCTAssertEqual(original, explicitLegacy)
                XCTAssertEqual(Set(corrected.keys), Set(Sahams.order))
                for name in Sahams.order where name != "Roga" {
                    XCTAssertEqual(corrected[name], original[name], "\(name), day=\(isDay), asc=\(ascendant)")
                }
            }
        }
    }

    func testAnnualYashaAndSastraMatchVisiblePL9ScreenshotWithinOneArcsecond() throws {
        // Expected values are transcribed from the user's PL9 Sahams report
        // for 2026–2027. They are independent external references. Unlike the
        // other visible Sahams, these formulas cancel the ascendant term;
        // they can be compared before exact PL coordinates are available.
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let zone = try XCTUnwrap(TimeZone(identifier: "Europe/Zagreb"))
        let annual = try Annual.calculate(
            birthDate: birth, latitude: 45.4881, longitude: 16.3745,
            year: 2026, birthTimeZone: zone, sahamsConvention: .tajikaRoga
        )
        let expectedYasha = 270.0 + 17 + 16.0 / 60 + 6.0 / 3600
        let expectedSastra = 30.0 + 26 + 40.0 / 60 + 25.0 / 3600
        XCTAssertEqual(try XCTUnwrap(annual.sahams["Yasha"]), expectedYasha, accuracy: 1.0 / 3600)
        XCTAssertEqual(try XCTUnwrap(annual.sahams["Sastra"]), expectedSastra, accuracy: 1.0 / 3600)
    }
}
