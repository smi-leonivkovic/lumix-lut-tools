// LumixCamera: CoreMediaIO camera extension ("LumixOS Camera") for Zoom, Meet, FaceTime, OBS, QuickTime...
// It shows the live view that LumixOS's camera service streams on 127.0.0.1:8765 (newest frame only), letterboxed
// into 1280x960 (4:3) or 1920x1080 (16:9). Without LumixOS running it shows a hint card instead.
// Built and embedded by build_app.sh; needs a Developer team to be activated (see README).
import AppKit
import CoreMediaIO
import CoreVideo
import Foundation
import ImageIO
import os.log

let log = Logger(subsystem: "lumixos.camera", category: "extension")
let streamURL = URL(string: "http://127.0.0.1:8765/stream?raw=1")!

// MARK: - Frames from the LumixOS camera service

final class FrameFeed: NSObject, URLSessionDataDelegate {
    var onImage: ((CGImage) -> Void)?
    private(set) var lastFrame = Date.distantPast
    private var session: URLSession?
    private var buffer = Data()
    private var running = false
    private let q: OperationQueue = { let q = OperationQueue(); q.maxConcurrentOperationCount = 1; return q }()

    func start() {
        running = true
        connect()
    }

    func stop() {
        running = false
        session?.invalidateAndCancel()
        session = nil
    }

    private func connect() {
        guard running else { return }
        buffer.removeAll()
        let cfg = URLSessionConfiguration.ephemeral
        cfg.timeoutIntervalForRequest = 5
        let s = URLSession(configuration: cfg, delegate: self, delegateQueue: q)
        session = s
        s.dataTask(with: streamURL).resume()
    }

    func urlSession(_ s: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        buffer.append(data)
        if buffer.count > 32 << 20 { buffer.removeAll(); return }
        var latest: Data?
        while let hdrEnd = buffer.range(of: Data("\r\n\r\n".utf8)) {
            let header = String(decoding: buffer[buffer.startIndex..<hdrEnd.lowerBound], as: UTF8.self)
            guard let line = header.split(separator: "\r\n").first(where: { $0.lowercased().hasPrefix("content-length") }),
                  let len = Int(line.split(separator: ":").last?.trimmingCharacters(in: .whitespaces) ?? "") else {
                buffer.removeSubrange(buffer.startIndex..<hdrEnd.upperBound); continue
            }
            let start = hdrEnd.upperBound
            guard buffer.distance(from: start, to: buffer.endIndex) >= len else { break }
            latest = buffer.subdata(in: start..<buffer.index(start, offsetBy: len))
            buffer.removeSubrange(buffer.startIndex..<buffer.index(start, offsetBy: len))
        }
        guard let jpg = latest,
              let src = CGImageSourceCreateWithData(jpg as CFData, nil),
              let img = CGImageSourceCreateImageAtIndex(src, 0, [kCGImageSourceShouldCacheImmediately: true] as CFDictionary)
        else { return }
        lastFrame = Date()
        onImage?(img)
    }

    func urlSession(_ s: URLSession, task: URLSessionTask, didCompleteWithError e: Error?) {
        s.finishTasksAndInvalidate()
        DispatchQueue.global().asyncAfter(deadline: .now() + 1) { self.connect() }  // LumixOS not running yet
    }
}

// MARK: - Device and stream

let formats: [(Int32, Int32)] = [(1280, 960), (1920, 1080)]
let fps: Int32 = 30

final class DeviceSource: NSObject, CMIOExtensionDeviceSource {
    private(set) var device: CMIOExtensionDevice!
    private var streamSource: StreamSource!
    private var pools: [CVPixelBufferPool] = []
    private var descriptions: [CMFormatDescription] = []
    private let feed = FrameFeed()
    private var clients = 0
    private var hintTimer: DispatchSourceTimer?
    private let renderQ = DispatchQueue(label: "render", qos: .userInteractive)
    var activeFormat = 0

