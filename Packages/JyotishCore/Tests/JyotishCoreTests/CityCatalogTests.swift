import XCTest
import Foundation
@testable import JyotishCore

final class CityCatalogTests: XCTestCase {
    func testRegionalSmallTownProvidesActualCoordinatesAndHistoricalIANAZone() throws {
        let city = try XCTUnwrap(CityCatalog.shared.search("Petrinja", limit: 1).first)
        XCTAssertEqual(city.id, 3193420)
        XCTAssertEqual(city.countryCode, "HR")
        XCTAssertEqual(city.latitude, 45.4375, accuracy: 1e-6)
        XCTAssertEqual(city.longitude, 16.29, accuracy: 1e-6)
        XCTAssertEqual(city.timeZone, "Europe/Zagreb")
        let clock = try XCTUnwrap(BirthMoment.calendar.date(from: DateComponents(year: 1985, month: 11, day: 4, hour: 1, minute: 15)))
        let instant = try XCTUnwrap(BirthMoment.candidates(wallClock: clock, zoneID: city.timeZone).first)
        XCTAssertEqual(BirthMoment.calendar.component(.hour, from: instant), 0)
        XCTAssertEqual(BirthMoment.calendar.component(.minute, from: instant), 15)
    }

    func testDiacriticsCroatianDigraphAndCommonAliasesFindSameCity() throws {
        for query in ["Đakovo", "Dakovo", "Djakovo", "ĐAKOVO"] {
            XCTAssertEqual(try CityCatalog.shared.search(query, limit: 1).first?.id, 3202220, query)
        }
        for query in ["München", "Munchen", "Munich"] {
            XCTAssertEqual(try CityCatalog.shared.search(query, limit: 1).first?.id, 2867714, query)
        }
        XCTAssertTrue(try CityCatalog.shared.search("Za").contains(where: { $0.id == 3186886 }))
        XCTAssertEqual(try CityCatalog.shared.search("Zagreb HR", limit: 1).first?.id, 3186886)
    }

    func testDuplicateCityNamesAreDisambiguatedByCountryAndSubdivision() throws {
        let matches = try CityCatalog.shared.search("Springfield US", limit: 30)
        XCTAssertGreaterThan(matches.count, 1)
        XCTAssertTrue(matches.contains(where: { $0.id == 4951788 && $0.admin1 == "MA" }))
        XCTAssertTrue(matches.contains(where: { $0.admin1 == "IL" }))
        let selected = try XCTUnwrap(CityCatalog.shared.search("Springfield US MA", limit: 1).first)
        XCTAssertEqual(selected.id, 4951788)
        XCTAssertEqual(selected.timeZone, "America/New_York")
        XCTAssertEqual(selected.longitude, -72.58981, accuracy: 1e-6)
    }

    func testWorldwideCitiesPreserveSouthernAndHalfHourTimeZones() throws {
        let sydney = try XCTUnwrap(CityCatalog.shared.search("Sydney AU", limit: 1).first)
        XCTAssertEqual(sydney.id, 2147714)
        XCTAssertLessThan(sydney.latitude, 0)
        XCTAssertEqual(sydney.timeZone, "Australia/Sydney")
        let kolkata = try XCTUnwrap(CityCatalog.shared.search("Kolkata IN", limit: 1).first)
        XCTAssertEqual(kolkata.timeZone, "Asia/Kolkata")
        let zone = try XCTUnwrap(TimeZone(identifier: kolkata.timeZone))
        XCTAssertEqual(zone.secondsFromGMT(for: Date(timeIntervalSince1970: 946728000)), 19800)
        XCTAssertTrue(CityCatalog.licenseNotice.contains("Creative Commons Attribution 4.0"))
        XCTAssertTrue(CityCatalog.licenseNotice.contains("GeoNames"))
    }

    func testMissingMalformedAndDuplicateResourcesAreExplicitFailures() throws {
        XCTAssertThrowsError(try CityCatalog(resourceURL: nil).search("Zagreb"))
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("jy-city-tests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let file = directory.appendingPathComponent("cities.json")
        try Data("not JSON".utf8).write(to: file)
        XCTAssertThrowsError(try CityCatalog(resourceURL: file).search("Zagreb"))
        let city = City(id: 1, name: "Test", countryCode: "HR", admin1: "", latitude: 45, longitude: 16, timeZone: "Europe/Zagreb")
        try JSONEncoder().encode([city, city]).write(to: file)
        XCTAssertThrowsError(try CityCatalog(resourceURL: file).search("Test"))
        let invalid = City(id: 2, name: "Invalid", countryCode: "HR", admin1: "", latitude: 100, longitude: 16, timeZone: "Europe/Zagreb")
        try JSONEncoder().encode([invalid]).write(to: file)
        XCTAssertThrowsError(try CityCatalog(resourceURL: file).search("Invalid"))
    }

    func testFutureIANATimeZoneDoesNotDiscardEntireValidCatalog() throws {
        let file = FileManager.default.temporaryDirectory.appendingPathComponent("jy-city-future-\(UUID().uuidString).json")
        defer { try? FileManager.default.removeItem(at: file) }
        let future = City(id: 2, name: "Future Place", countryCode: "HR", admin1: "", latitude: 45, longitude: 16, timeZone: "Example/Future_Zone")
        let known = City(id: 3, name: "Known Place", countryCode: "HR", admin1: "", latitude: 45, longitude: 16, timeZone: "Europe/Zagreb")
        try JSONEncoder().encode([future, known]).write(to: file)
        let catalog = CityCatalog(resourceURL: file)
        XCTAssertEqual(try catalog.search("Known").first?.id, 3)
        XCTAssertEqual(try catalog.search("Future").first?.timeZone, "Example/Future_Zone")
        XCTAssertNil(TimeZone(identifier: future.timeZone))
    }
}
