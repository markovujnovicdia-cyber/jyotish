import SwiftUI
import JyotishCore

private enum Screen: String, CaseIterable, Identifiable {
    case natal = "Karte", dasha = "Daše", annual = "Varshaphala", masa = "Masa Praveša", transit = "Tranziti", ashtakavarga = "Ashtakavarga"
    var id: String { rawValue }
    var symbol: String {
        switch self {
        case .natal: return "square.on.square"
        case .dasha: return "timeline.selection"
        case .annual: return "sun.max"
        case .masa: return "calendar"
        case .transit: return "globe.europe.africa"
        case .ashtakavarga: return "chart.bar.xaxis"
        }
    }
    var kind: CalculationKind {
        switch self {
        case .natal: return .natal
        case .dasha: return .dasha
        case .annual: return .annual
        case .masa: return .masa
        case .transit: return .transit
        case .ashtakavarga: return .ashtakavarga
        }
    }
}

@MainActor
struct ContentView: View {
    @StateObject private var store: PersonStore
    @StateObject private var calculations = CalculationModel()
    @State private var selectedID: UUID?
    @State private var screen: Screen = .natal
    @State private var year = Calendar.current.component(.year, from: .now)
    @State private var referenceDate = Date.now
    @State private var annualSelectionGeneration = UUID()
    @State private var annualSelectionError: String?
    @State private var showAdd = false
    @State private var showPeople = false
    @State private var showLicenses = false
    @State private var editing: Person?

    init() {
        let testing = ProcessInfo.processInfo.arguments.contains("-ui-testing-reset")
        let defaults: UserDefaults
        if testing, let isolated = UserDefaults(suiteName: "JyotishUITests") {
            isolated.removePersistentDomain(forName: "JyotishUITests")
            defaults = isolated
        } else {
            defaults = .standard
        }
        _store = StateObject(wrappedValue: PersonStore(defaults: defaults))
    }