    init(localizedName: String) {
        super.init()
        device = CMIOExtensionDevice(localizedName: localizedName,
                                     deviceID: UUID(uuidString: "6C2C6B7E-4A2E-4D3B-9C55-7B1C3B0E5A11")!,
                                     legacyDeviceID: nil, source: self)
        var streamFormats: [CMIOExtensionStreamFormat] = []
        for (w, h) in formats {
            var desc: CMFormatDescription?
            CMVideoFormatDescriptionCreate(allocator: kCFAllocatorDefault, codecType: kCVPixelFormatType_32BGRA,
                                           width: w, height: h, extensions: nil, formatDescriptionOut: &desc)
            var pool: CVPixelBufferPool?
            let attrs: NSDictionary = [kCVPixelBufferWidthKey: w, kCVPixelBufferHeightKey: h,
                                       kCVPixelBufferPixelFormatTypeKey: kCVPixelFormatType_32BGRA,
                                       kCVPixelBufferIOSurfacePropertiesKey: [:] as NSDictionary]
            CVPixelBufferPoolCreate(kCFAllocatorDefault, nil, attrs, &pool)
            descriptions.append(desc!)
            pools.append(pool!)
            let d = CMTime(value: 1, timescale: fps)
            streamFormats.append(CMIOExtensionStreamFormat(formatDescription: desc!, maxFrameDuration: d,
                                                           minFrameDuration: d, validFrameDurations: nil))
        }
        streamSource = StreamSource(localizedName: "LumixOS Camera.Video",
                                    streamID: UUID(uuidString: "0E0A6B1D-2C64-4C2F-8F4B-3B6C1A9D7E22")!,
                                    formats: streamFormats, device: self)
        do { try device.addStream(streamSource.stream) } catch { log.error("addStream: \(error.localizedDescription)") }
        feed.onImage = { [weak self] img in self?.renderQ.async { self?.send(img) } }
    }

    var availableProperties: Set<CMIOExtensionProperty> { [.deviceTransportType, .deviceModel] }

    func deviceProperties(forProperties properties: Set<CMIOExtensionProperty>) throws -> CMIOExtensionDeviceProperties {
        let p = CMIOExtensionDeviceProperties(dictionary: [:])
        if properties.contains(.deviceTransportType) { p.transportType = 0x7669_7274 }  // 'virt'
        if properties.contains(.deviceModel) { p.model = "LUMIX live view via LumixOS" }
        return p
    }

    func setDeviceProperties(_ deviceProperties: CMIOExtensionDeviceProperties) throws {}

    func startStreaming() {
        clients += 1
        guard clients == 1 else { return }
        feed.start()
        let t = DispatchSource.makeTimerSource(queue: renderQ)  // hint card while no live view arrives
        t.schedule(deadline: .now() + 0.5, repeating: 0.5)
        t.setEventHandler { [weak self] in
            guard let self, Date().timeIntervalSince(self.feed.lastFrame) > 1 else { return }
            self.send(nil)
        }
        t.resume()
        hintTimer = t
    }

    func stopStreaming() {
        clients = max(0, clients - 1)
        guard clients == 0 else { return }
        feed.stop()
        hintTimer?.cancel()
        hintTimer = nil
    }

    /// Draw the frame (or the hint card when nil) into a pixel buffer and hand it to the stream.
    private func send(_ img: CGImage?) {
        let i = min(activeFormat, pools.count - 1)
        var pb: CVPixelBuffer?
        guard CVPixelBufferPoolCreatePixelBuffer(kCFAllocatorDefault, pools[i], &pb) == kCVReturnSuccess, let pb else { return }
        CVPixelBufferLockBaseAddress(pb, [])
        let w = CVPixelBufferGetWidth(pb), h = CVPixelBufferGetHeight(pb)
        if let ctx = CGContext(data: CVPixelBufferGetBaseAddress(pb), width: w, height: h, bitsPerComponent: 8,
                               bytesPerRow: CVPixelBufferGetBytesPerRow(pb), space: CGColorSpaceCreateDeviceRGB(),
                               bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue) {
            ctx.setFillColor(CGColor(gray: 0, alpha: 1))
            ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
            if let img {
                let s = min(CGFloat(w) / CGFloat(img.width), CGFloat(h) / CGFloat(img.height))
                let dw = CGFloat(img.width) * s, dh = CGFloat(img.height) * s
                ctx.interpolationQuality = .medium
                ctx.draw(img, in: CGRect(x: (CGFloat(w) - dw) / 2, y: (CGFloat(h) - dh) / 2, width: dw, height: dh))
            } else {
                drawHint(ctx, w: w, h: h)
            }
        }
        CVPixelBufferUnlockBaseAddress(pb, [])

        var timing = CMSampleTimingInfo(duration: CMTime(value: 1, timescale: fps),
                                        presentationTimeStamp: CMClockGetTime(CMClockGetHostTimeClock()),
                                        decodeTimeStamp: .invalid)
        var sb: CMSampleBuffer?
        guard CMSampleBufferCreateForImageBuffer(allocator: kCFAllocatorDefault, imageBuffer: pb, dataReady: true,
                                                 makeDataReadyCallback: nil, refcon: nil,
                                                 formatDescription: descriptions[i], sampleTiming: &timing,
                                                 sampleBufferOut: &sb) == noErr, let sb else { return }
        streamSource.stream.send(sb, discontinuity: [],
                                 hostTimeInNanoseconds: UInt64(timing.presentationTimeStamp.seconds * 1e9))
    }

