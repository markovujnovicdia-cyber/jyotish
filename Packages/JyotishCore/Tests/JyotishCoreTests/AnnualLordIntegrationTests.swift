import Foundation
import XCTest
@testable import JyotishCore

final class AnnualLordIntegrationTests: XCTestCase {
    private func referenceAnnual() throws -> AnnualResult {
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        return try Annual.calculate(
            birthDate: birth, latitude: 45.45, longitude: 16 + 22.0 / 60,
            year: 2026, birthTimeZone: TimeZone(identifier: "Europe/Zagreb")!,
            tajikaConvention: .longitudeBothOrbs, muddaYearConvention: .fixedGregorianYear,
            sahamsConvention: .tajikaSripati, nodeConvention: .meanTropicalTrueAyanamsa,
            timeConvention: .historical2019Forecast, varsheshwaraConvention: .signAspect
        )
    }

    private func months(_ annual: AnnualResult, withContext: Bool = true) throws -> [MasaResult] {
        try Annual.masa(
            natalSunLongitude: XCTUnwrap(annual.chart.positions["Sunce"]?.longitude),
            annualJulianDay: annual.chart.julianDay, latitude: 45.45, longitude: 16 + 22.0 / 60,
            nodeConvention: .meanTropicalTrueAyanamsa, timeConvention: .historical2019Forecast,
            annualContext: withContext ? annual : nil
        )
    }

    func testAnnualContextProducesSixReferenceLordsAndFullMunthaPositions() throws {
        let annual = try referenceAnnual()
        let result = try months(annual)
        XCTAssertEqual(result.count, 12)
        XCTAssertEqual(annual.munthaSignIndex, 1)
        XCTAssertEqual(annual.munthaLord, "Venera")
        // These six labels and degrees are transcribed from the PL9 report.
        let lords = ["Jupiter", "Venera", "Jupiter", "Venera", "Venera", "Venera"]
        let dms: [(Int, Int, Int)] = [(16,30,57), (18,56,6), (21,22,10), (23,50,12), (26,20,45), (28,53,44)]
        for (index, month) in result.prefix(6).enumerated() {
            XCTAssertEqual(month.monthLord?.winner?.planet, lords[index])
            let longitude = try XCTUnwrap(month.munthaLongitude)
            let (degree, minute, second) = dms[index]
            let reference = 30 + Double(degree) + Double(minute) / 60 + Double(second) / 3600
            // Inherited natal-ascendant discrepancy plus the report's own
            // 2″ natal/annual-base difference is ~5.7″. Do not fit it away.
            XCTAssertEqual(Astro.signedDifference(longitude - reference), 0, accuracy: 10.0 / 3600)
            XCTAssertEqual(month.munthaLord, "Venera")
        }
        XCTAssertEqual(result.first?.munthaLongitude, annual.munthaLongitude)
    }

    func testMissingAnnualContextDoesNotInventMonthlyLordsOrMuntha() throws {
        let result = try months(referenceAnnual(), withContext: false)
        XCTAssertEqual(result.count, 12)
        XCTAssertTrue(result.allSatisfy { $0.monthLord == nil && $0.munthaLongitude == nil && $0.munthaLord == nil })
    }

    func testMismatchedAnnualContextIsRejected() throws {
        let annual = try referenceAnnual()
        let sun = try XCTUnwrap(annual.chart.positions["Sunce"]?.longitude)
        XCTAssertThrowsError(try Annual.masa(
            natalSunLongitude: sun, annualJulianDay: annual.chart.julianDay + 1,
            latitude: 45.45, longitude: 16 + 22.0 / 60,
            nodeConvention: .meanTropicalTrueAyanamsa, timeConvention: .historical2019Forecast,
            annualContext: annual
        ))
        XCTAssertThrowsError(try Annual.masa(
            natalSunLongitude: sun + 1, annualJulianDay: annual.chart.julianDay,
            latitude: 45.45, longitude: 16 + 22.0 / 60,
            nodeConvention: .meanTropicalTrueAyanamsa, timeConvention: .historical2019Forecast,
            annualContext: annual
        ))
        XCTAssertThrowsError(try Annual.masa(
            natalSunLongitude: sun, annualJulianDay: annual.chart.julianDay,
            latitude: 45.45, longitude: 16 + 22.0 / 60, annualContext: annual
        ))
    }

    func testMonthlyMunthaKeepsAdvancingAcrossASignBoundary() throws {
        let annual = try referenceAnnual()
        let result = try months(annual)
        XCTAssertEqual(Int(try XCTUnwrap(result[0].munthaLongitude) / 30), 1)
        XCTAssertEqual(Int(try XCTUnwrap(result[6].munthaLongitude) / 30), 2)
        for (previous, next) in zip(result, result.dropFirst()) {
            XCTAssertGreaterThan(Astro.signedDifference(
                try XCTUnwrap(next.munthaLongitude) - XCTUnwrap(previous.munthaLongitude)
            ), 0)
        }
    }
}
