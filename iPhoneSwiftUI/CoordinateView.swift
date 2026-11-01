import SwiftUI
import JyotishCore

struct CoordinateView: View {
    @State private var longitudeText = "201.69"
    private var longitude: Double? { AstroMath.number(longitudeText) }
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            VStack(alignment: .leading, spacing: 10) {
                Text("Siderealna ekliptička dužina").font(.headline)
                TextField("Stupnjevi, npr. 201,69", text: $longitudeText)
                    .keyboardType(.numbersAndPunctuation).textFieldStyle(.roundedBorder)
                Text("Za već poznatu dužinu prikazuje znak, nakšatru i padu. Vrijednost se normalizira na 0–360°.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            if let longitude, let nak = try? Nakshatra.at(longitude: longitude) {
                let sign = AstroMath.sign(longitude)
                LabeledContent("Znak", value: sign.name)
                LabeledContent("Stupnjevi u znaku", value: String(format: "%.5f°", sign.degrees))
                LabeledContent("Nakšatra", value: nak.name)
                LabeledContent("Pada", value: "\(nak.pada)")
                LabeledContent("Vladar nakšatre", value: nak.lord)
            } else {
                Text("Unesite konačan broj.").foregroundStyle(.red)
            }
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 20))
    }
}