    private var person: Person? { store.people.first(where: { $0.id == selectedID }) ?? store.people.first }
    private var request: CalculationRequest? {
        guard let person else { return nil }
        return CalculationRequest(person: person, kind: screen.kind, year: year, referenceDate: referenceDate)
    }
    private var birthYear: Int {
        guard let person else { return 1800 }
        var calendar = BirthMoment.calendar
        calendar.timeZone = TimeZone(identifier: person.timeZone) ?? BirthMoment.utc
        return calendar.component(.year, from: person.birthDate)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                screenPicker
                ScrollView {
                    VStack(alignment: .leading, spacing: 18) {
                        personHeader
                        if let message = store.storageError { ErrorCard(message: message) }
                        if let person {
                            controls(for: person)
                            if calculations.isLoading {
                                ProgressView("Računanje na uređaju…")
                                    .frame(maxWidth: .infinity).padding(32)
                                    .accessibilityIdentifier("calculation-progress")
                            } else if let error = calculations.error {
                                ErrorCard(message: error)
                            } else if let output = calculations.output {
                                results(output, person: person)
                            }
                        } else {
                            ContentUnavailableView("Vaša prva karta", systemImage: "sparkles", description: Text("Dodajte podatke rođenja. Svi izračuni i spremljene osobe ostaju na iPhoneu."))
                            Button("Dodaj osobu", systemImage: "plus") { showAdd = true }
                                .buttonStyle(.borderedProminent).frame(maxWidth: .infinity)
                        }
                        Button("O aplikaciji i licencama", systemImage: "info.circle") { showLicenses = true }
                            .font(.footnote).frame(maxWidth: .infinity)
                        Text("Lahiri · siderealni zodijak · mean Rahu · Whole Sign")
                            .font(.caption).foregroundStyle(.secondary)
                            .frame(maxWidth: .infinity, alignment: .center)
                    }
                    .padding()
                }
                .background(Color(uiColor: .systemGroupedBackground))
            }
            .navigationTitle("Jyotish")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Osobe", systemImage: "person.2") { showPeople = true }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Dodaj osobu", systemImage: "plus") { showAdd = true }
                        .accessibilityIdentifier("add-person")
                }
            }
            .sheet(isPresented: $showAdd) {
                PersonEditor { saved in try store.save(saved); selectedID = saved.id }
            }
            .sheet(item: $editing) { person in
                PersonEditor(person: person) { saved in try store.save(saved); selectedID = saved.id }
            }
            .sheet(isPresented: $showPeople) {
                PeopleView(store: store, selectedID: $selectedID)
            }
            .sheet(isPresented: $showLicenses) { LicenseView() }
            .task(id: request) {
                if let request { await calculations.calculate(request) }
            }
            .task(id: person) {
                if let person { await selectCurrentAnnualYear(for: person) }
            }
            .onChange(of: person, initial: true) { _, _ in
                year = min(2398, max(birthYear, year))
                if let person, referenceDate < person.birthDate { referenceDate = person.birthDate }
            }
        }
        .tint(.teal)
    }

    private var screenPicker: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(Screen.allCases) { item in
                    Button { screen = item } label: {
                        Label(item.rawValue, systemImage: item.symbol)
                            .font(.subheadline.weight(.semibold))
                            .padding(.horizontal, 14).padding(.vertical, 11)
                            .background(screen == item ? Color.teal : Color(uiColor: .secondarySystemGroupedBackground), in: Capsule())
                            .foregroundStyle(screen == item ? Color.white : Color.primary)
                    }
                    .accessibilityAddTraits(screen == item ? .isSelected : [])
                    .accessibilityIdentifier("screen-\(item.kind.rawValue)")
                }
            }.padding(.horizontal).padding(.vertical, 10)
        }
        .accessibilityIdentifier("screen-picker")
    }

    private var personHeader: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 6) {
                Text(screen.rawValue).font(.largeTitle.bold()).accessibilityAddTraits(.isHeader)
                if let person {
                    Menu {
                        ForEach(store.people) { saved in
                            Button(saved.name) { selectedID = saved.id }
                        }
                        Divider()
                        Button("Uredi osobu", systemImage: "pencil") { editing = person }
                    } label: {
                        Label(person.name, systemImage: "person.crop.circle").font(.headline)
                    }
                    Text("\(BirthMoment.display(person.birthDate, zoneID: person.timeZone)) · \(person.timeZone)")
                        .font(.caption).foregroundStyle(.secondary)
                    if let place = person.birthPlace, !place.isEmpty {
                        Text(place).font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
            Spacer(minLength: 0)
        }
    }

    @ViewBuilder private func controls(for person: Person) -> some View {
        if screen == .annual || screen == .masa {
            DataCard {
                Stepper("Godina povratka: \(year.formatted(.number.grouping(.never)))", value: Binding(
                    get: { year },
                    set: { value in annualSelectionGeneration = UUID(); year = value }
                ), in: min(2398, birthYear)...2398)
                Button("Trenutačna Varshaphala", systemImage: "clock.arrow.circlepath") {
                    Task { await selectCurrentAnnualYear(for: person) }
                }
                if let annualSelectionError { Text(annualSelectionError).font(.caption).foregroundStyle(.red) }
                Text("Godišnja karta počinje u trenutku solarnog povratka, ne 1. siječnja.")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }
        if screen == .dasha || screen == .transit {
            DataCard {
                DatePicker("Trenutak pregleda", selection: $referenceDate, in: BirthMoment.supportedDates, displayedComponents: [.date, .hourAndMinute])
                    .environment(\.timeZone, TimeZone(identifier: person.timeZone) ?? BirthMoment.utc)
                Text(person.timeZone).font(.caption).foregroundStyle(.secondary)
            }
        }
    }

    private func selectCurrentAnnualYear(for selected: Person) async {
        let token = UUID()
        annualSelectionGeneration = token
        annualSelectionError = nil
        let now = Date.now
        let work = Task.detached(priority: .userInitiated) {
            guard let zone = TimeZone(identifier: selected.timeZone) else { throw InputError.message("Nepoznata vremenska zona.") }
            if now < selected.birthDate {
                var calendar = BirthMoment.calendar
                calendar.timeZone = zone
                return calendar.component(.year, from: selected.birthDate)
            }
            return try Annual.activeYear(birthDate: selected.birthDate, latitude: selected.latitude, longitude: selected.longitude, referenceDate: now, birthTimeZone: zone)
        }
        do {
            let activeYear = try await withTaskCancellationHandler(operation: { try await work.value }, onCancel: { work.cancel() })
            guard !Task.isCancelled, annualSelectionGeneration == token, person == selected else { return }
            year = min(2398, max(birthYear, activeYear))
        } catch is CancellationError {
        } catch {
            guard !Task.isCancelled, annualSelectionGeneration == token, person == selected else { return }
            annualSelectionError = error.localizedDescription
        }
    }

    @ViewBuilder private func results(_ output: CalculationOutput, person: Person) -> some View {
        switch screen {
        case .natal:
            NatalView(chart: output.natal, special: output.specialPoints)
                .accessibilityElement(children: .contain)
                .accessibilityIdentifier("natal-results")
        case .dasha:
            DashaView(periods: output.mahaDashas, current: output.currentDashas, referenceDate: referenceDate, zoneID: person.timeZone)
        case .annual:
            if let annual = output.annual { AnnualView(annual: annual, zoneID: person.timeZone) }
        case .masa:
            MasaView(months: output.months, zoneID: person.timeZone)
        case .transit:
            if let transit = output.transit {
                TransitComparisonView(natal: output.natal, transit: transit, date: referenceDate, zoneID: person.timeZone)
            }
        case .ashtakavarga:
            if let result = output.ashtakavarga {
                AshtakavargaView(result: result, ascendantSign: output.natal.ascendantSign)
            }
        }
    }
}

private struct DataCard<Content: View>: View {
    let content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }
    var body: some View {
        VStack(alignment: .leading, spacing: 12) { content }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 20))
    }
}

