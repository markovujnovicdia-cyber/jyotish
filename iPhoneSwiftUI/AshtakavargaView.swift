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
                Text("Σ \(total)").font(.subheadline).monospacedDigit()
            }
            ForEach(0..<min(12, values.count), id: \.self) { sign in
                HStack(spacing: 10) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(Astro.signs[sign]).font(.subheadline)
                        Text("Kuća \(Astro.house(sign: sign, ascendantSign: ascendantSign))")
                            .font(.caption2).foregroundStyle(.secondary)
                    }.frame(width: 90, alignment: .leading)
                    ProgressView(value: Double(values[sign]), total: scale)
                        .tint(.teal).accessibilityHidden(true)
                    Text("\(values[sign])").font(.subheadline.weight(.semibold))
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
            ScrollView(.horizontal, showsIndicators: true) {
                Grid(alignment: .trailing, horizontalSpacing: 16, verticalSpacing: 12) {
                    GridRow {
                        Text("Planet / znak").font(.caption.bold())
                        ForEach(0..<12, id: \.self) { sign in
                            Text(Astro.signs[sign]).font(.caption.bold())
                        }
                        Text("Σ").font(.caption.bold())
                    }
                    ForEach(Ashtakavarga.planetOrder, id: \.self) { planet in
                        if let row = result.bhinna[planet] {
                            GridRow {
                                Text(planet).font(.subheadline.weight(.medium))
                                ForEach(0..<min(12, row.count), id: \.self) { sign in
                                    Text("\(row[sign])").monospacedDigit()
                                        .accessibilityLabel("\(planet), \(Astro.signs[sign]), \(row[sign]) bindua")
                                }
                                Text("\(row.reduce(0, +))").fontWeight(.semibold).monospacedDigit()
                            }
                        }
                    }
                    GridRow {
                        Text("SAV").fontWeight(.bold())
                        ForEach(0..<min(12, result.sarva.count), id: \.self) { sign in
                            Text("\(result.sarva[sign])").fontWeight(.bold()).monospacedDigit()
                                .accessibilityLabel("SAV, \(Astro.signs[sign]), \(result.sarva[sign]) bindua")
                        }
                        Text("\(result.total)").fontWeight(.bold()).monospacedDigit()
                    }.foregroundStyle(.teal)
                }.padding(.vertical, 8)
            }
        }
    }

    private func card<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12, content: content)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 20))
    }
}
