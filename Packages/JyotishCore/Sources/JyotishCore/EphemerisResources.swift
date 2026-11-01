import Foundation
import CSwissEphemeris

/// Swiss 2.10.03 silently ignores paths over 242 UTF-8 bytes. Simulator bundle
/// paths commonly exceed that limit. Keep the immutable bundle as the source of
/// truth and stage identical data in a short, app-private location when needed.
/// Access is serialized by Ephemeris.lock; this type does not change the cwd or
/// process environment, and never changes the astronomical calculation flags.
final class EphemerisResources {
    static let names = ["sepl_18.se1", "semo_18.se1"]
    static var maximumPathBytes: Int { Int(jy_max_path_bytes()) }
    private let fileManager: FileManager
    private let storageRoots: [URL]
    private var preparedSource: URL?
    private var preparedDirectory: URL?

    init(fileManager: FileManager = .default, storageRoots: [URL]? = nil) {
        self.fileManager = fileManager
        self.storageRoots = storageRoots ?? (
            [fileManager.temporaryDirectory] + fileManager.urls(for: .cachesDirectory, in: .userDomainMask)
        )
    }

    private func containsData(_ directory: URL) -> Bool {
        Self.names.allSatisfy { name in
            let path = directory.appendingPathComponent(name).path
            var isDirectory: ObjCBool = false
            return fileManager.fileExists(atPath: path, isDirectory: &isDirectory) && !isDirectory.boolValue
        }
    }

    func directory(bundleDirectory source: URL) throws -> URL {
        guard containsData(source) else { throw EphemerisError.missingResources }
        if source.path.utf8.count <= Self.maximumPathBytes { return source }

        // Temporary data can be purged by the OS. Re-create it on the next call.
        if preparedSource == source, let preparedDirectory, containsData(preparedDirectory) {
            return preparedDirectory
        }

        let candidates = storageRoots.map { $0.appendingPathComponent("jy-ephe-2.10.03", isDirectory: true) }
            .filter { $0.path.utf8.count <= Self.maximumPathBytes }
            .sorted { $0.path.utf8.count < $1.path.utf8.count }
        guard !candidates.isEmpty else { throw EphemerisError.resourcePathTooLong }
        var lastError: Error?
        for target in candidates {
            do {
                try fileManager.createDirectory(at: target, withIntermediateDirectories: true)
                for name in Self.names {
                    let original = source.appendingPathComponent(name)
                    let copy = target.appendingPathComponent(name)
                    // Check retained files once per resolver/app launch. This also
                    // replaces stale data after an application/data-file update.
                    if !fileManager.contentsEqual(atPath: original.path, andPath: copy.path) {
                        let bytes = try Data(contentsOf: original)
                        try bytes.write(to: copy, options: .atomic)
                    }
                    guard fileManager.contentsEqual(atPath: original.path, andPath: copy.path) else {
                        throw EphemerisError.resourcePreparation("Kopija efemerida ne odgovara ugrađenim podacima.")
                    }
                }
                preparedSource = source
                preparedDirectory = target
                return target
            } catch { lastError = error }
        }
        throw EphemerisError.resourcePreparation(lastError?.localizedDescription ?? "Lokalna mapa nije dostupna.")
    }
}