private struct ErrorCard: View {
    let message: String
    var body: some View {
        DataCard {
            Label("Provjerite podatke", systemImage: "exclamationmark.triangle").font(.headline).foregroundStyle(.orange)
            Text(message).font(.subheadline)
        }
    }
}

private struct NatalView: View {
    let chart: Chart
    let special: NatalSpecialPoints?
    @State private var varga: Varga = .d1
    var body: some View {
        DataCard {
            Picker("Divizijska karta", selection: $varga) {
                ForEach(Varga.allCases) { option in Text(option.label).tag(option) }
            }.pickerStyle(.menu)
            Text(Ephemeris.backendDescription).font(.caption).foregroundStyle(.secondary)
        }
        ChartDataView(chart: chart, varga: varga)
        if let special {
            DataCard {
                Text("Posebne točke · D1").font(.headline)
                LabeledContent("Arudha Lagna · AL", value: Astro.signs[special.arudhaSign])
                LabeledContent("Upapada · UL", value: Astro.signs[special.upapadaSign])
                LabeledContent("Darapada · A7", value: Astro.signs[special.darapadaSign])
                LabeledContent("Bhrigu Bindu", value: AstroMath.position(special.bhriguBinduLongitude))
                GulikaRows(gulika: special.gulika, error: special.gulikaError)
            }
        }
    }
}

private struct ChartDataView: View {
    let chart: Chart
    var varga: Varga = .d1
    private var ascendantSign: Int? { try? varga.signIndex(longitude: chart.ascendantLongitude) }
    var body: some View {
        DataCard {
            Text(varga.label).font(.headline)
            if let ascendantSign {
                NorthIndianChart(chart: chart, varga: varga, ascendantSign: ascendantSign)
                LabeledContent("Lagna", value: Astro.signs[ascendantSign])
                if varga == .d1 {
                    Text("\(AstroMath.position(chart.ascendantLongitude)) · JD \(chart.julianDay, specifier: "%.7f")")
                        .font(.caption).monospacedDigit().foregroundStyle(.secondary)
                }
                Divider()
                ForEach(Astro.planetOrder, id: \.self) { name in
                    if let position = chart.positions[name], let sign = try? varga.signIndex(longitude: position.longitude) {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack(alignment: .firstTextBaseline) {
                                Text(name).fontWeight(.semibold)
                                if position.isRetrograde { Text("R").font(.caption.bold()).accessibilityLabel("Retrogradno") }
                                Spacer()
                                Text(Astro.signs[sign])
                            }
                            if varga == .d1 {
                                Text("\(position.degree, specifier: "%.5f")° · kuća \(Astro.house(sign: sign, ascendantSign: ascendantSign))")
                                    .font(.subheadline).monospacedDigit()
                                if let nak = try? Nakshatra.at(longitude: position.longitude) {
                                    Text("\(nak.name) · pada \(nak.pada) · \(nak.lord)")
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                            } else {
                                Text("Kuća \(Astro.house(sign: sign, ascendantSign: ascendantSign)) · natalna dužina \(position.longitude, specifier: "%.5f")°")
                                    .font(.caption).monospacedDigit().foregroundStyle(.secondary)
                            }
                        }
                        .accessibilityElement(children: .combine)
                        Divider()
                    }
                }
            } else {
                Text("Divizijsku kartu nije moguće izračunati.").foregroundStyle(.red)
            }
        }
    }
}

