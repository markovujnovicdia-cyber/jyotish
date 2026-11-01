import XCTest
@testable import JyotishCore

final class DashaTests: XCTestCase {
    private let birth = Date(timeIntervalSince1970: 946684800) // 2000-01-01 UTC

    func testFirstMahadashaIsWholeAndFiveLevelsPreserveBirthPhase() throws {
        let moon = (360.0 / 27) / 2
        let periods = try Dasha.mahadashas(moonLongitude: moon, birthDate: birth)
        let first = try XCTUnwrap(periods.first)
        XCTAssertEqual(first.lord, "Ketu")
        XCTAssertLessThan(first.start, birth)
        XCTAssertGreaterThan(first.end, birth)
        XCTAssertEqual(first.end.timeIntervalSince(first.start) / 86400 / Dasha.daysPerYear, 7,
                       accuracy: 1e-12)
        let children = try Dasha.subperiods(parent: first)
        XCTAssertEqual(children[0].end.timeIntervalSince(children[0].start) / 86400 / Dasha.daysPerYear,
                       49.0 / 120, accuracy: 1e-12)
        let levels = try Dasha.currentFiveLevels(moonLongitude: moon, birthDate: birth, at: birth)
        XCTAssertEqual(levels.count, 5)
        XCTAssertEqual(Array(levels.prefix(2)).map(\.lord), ["Ketu", "Rahu"])
        XCTAssertTrue(levels.allSatisfy { $0.contains(birth) })
    }

    func testSubperiodsCoverParentExactlyAndUseHalfOpenDates() throws {
        var parent = try XCTUnwrap(Dasha.mahadashas(moonLongitude: 6, birthDate: birth).first)
        for _ in 0..<4 {
            let children = try Dasha.subperiods(parent: parent)
            XCTAssertEqual(children.first?.start, parent.start)
            XCTAssertEqual(children.last?.end, parent.end)
            for (left, right) in zip(children, children.dropFirst()) {
                XCTAssertEqual(left.end, right.start)
                XCTAssertFalse(left.contains(left.end))
                XCTAssertEqual(try Dasha.current(in: children, at: right.start), right)
            }
            parent = try XCTUnwrap(children.last)
        }
        XCTAssertThrowsError(try Dasha.subperiods(parent: DashaPeriod(lord: "Unknown", start: birth,
                                                                     end: birth.addingTimeInterval(100))))
    }

    func testFiveLevelPythonTimestampReference() throws {
        let originalBirth = Date(timeIntervalSince1970: 499911300) // 1985-11-04T00:15:00Z
        let reference = Date(timeIntervalSince1970: 1793491200) // 2026-11-01T00:00:00Z
        let levels = try Dasha.currentFiveLevels(moonLongitude: 103.212345,
                                                 birthDate: originalBirth, at: reference)
        let expected: [(String, Double, Double)] = [
            ("Venera", 1412614352.814273, 2043753392.814273),
            ("Jupiter", 1733443364.814273, 1817595236.814273),
            ("Mjesec", 1793050940.814273, 1800063596.814273),
            ("Mjesec", 1793050940.814273, 1793635328.814273),
            ("Ketu", 1793474622.114273, 1793508711.414273)
        ]
        for (period, expected) in zip(levels, expected) {
            XCTAssertEqual(period.lord, expected.0)
            XCTAssertEqual(period.start.timeIntervalSince1970, expected.1, accuracy: 0.00001)
            XCTAssertEqual(period.end.timeIntervalSince1970, expected.2, accuracy: 0.00001)
        }
    }

    func testMuddaLordTableBalanceAndLegacyDuration() throws {
        let moon = (360.0 / 27) * 0.25
        XCTAssertEqual(try Dasha.muddaStartingLord(natalMoonLongitude: moon, completedYears: 29), "Sunce")
        XCTAssertEqual(try Dasha.muddaStartingLord(natalMoonLongitude: moon, completedYears: 1), "Venera")
        XCTAssertEqual(try Dasha.muddaStartingLord(natalMoonLongitude: moon, completedYears: 9), "Ketu")
        let periods = try Dasha.mudda(natalMoonLongitude: moon, completedYears: 29, start: birth)
        XCTAssertEqual(periods.first?.lord, "Sunce")
        XCTAssertEqual(try XCTUnwrap(periods.first).end.timeIntervalSince(birth) / 86400, 13.5,
                       accuracy: 1e-12)
        XCTAssertEqual(try XCTUnwrap(periods.last).end.timeIntervalSince(birth) / 86400, 360,
                       accuracy: 1e-9)
        for (a, b) in zip(periods, periods.dropFirst()) { XCTAssertEqual(a.end, b.start) }
    }

    func testMuddaScalesTraditionalPartsToNextReturn() throws {
        let end = birth.addingTimeInterval(365.257 * 86400)
        let periods = try Dasha.mudda(natalMoonLongitude: 103.212345, completedYears: 41,
                                      start: birth, end: end)
        XCTAssertEqual(periods.first?.start, birth)
        XCTAssertEqual(periods.last?.end, end)
        XCTAssertTrue(periods.allSatisfy { $0.end >= $0.start })
        XCTAssertThrowsError(try Dasha.mudda(natalMoonLongitude: 1, completedYears: 1,
                                            start: birth, end: birth))
        XCTAssertThrowsError(try Dasha.mahadashas(moonLongitude: .nan, birthDate: birth))
        XCTAssertThrowsError(try Dasha.mahadashas(moonLongitude: 0, birthDate: birth, yearsToCover: 0))
    }
}
