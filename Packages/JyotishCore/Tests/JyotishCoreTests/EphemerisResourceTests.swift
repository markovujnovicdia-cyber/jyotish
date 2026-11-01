import XCTest
import Foundation
@testable import JyotishCore

final class EphemerisResourceTests: XCTestCase {
    private let manager = FileManager.default

    private func temporaryRoot() throws -> URL {
        let root = manager.temporaryDirectory.appendingPathComponent("jy-path-test-\(UUID().uuidString)", isDirectory: true)
        try manager.createDirectory(at: root, withIntermediateDirectories: true)
        addTeardownBlock { try? FileManager.default.removeItem(at: root) }
        return root
    }

    private func makeSource(in root: URL, long: Bool) throws -> URL {
        var directory = root
        if long {
            // Both spaces and non-ASCII names occur in real macOS home paths.
            while directory.path.utf8.count <= EphemerisResources.maximumPathBytes + 80 {
                directory.appendPathComponent("Simulator podaci žćšđ-1234567890", isDirectory: true)
            }
        }
        directory.appendPathComponent("Ephemeris", isDirectory: true)
        try manager.createDirectory(at: directory, withIntermediateDirectories: true)
        for name in EphemerisResources.names {
            try Data("synthetic resource \(name)".utf8).write(to: directory.appendingPathComponent(name))
        }
        return directory
    }

    func testShortBundlePathsUseOriginalReadOnlyResources() throws {
        let root = try temporaryRoot()
        let source = try makeSource(in: root, long: false)
        let resolver = EphemerisResources(storageRoots: [])
        XCTAssertEqual(try resolver.directory(bundleDirectory: source), source)
    }

    func testLongUTF8BundlePathsStageByteIdenticalDataAndRestorePurgedFiles() throws {
        let root = try temporaryRoot()
        let source = try makeSource(in: root, long: true)
        let resolver = EphemerisResources(storageRoots: [root.appendingPathComponent("cache")])
        let resolved = try resolver.directory(bundleDirectory: source)
        XCTAssertNotEqual(resolved, source)
        XCTAssertLessThanOrEqual(resolved.path.utf8.count, EphemerisResources.maximumPathBytes)
        for name in EphemerisResources.names {
            XCTAssertEqual(try Data(contentsOf: resolved.appendingPathComponent(name)),
                           try Data(contentsOf: source.appendingPathComponent(name)))
        }
        try manager.removeItem(at: resolved.appendingPathComponent("semo_18.se1"))
        XCTAssertEqual(try resolver.directory(bundleDirectory: source), resolved)
        XCTAssertEqual(try Data(contentsOf: resolved.appendingPathComponent("semo_18.se1")),
                       try Data(contentsOf: source.appendingPathComponent("semo_18.se1")))
        try manager.removeItem(at: resolved)
        XCTAssertEqual(try resolver.directory(bundleDirectory: source), resolved)
    }

    func testNewResolverRepairsStaleCacheAfterAppUpdate() throws {
        let root = try temporaryRoot()
        let source = try makeSource(in: root, long: true)
        let storage = [root.appendingPathComponent("cache")]
        let resolved = try EphemerisResources(storageRoots: storage).directory(bundleDirectory: source)
        try Data("outdated file".utf8).write(to: resolved.appendingPathComponent("sepl_18.se1"))
        let refreshed = try EphemerisResources(storageRoots: storage).directory(bundleDirectory: source)
        XCTAssertEqual(try Data(contentsOf: refreshed.appendingPathComponent("sepl_18.se1")),
                       try Data(contentsOf: source.appendingPathComponent("sepl_18.se1")))
    }

    func testOverlongCachePathsAndMissingDataProduceExplicitErrors() throws {
        let root = try temporaryRoot()
        let source = try makeSource(in: root, long: true)
        let resolver = EphemerisResources(storageRoots: [source.appendingPathComponent("cache")])
        XCTAssertThrowsError(try resolver.directory(bundleDirectory: source)) { error in
            guard case EphemerisError.resourcePathTooLong = error else {
                return XCTFail("Unexpected error: \(error)")
            }
        }
        try manager.removeItem(at: source.appendingPathComponent("sepl_18.se1"))
        XCTAssertThrowsError(try resolver.directory(bundleDirectory: source)) { error in
            guard case EphemerisError.missingResources = error else {
                return XCTFail("Unexpected error: \(error)")
            }
        }
    }
}
