// Installs/removes the "LumixOS Camera" system extension (CoreMediaIO) embedded in the app bundle.
import AppKit
import SystemExtensions

@MainActor
final class VirtualCamera: NSObject, OSSystemExtensionRequestDelegate {
    static let shared = VirtualCamera()

    var extensionID: String { (Bundle.main.bundleIdentifier ?? "local.lumixos.app") + ".camera" }
    var embedded: Bool {
        FileManager.default.fileExists(atPath: Bundle.main.bundleURL
            .appendingPathComponent("Contents/Library/SystemExtensions/\(extensionID).systemextension").path)
    }

    func install() { submit(activate: true) }
    func remove() { submit(activate: false) }

    private func submit(activate: Bool) {
        guard embedded else {
            return alert("This LumixOS build has no camera extension.",
                         "macOS only loads camera extensions signed by an Apple Developer team. Build with TEAM_ID, "
                         + "SIGN_ID and provisioning profiles set (see apps/LumixOS/README.md).\n\n"
                         + "Until then: in OBS add a Media Source with the stream URL (Camera → Copy stream URL), "
                         + "then use OBS's Virtual Camera.")
        }
        guard Bundle.main.bundlePath.hasPrefix("/Applications/") else {
            return alert("Move LumixOS to Applications first.", "macOS installs camera extensions only from apps in /Applications.")
        }
        let r = activate
            ? OSSystemExtensionRequest.activationRequest(forExtensionWithIdentifier: extensionID, queue: .main)
            : OSSystemExtensionRequest.deactivationRequest(forExtensionWithIdentifier: extensionID, queue: .main)
        r.delegate = self
        OSSystemExtensionManager.shared.submitRequest(r)
    }

    nonisolated func request(_ request: OSSystemExtensionRequest,
                             actionForReplacingExtension existing: OSSystemExtensionProperties,
                             withExtension ext: OSSystemExtensionProperties) -> OSSystemExtensionRequest.ReplacementAction {
        .replace
    }

    nonisolated func requestNeedsUserApproval(_ request: OSSystemExtensionRequest) {
        MainActor.assumeIsolated {
            alert("Allow the LumixOS Camera",
                  "Open System Settings → General → Login Items & Extensions → Camera Extensions and switch on LumixOS Camera.")
        }
    }

    nonisolated func request(_ request: OSSystemExtensionRequest, didFinishWithResult result: OSSystemExtensionRequest.Result) {
        MainActor.assumeIsolated {
            if result == .willCompleteAfterReboot {
                alert("Almost done", "Restart the Mac to finish.")
            } else {
                alert("Done", "LumixOS Camera is ready: choose it as the camera in Zoom, Meet, FaceTime, OBS or QuickTime. "
                      + "It shows the live view while LumixOS is open.")
            }
        }
    }

    nonisolated func request(_ request: OSSystemExtensionRequest, didFailWithError error: Error) {
        let code = (error as NSError).code
        MainActor.assumeIsolated {
            let why: String
            switch OSSystemExtensionError.Code(rawValue: code) {
            case .missingEntitlement, .codeSignatureInvalid, .validationFailed:
                why = "The app or extension isn't signed with the required entitlement (Apple Developer team needed)."
            case .unsupportedParentBundleLocation: why = "Move LumixOS to /Applications."
            case .extensionNotFound: why = "The camera extension is missing from the app bundle."
            case .requestCanceled: why = "Cancelled."
            case .authorizationRequired: why = "Approval needed in System Settings → Login Items & Extensions."
            default: why = error.localizedDescription
            }
            alert("Camera extension: failed", "\(why)\n(code \(code))")
        }
    }

    func alert(_ title: String, _ text: String) {
        let a = NSAlert()
        a.messageText = title
        a.informativeText = text
        a.runModal()
    }
}