private struct NorthIndianChart: View {
    let chart: Chart
    let varga: Varga
    let ascendantSign: Int
    private let centers: [CGPoint] = [
        CGPoint(x: 0.50, y: 0.25), CGPoint(x: 0.25, y: 0.085), CGPoint(x: 0.085, y: 0.25),
        CGPoint(x: 0.25, y: 0.50), CGPoint(x: 0.085, y: 0.75), CGPoint(x: 0.25, y: 0.915),
        CGPoint(x: 0.50, y: 0.75), CGPoint(x: 0.75, y: 0.915), CGPoint(x: 0.915, y: 0.75),
        CGPoint(x: 0.75, y: 0.50), CGPoint(x: 0.915, y: 0.25), CGPoint(x: 0.75, y: 0.085)
    ]
    private let shortNames = ["Sunce": "Su", "Mjesec": "Mo", "Mars": "Ma", "Merkur": "Me", "Jupiter": "Ju", "Venera": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"]
    private func names(in house: Int) -> String {
        let names = Astro.planetOrder.compactMap { name -> String? in
            guard let position = chart.positions[name], let sign = try? varga.signIndex(longitude: position.longitude), Astro.house(sign: sign, ascendantSign: ascendantSign) == house else { return nil }
            return (shortNames[name] ?? name) + (position.isRetrograde ? "ᴿ" : "")
        }
        return names.joined(separator: " ")
    }
    var body: some View {
        GeometryReader { geometry in
            let side = min(geometry.size.width, geometry.size.height)
            ZStack {
                Path { path in
                    path.addRect(CGRect(x: 1, y: 1, width: side - 2, height: side - 2))
                    path.move(to: .zero); path.addLine(to: CGPoint(x: side, y: side))
                    path.move(to: CGPoint(x: side, y: 0)); path.addLine(to: CGPoint(x: 0, y: side))
                    path.move(to: CGPoint(x: side / 2, y: 0))
                    for point in [CGPoint(x: side, y: side / 2), CGPoint(x: side / 2, y: side), CGPoint(x: 0, y: side / 2), CGPoint(x: side / 2, y: 0)] { path.addLine(to: point) }
                }.stroke(Color.teal.opacity(0.65), lineWidth: 1)
                ForEach(0..<12, id: \.self) { index in
                    VStack(spacing: 2) {
                        Text("\((ascendantSign + index) % 12 + 1)")
                            .font(.system(size: side * 0.032, weight: .medium)).foregroundStyle(.secondary)
                        Text(names(in: index + 1))
                            .font(.system(size: side * 0.035, weight: .semibold))
                            .multilineTextAlignment(.center).minimumScaleFactor(0.6)
                            .lineLimit(3)
                    }
                    .frame(width: side * 0.19, height: side * 0.16)
                    .position(x: side * centers[index].x, y: side * centers[index].y)
                }
            }
        }
        .aspectRatio(1, contentMode: .fit)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Sjevernoindijska \(varga.label) karta. Lagna \(Astro.signs[ascendantSign]). Položaji su navedeni u tablici ispod.")
    }
}

private struct GulikaRows: View {
    let gulika: GulikaResult?
    let error: String?
    var body: some View {
        if let gulika {
            LabeledContent("Gulika", value: AstroMath.position(gulika.longitude))
            if let mandi = gulika.mandiLongitude { LabeledContent("Mandi", value: AstroMath.position(mandi)) }
            if let ghatikas = gulika.mandiGhatikas { LabeledContent("Mandi · ghatike", value: String(format: "%.2f", ghatikas)) }
        } else if let error {
            Text("Gulika / Mandi: \(error)").font(.caption).foregroundStyle(.secondary)
        }
    }
}

private struct DashaView: View {
    let periods: [DashaPeriod]
    let current: [DashaPeriod]
    let referenceDate: Date
    let zoneID: String
    private let levels = ["Maha", "Antar", "Pratyantar", "Sookshma", "Prana"]
    var body: some View {
        DataCard {
            Text("Vimshottari · 5 razina").font(.headline)
            Text(BirthMoment.display(referenceDate, zoneID: zoneID, seconds: true)).font(.caption).foregroundStyle(.secondary)
            ForEach(Array(current.enumerated()), id: \.offset) { index, period in
                PeriodRow(period: period, title: "\(levels[min(index, levels.count - 1)]) · \(period.lord)", zoneID: zoneID)
            }
        }
        DataCard {
            Text("Mahadaše i podrazdoblja").font(.headline)
            Text("Godina = 365,2425 dana. Prvo puno razdoblje može početi prije rođenja.").font(.caption).foregroundStyle(.secondary)
            ForEach(Array(periods.enumerated()), id: \.offset) { _, period in
                DashaDisclosure(period: period, depth: 0, zoneID: zoneID)
            }
        }
    }
}

private struct DashaDisclosure: View {
    let period: DashaPeriod
    let depth: Int
    let zoneID: String
    @State private var expanded = false
    var body: some View {
        DisclosureGroup(isExpanded: $expanded) {
            if expanded {
                if let children = try? Dasha.subperiods(parent: period) {
                    ForEach(Array(children.enumerated()), id: \.offset) { _, child in
                        if depth < 3 {
                            DashaDisclosure(period: child, depth: depth + 1, zoneID: zoneID)
                        } else {
                            PeriodRow(period: child, zoneID: zoneID)
                        }
                    }
                }
            }
        } label: {
            PeriodRow(period: period, zoneID: zoneID)
        }
    }
}

private struct PeriodRow: View {
    let period: DashaPeriod
    var title: String? = nil
    let zoneID: String
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title ?? period.lord).font(.subheadline.weight(.semibold))
            Text("\(BirthMoment.display(period.start, zoneID: zoneID, seconds: true)) – \(BirthMoment.display(period.end, zoneID: zoneID, seconds: true))")
                .font(.caption).foregroundStyle(.secondary).monospacedDigit()
        }.padding(.vertical, 4).accessibilityElement(children: .combine)
    }
}

