// Feeds the live view into OBS's virtual camera ("OBS Virtual Camera", OBS 30+ camera extension), so Zoom, Meet,
// FaceTime etc. can use the LUMIX without our own (Developer-team-signed) extension and without OBS running.
// OBS's extension has a source stream (what apps see) and a sink stream (what OBS writes into); its sink accepts
// any client. We do what OBS's mac-virtualcam plugin does: CMIOStreamCopyBufferQueue on the sink, start it, and
// enqueue 1920x1080 BGRA sample buffers.
import CoreMediaIO
import CoreVideo
import Foundation

final class OBSCameraFeed {
    static let deviceName = "OBS Virtual Camera"
    static let width = 1920, height = 1080

    private let q = DispatchQueue(label: "obs-feed", qos: .userInteractive)
    private var deviceID: CMIODeviceID = 0
    private var streamID: CMIOStreamID = 0
    private var queue: CMSimpleQueue?
    private var pool: CVPixelBufferPool?
    private var format: CMFormatDescription?
    private var busy = false
    private(set) var running = false
    var onStatus: ((String?, Bool) -> Void)?  // (error or nil, running)

    // MARK: CMIO helpers

    private static func address(_ selector: Int, scope: Int = kCMIOObjectPropertyScopeGlobal) -> CMIOObjectPropertyAddress {
        CMIOObjectPropertyAddress(mSelector: CMIOObjectPropertySelector(selector),
                                  mScope: CMIOObjectPropertyScope(scope),
                                  mElement: CMIOObjectPropertyElement(kCMIOObjectPropertyElementMain))
    }

    private static func ids(_ object: CMIOObjectID, _ selector: Int) -> [CMIOObjectID] {
        var addr = address(selector)
        var size: UInt32 = 0
        guard CMIOObjectGetPropertyDataSize(object, &addr, 0, nil, &size) == noErr, size > 0 else { return [] }
        var out = [CMIOObjectID](repeating: 0, count: Int(size) / MemoryLayout<CMIOObjectID>.size)
        var used: UInt32 = 0
        guard CMIOObjectGetPropertyData(object, &addr, 0, nil, size, &used, &out) == noErr else { return [] }
        return out
    }

    private static func name(_ object: CMIOObjectID) -> String? {
        var addr = address(kCMIOObjectPropertyName)
        var name: Unmanaged<CFString>?
        let size = UInt32(MemoryLayout<Unmanaged<CFString>?>.size)
        var used: UInt32 = 0
        guard CMIOObjectGetPropertyData(object, &addr, 0, nil, size, &used, &name) == noErr else { return nil }
        return name?.takeRetainedValue() as String?
    }

    static func available() -> Bool {
        ids(CMIOObjectID(kCMIOObjectSystemObject), kCMIOHardwarePropertyDevices).contains { name($0) == deviceName }
    }

    // MARK: start / stop

    func start() {
        q.async { self.startOnQueue() }
    }

