import XCTest
import JyotishCore
@testable import Jyotish

/// These run inside the iOS test host, including the packaged C library/resources.
final class NativeCalculationTests: XCTestCase {
    func testJ2000ReferenceChartAndMeanNodes() throws {
        let chart = try Ephemeris.chart(
            date: Date(timeIntervalSince1970: 946_728_000),
            latitude: 45.44, longitude: 16.28
        )
        XCTAssertEqual(chart.julianDay, 2_451_545, accuracy: 1e-9)
        XCTAssertEqual(chart.positions.count, 9)
        // Python pyswisseph 2.10.3.2 reference using the identical bundled Swiss files.
        // Flag 65858: SWIEPH | SIDEREAL | SPEED, Lahiri and mean lunar node.
        let sun = try XCTUnwrap(chart.positions["Sunce"])
        let moon = try XCTUnwrap(chart.positions["Mjesec"])
        XCTAssertEqual(sun.longitude, 256.51569618387066, accuracy: 1e-7)
        XCTAssertEqual(moon.longitude, 199.47052896032176, accuracy: 1e-7)
        XCTAssertEqual(chart.ascendantLongitude, 23.42376796443993, accuracy: 1e-7)
        let rahu = try XCTUnwrap(chart.positions["Rahu"])
        let ketu = try XCTUnwrap(chart.positions["Ketu"])
        XCTAssertEqual(Astro.normalize(ketu.longitude - rahu.longitude), 180, accuracy: 1e-10)
        for position in chart.positions.values {
            XCTAssertTrue(position.longitude.isFinite)
            XCTAssertTrue((0..<360).contains(position.longitude))
        }
    }

    func testInvalidCoordinatesAreRejected() {
        XCTAssertThrowsError(try Ephemeris.chart(date: Date(), latitude: 100, longitude: 16))
        XCTAssertThrowsError(try Ephemeris.chart(date: Date(), latitude: .nan, longitude: 16))
        XCTAssertThrowsError(try Ephemeris.chart(date: Date(), latitude: 45, longitude: .infinity))
    }
}

final class BirthInputTests: XCTestCase {
    private func wall(_ year: Int, _ month: Int, _ day: Int, _ hour: Int, _ minute: Int) throws -> Date {
        try XCTUnwrap(BirthMoment.calendar.date(from: DateComponents(year: year, month: month, day: day, hour: hour, minute: minute)))
    }

    func testSelectedTimeZoneDeterminesBirthInstant() throws {
        let input = try wall(1985, 11, 4, 1, 15)
        let candidates = try BirthMoment.candidates(wallClock: input, zoneID: "Europe/Zagreb")
        XCTAssertEqual(candidates.count, 1)
        let instant = try XCTUnwrap(candidates.first)
        let expected = try wall(1985, 11, 4, 0, 15)
        XCTAssertEqual(instant.timeIntervalSince1970, expected.timeIntervalSince1970, accuracy: 1e-6)
        XCTAssertEqual(BirthMoment.wallClock(from: instant, zoneID: "Europe/Zagreb"), input)
    }

    func testSkippedAndRepeatedDaylightSavingTimesAreExplicit() throws {
        let skipped = try BirthMoment.candidates(wallClock: wall(2026, 3, 29, 2, 30), zoneID: "Europe/Zagreb")
        XCTAssertTrue(skipped.isEmpty)
        let repeated = try BirthMoment.candidates(wallClock: wall(2026, 10, 25, 2, 30), zoneID: "Europe/Zagreb")
        XCTAssertEqual(repeated.count, 2)
        XCTAssertEqual(try XCTUnwrap(repeated.last).timeIntervalSince(try XCTUnwrap(repeated.first)), 3600, accuracy: 1e-6)
    }

    func testUnknownTimeZoneIsRejected() throws {
        XCTAssertThrowsError(try BirthMoment.candidates(wallClock: wall(2000, 1, 1, 12, 0), zoneID: "Invalid/Zone"))
    }

    @MainActor
    func testPersonPersistenceUpdatesDeletesAndReloads() throws {
        let suite = "JyotishUnitTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = PersonStore(defaults: defaults)
        var person = Person(name: "Test record", birthDate: try wall(2000, 1, 1, 11, 0), latitude: 45.44, longitude: 16.28, timeZone: "Europe/Zagreb")
        try store.save(person)
        XCTAssertEqual(store.people.count, 1)
        person.name = "Edited record"
        try store.save(person)
        XCTAssertEqual(store.people.count, 1)
        let reloaded = PersonStore(defaults: defaults)
        XCTAssertEqual(reloaded.people.first?.name, "Edited record")
        try reloaded.delete(person.id)
        XCTAssertTrue(PersonStore(defaults: defaults).people.isEmpty)
    }