private struct AnnualView: View {
    let annual: AnnualResult
    let zoneID: String
    @State private var karyeshaHouse = 7
    var body: some View {
        summaryCard
        ChartDataView(chart: annual.chart)
        specialCard
        lordCard
        aspectsCard
        yogasCard
        sahamsCard
        muddaCard
    }

    private var summaryCard: some View {
        DataCard {
            Text("Solarni povratak \(annual.year.formatted(.number.grouping(.never)))").font(.headline)
            LabeledContent("Početak", value: BirthMoment.display(annual.returnDate, zoneID: zoneID, seconds: true))
            LabeledContent("Sljedeći povratak", value: BirthMoment.display(annual.nextReturnDate, zoneID: zoneID, seconds: true))
            LabeledContent("Navršene godine", value: "\(annual.completedYears)")
            LabeledContent("Godina života", value: "\(annual.lifeYear)")
            LabeledContent("Muntha", value: annual.munthaSign)
            LabeledContent("Dnevni povratak", value: annual.isDay ? "Da" : "Ne")
            Text(zoneID).font(.caption).foregroundStyle(.secondary)
        }
    }

    private var specialCard: some View {
        DataCard {
            Text("Godišnje posebne točke").font(.headline)
            LabeledContent("Arudha Lagna", value: Astro.signs[annual.arudhaSign])
            LabeledContent("Bhrigu Bindu", value: AstroMath.position(annual.bhriguBinduLongitude))
            GulikaRows(gulika: annual.gulika, error: annual.gulikaError)
        }
    }

    private var lordCard: some View {
        DataCard {
            Text("Varshesha · godišnji vladar").font(.headline)
            LabeledContent("Odabir", value: annual.varsheshwara.winner?.planet ?? "Nema kvalificiranog kandidata")
            ForEach(Array(annual.varsheshwara.candidates.enumerated()), id: \.offset) { _, candidate in
                VStack(alignment: .leading, spacing: 4) {
                    Text("\(candidate.role) · \(candidate.planet)").font(.subheadline.weight(.semibold))
                    Text("Bala \(candidate.strengthScore, specifier: "%.3f") · aspekt lagne: \(candidate.aspectsAscendant ? "da" : "ne")")
                        .font(.caption).monospacedDigit()
                    Text("Kshetra \(candidate.bala.kshetra, specifier: "%.2f") · Uchcha \(candidate.bala.uchcha, specifier: "%.2f") · Hadda \(candidate.bala.hadda, specifier: "%.2f") · Drekkana \(candidate.bala.drekkana, specifier: "%.2f") · Navamsa \(candidate.bala.navamsa, specifier: "%.2f")")
                        .font(.caption2).foregroundStyle(.secondary)
                }
                Divider()
            }
            Text("Hadda: postojeća egipatska tablica termina; povijesna Tajika konvencija nije dodatno potvrđena.")
                .font(.caption).foregroundStyle(.secondary)
        }
    }