    private func startOnQueue() {
        guard !running else { return }
        let devices = Self.ids(CMIOObjectID(kCMIOObjectSystemObject), kCMIOHardwarePropertyDevices)
        guard let dev = devices.first(where: { Self.name($0) == Self.deviceName }) else {
            return report("OBS Virtual Camera not found. Install OBS (30 or newer), click Start Virtual Camera once, allow the "
                          + "extension in System Settings, then stop it in OBS. OBS doesn't need to stay open.")
        }
        let streams = Self.ids(dev, kCMIODevicePropertyStreams)
        guard streams.count >= 2 else {
            return report("OBS Virtual Camera has no input stream (found \(streams.count) stream(s)). Update OBS to 30 or newer.")
        }
        deviceID = dev
        streamID = streams[1]  // [0] source (what apps see), [1] sink (input)
        var unmanaged: Unmanaged<CMSimpleQueue>?
        let st = CMIOStreamCopyBufferQueue(streamID, { _, _, _ in }, nil, &unmanaged)
        guard st == noErr, let qq = unmanaged?.takeRetainedValue() else {
            return report("Could not open OBS Virtual Camera's input (error \(st)). Is OBS's own virtual camera running? Stop it in OBS.")
        }
        queue = qq
        var desc: CMFormatDescription?
        CMVideoFormatDescriptionCreate(allocator: kCFAllocatorDefault, codecType: kCVPixelFormatType_32BGRA,
                                       width: Int32(Self.width), height: Int32(Self.height), extensions: nil,
                                       formatDescriptionOut: &desc)
        format = desc
        let attrs: NSDictionary = [kCVPixelBufferWidthKey: Self.width, kCVPixelBufferHeightKey: Self.height,
                                   kCVPixelBufferPixelFormatTypeKey: kCVPixelFormatType_32BGRA,
                                   kCVPixelBufferIOSurfacePropertiesKey: [:] as NSDictionary]
        CVPixelBufferPoolCreate(kCFAllocatorDefault, nil, attrs, &pool)
        let r = CMIODeviceStartStream(deviceID, streamID)
        guard r == noErr else {
            queue = nil
            return report("OBS Virtual Camera refused the input (error \(r)). Stop the virtual camera inside OBS and retry.")
        }
        running = true
        report(nil)
    }

    func stop() {
        q.async {
            guard self.running else { return }
            CMIODeviceStopStream(self.deviceID, self.streamID)
            self.running = false
            self.queue = nil
            self.report(nil)
        }
    }

    private func report(_ error: String?) {
        let r = running
        DispatchQueue.main.async { self.onStatus?(error, r) }
    }

    // MARK: frames

    /// Called for every decoded live view frame (any thread). Drops frames while the previous one is still being sent.
    func send(_ img: CGImage) {
        guard running else { return }
        q.async {
            guard self.running, !self.busy, let queue = self.queue, let pool = self.pool, let format = self.format else { return }
            if CMSimpleQueueGetCount(queue) >= CMSimpleQueueGetCapacity(queue) { return }  // consumer behind: newest wins later
            self.busy = true
            defer { self.busy = false }
            var pb: CVPixelBuffer?
            guard CVPixelBufferPoolCreatePixelBuffer(kCFAllocatorDefault, pool, &pb) == kCVReturnSuccess, let pb else { return }
            CVPixelBufferLockBaseAddress(pb, [])
            if let ctx = CGContext(data: CVPixelBufferGetBaseAddress(pb), width: Self.width, height: Self.height,
                                   bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pb),
                                   space: CGColorSpaceCreateDeviceRGB(),
                                   bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue) {
                ctx.setFillColor(CGColor(gray: 0, alpha: 1))
                ctx.fill(CGRect(x: 0, y: 0, width: Self.width, height: Self.height))
                let s = min(CGFloat(Self.width) / CGFloat(img.width), CGFloat(Self.height) / CGFloat(img.height))
                let w = CGFloat(img.width) * s, h = CGFloat(img.height) * s
                ctx.interpolationQuality = .medium
                ctx.draw(img, in: CGRect(x: (CGFloat(Self.width) - w) / 2, y: (CGFloat(Self.height) - h) / 2, width: w, height: h))
            }
            CVPixelBufferUnlockBaseAddress(pb, [])
            var timing = CMSampleTimingInfo(duration: CMTime(value: 1, timescale: 30),
                                            presentationTimeStamp: CMClockGetTime(CMClockGetHostTimeClock()),
                                            decodeTimeStamp: .invalid)
            var sb: CMSampleBuffer?
            guard CMSampleBufferCreateForImageBuffer(allocator: kCFAllocatorDefault, imageBuffer: pb, dataReady: true,
                                                     makeDataReadyCallback: nil, refcon: nil, formatDescription: format,
                                                     sampleTiming: &timing, sampleBufferOut: &sb) == noErr, let sb else { return }
            // the extension takes ownership of the enqueued buffer (as in OBS's plugin)
            let st = CMSimpleQueueEnqueue(queue, element: Unmanaged.passRetained(sb).toOpaque())
            if st != noErr { Unmanaged.passUnretained(sb).release() }
        }
    }
}
