import SwiftUI
import JyotishCore

struct AshtakavargaView: View {
    let result: AshtakavargaResult
    let ascendantSign: Int
    @State private var selected = "SAV"

    private var values: [Int] { selected == "SAV" ? result.sarva : (result.bhinna[selected] ?? []) }
    private var total: Int { values.reduce(0, +) }
    private var scale: Double { selected == "SAV" ? 56 : 8 }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            summary
            distribution
            table
        }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("ashtakavarga-results")
    }

    private var summary: some View {
        card {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Sarvashtakavarga").font(.headline)
                    Text("SAV · zbroj sedam BAV tablica").font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Text("\(result.total)").font(.largeTitle.bold()).monospacedDigit()
                    .accessibilityLabel("Ukupno \(result.total) bindua")
                    .accessibilityIdentifier("ashtakavarga-total")
            }
            Text("Izvori: sedam klasičnih planeta i Lagna. Rahu i Ketu nisu uključeni. Bez Trikona i Ekadhipatya redukcija.")
                .font(.caption).foregroundStyle(.secondary)
        }
    }

    private var distribution: some View {
        card {
            Picker("Tablica", selection: $selected) {
                Text("SAV · ukupno").tag("SAV")
                ForEach(Ashtakavarga.planetOrder, id: \.self) { planet in
                    Text("BAV · \(planet)").tag(planet)
                }
            }.pickerStyle(.menu)
            HStack {
                Text(selected == "SAV" ? "Bindui po znaku" : "\(selected) · bindui po znaku")
                    .font(.headline)
                Spacer()
                Text("Σ \(total)").font(.body).monospacedDigit()
            }
            ForEach(0..<min(12, values.count), id: \.self) { sign in
                HStack(spacing: 10) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(Astro.signs[sign]).font(.body)
                        Text("Kuća \(Astro.house(sign: sign, ascendantSign: ascendantSign))")
                            .font(.subheadline).foregroundStyle(.secondary)
                    }.frame(width: 100, alignment: .leading)
                    ProgressView(value: Double(values[sign]), total: scale)
                        .tint(.teal).accessibilityHidden(true)
                    Text("\(values[sign])").font(.body.weight(.semibold))
                        .monospacedDigit().frame(width: 28, alignment: .trailing)
                }
                .accessibilityElement(children: .combine)
                .accessibilityLabel("\(Astro.signs[sign]), kuća \(Astro.house(sign: sign, ascendantSign: ascendantSign)), \(values[sign]) bindua")
            }
        }
    }

    private var table: some View {
        card {
            Text("Bhinna i Sarva · sve vrijednosti").font(.headline)
            Text("Pomičite tablicu vodoravno za svih 12 znakova.").font(.caption).foregroundStyle(.secondary)
            AshtakavargaMatrix(result: result)
        }
    }

    private func card<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12, content: content)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 20))
    }
}

/// Separate concrete rows keep SwiftUI's generic expressions small enough for
/// Xcode to type-check, while retaining all twelve columns and their sums.
private struct AshtakavargaMatrix: View {
    let result: AshtakavargaResult
    var body: some View {
        ScrollView(.horizontal, showsIndicators: true) {
            VStack(alignment: .leading, spacing: 12) {
                AshtakavargaMatrixHeader()
                ForEach(Ashtakavarga.planetOrder, id: \.self) { planet in
                    if let row = result.bhinna[planet] {
                        AshtakavargaMatrixRow(label: planet, values: row)
                    }
                }
                AshtakavargaMatrixRow(label: "SAV", values: result.sarva, isTotal: true)
            }.padding(.vertical, 8)
        }
    }
}

private struct AshtakavargaMatrixHeader: View {
    var body: some View {
        HStack(alignment: .bottom, spacing: 12) {
            Text("Planet / znak").frame(width: 96, alignment: .leading)
            ForEach(0..<12, id: \.self) { sign in
                Text(Astro.signs[sign]).frame(width: 88)
            }
            Text("Σ").frame(width: 52, alignment: .trailing)
        }.font(.subheadline.bold())
    }
}

private struct AshtakavargaMatrixRow: View {
    let label: String
    let values: [Int]
    var isTotal = false

    var body: some View {
        HStack(spacing: 12) {
            Text(label).frame(width: 96, alignment: .leading)
            ForEach(0..<min(12, values.count), id: \.self) { sign in
                Text("\(values[sign])").frame(width: 88)
                    .accessibilityLabel("\(label), \(Astro.signs[sign]), \(values[sign]) bindua")
            }
            Text("\(values.reduce(0, +))").frame(width: 52, alignment: .trailing)
        }
        .font(.body.weight(isTotal ? .bold : .medium))
        .foregroundStyle(isTotal ? Color.teal : Color.primary)
        .monospacedDigit()
    }
}
