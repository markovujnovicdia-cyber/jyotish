import Foundation
import XCTest
@testable import JyotishCore

final class VimshottariPLSettingsTests: XCTestCase {
    private let birth = Date(timeIntervalSince1970: 946684800)
    private var quarterNakshatra: Double { Nakshatra.arc / 4 }

    // These are mathematical consequences of the user's PL9 settings screenshot
    // (365.25 days; balance by degree), not invented PL9 report timestamps.
    func testJulianYearAndDegreeBalanceCoverFull120YearCycle() throws {
        let periods = try Dasha.mahadashas(moonLongitude: quarterNakshatra, birthDate: birth,
                                           yearConvention: .julian)
        XCTAssertGreaterThanOrEqual(periods.count, 9)
        XCTAssertEqual(Array(periods.prefix(9)).map(\.lord), Dasha.lordOrder)
        let first = try XCTUnwrap(periods.first)
        XCTAssertEqual(first.start.timeIntervalSince(birth), -7 * 0.25 * 365.25 * 86400,
                       accuracy: 0.00001)
        XCTAssertEqual(first.end.timeIntervalSince(birth), 7 * 0.75 * 365.25 * 86400,
                       accuracy: 0.00001)
        XCTAssertEqual(periods[8].end.timeIntervalSince(first.start), 120 * 365.25 * 86400,
                       accuracy: 0.00001)
        for (left, right) in zip(periods, periods.dropFirst()) {
            XCTAssertEqual(left.end, right.start)
        }
        XCTAssertTrue(periods.allSatisfy { $0.end > $0.start })
    }

    func testCurrentFiveLevelsUseTheSelectedYearAtChangedBoundary() throws {
        let legacy = try Dasha.mahadashas(moonLongitude: quarterNakshatra, birthDate: birth)
        let julian = try Dasha.mahadashas(moonLongitude: quarterNakshatra, birthDate: birth,
                                         yearConvention: .julian)
        let reference = legacy[0].end.addingTimeInterval(60)
        XCTAssertLessThan(reference, julian[0].end)
        let legacyLevels = try Dasha.currentFiveLevels(moonLongitude: quarterNakshatra,
                                                      birthDate: birth, at: reference)
        let julianLevels = try Dasha.currentFiveLevels(moonLongitude: quarterNakshatra,
                                                      birthDate: birth, at: reference,
                                                      yearConvention: .julian)
        XCTAssertEqual(legacyLevels.first?.lord, "Venera")
        XCTAssertEqual(julianLevels.first?.lord, "Ketu")
        XCTAssertEqual(julianLevels.count, 5)
        XCTAssertTrue(julianLevels.allSatisfy { $0.contains(reference) })
        var parent = try Dasha.current(in: julian, at: reference)
        XCTAssertEqual(julianLevels[0], parent)
        for actual in julianLevels.dropFirst() {
            parent = try Dasha.current(in: Dasha.subperiods(parent: parent), at: reference)
            XCTAssertEqual(actual, parent)
        }
    }

    func testSelectedYearExtendsHorizonBeyondFirstCycle() throws {
        let reference = birth.addingTimeInterval(241 * 365.25 * 86400)
        let levels = try Dasha.currentFiveLevels(moonLongitude: quarterNakshatra,
                                                birthDate: birth, at: reference,
                                                yearConvention: .julian)
        let longSequence = try Dasha.mahadashas(moonLongitude: quarterNakshatra, birthDate: birth,
                                               yearsToCover: 242, yearConvention: .julian)
        XCTAssertEqual(levels.first, try Dasha.current(in: longSequence, at: reference))
        XCTAssertTrue(levels.allSatisfy { $0.contains(reference) })
    }

    func testLegacyDefaultIsUnchangedAndMuddaConventionIsIndependent() throws {
        let defaultPeriods = try Dasha.mahadashas(moonLongitude: quarterNakshatra, birthDate: birth)
        let explicitLegacy = try Dasha.mahadashas(moonLongitude: quarterNakshatra, birthDate: birth,
                                                 yearConvention: .gregorianMean)
        XCTAssertEqual(defaultPeriods, explicitLegacy)
        XCTAssertEqual(VimshottariYearConvention.gregorianMean.daysPerYear, Dasha.daysPerYear)
        XCTAssertEqual(VimshottariYearConvention.julian.daysPerYear, 365.25)
        let mudda = try Dasha.mudda(natalMoonLongitude: quarterNakshatra, completedYears: 29,
                                    start: birth, yearConvention: .fixedGregorianYear)
        XCTAssertEqual(try XCTUnwrap(mudda.last).end.timeIntervalSince(birth) / 86400,
                       365.2425, accuracy: 1e-9)
    }

    func testJulianSelectionRetainsInputValidation() throws {
        XCTAssertThrowsError(try Dasha.mahadashas(moonLongitude: .nan, birthDate: birth,
                                                  yearConvention: .julian))
        XCTAssertThrowsError(try Dasha.mahadashas(moonLongitude: 0, birthDate: birth,
                                                  yearsToCover: 0, yearConvention: .julian))
        XCTAssertThrowsError(try Dasha.mahadashas(moonLongitude: 0, birthDate: birth,
                                                  yearsToCover: 10_001, yearConvention: .julian))
        XCTAssertThrowsError(try Dasha.currentFiveLevels(moonLongitude: 0, birthDate: birth,
                                                        at: Date(timeIntervalSince1970: .infinity),
                                                        yearConvention: .julian))
    }
}
