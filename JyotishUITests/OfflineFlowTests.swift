import XCTest

final class OfflineFlowTests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    private func freshApp() -> XCUIApplication {
        let app = XCUIApplication()
        // The app uses a dedicated test defaults suite, preserving real saved people.
        app.launchArguments = ["-ui-testing-reset"]
        app.launch()
        return app
    }

    func testCreatePersonAndCalculateWithoutServer() throws {
        let app = freshApp()
        let add = app.buttons["add-person"].firstMatch
        XCTAssertTrue(add.waitForExistence(timeout: 10))
        add.tap()
        let name = app.textFields["person-name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        name.tap()
        name.typeText("Simulator reference")
        // The form supplies a fixed valid date, Zagreb time zone and coordinates.
        let save = app.buttons["save-person"]
        XCTAssertTrue(save.isEnabled)
        save.tap()
        let natal = app.descendants(matching: .any)
            .matching(identifier: "natal-results").firstMatch
        XCTAssertTrue(natal.waitForExistence(timeout: 30), "Native natal results did not appear")
        XCTAssertFalse(app.textFields["Adresa servisa (Mac IP:8765)"].exists)
    }

    func testOutOfRangeLatitudeCannotBeSaved() throws {
        let app = freshApp()
        let add = app.buttons["add-person"].firstMatch
        XCTAssertTrue(add.waitForExistence(timeout: 10))
        add.tap()
        let name = app.textFields["person-name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        name.tap()
        name.typeText("Invalid coordinates")
        let latitude = app.textFields["person-latitude"]
        let form: XCUIElement
        if app.collectionViews.firstMatch.exists {
            form = app.collectionViews.firstMatch
        } else if app.tables.firstMatch.exists {
            form = app.tables.firstMatch
        } else if app.scrollViews.firstMatch.exists {
            form = app.scrollViews.firstMatch
        } else {
            form = app
        }
        for _ in 0..<5 {
            if latitude.isHittable { break }
            form.swipeUp()
        }
        XCTAssertTrue(latitude.isHittable, "Latitude field could not be reached in the birth form")
        latitude.tap()
        let existing = latitude.value as? String ?? ""
        latitude.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: existing.count) + "100")
        let disabledSave = XCTNSPredicateExpectation(
            predicate: NSPredicate(format: "enabled == false"),
            object: app.buttons["save-person"]
        )
        XCTAssertEqual(XCTWaiter.wait(for: [disabledSave], timeout: 5), .completed,
                       "Out-of-range latitude must disable saving")
    }
}
