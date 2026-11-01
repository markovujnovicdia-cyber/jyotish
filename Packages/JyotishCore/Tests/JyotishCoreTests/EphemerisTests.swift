import XCTest
import Foundation
import Dispatch
@testable import JyotishCore

final class EphemerisTests: XCTestCase {
    func testBundledSwissFilesAndLicenseAreAvailable() throws {
        let chart = try Ephemeris.chart(date: Ephemeris.date(julianDay: 2451545), latitude: 45.44, longitude: 16.28)
        XCTAssertEqual(Ephemeris.version, "2.10.03")
        // Python 2.10.03 with the SAME bundled files and Lahiri flags 65858.
        XCTAssertEqual(try XCTUnwrap(chart.positions["Sunce"]).longitude, 256.51569618387066, accuracy: 1e-7)
        XCTAssertEqual(try XCTUnwrap(chart.positions["Mjesec"]).longitude, 199.47052896032176, accuracy: 1e-7)
        XCTAssertEqual(chart.ascendantLongitude, 23.42376796443993, accuracy: 1e-7)
        XCTAssertEqual(chart.positions.count, 9)
        XCTAssertTrue(Ephemeris.licenseNotice.contains("Professional License"))
        XCTAssertTrue(Ephemeris.licenseNotice.contains("GNU AFFERO GENERAL PUBLIC LICENSE"))
    }

    func testInvalidLocationsAndDatesAreRejectedBeforeCallingC() {
        let date = Ephemeris.date(julianDay: 2451545)
        for latitude in [Double.nan, .infinity, -90, 90] {
            XCTAssertThrowsError(try Ephemeris.chart(date: date, latitude: latitude, longitude: 0))
        }
        for longitude in [Double.nan, .infinity, -180.01, 180.01] {
            XCTAssertThrowsError(try Ephemeris.chart(date: date, latitude: 0, longitude: longitude))
        }
        for jd in [Double.nan, .infinity, 2378496.49, 2597641.5] {
            XCTAssertThrowsError(try Ephemeris.positions(julianDay: jd))
        }
    }

    func testNegativeSubnormalLongitudeCannotCreateThirteenthSign() throws {
        XCTAssertEqual(Astro.normalize(-Double.leastNonzeroMagnitude), 0)
        XCTAssertEqual(PlanetPosition(name: "Sunce", longitude: -Double.leastNonzeroMagnitude, speed: 1).signIndex, 0)
        XCTAssertEqual(try Varga.d1.signIndex(longitude: -Double.leastNonzeroMagnitude), 0)
    }

    func testConcurrentCallsDoNotCorruptSwissGlobalState() throws {
        let instants = [2451545.0, 2446350.510416667, 2460983.5]
        let expected = try instants.map { try Ephemeris.positions(julianDay: $0) }
        let failures = Failures()
        DispatchQueue.concurrentPerform(iterations: 48) { index in
            let slot = index % instants.count
            do {
                let result = try Ephemeris.positions(julianDay: instants[slot])
                if result != expected[slot] { failures.append("Concurrent result differs") }
            } catch { failures.append(error.localizedDescription) }
        }
        XCTAssertTrue(failures.messages.isEmpty, failures.messages.joined(separator: "; "))
    }

    private final class Failures: @unchecked Sendable {
        private let lock = NSLock()
        private(set) var messages: [String] = []
        func append(_ value: String) { lock.lock(); defer { lock.unlock() }; messages.append(value) }
    }
}
