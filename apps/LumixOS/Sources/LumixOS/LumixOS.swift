// LumixOS: native macOS live view + settings for a LUMIX camera on USB.
// Talks to `python -m lumix.server` on 127.0.0.1:8765 (started automatically from the repo's .venv).
import AppKit
import ImageIO
import SwiftUI

let serverURL = URL(string: "http://127.0.0.1:8765")!

// MARK: - Backend process

final class Backend {
    static let shared = Backend()
    private var process: Process?

    var repo: URL {
        if let r = ProcessInfo.processInfo.environment["LUMIX_REPO"] { return URL(fileURLWithPath: r) }
        return FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Projects/lumix-lut-tools")
    }

    func start() {
        let python = repo.appendingPathComponent(".venv/bin/python")
        guard FileManager.default.isExecutableFile(atPath: python.path) else { return }
        let p = Process()
        p.executableURL = python
        p.arguments = ["-m", "lumix.server", "--size", "1280x960"]
        p.currentDirectoryURL = repo
        p.standardOutput = FileHandle.nullDevice
        p.standardError = FileHandle.nullDevice
        try? p.run()
        process = p
    }

    func stop() { process?.terminate() }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ n: Notification) {
        Backend.shared.start()
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }
    func applicationWillTerminate(_ n: Notification) { Backend.shared.stop() }
    func applicationShouldTerminateAfterLastWindowClosed(_ s: NSApplication) -> Bool { true }
}

// MARK: - MJPEG stream (newest frame only)

final class LiveStream: NSObject, ObservableObject, URLSessionDataDelegate {
    @Published var image: CGImage?
    @Published var displayFPS: Double = 0
    private var buffer = Data()
    private var session: URLSession!
    private var frames = 0
    private var fpsStart = Date()
    private let decodeQueue = DispatchQueue(label: "decode", qos: .userInteractive)
    private var decoding = false

    func connect() {
        buffer.removeAll()
        let cfg = URLSessionConfiguration.ephemeral
        cfg.timeoutIntervalForRequest = 3600
        session = URLSession(configuration: cfg, delegate: self, delegateQueue: nil)
        session.dataTask(with: serverURL.appendingPathComponent("stream")).resume()
    }

    func urlSession(_ s: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        buffer.append(data)
        var latest: Data?
        // take every complete part, keep only the newest JPEG
        while let hdrEnd = buffer.range(of: Data("\r\n\r\n".utf8)) {
            let header = String(decoding: buffer[buffer.startIndex..<hdrEnd.lowerBound], as: UTF8.self)
            guard let lenLine = header.split(separator: "\r\n").first(where: { $0.lowercased().hasPrefix("content-length") }),
                  let len = Int(lenLine.split(separator: ":")[1].trimmingCharacters(in: .whitespaces)) else {
                buffer.removeSubrange(buffer.startIndex..<hdrEnd.upperBound); continue
            }
            let start = hdrEnd.upperBound
            guard buffer.distance(from: start, to: buffer.endIndex) >= len else { break }
            latest = buffer.subdata(in: start..<buffer.index(start, offsetBy: len))
            buffer.removeSubrange(buffer.startIndex..<buffer.index(start, offsetBy: len))
        }
        guard let jpg = latest, !decoding else { return }  // drop frames while decoding: lowest latency
        decoding = true
        decodeQueue.async {
            let opts = [kCGImageSourceShouldCacheImmediately: true] as CFDictionary
            let img = CGImageSourceCreateWithData(jpg as CFData, nil).flatMap { CGImageSourceCreateImageAtIndex($0, 0, opts) }
            DispatchQueue.main.async {
                self.decoding = false
                if let img { self.image = img; self.tick() }
            }
        }
    }

    func urlSession(_ s: URLSession, task: URLSessionTask, didCompleteWithError e: Error?) {
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) { self.connect() }  // server starting or restarted
    }

    private func tick() {
        frames += 1
        let dt = Date().timeIntervalSince(fpsStart)
        if dt >= 1 { displayFPS = Double(frames) / dt; frames = 0; fpsStart = Date() }
    }
}

// MARK: - Camera state and commands

struct CameraState: Decodable {
    var status: String
    var fps: Double
    var fetch_ms: Double
    var size: String
    var options: [String: [String]]
    var current: [String: String]
}

@MainActor
final class CameraModel: ObservableObject {
    @Published var state: CameraState?
    private var timer: Timer?

    func startPolling() {
        timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { _ in Task { await self.refresh() } }
    }

    func refresh() async {
        guard let (data, _) = try? await URLSession.shared.data(from: serverURL.appendingPathComponent("state")),
              let s = try? JSONDecoder().decode(CameraState.self, from: data) else { return }
        state = s
    }

    func post(_ path: String, _ body: [String: String] = [:]) {
        var req = URLRequest(url: serverURL.appendingPathComponent(path))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        Task {
            _ = try? await URLSession.shared.data(for: req)
            try? await Task.sleep(nanoseconds: 300_000_000)
            await refresh()
        }
    }
}

// MARK: - UI