    private var aspectsCard: some View {
        DataCard {
            Text("Tajika aspekti").font(.headline)
            relationRows(annual.ithasala, heading: "Ithasala · primjena")
            relationRows(annual.isarapha, heading: "Isarapha · separacija")
        }
    }

    private var yogasCard: some View {
        DataCard {
            Text("Tajika yoge").font(.headline)
            Picker("Kuća Karyeshe", selection: $karyeshaHouse) {
                ForEach(1...12, id: \.self) { Text("Kuća \($0)").tag($0) }
            }
            let asc = annual.chart.ascendantSign
            let lagnesha = Astro.signLords[asc]
            let karyesha = Astro.signLords[(asc + karyeshaHouse - 1) % 12]
            LabeledContent("Lagnesha / Karyesha", value: "\(lagnesha) / \(karyesha)")
            if let yogas = try? Tajika.karyeshaYogas(lagnesha: lagnesha, karyesha: karyesha, positions: annual.chart.positions, ascendantSign: asc) {
                ForEach(Array(yogas.enumerated()), id: \.offset) { _, yoga in
                    LabeledContent(yoga.name, value: yoga.applicable ? (yoga.found ? "Da" : "Ne") : "Nije primjenjivo")
                }
            }
            if let global = try? Tajika.globalYogas(positions: annual.chart.positions, ascendantSign: asc) {
                ForEach(Array(global.enumerated()), id: \.offset) { _, yoga in
                    LabeledContent(yoga.name, value: yoga.applicable ? (yoga.found ? "Da" : "Ne") : "Nije primjenjivo")
                }
            }
        }
    }

    private var sahamsCard: some View {
        DataCard {
            Text("Sahami · 20 točaka").font(.headline)
            ForEach(Sahams.order, id: \.self) { name in
                if let value = annual.sahams[name] { LabeledContent(name, value: AstroMath.position(value)) }
            }
            Text("Vivaha i Putra: bez noćnog obrata. Zadržana korekcija luka +30°.").font(.caption).foregroundStyle(.secondary)
        }
    }

    private var muddaCard: some View {
        DataCard {
            Text("Mudda daše").font(.headline)
            Text("360 tradicionalnih dijelova razmjerno do sljedećeg solarnog povratka.").font(.caption).foregroundStyle(.secondary)
            ForEach(Array(annual.muddaDasha.enumerated()), id: \.offset) { _, period in
                PeriodRow(period: period, zoneID: zoneID)
            }
        }
    }
    @ViewBuilder private func relationRows(_ relations: [TajikaRelation], heading: String) -> some View {
        Text(heading).font(.subheadline.weight(.semibold))
        if relations.isEmpty { Text("Nema parova.").font(.caption).foregroundStyle(.secondary) }
        ForEach(Array(relations.enumerated()), id: \.offset) { _, relation in
            VStack(alignment: .leading, spacing: 3) {
                Text("\(relation.planetA) — \(relation.planetB) · \(relation.aspect ?? "–")").font(.subheadline)
                Text("Odstupanje \(relation.orbDifference, specifier: "%.4f")° · orbis \(relation.combinedOrb, specifier: "%.2f")°")
                    .font(.caption).monospacedDigit().foregroundStyle(.secondary)
            }
        }
    }
}

private struct MasaView: View {
    let months: [MasaResult]
    let zoneID: String
    @State private var selectedMonth = 1
    private var month: MasaResult? { months.first { $0.monthNumber == selectedMonth } }
    var body: some View {
        DataCard {
            Text("12 solarnih mjesečnih ulazaka").font(.headline)
            Picker("Masa", selection: $selectedMonth) {
                ForEach(months) { Text("Masa \($0.monthNumber) · \(BirthMoment.display($0.returnDate, zoneID: zoneID))").tag($0.monthNumber) }
            }.pickerStyle(.menu)
            Text("Prvi ulazak je Varsha Praveša; svaki sljedeći prati natalno Sunce +30°.").font(.caption).foregroundStyle(.secondary)
        }
        if let month {
            DataCard {
                LabeledContent("Masa \(month.monthNumber)", value: BirthMoment.display(month.returnDate, zoneID: zoneID, seconds: true))
                Text(zoneID).font(.caption).foregroundStyle(.secondary)
            }
            ChartDataView(chart: month.chart)
            DataCard {
                LabeledContent("Arudha Lagna", value: Astro.signs[month.arudhaSign])
                LabeledContent("Bhrigu Bindu", value: AstroMath.position(month.bhriguBinduLongitude))
                GulikaRows(gulika: month.gulika, error: month.gulikaError)
            }
        }
    }
}

