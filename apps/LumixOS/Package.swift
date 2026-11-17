// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "LumixOS",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(name: "LumixOS", path: "Sources/LumixOS")
    ]
)
