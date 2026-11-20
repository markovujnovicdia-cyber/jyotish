import Foundation
import XCTest
import CSwissEphemeris
@testable import JyotishCore

final class EphemerisTimeReferenceTests: XCTestCase {
    private let latitude = 45.45
    private let longitude = 16.0 + 22.0 / 60.0

    private func date(_ text: String) throws -> Date {
        try XCTUnwrap(ISO8601DateFormatter().date(from: text))
    }

    func testPublishedHistoricalForecastAgainstSeparatelyCompiledOfficialSource() {
        // Values obtained by separately compiling the unchanged authoritative
        // swephlib.c at commit cb7971a07d166ff8768e22247f63568718f2cd66,
        // then invoking its swe_deltat_ex(JD, SEFLG_SWIEPH). The test does not
        // duplicate the forecast polynomial or fit any PL9 timestamp.
        let references: [(Double, Double)] = [
            (2458849.5, 71.06802400174463), // 2020-01-01
            (2461041.5, 80.61777647656066), // 2026-01-01
            (2469807.5, 121.0402666163191), // 2050-01-01, blended branch
            (2524593.5, 427.6400000000001) // 2200-01-01, quadratic branch
        ]
        for (jd, seconds) in references {
            XCTAssertEqual(jy_historical_2019_forecast_seconds(jd), seconds, accuracy: 1e-10)
        }
        XCTAssertTrue(jy_historical_2019_forecast_seconds(2451545).isNaN)
        XCTAssertTrue(jy_historical_2019_forecast_seconds(.nan).isNaN)
        XCTAssertTrue(jy_historical_2019_forecast_seconds(.infinity).isNaN)
    }

    func testHistoricalForecastMatchesPrintedAnnualReturnAndAscendant() throws {
        // Exact place and birth time are confirmed by the user's PL9 location
        // screenshot. var.pdf gives the independent annual timestamp/ascendant.
        let birth = try date("1976-12-26T10:55:00Z")
        let zone = try XCTUnwrap(TimeZone(identifier: "Europe/Zagreb"))
        let annual = try Annual.calculate(
            birthDate: birth, latitude: latitude, longitude: longitude,
            year: 2026, birthTimeZone: zone, nodeConvention: .meanTropicalTrueAyanamsa,
            timeConvention: .historical2019Forecast
        )
        let printedReturn = try date("2026-12-27T06:43:23Z")
        XCTAssertEqual(annual.returnDate.timeIntervalSince1970,
                       printedReturn.timeIntervalSince1970, accuracy: 0.5)
        let printedAscendant = 252.0 + 15.0 / 60.0 + 23.0 / 3600.0
        // The remaining ~2.3″ residual and the root solver's 1e-6° solar
        // tolerance are recorded explicitly; no ascendant offset is applied.
        XCTAssertEqual(Astro.signedDifference(annual.chart.ascendantLongitude - printedAscendant),
                       0, accuracy: 4.0 / 3600)
        let current = try Annual.calculate(
            birthDate: birth, latitude: latitude, longitude: longitude,
            year: 2026, birthTimeZone: zone
        )
        XCTAssertGreaterThan(current.returnDate.timeIntervalSince(annual.returnDate), 10)
        XCTAssertLessThan(current.returnDate.timeIntervalSince(annual.returnDate), 20)
    }

    func testHistoricalForecastPreservesCurrentObservedBirthEpoch() throws {
        let birth = try date("1976-12-26T10:55:00Z")
        let later = Ephemeris.julianDay(date: try date("2026-12-27T06:43:23Z"))
        let current = try Ephemeris.chart(date: birth, latitude: latitude, longitude: longitude)
        _ = try Ephemeris.positions(julianDay: later, timeConvention: .historical2019Forecast)
        let historical = try Ephemeris.chart(
            date: birth, latitude: latitude, longitude: longitude,
            timeConvention: .historical2019Forecast
        )
        XCTAssertEqual(historical.positions, current.positions)
        XCTAssertEqual(historical.ascendantLongitude, current.ascendantLongitude)
        XCTAssertEqual(historical.julianDay, current.julianDay)
    }

    func testTimeModesDoNotLeakAcrossPublicEphemerisOperations() throws {
        let jd = Ephemeris.julianDay(date: try date("2026-12-27T06:43:23Z"))
        let currentPositions = try Ephemeris.positions(julianDay: jd)
        let currentSun = try Ephemeris.sunLongitude(julianDay: jd)
        let currentAscendant = try Ephemeris.ascendant(julianDay: jd, latitude: latitude, longitude: longitude)
        let currentCusps = try Ephemeris.sripatiCusps(julianDay: jd, latitude: latitude, longitude: longitude)
        let currentRise = try Ephemeris.riseOrSet(julianDay: jd, latitude: latitude, longitude: longitude, isRise: true)

        _ = try Ephemeris.positions(julianDay: jd, timeConvention: .historical2019Forecast)
        XCTAssertEqual(try Ephemeris.sunLongitude(julianDay: jd), currentSun)
        _ = try Ephemeris.sunLongitude(julianDay: jd, timeConvention: .historical2019Forecast)
        XCTAssertEqual(try Ephemeris.positions(julianDay: jd), currentPositions)
        _ = try Ephemeris.positions(julianDay: jd, timeConvention: .historical2019Forecast)
        XCTAssertEqual(try Ephemeris.ascendant(julianDay: jd, latitude: latitude, longitude: longitude), currentAscendant)
        _ = try Ephemeris.positions(julianDay: jd, timeConvention: .historical2019Forecast)
        XCTAssertEqual(try Ephemeris.sripatiCusps(julianDay: jd, latitude: latitude, longitude: longitude), currentCusps)
        _ = try Ephemeris.positions(julianDay: jd, timeConvention: .historical2019Forecast)
        XCTAssertEqual(try Ephemeris.riseOrSet(julianDay: jd, latitude: latitude, longitude: longitude, isRise: true), currentRise)
    }
}
