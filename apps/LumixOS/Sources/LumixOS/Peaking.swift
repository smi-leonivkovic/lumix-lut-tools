// Focus peaking on the GPU (Core Image): luminance -> edge strength -> threshold -> coloured, transparent overlay.
// Runs on the decode queue for each displayed frame; at 1280x960 it costs a few ms on Apple silicon.
import CoreImage
import CoreGraphics

enum PeakLevel: String, CaseIterable, Identifiable {
    case off = "Off", low = "Low", mid = "Mid", high = "High"
    var id: String { rawValue }
    /// edge threshold (0..1, lower = more highlighted)
    var threshold: Float? {
        switch self { case .off: nil; case .low: 0.35; case .mid: 0.20; case .high: 0.10 }
    }
}

enum PeakColor: String, CaseIterable, Identifiable {
    case red = "Red", yellow = "Yellow", blue = "Blue", white = "White"
    var id: String { rawValue }
    var rgb: (CGFloat, CGFloat, CGFloat) {
        switch self {
        case .red: (1, 0.15, 0.1)
        case .yellow: (1, 0.85, 0)
        case .blue: (0.2, 0.55, 1)
        case .white: (1, 1, 1)
        }
    }
}

final class Peaking {
    static var intensity: Double = 8.0  // tuned on DC-S9 1280x960 live view
    private let ctx = CIContext(options: [.cacheIntermediates: false, .priorityRequestLow: false])

    /// Transparent image with the in-focus edges in `color`, same size as `img`; nil if nothing to draw.
    func overlay(_ img: CGImage, threshold: Float, color: PeakColor) -> CGImage? {
        let src = CIImage(cgImage: img)
        let (r, g, b) = color.rgb
        let luma = src.applyingFilter("CIColorControls", parameters: [kCIInputSaturationKey: 0])
            .applyingFilter("CIGaussianBlur", parameters: [kCIInputRadiusKey: 0.6])  // tame JPEG block noise
            .cropped(to: src.extent)
        let edges = luma.applyingFilter("CIEdges", parameters: [kCIInputIntensityKey: Peaking.intensity])
        let mask = edges.applyingFilter("CIColorThreshold", parameters: ["inputThreshold": threshold])
        // red channel of the mask -> alpha; colour from the bias vector
        let colored = mask.applyingFilter("CIColorMatrix", parameters: [
            "inputRVector": CIVector(x: 0, y: 0, z: 0, w: 0),
            "inputGVector": CIVector(x: 0, y: 0, z: 0, w: 0),
            "inputBVector": CIVector(x: 0, y: 0, z: 0, w: 0),
            "inputAVector": CIVector(x: 1, y: 0, z: 0, w: 0),
            "inputBiasVector": CIVector(x: r, y: g, z: b, w: 0),
        ])
        return ctx.createCGImage(colored, from: src.extent)
    }

    /// Share of highlighted pixels (for tuning the thresholds).
    func coverage(_ img: CGImage, threshold: Float) -> Double {
        guard let o = overlay(img, threshold: threshold, color: .white),
              let data = o.dataProvider?.data, let p = CFDataGetBytePtr(data) else { return 0 }
        let n = o.width * o.height, bpp = o.bitsPerPixel / 8
        var hit = 0
        let alphaFirst = [CGImageAlphaInfo.premultipliedFirst, .first].contains(o.alphaInfo)
        for i in 0..<n where p[i * bpp + (alphaFirst ? 0 : 3)] > 127 { hit += 1 }
        return Double(hit) / Double(n)
    }
}
