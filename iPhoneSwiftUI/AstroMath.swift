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
    static func number(_ value: String) -> Double? {
        guard let result = Double(value.trimmingCharacters(in: .whitespacesAndNewlines).replacingOccurrences(of: ",", with: ".")), result.isFinite else { return nil }
        return result
    }
}

