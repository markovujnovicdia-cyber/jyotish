import SwiftUI
import JyotishCore

/// Both layers use the same natal frame: changing the reference changes the
/// house numbering, never the computed zodiac positions of either chart.
public struct TransitComparisonView: View {
    private let natal: Chart
    private let date: Date
    private let zoneID: String
    private let comparison: Result<[TransitRow], Error>
    @State private var reference: TransitReference = .lagna
    @State private var importantOnly = false

    public init(natal: Chart, transit: Chart, date: Date, zoneID: String) {
        self.natal = natal
        self.date = date
        self.zoneID = zoneID
        self.comparison = Result { try Transits.calculate(natal: natal, transit: transit) }
    }

    public var body: some View {
        switch comparison {
        case .success(let rows):
            content(rows: rows)
        case .failure(let error):
            TransitCard {
                Label("Tranzitnu usporedbu nije moguće prikazati", systemImage: "exclamationmark.triangle")
                    .font(.headline)
                Text(error.localizedDescription).font(.subheadline)
            }
        }
    }

    private func referenceSign() -> Int {
        let longitude = reference == .lagna ? natal.ascendantLongitude : natal.positions["Mjesec"]!.longitude
        return Int(Astro.normalize(longitude) / 30)
    }

    @ViewBuilder private func content(rows: [TransitRow]) -> some View {
        TransitCard {
            Text("Natalna i tranzitna karta").font(.headline)
            Text(BirthMoment.display(date, zoneID: zoneID, seconds: true))
                .font(.body).monospacedDigit()
            Text(zoneID).font(.subheadline).foregroundStyle(.secondary)
            Picker("Kuće promatrane od", selection: $reference) {
                ForEach(TransitReference.allCases) { option in Text(option.rawValue).tag(option) }
            }
            .pickerStyle(.segmented)
            .accessibilityIdentifier("transit-reference")
            HStack(spacing: 16) {
                Label("N · natalno", systemImage: "circle.fill").foregroundStyle(.teal)
                Label("T · tranzitno", systemImage: "diamond.fill").foregroundStyle(.orange)
            }
            .font(.subheadline.weight(.semibold))
            TransitOverlayChart(natal: natal, rows: rows, referenceSign: referenceSign(), reference: reference)
                .accessibilityIdentifier("transit-overlay-chart")
            Text("Prva kuća: \(Astro.signs[referenceSign()]). Oba sloja prikazuju položaje u istom zodijaku.")
                .font(.subheadline).foregroundStyle(.secondary)
        }
        TransitCard {
            Text("Položaji i kuće").font(.headline)
            Toggle("Samo Saturn, Jupiter, Rahu, Ketu i Mars", isOn: $importantOnly)
                .font(.subheadline)
            ForEach(rows.filter { !importantOnly || $0.highlighted }) { row in
                if let natalPosition = natal.positions[row.planet] {
                    TransitPositionRow(row: row, natalPosition: natalPosition)
                    Divider()
                }
            }
        }
        .accessibilityIdentifier("transit-comparison-results")
    }
}

private enum TransitReference: String, CaseIterable, Identifiable {
    case lagna = "Od natalne lagne"
    case moon = "Od natalnog Mjeseca"
    var id: String { rawValue }
}

private struct TransitCard<Content: View>: View {
    let content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }
    var body: some View {
        VStack(alignment: .leading, spacing: 12) { content }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 20))
    }
}