let settingOrder: [(String, String)] = [
    ("photo_style", "Photo Style"), ("lut1_opacity", "LUT opacity"), ("white_balance", "White balance"),
    ("kelvin", "Kelvin"), ("iso", "ISO"), ("exposure_comp", "Exposure comp."), ("aperture", "Aperture"),
    ("shutter", "Shutter"), ("color_noise", "Colour noise"), ("image_format", "Image format"),
]

struct ContentView: View {
    @StateObject var stream = LiveStream()
    @StateObject var camera = CameraModel()
    @State var zebras = false

    var body: some View {
        GeometryReader { geo in
            let wide = geo.size.width >= 900 || geo.size.width > geo.size.height * 1.25
            Group {
                if wide {
                    HStack(spacing: 0) { live; Divider(); panel.frame(width: min(280, max(220, geo.size.width * 0.22))) }
                } else {
                    VStack(spacing: 0) { live; Divider(); panel.frame(height: min(320, geo.size.height * 0.42)) }
                }
            }
        }
        .frame(minWidth: 520, minHeight: 420)
        .onAppear { stream.connect(); camera.startPolling() }
        .background(KeyCatcher(onKey: key))
    }

    var live: some View {
        ZStack {
            Color.black
            if let img = stream.image {
                Image(decorative: img, scale: 1).resizable().interpolation(.medium).aspectRatio(contentMode: .fit)
            } else {
                Text(camera.state?.status ?? "starting camera service…").foregroundStyle(.secondary)
            }
            VStack {
                HStack { styleBadge; Spacer() }
                Spacer()
                HStack {
                    Text(statusLine).font(.system(size: 11, design: .monospaced)).foregroundStyle(.white)
                        .padding(6).background(.black.opacity(0.55), in: RoundedRectangle(cornerRadius: 6))
                    Spacer()
                }
            }
            .padding(10)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    var styleBadge: some View {
        let c = camera.state?.current ?? [:]
        let parts = [c["photo_style"].map { $0.replacingOccurrences(of: "_", with: " ").uppercased() },
                     c["white_balance"].map { $0 == "kelvin" ? (c["kelvin"] ?? "K") : $0.replacingOccurrences(of: "_", with: " ") },
                     c["iso"].map { "ISO " + $0 }, c["aperture"], c["shutter"], c["exposure_comp"]].compactMap { $0 }
        return Text(parts.joined(separator: "  ·  "))
            .font(.system(size: 13, weight: .semibold)).foregroundStyle(.white)
            .padding(.horizontal, 10).padding(.vertical, 6)
            .background(.black.opacity(0.55), in: RoundedRectangle(cornerRadius: 8))
            .opacity(parts.isEmpty ? 0 : 1)
    }

    var statusLine: String {
        guard let s = camera.state else { return "connecting…" }
        return String(format: "%.0f fps shown · camera %.0f fps · fetch %.0f ms · %@ · %@", stream.displayFPS, s.fps, s.fetch_ms, s.size, s.status)
    }

    var panel: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 220), alignment: .topLeading)], alignment: .leading, spacing: 10) {
                Text("LUMIX").font(.title2.bold())
                HStack {
                    Button("AF  (f)") { camera.post("af") }
                    Button("Shutter  (space)") { camera.post("shutter") }.keyboardShortcut(.defaultAction)
                }
                if let s = camera.state {
                    ForEach(settingOrder, id: \.0) { key, label in
                        if let opts = s.options[key], !opts.isEmpty {
                            Picker(label, selection: Binding(
                                get: { s.current[key] ?? "" },
                                set: { camera.post("set", ["key": key, "label": $0]) })) {
                                ForEach(opts, id: \.self) { Text($0).tag($0) }
                            }
                        }
                    }
                    Picker("Live view", selection: Binding(get: { s.size }, set: { camera.post("size", ["size": $0]) })) {
                        ForEach(["640x480", "960x720", "1280x960"], id: \.self) { Text($0).tag($0) }
                    }
                }
                Button("Undo all changes") { camera.post("undo") }
                Text("P/A/S/M and the active LUT are chosen on the camera.")
                    .font(.footnote).foregroundStyle(.secondary)
            }
            .padding(14)
        }
    }

    func key(_ c: String) {
        switch c {
        case "f": camera.post("af")
        case " ": camera.post("shutter")
        default: break
        }
    }
}

struct KeyCatcher: NSViewRepresentable {
    let onKey: (String) -> Void
    func makeNSView(context: Context) -> NSView {
        let v = KeyView(); v.onKey = onKey
        DispatchQueue.main.async { v.window?.makeFirstResponder(v) }
        return v
    }
    func updateNSView(_ v: NSView, context: Context) {}
    final class KeyView: NSView {
        var onKey: ((String) -> Void)?
        override var acceptsFirstResponder: Bool { true }
        override func keyDown(with e: NSEvent) { onKey?(e.charactersIgnoringModifiers ?? "") }
    }
}

@main
struct LumixOSApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var delegate
    var body: some Scene {
        WindowGroup("LumixOS") { ContentView() }
            .windowResizability(.contentMinSize)
    }
}