private struct PersonEditor: View {
    @Environment(\.dismiss) private var dismiss
    let person: Person?
    let onSave: (Person) throws -> Void
    @State private var name: String
    @State private var wallClock: Date
    @State private var latitude: String
    @State private var longitude: String
    @State private var zone: String
    @State private var birthPlace: String
    @State private var showCityPicker = false
    @State private var repeatedChoice: Int?
    @State private var error: String?

    init(person: Person? = nil, onSave: @escaping (Person) throws -> Void) {
        self.person = person
        self.onSave = onSave
        _name = State(initialValue: person?.name ?? "")
        _wallClock = State(initialValue: person.map { BirthMoment.wallClock(from: $0.birthDate, zoneID: $0.timeZone) } ?? BirthMoment.defaultWallClock)
        _latitude = State(initialValue: person.map { String($0.latitude) } ?? "45.44")
        _longitude = State(initialValue: person.map { String($0.longitude) } ?? "16.28")
        _zone = State(initialValue: person?.timeZone ?? "Europe/Zagreb")
        _birthPlace = State(initialValue: person?.birthPlace ?? "")
    }

    private var candidates: [Date] { (try? BirthMoment.candidates(wallClock: wallClock, zoneID: zone)) ?? [] }
    private var coordinatesValid: Bool {
        guard let lat = AstroMath.number(latitude), let lon = AstroMath.number(longitude) else { return false }
        return lat > -90 && lat < 90 && (-180...180).contains(lon)
    }
    var body: some View {
        NavigationStack {
            Form {
                SwiftUI.Section("Osoba") {
                    TextField("Ime", text: $name).textContentType(.name).accessibilityIdentifier("person-name")
                }
                SwiftUI.Section("Mjesto rođenja") {
                    Button {
                        showCityPicker = true
                    } label: {
                        Label("Pronađi grad", systemImage: "magnifyingglass")
                    }.accessibilityIdentifier("birthplace-picker")
                    TextField("Naziv mjesta (opcionalno)", text: $birthPlace)
                        .accessibilityIdentifier("person-birthplace")
                    Text("Odabir grada automatski popunjava koordinate i vremensku zonu. Pretraga radi bez interneta.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                SwiftUI.Section {
                    DatePicker("Datum i lokalno vrijeme rođenja", selection: $wallClock, in: BirthMoment.supportedDates, displayedComponents: [.date, .hourAndMinute])
                        .environment(\.timeZone, BirthMoment.utc)
                        .environment(\.calendar, BirthMoment.calendar)
                    Stepper("Sekunde: \(BirthMoment.calendar.component(.second, from: wallClock))", value: Binding(
                        get: { BirthMoment.calendar.component(.second, from: wallClock) },
                        set: { value in
                            let previous = BirthMoment.calendar.component(.second, from: wallClock)
                            wallClock = wallClock.addingTimeInterval(Double(value - previous))
                        }
                    ), in: 0...59)
                    TextField("IANA vremenska zona", text: $zone)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                        .accessibilityIdentifier("person-timezone")
                    Menu("Česte vremenske zone") {
                        ForEach(["Europe/Zagreb", "Europe/London", "America/New_York", "Asia/Kolkata", "Australia/Sydney", "UTC"], id: \.self) { value in
                            Button(value) { zone = value }
                        }
                    }
                    if candidates.count > 1 {
                        Picker("Ponavljanje sata", selection: $repeatedChoice) {
                            Text("Odaberite pojavljivanje").tag(Optional<Int>.none)
                            ForEach(Array(candidates.enumerated()), id: \.offset) { index, date in
                                Text("\(index + 1). · \(BirthMoment.display(date)) UTC").tag(Optional(index))
                            }
                        }
                        Text("Ovo lokalno vrijeme pojavljuje se dvaput pri promjeni sata. Odaberite točan UTC trenutak.").font(.caption)
                    } else if let date = candidates.first {
                        LabeledContent("UTC trenutak", value: BirthMoment.display(date, seconds: true))
                    } else {
                        Text(TimeZone(identifier: zone) == nil ? "Nepoznata vremenska zona." : "Ovo lokalno vrijeme ne postoji zbog promjene sata. Odaberite drugo vrijeme.")
                            .font(.caption).foregroundStyle(.red)
                    }
                } header: { Text("Rođenje") } footer: {
                    Text("Unesite vrijeme zapisano na mjestu rođenja. Odabrana zona automatski primjenjuje povijesni pomak i ljetno računanje vremena.")
                }
                SwiftUI.Section {
                    TextField("Geografska širina", text: $latitude).keyboardType(.numbersAndPunctuation).accessibilityIdentifier("person-latitude")
                    TextField("Geografska dužina", text: $longitude).keyboardType(.numbersAndPunctuation).accessibilityIdentifier("person-longitude")
                } header: { Text("Koordinate mjesta rođenja") } footer: {
                    Text("Sjever i istok su pozitivni; jug i zapad negativni. Ručni unos radi bez interneta.")
                }
                if let error { SwiftUI.Section { Text(error).foregroundStyle(.red) } }
            }
            .navigationTitle(person == nil ? "Nova osoba" : "Uredi osobu")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Odustani") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Spremi", action: save)
                        .disabled(name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !coordinatesValid || candidates.isEmpty || (candidates.count > 1 && repeatedChoice == nil))
                        .accessibilityIdentifier("save-person")
                }
            }
            .onChange(of: wallClock) { _, _ in repeatedChoice = nil; error = nil }
            .onChange(of: zone) { _, _ in repeatedChoice = nil; error = nil }
            .sheet(isPresented: $showCityPicker) {
                CityPickerView { city in
                    birthPlace = city.displayLabel
                    latitude = String(city.latitude)
                    longitude = String(city.longitude)
                    zone = city.timeZone
                    repeatedChoice = nil
                    error = nil
                }
            }
        }
    }
    private func save() {
        do {
            guard let lat = AstroMath.number(latitude), let lon = AstroMath.number(longitude) else {
                throw InputError.message("Unesite brojčane koordinate.")
            }
            let possibilities = try BirthMoment.candidates(wallClock: wallClock, zoneID: zone)
            let index = possibilities.count > 1 ? (repeatedChoice ?? -1) : 0
            guard possibilities.indices.contains(index) else { throw InputError.message("Provjerite lokalno vrijeme rođenja.") }
            let place = birthPlace.trimmingCharacters(in: .whitespacesAndNewlines)
            let value = Person(id: person?.id ?? UUID(), name: name.trimmingCharacters(in: .whitespacesAndNewlines), birthDate: possibilities[index], latitude: lat, longitude: lon, timeZone: zone, birthPlace: place.isEmpty ? nil : place)
            try value.validate()
            try onSave(value)
            dismiss()
        } catch { self.error = error.localizedDescription }
    }
}

