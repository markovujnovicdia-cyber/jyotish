import Foundation
import XCTest
@testable import JyotishCore

final class MasaLordPLReferenceTests: XCTestCase {
    func testSixVisibleMonthlyLordsAgainstSuppliedPL9Report() throws {
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let latitude = 45.45, longitude = 16 + 22.0 / 60
        let natal = try Ephemeris.chart(date: birth, latitude: latitude, longitude: longitude,
                                       timeConvention: .historical2019Forecast)
        let annual = try Annual.calculate(birthDate: birth, latitude: latitude, longitude: longitude,
                                         year: 2026, birthTimeZone: TimeZone(identifier: "Europe/Zagreb")!,
                                         timeConvention: .historical2019Forecast)
        let yearElection = try Varsheshwara.calculate(natalAscendantSign: natal.ascendantSign,
                                                     munthaSign: annual.munthaSignIndex,
                                                     chart: annual.chart, isDaytime: annual.isDay,
                                                     convention: .signAspect)
        let yearLord = try XCTUnwrap(yearElection.winner?.planet)
        XCTAssertEqual(yearLord, "Jupiter")
        let months = try Annual.masa(natalSunLongitude: natal.positions["Sunce"]!.longitude,
                                    annualJulianDay: annual.chart.julianDay,
                                    latitude: latitude, longitude: longitude,
                                    timeConvention: .historical2019Forecast)
        // ML labels transcribed from the six complete visible panels in the
        // user's PL9 screenshot (December 2026 through May 2027). Both fixed
        // annual and progressed monthly Muntha remain in Taurus for these six
        // panels; this test does not disambiguate their later candidate scope.
        let expected = ["Jupiter", "Venera", "Jupiter", "Venera", "Venera", "Venera"]
        XCTAssertEqual(months.count, 12)
        for (month, lord) in zip(months, expected) {
            let day = try Ephemeris.isDaytime(julianDay: month.chart.julianDay,
                                             latitude: latitude, longitude: longitude,
                                             timeConvention: .historical2019Forecast)
            let result = try MasaLord.calculate(natalAscendantSign: natal.ascendantSign,
                                                annualLord: yearLord, munthaSign: annual.munthaSignIndex,
                                                chart: month.chart, isDaytime: day)
            XCTAssertEqual(result.winner?.planet, lord, "Month \(month.monthNumber)")
            XCTAssertEqual(result.candidates.count, 6)
            XCTAssertTrue(result.candidates.contains { $0.role == "Masa Lagna Pati" })
            XCTAssertTrue(result.candidates.contains { $0.role == "Varshesha" && $0.planet == yearLord })
        }
    }

    func testAnnualLordIsASeparateEligibleSixthCandidate() throws {
        let chart = syntheticChart()
        let without = try MasaLord.calculate(natalAscendantSign: 2, annualLord: nil,
                                             munthaSign: 2, chart: chart, isDaytime: true)
        let with = try MasaLord.calculate(natalAscendantSign: 2, annualLord: "Jupiter",
                                          munthaSign: 2, chart: chart, isDaytime: true)
        XCTAssertEqual(without.candidates.count, 5)
        XCTAssertEqual(with.candidates.count, 6)
        XCTAssertFalse(without.candidates.contains { $0.planet == "Jupiter" })
        XCTAssertEqual(with.winner?.planet, "Jupiter")
        XCTAssertEqual(with.winner?.role, "Varshesha")
    }

    func testMunthaCandidateUsesExplicitCallerSign() throws {
        let chart = syntheticChart()
        let mercury = try MasaLord.calculate(natalAscendantSign: 2, annualLord: "Jupiter",
                                             munthaSign: 2, chart: chart, isDaytime: true)
        let venus = try MasaLord.calculate(natalAscendantSign: 2, annualLord: "Jupiter",
                                           munthaSign: 1, chart: chart, isDaytime: true)
        XCTAssertEqual(mercury.candidates.first { $0.role == "Muntha Pati" }?.planet, "Merkur")
        XCTAssertEqual(venus.candidates.first { $0.role == "Muntha Pati" }?.planet, "Venera")
    }

    func testInvalidMonthlyElectionInputsThrow() throws {
        let chart = syntheticChart()
        XCTAssertThrowsError(try MasaLord.calculate(natalAscendantSign: -1, annualLord: nil,
                                                    munthaSign: 1, chart: chart, isDaytime: true))
        XCTAssertThrowsError(try MasaLord.calculate(natalAscendantSign: 2, annualLord: "Rahu",
                                                    munthaSign: 1, chart: chart, isDaytime: true))
        XCTAssertThrowsError(try MasaLord.calculate(natalAscendantSign: 2, annualLord: nil,
                                                    munthaSign: 12, chart: chart, isDaytime: true))
        XCTAssertThrowsError(try MasaLord.calculate(natalAscendantSign: 2, annualLord: nil,
                                                    munthaSign: 1,
                                                    chart: Chart(julianDay: 2451545, ascendantLongitude: 0, positions: [:]),
                                                    isDaytime: true))
    }

    private func syntheticChart() -> Chart {
        let longitudes: [String: Double] = [
            "Mjesec": 103, "Merkur": 100, "Venera": 15, "Sunce": 280,
            "Mars": 118, "Jupiter": 95, "Saturn": 125
        ]
        let positions = Dictionary(uniqueKeysWithValues: longitudes.map {
            ($0.key, PlanetPosition(name: $0.key, longitude: $0.value, speed: 1))
        })
        return Chart(julianDay: 2451545, ascendantLongitude: 10, positions: positions)
    }
}