    private func drawHint(_ ctx: CGContext, w: Int, h: Int) {
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = NSGraphicsContext(cgContext: ctx, flipped: false)
        let title = NSAttributedString(string: "LumixOS Camera", attributes: [
            .font: NSFont.systemFont(ofSize: CGFloat(h) / 14, weight: .bold), .foregroundColor: NSColor.white])
        let sub = NSAttributedString(string: "Open LumixOS and connect the camera by USB (PC Tether).", attributes: [
            .font: NSFont.systemFont(ofSize: CGFloat(h) / 32), .foregroundColor: NSColor(white: 0.75, alpha: 1)])
        let tb = title.size(), sbz = sub.size()
        title.draw(at: NSPoint(x: (CGFloat(w) - tb.width) / 2, y: CGFloat(h) / 2 + 8))
        sub.draw(at: NSPoint(x: (CGFloat(w) - sbz.width) / 2, y: CGFloat(h) / 2 - sbz.height - 8))
        NSGraphicsContext.restoreGraphicsState()
    }
}

final class StreamSource: NSObject, CMIOExtensionStreamSource {
    private(set) var stream: CMIOExtensionStream!
    let formats: [CMIOExtensionStreamFormat]
    unowned let deviceSource: DeviceSource

    init(localizedName: String, streamID: UUID, formats: [CMIOExtensionStreamFormat], device: DeviceSource) {
        self.formats = formats
        self.deviceSource = device
        super.init()
        stream = CMIOExtensionStream(localizedName: localizedName, streamID: streamID, direction: .source,
                                     clockType: .hostTime, source: self)
    }

    var availableProperties: Set<CMIOExtensionProperty> { [.streamActiveFormatIndex, .streamFrameDuration] }

    func streamProperties(forProperties properties: Set<CMIOExtensionProperty>) throws -> CMIOExtensionStreamProperties {
        let p = CMIOExtensionStreamProperties(dictionary: [:])
        if properties.contains(.streamActiveFormatIndex) { p.activeFormatIndex = deviceSource.activeFormat }
        if properties.contains(.streamFrameDuration) { p.frameDuration = CMTime(value: 1, timescale: fps) }
        return p
    }

    func setStreamProperties(_ streamProperties: CMIOExtensionStreamProperties) throws {
        if let i = streamProperties.activeFormatIndex, i >= 0, i < formats.count { deviceSource.activeFormat = i }
    }

    func authorizedToStartStream(for client: CMIOExtensionClient) -> Bool { true }
    func startStream() throws { deviceSource.startStreaming() }
    func stopStream() throws { deviceSource.stopStreaming() }
}

final class ProviderSource: NSObject, CMIOExtensionProviderSource {
    private(set) var provider: CMIOExtensionProvider!
    private var deviceSource: DeviceSource!

    init(clientQueue: DispatchQueue?) {
        super.init()
        provider = CMIOExtensionProvider(source: self, clientQueue: clientQueue)
        deviceSource = DeviceSource(localizedName: "LumixOS Camera")
        do { try provider.addDevice(deviceSource.device) } catch { log.error("addDevice: \(error.localizedDescription)") }
    }

    func connect(to client: CMIOExtensionClient) throws {}
    func disconnect(from client: CMIOExtensionClient) {}
    var availableProperties: Set<CMIOExtensionProperty> { [.providerManufacturer] }

    func providerProperties(forProperties properties: Set<CMIOExtensionProperty>) throws -> CMIOExtensionProviderProperties {
        let p = CMIOExtensionProviderProperties(dictionary: [:])
        if properties.contains(.providerManufacturer) { p.manufacturer = "LumixOS" }
        return p
    }

    func setProviderProperties(_ providerProperties: CMIOExtensionProviderProperties) throws {}
}

let providerSource = ProviderSource(clientQueue: nil)
CMIOExtensionProvider.startService(provider: providerSource.provider)
CFRunLoopRun()