@MainActor
private struct PeopleView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var store: PersonStore
    @Binding var selectedID: UUID?
    @State private var editing: Person?
    @State private var deleting: Person?
    @State private var error: String?
    var body: some View {
        NavigationStack {
            List {
                if store.people.isEmpty { Text("Još nema spremljenih osoba.").foregroundStyle(.secondary) }
                ForEach(store.people) { person in
                    Button {
                        selectedID = person.id
                        dismiss()
                    } label: {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(person.name).foregroundStyle(.primary)
                            Text("\(BirthMoment.display(person.birthDate, zoneID: person.timeZone)) · \(person.timeZone)")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .swipeActions(edge: .trailing) {
                        Button("Obriši", role: .destructive) { deleting = person }
                        Button("Uredi") { editing = person }.tint(.teal)
                    }
                }
                if let error { Text(error).foregroundStyle(.red) }
            }
            .navigationTitle("Osobe")
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Gotovo") { dismiss() } } }
            .sheet(item: $editing) { person in PersonEditor(person: person) { try store.save($0) } }
            .confirmationDialog("Obrisati osobu?", isPresented: Binding(get: { deleting != nil }, set: { if !$0 { deleting = nil } }), titleVisibility: .visible) {
                Button("Obriši osobu", role: .destructive) {
                    guard let person = deleting else { return }
                    do { try store.delete(person.id) } catch { self.error = error.localizedDescription }
                    deleting = nil
                }
                Button("Odustani", role: .cancel) { deleting = nil }
            }
        }
    }
}

private struct LicenseView: View {
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    Label("Jyotish", systemImage: "sparkles").font(.largeTitle.bold())
                    Text("Swiss Ephemeris \(Ephemeris.version)").font(.headline)
                    Text(CityCatalog.licenseNotice).textSelection(.enabled)
                    Text(Ephemeris.licenseNotice).textSelection(.enabled)
                }.frame(maxWidth: .infinity, alignment: .leading).padding()
            }
            .navigationTitle("O aplikaciji")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Gotovo") { dismiss() } } }
        }
    }
}
