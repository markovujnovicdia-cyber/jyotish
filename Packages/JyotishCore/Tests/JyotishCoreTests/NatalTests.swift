import XCTest
@testable import JyotishCore

final class NatalTests: XCTestCase {
    /// Values independently evaluated from the unchanged Python modules,
    /// including boundaries where Python's float // differs from floor(x / y).
    func testPythonNakshatraAndVargaBoundaryReferences() throws {
        let rows: [(Double, Int, Int, [Int])] = [
            (-360.1, 26, 4, [11,11,11,4,10]),
            (-0.1, 26, 4, [11,11,11,4,10]),
            (0, 0, 1, [0,0,0,0,0]),
            (3.3333333333333335, 0, 2, [0,0,1,1,1]),
            (6.666666666666667, 0, 3, [0,1,2,2,2]),
            (13.333333333333334, 1, 1, [0,3,4,4,5]),
            (26.666666666666668, 2, 1, [0,6,8,8,10]),
            (30, 2, 1, [1,7,9,9,1]),
            (40, 2, 4, [1,9,0,0,5]),
            (60, 4, 2, [2,2,6,2,2]),
            (80, 5, 4, [2,6,0,8,10]),
            (120, 8, 4, [4,4,0,4,4]),
            (160, 11, 4, [5,1,0,4,9]),
            (240, 17, 4, [8,8,0,8,8]),
            (280, 20, 4, [9,5,0,8,1]),
            (359.999999, 26, 4, [11,11,11,4,10]),
            (360, 0, 1, [0,0,0,0,0]),
            (720.5, 0, 1, [0,0,0,0,0])
        ]
        let vargas: [Varga] = [.d1, .d7, .d9, .d10, .d12]
        for (longitude, index, pada, signs) in rows {
            let nakshatra = try Nakshatra.at(longitude: longitude)
            XCTAssertEqual(nakshatra.index, index, "longitude=\(longitude)")
            XCTAssertEqual(nakshatra.pada, pada, "longitude=\(longitude)")
            for (varga, expected) in zip(vargas, signs) {
                XCTAssertEqual(try varga.signIndex(longitude: longitude), expected,
                               "\(varga) longitude=\(longitude)")
            }
        }
    }

    func testNonFiniteCoordinatesRejected() {
        for value in [Double.nan, .infinity, -.infinity] {
            XCTAssertThrowsError(try Nakshatra.at(longitude: value))
            for varga in Varga.allCases {
                XCTAssertThrowsError(try varga.signIndex(longitude: value))
            }
        }
    }

    func testArudhaExceptionsAndForwardBhriguArc() throws {
        func positions(lordSign: Int) -> [String: PlanetPosition] {
            ["Mars": PlanetPosition(name: "Mars", longitude: Double(lordSign) * 30 + 1, speed: 1)]
        }
        XCTAssertEqual(try SpecialPoints.arudha(houseSign: 0, positions: positions(lordSign: 0)), 9)
        XCTAssertEqual(try SpecialPoints.arudha(houseSign: 0, positions: positions(lordSign: 3)), 3)
        XCTAssertEqual(try SpecialPoints.arudha(houseSign: 0, positions: positions(lordSign: 2)), 4)
        XCTAssertThrowsError(try SpecialPoints.arudha(houseSign: 0, positions: [:]))
        XCTAssertEqual(try SpecialPoints.bhriguBindu(moonLongitude: 20, rahuLongitude: 340), 0,
                       accuracy: 1e-12)
        // Deliberately forward arc (340-20)=320, not the shorter 40-degree arc.
        XCTAssertEqual(try SpecialPoints.bhriguBindu(moonLongitude: 340, rahuLongitude: 20), 180,
                       accuracy: 1e-12)
    }

    func testGulikaDayAndPreSunriseWeekdayShift() throws {
        let midnight = Date(timeIntervalSince1970: 0)
        func hour(_ value: Double) -> Date { midnight.addingTimeInterval(value * 3600) }
        func longitude(_ date: Date) -> Double { date.timeIntervalSince(midnight) / 3600 }
        // Sunday daylight: Saturn rules part 7, beginning 6/8 through day.
        let day = try SpecialPoints.gulika(birthDate: hour(12), weekday: 6,
            sunrise: hour(6), sunset: hour(18), previousSunset: hour(-6), nextSunrise: hour(30),
            ascendantAt: longitude)
        XCTAssertTrue(day.isDayBirth)
        XCTAssertEqual(day.segmentNumber, 7)
        XCTAssertEqual(day.longitude, 15)
        XCTAssertEqual(day.mandiGhatikas, 26)
        XCTAssertEqual(try XCTUnwrap(day.mandiLongitude), 16.4, accuracy: 1e-12)
        // Monday 02:00 belongs to Sunday's night, whose first lord is Jupiter.
        let night = try SpecialPoints.gulika(birthDate: hour(2), weekday: 0,
            sunrise: hour(6), sunset: hour(18), previousSunset: hour(-6), nextSunrise: hour(30),
            ascendantAt: longitude)
        XCTAssertFalse(night.isDayBirth)
        XCTAssertEqual(night.weekdayForLord, 6)
        XCTAssertEqual(night.segmentNumber, 3)
        XCTAssertEqual(night.longitude, -3)
        XCTAssertEqual(night.mandiGhatikas, 10)
        XCTAssertEqual(try XCTUnwrap(night.mandiLongitude), -2, accuracy: 1e-12)
    }
}