    func testExistingPersonRecordsDecodeWithoutBirthPlace() throws {
        let person = Person(name: "Legacy profile", birthDate: try wall(2000, 1, 1, 11, 0), latitude: 45.44, longitude: 16.28, timeZone: "Europe/Zagreb")
        var record = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(person)) as? [String: Any])
        record.removeValue(forKey: "birthPlace")
        let restored = try JSONDecoder().decode(Person.self, from: JSONSerialization.data(withJSONObject: record))
        XCTAssertNil(restored.birthPlace)
        XCTAssertEqual(restored.id, person.id)
        XCTAssertEqual(restored.birthDate, person.birthDate)
        try restored.validate()
    }

    @MainActor
    func testSelectedOfflineCitySurvivesProfileReload() throws {
        let city = try XCTUnwrap(CityCatalog.shared.search("Petrinja").first(where: { $0.id == 3193420 }))
        let suite = "JyotishCityTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let person = Person(name: "City profile", birthDate: try wall(2000, 1, 1, 11, 0), latitude: city.latitude, longitude: city.longitude, timeZone: city.timeZone, birthPlace: city.displayLabel)
        try PersonStore(defaults: defaults).save(person)
        let restored = try XCTUnwrap(PersonStore(defaults: defaults).people.first)
        XCTAssertEqual(restored.birthPlace, city.displayLabel)
        XCTAssertEqual(restored.latitude, city.latitude)
        XCTAssertEqual(restored.longitude, city.longitude)
        XCTAssertEqual(restored.timeZone, "Europe/Zagreb")
        let output = try NativeCalculations.calculate(CalculationRequest(person: restored, kind: .ashtakavarga, year: 2026, referenceDate: Date()))
        XCTAssertEqual(output.ashtakavarga?.total, 337)
    }

    func testAnnualReportConventionsReachApplicationCalculations() throws {
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let person = Person(name: "Annual reference", birthDate: birth,
                            latitude: 45.45, longitude: 16.0 + 22.0 / 60.0, timeZone: "Europe/Zagreb")
        let request = CalculationRequest(person: person, kind: .annual, year: 2026, referenceDate: birth)
        let result = try XCTUnwrap(NativeCalculations.calculate(request).annual)
        XCTAssertEqual(result.tajikaConvention, .longitudeBothOrbs)
        XCTAssertEqual(result.muddaYearConvention, .fixedGregorianYear)
        XCTAssertEqual(result.sahamsConvention, .tajikaSripati)
        XCTAssertEqual(result.lunarNodeConvention, .meanTropicalTrueAyanamsa)
        XCTAssertEqual(result.timeConvention, .historical2019Forecast)
        let printedReturn = try XCTUnwrap(ISO8601DateFormatter().date(from: "2026-12-27T06:43:23Z"))
        XCTAssertEqual(result.returnDate.timeIntervalSince1970, printedReturn.timeIntervalSince1970, accuracy: 0.5)
        let rahu = try XCTUnwrap(result.chart.positions["Rahu"])
        XCTAssertEqual(rahu.longitude, 298 + 51.0 / 60 + 15.0 / 3600, accuracy: 1.0 / 3600)
        XCTAssertEqual(result.ithasala.count, 6)
        XCTAssertEqual(result.isarapha.count, 3)
        XCTAssertEqual(result.muddaDasha.last!.end.timeIntervalSince(result.returnDate) / 86400,
                       365.2425, accuracy: 1e-8)
    }


    func testChangingTimeModelChangesRequestAndRecomputesAnnualReturn() throws {
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let person = Person(name: "Annual reference", birthDate: birth,
                            latitude: 45.45, longitude: 16.0 + 22.0 / 60.0, timeZone: "Europe/Zagreb")
        let reference = CalculationRequest(person: person, kind: .annual, year: 2026, referenceDate: birth)
        let current = CalculationRequest(person: person, kind: .annual, year: 2026, referenceDate: birth,
                                         timeConvention: .currentSwiss)
        XCTAssertNotEqual(reference, current)
        let referenceOutput = try XCTUnwrap(NativeCalculations.calculate(reference).annual)
        let currentOutput = try XCTUnwrap(NativeCalculations.calculate(current).annual)
        XCTAssertEqual(currentOutput.timeConvention, .currentSwiss)
        XCTAssertGreaterThan(currentOutput.returnDate.timeIntervalSince(referenceOutput.returnDate), 13)
        XCTAssertLessThan(currentOutput.returnDate.timeIntervalSince(referenceOutput.returnDate), 14)
    }

    func testVimshottariYearMatchesConfirmedPLSettings() throws {
        let birth = try XCTUnwrap(ISO8601DateFormatter().date(from: "1976-12-26T10:55:00Z"))
        let person = Person(name: "Dasha reference", birthDate: birth,
                            latitude: 45.45, longitude: 16.0 + 22.0 / 60.0, timeZone: "Europe/Zagreb")
        let request = CalculationRequest(person: person, kind: .dasha, year: 2026, referenceDate: birth)
        let output = try NativeCalculations.calculate(request)
        XCTAssertEqual(output.vimshottariYear, .julian)
        let first = try XCTUnwrap(output.mahaDashas.first)
        let years = try XCTUnwrap(Dasha.lordYears[first.lord])
        XCTAssertEqual(first.end.timeIntervalSince(first.start) / 86400, years * 365.25, accuracy: 1e-8)
    }

}
