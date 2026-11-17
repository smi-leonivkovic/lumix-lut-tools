// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "LumixOS",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(name: "LumixOS", path: "Sources/LumixOS"),
        // CoreMediaIO camera extension, embedded by build_app.sh when a Developer team is configured
        .executableTarget(name: "LumixCamera", path: "Sources/LumixCamera"),
    ]
)
