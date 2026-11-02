import SwiftUI
import JyotishCore

@MainActor
struct CityPickerView: View {
    @Environment(\.dismiss) private var dismiss
    let onSelect: (City) -> Void
    @State private var query = ""
    @State private var cities: [City] = []
    @State private var loading = false
    @State private var error: String?
    @State private var selectionError: String?
    @State private var generation = UUID()

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                HStack(spacing: 10) {
                    Image(systemName: "magnifyingglass").foregroundStyle(.secondary)
                    TextField("Grad, država ili oznaka države", text: $query)
                        .textInputAutocapitalization(.words)
                        .autocorrectionDisabled()
                        .submitLabel(.search)
                        .accessibilityLabel("Pretraži grad")
                        .accessibilityIdentifier("city-search")
                    if !query.isEmpty {
                        Button { query = "" } label: { Image(systemName: "xmark.circle.fill") }
                            .accessibilityLabel("Obriši pretragu")
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(12)
                .background(Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
                .padding()

                if loading {
                    Spacer()
                    ProgressView("Pretraživanje na uređaju…")
                        .accessibilityIdentifier("city-search-progress")
                    Spacer()
                } else if let error {
                    ContentUnavailableView("Baza gradova nije dostupna", systemImage: "exclamationmark.triangle", description: Text(error))
                } else if cities.isEmpty {
                    ContentUnavailableView.search(text: query)
                    Text("Grad nije u bazi? Vratite se i unesite koordinate i vremensku zonu ručno.")
                        .font(.footnote).foregroundStyle(.secondary).padding()
                } else {
                    cityList
                }
                Text("GeoNames · offline baza. Odaberite mjesto rođenja, zatim provjerite podatke u obrascu.")
                    .font(.caption).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading).padding()
            }
            .background(Color(uiColor: .systemGroupedBackground))
            .navigationTitle("Mjesto rođenja")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Odustani") { dismiss() } }
            }
            .task(id: query) { await search(query) }
            .alert("Provjerite vremensku zonu", isPresented: Binding(
                get: { selectionError != nil }, set: { if !$0 { selectionError = nil } }
            )) {
                Button("U redu", role: .cancel) { selectionError = nil }
            } message: { Text(selectionError ?? "") }
        }
        .tint(.teal)
    }

    private var cityList: some View {
        List(cities) { city in
            Button {
                guard TimeZone(identifier: city.timeZone) != nil else {
                    selectionError = "Ovaj uređaj ne prepoznaje vremensku zonu \(city.timeZone). Ažurirajte sustav ili unesite potvrđenu zonu i koordinate ručno."
                    return
                }
                onSelect(city)
                dismiss()
            } label: {
                VStack(alignment: .leading, spacing: 5) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(city.name).font(.headline).foregroundStyle(.primary)
                        Spacer(minLength: 8)
                        Text(city.regionLabel).font(.caption).foregroundStyle(.secondary)
                    }
                    Text(city.countryName).font(.subheadline).foregroundStyle(.primary)
                    Text("\(city.latitude, specifier: "%.4f")°, \(city.longitude, specifier: "%.4f")° · \(city.timeZone)")
                        .font(.caption).monospacedDigit().foregroundStyle(.secondary)
                    if TimeZone(identifier: city.timeZone) == nil {
                        Label("Vremenska zona nije podržana na ovom uređaju", systemImage: "exclamationmark.triangle")
                            .font(.caption).foregroundStyle(.orange)
                    }
                }
                .padding(.vertical, 5)
            }
            .accessibilityElement(children: .combine)
            .accessibilityIdentifier("city-result-\(city.id)")
        }
        .listStyle(.plain)
    }

    private func search(_ query: String) async {
        let token = UUID()
        generation = token
        loading = true
        error = nil
        do {
            try await Task.sleep(nanoseconds: 200_000_000)
            let work = Task.detached(priority: .userInitiated) {
                try CityCatalog.shared.search(query, limit: 40)
            }
            let matches = try await withTaskCancellationHandler(operation: { try await work.value }, onCancel: { work.cancel() })
            guard !Task.isCancelled, generation == token else { return }
            cities = matches
        } catch is CancellationError {
            // A newer query owns the result and loading state.
        } catch {
            guard !Task.isCancelled, generation == token else { return }
            self.error = error.localizedDescription
            cities = []
        }
        if generation == token { loading = false }
    }
}
