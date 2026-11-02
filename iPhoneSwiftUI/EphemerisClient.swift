import Foundation
import Combine
import JyotishCore

/// On-device data and calculations. No networking is used by the iPhone app.
struct Person: Identifiable, Codable, Hashable, Sendable {
    var id = UUID()
    var name: String
    var birthDate: Date
    var latitude: Double
    var longitude: Double
    var timeZone: String
    var birthPlace: String? = nil

    func validate() throws {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw InputError.message("Unesite ime osobe.")
        }
        guard latitude.isFinite, longitude.isFinite, latitude > -90, latitude < 90,
              (-180...180).contains(longitude) else {
            throw InputError.message("Širina mora biti između −90° i 90°, a dužina od −180° do 180°.")
        }
        guard TimeZone(identifier: timeZone) != nil else {
            throw InputError.message("Odaberite valjanu IANA vremensku zonu, primjerice Europe/Zagreb.")
        }
        guard BirthMoment.supportedDates.contains(birthDate) else {
            throw InputError.message("Podržani datumi rođenja su od 1800. do 2398. godine.")
        }
    }
}

enum InputError: LocalizedError {
    case message(String)
    var errorDescription: String? {
        switch self { case .message(let text): return text }
    }
}

@MainActor
final class PersonStore: ObservableObject {
    @Published private(set) var people: [Person] = []
    @Published var storageError: String?
    private let defaults: UserDefaults
    private let key = "people.v2"

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        guard let data = defaults.data(forKey: key) ?? defaults.data(forKey: "people") else { return }
        do {
            let decoded = try JSONDecoder().decode([Person].self, from: data)
            for person in decoded { try person.validate() }
            people = decoded
        } catch {
            storageError = "Spremljene podatke nije moguće otvoriti. Izvorni zapis je sačuvan: \(error.localizedDescription)"
        }
    }

    func save(_ person: Person) throws {
        try person.validate()
        var updated = people
        if let index = updated.firstIndex(where: { $0.id == person.id }) {
            updated[index] = person
        } else {
            updated.append(person)
        }
        try persist(updated)
    }

    func delete(_ id: UUID) throws {
        try persist(people.filter { $0.id != id })
    }

    private func persist(_ updated: [Person]) throws {
        let data = try JSONEncoder().encode(updated)
        defaults.set(data, forKey: key)
        people = updated
        storageError = nil
    }
}

enum CalculationKind: String, Hashable, Sendable {
    case natal, dasha, annual, masa, transit, ashtakavarga
}

struct CalculationRequest: Hashable, Sendable {
    let person: Person
    let kind: CalculationKind
    let year: Int
    let referenceDate: Date
}

struct CalculationOutput: Sendable {
    let natal: Chart
    let specialPoints: NatalSpecialPoints?
    let annual: AnnualResult?
    let months: [MasaResult]
    let mahaDashas: [DashaPeriod]
    let currentDashas: [DashaPeriod]
    let transit: Chart?
    let ashtakavarga: AshtakavargaResult?
}

enum NativeCalculations {
    static func calculate(_ request: CalculationRequest) throws -> CalculationOutput {
        try Task.checkCancellation()
        let person = request.person
        try person.validate()
        let natal = try Ephemeris.chart(date: person.birthDate, latitude: person.latitude, longitude: person.longitude)
        try Task.checkCancellation()
        var special: NatalSpecialPoints?
        var annual: AnnualResult?
        var months: [MasaResult] = []
        var major: [DashaPeriod] = []
        var current: [DashaPeriod] = []
        var transit: Chart?
        var ashtakavarga: AshtakavargaResult?
        switch request.kind {
        case .natal:
            special = try SpecialPoints.compute(chart: natal, localDate: BirthMoment.localDateString(person.birthDate, zoneID: person.timeZone), latitude: person.latitude, longitude: person.longitude)
        case .dasha:
            guard request.referenceDate >= person.birthDate else {
                throw InputError.message("Za pregled daša odaberite datum nakon rođenja.")
            }
            guard let moon = natal.positions["Mjesec"] else { throw InputError.message("Nedostaje položaj Mjeseca.") }
            let years = max(120, request.referenceDate.timeIntervalSince(person.birthDate) / (86400 * 365.2425) + 1)
            major = try Dasha.mahadashas(moonLongitude: moon.longitude, birthDate: person.birthDate, yearsToCover: years)
            current = try Dasha.currentFiveLevels(moonLongitude: moon.longitude, birthDate: person.birthDate, at: request.referenceDate)
        case .annual, .masa:
            annual = try Annual.calculate(birthDate: person.birthDate, latitude: person.latitude, longitude: person.longitude, year: request.year, birthTimeZone: TimeZone(identifier: person.timeZone)!)
            try Task.checkCancellation()
            if request.kind == .masa, let annual, let sun = natal.positions["Sunce"] {
                months = try Annual.masa(natalSunLongitude: sun.longitude, annualJulianDay: annual.chart.julianDay, latitude: person.latitude, longitude: person.longitude)
            }
        case .transit:
            transit = try Ephemeris.chart(date: request.referenceDate, latitude: person.latitude, longitude: person.longitude)
        case .ashtakavarga:
            ashtakavarga = try Ashtakavarga.calculate(chart: natal)
        }
        try Task.checkCancellation()
        return CalculationOutput(natal: natal, specialPoints: special, annual: annual, months: months, mahaDashas: major, currentDashas: current, transit: transit, ashtakavarga: ashtakavarga)
    }
}

@MainActor
final class CalculationModel: ObservableObject {
    @Published private(set) var output: CalculationOutput?
    @Published private(set) var error: String?
    @Published private(set) var isLoading = false
    private var generation = UUID()

    func calculate(_ request: CalculationRequest) async {
        let token = UUID()
        generation = token
        output = nil
        error = nil
        isLoading = true
        let work = Task.detached(priority: .userInitiated) {
            try NativeCalculations.calculate(request)
        }
        do {
            let result = try await withTaskCancellationHandler(operation: { try await work.value }, onCancel: { work.cancel() })
            guard !Task.isCancelled, generation == token else { return }
            output = result
        } catch is CancellationError {
            // A newer selection owns the visible result.
        } catch {
            guard !Task.isCancelled, generation == token else { return }
            self.error = error.localizedDescription
        }
        if generation == token { isLoading = false }
    }
}
