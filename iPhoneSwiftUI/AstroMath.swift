import Foundation
import JyotishCore

enum AstroMath {
    static var signs: [String] { Astro.signs }
    static func sign(_ longitude: Double) -> (name: String, degrees: Double) {
        let value = Astro.normalize(longitude)
        return (Astro.signs[Int(value / 30)], value.truncatingRemainder(dividingBy: 30))
    }
    static func position(_ longitude: Double) -> String {
        let value = sign(longitude)
        return String(format: "%@ · %.4f°", value.name, value.degrees)
    }
    static func positionDMS(_ longitude: Double) -> String {
        guard longitude.isFinite else { return "—" }
        let seconds = Int((Astro.normalize(longitude) * 3600).rounded()) % (360 * 3600)
        let signIndex = seconds / (30 * 3600)
        let degree = (seconds / 3600) % 30
        let minute = (seconds / 60) % 60
        let second = seconds % 60
        return String(format: "%@ · %02d°%02d′%02d″", Astro.signs[signIndex], degree, minute, second)
    }
    static func number(_ value: String) -> Double? {
        guard let result = Double(value.trimmingCharacters(in: .whitespacesAndNewlines).replacingOccurrences(of: ",", with: ".")), result.isFinite else { return nil }
        return result
    }
}

