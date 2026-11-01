import Foundation
import XCTest
@testable import JyotishCore

final class BirthMomentTests: XCTestCase {
    private func wall(_ year: Int, _ month: Int, _ day: Int, _ hour: Int, _ minute: Int, _ second: Int = 0) throws -> Date {
        try XCTUnwrap(BirthMoment.calendar.date(from: DateComponents(year: year, month: month, day: day, hour: hour, minute: minute, second: second)))
    }

    func testSelectedIANAZoneDeterminesUTCInstantAndRoundTripsSeconds() throws {
        let local = try wall(1985, 11, 4, 1, 15, 42)
        let actual = try BirthMoment.candidates(wallClock: local, zoneID: "Europe/Zagreb")
        XCTAssertEqual(actual, [try wall(1985, 11, 4, 0, 15, 42)])
        XCTAssertEqual(BirthMoment.wallClock(from: try XCTUnwrap(actual.first), zoneID: "Europe/Zagreb"), local)
    }

    func testZagrebDSTGapIsRejectedAndFoldExposesBothInstants() throws {
        XCTAssertTrue(try BirthMoment.candidates(wallClock: wall(2026, 3, 29, 2, 30), zoneID: "Europe/Zagreb").isEmpty)
        let repeated = try BirthMoment.candidates(wallClock: wall(2026, 10, 25, 2, 30), zoneID: "Europe/Zagreb")
        XCTAssertEqual(repeated.count, 2)
        XCTAssertEqual(try XCTUnwrap(repeated.first), try wall(2026, 10, 25, 0, 30))
        XCTAssertEqual(try XCTUnwrap(repeated.last), try wall(2026, 10, 25, 1, 30))
    }

    func testSouthernHemisphereAndHalfHourOffsets() throws {
        let sydney = try BirthMoment.candidates(wallClock: wall(2000, 1, 1, 12, 0), zoneID: "Australia/Sydney")
        XCTAssertEqual(sydney, [try wall(2000, 1, 1, 1, 0)])
        let india = try BirthMoment.candidates(wallClock: wall(2000, 1, 1, 12, 0), zoneID: "Asia/Kolkata")
        XCTAssertEqual(india, [try wall(2000, 1, 1, 6, 30)])
        let buenosAires = try BirthMoment.candidates(wallClock: wall(2000, 1, 1, 12, 0), zoneID: "America/Argentina/Buenos_Aires")
        XCTAssertEqual(buenosAires, [try wall(2000, 1, 1, 15, 0)])
    }

    func testInvalidZoneAndNonFiniteTimeAreRejected() throws {
        XCTAssertThrowsError(try BirthMoment.candidates(wallClock: wall(2000, 1, 1, 12, 0), zoneID: "Invalid/Zone"))
        XCTAssertThrowsError(try BirthMoment.candidates(wallClock: Date(timeIntervalSince1970: .infinity), zoneID: "UTC"))
    }
}