private struct TransitPositionRow: View {
    let row: TransitRow
    let natalPosition: PlanetPosition
    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack {
                Text(row.planet).font(.headline)
                Spacer()
                if row.isRetrograde {
                    Label("Retrogradno", systemImage: "arrow.uturn.backward")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            LabeledContent("N · natalno", value: position(natalPosition))
                .font(.body).foregroundStyle(.teal)
            LabeledContent("T · tranzitno", value: String(format: "%@ · %.4f°", row.sign, row.degreeInSign))
                .font(.body).foregroundStyle(.orange)
            ViewThatFits(in: .horizontal) {
                HStack(spacing: 16) { houseLabels }
                VStack(alignment: .leading, spacing: 4) { houseLabels }
            }
            .font(.subheadline).foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
        .accessibilityElement(children: .combine)
    }
    @ViewBuilder private var houseLabels: some View {
        Text("Od lagne: kuća \(row.houseFromAscendant)")
        Text("Od Mjeseca: kuća \(row.houseFromMoon)")
    }
    private func position(_ value: PlanetPosition) -> String {
        String(format: "%@ · %.4f°%@", value.sign, value.degree, value.isRetrograde ? " · R" : "")
    }
}

private struct TransitOverlayChart: View {
    let natal: Chart
    let rows: [TransitRow]
    let referenceSign: Int
    let reference: TransitReference
    private let centers: [CGPoint] = [
        CGPoint(x: 0.50, y: 0.25), CGPoint(x: 0.25, y: 0.085), CGPoint(x: 0.085, y: 0.25),
        CGPoint(x: 0.25, y: 0.50), CGPoint(x: 0.085, y: 0.75), CGPoint(x: 0.25, y: 0.915),
        CGPoint(x: 0.50, y: 0.75), CGPoint(x: 0.75, y: 0.915), CGPoint(x: 0.915, y: 0.75),
        CGPoint(x: 0.75, y: 0.50), CGPoint(x: 0.915, y: 0.25), CGPoint(x: 0.75, y: 0.085)
    ]
    private let shortNames = ["Sunce": "Su", "Mjesec": "Mo", "Mars": "Ma", "Merkur": "Me", "Jupiter": "Ju", "Venera": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"]
    private func natalLabels(house: Int) -> String {
        Astro.planetOrder.compactMap { name -> String? in
            guard let position = natal.positions[name], Astro.house(sign: position.signIndex, ascendantSign: referenceSign) == house else { return nil }
            return (shortNames[name] ?? name) + (position.isRetrograde ? "ᴿ" : "")
        }.joined(separator: " ")
    }
    private func transitLabels(house: Int) -> String {
        rows.filter { (reference == .lagna ? $0.houseFromAscendant : $0.houseFromMoon) == house }
            .map { (shortNames[$0.planet] ?? $0.planet) + ($0.isRetrograde ? "ᴿ" : "") }
            .joined(separator: " ")
    }
    var body: some View {
        GeometryReader { geometry in
            let side = min(geometry.size.width, geometry.size.height)
            ZStack {
                NorthIndianChartFrame().stroke(Color.teal.opacity(0.6), lineWidth: 1)
                ForEach(0..<12, id: \.self) { index in
                    TransitHouseCell(sign: (referenceSign + index) % 12 + 1,
                                     natalLabels: natalLabels(house: index + 1),
                                     transitLabels: transitLabels(house: index + 1), side: side)
                        .frame(width: side * 0.21, height: side * 0.18)
                        .position(x: side * centers[index].x, y: side * centers[index].y)
                }
            }
        }
        .aspectRatio(1, contentMode: .fit)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Usporedna sjevernoindijska karta. \(reference.rawValue), prvi znak \(Astro.signs[referenceSign]). N označava natalne, T tranzitne položaje. Svi položaji i kuće dostupni su u tablici ispod.")
    }
}

private struct TransitHouseCell: View {
    let sign: Int
    let natalLabels: String
    let transitLabels: String
    let side: CGFloat
    var body: some View {
        VStack(spacing: 2) {
            Text("\(sign)")
                .font(.system(size: max(12, side * 0.036), weight: .semibold))
            if !natalLabels.isEmpty {
                Text("N \(natalLabels)").foregroundStyle(.teal)
                    .font(.system(size: max(13, side * 0.041), weight: .bold))
            }
            if !transitLabels.isEmpty {
                Text("T \(transitLabels)").foregroundStyle(.orange)
                    .font(.system(size: max(13, side * 0.041), weight: .bold))
            }
        }
        .multilineTextAlignment(.center)
        .lineLimit(3)
        .minimumScaleFactor(0.85)
    }
}
