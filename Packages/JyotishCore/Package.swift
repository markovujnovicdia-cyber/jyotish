// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "JyotishCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "JyotishCore", targets: ["JyotishCore"])],
    targets: [
        .target(name: "CSwissEphemeris", exclude: ["LICENSE"], publicHeadersPath: "include",
                linkerSettings: [.linkedLibrary("m")]),
        .target(name: "JyotishCore", dependencies: ["CSwissEphemeris"],
                resources: [.copy("Resources/Ephemeris"), .copy("Resources/Licenses")]),
        .testTarget(name: "JyotishCoreTests", dependencies: ["JyotishCore"],
                    resources: [.process("Fixtures")])
    ]
)
