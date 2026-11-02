import Foundation

public struct City: Codable, Hashable, Identifiable, Sendable {
    public let id: Int
    public let name: String
    public let countryCode: String
    /// GeoNames first-order administrative subdivision code (e.g. MA or HR's 21).
    public let admin1: String
    public let latitude: Double
    public let longitude: Double
    public let timeZone: String
    public let population: Int
    public let aliases: [String]

    public var countryName: String {
        Locale(identifier: "hr_HR").localizedString(forRegionCode: countryCode) ?? countryCode
    }
    public var displayLabel: String { "\(name), \(countryName)" }
    public var regionLabel: String { admin1.isEmpty ? countryCode : "\(countryCode) · \(admin1)" }

    public init(id: Int, name: String, countryCode: String, admin1: String,
                latitude: Double, longitude: Double, timeZone: String,
                population: Int = 0, aliases: [String] = []) {
        self.id = id; self.name = name; self.countryCode = countryCode; self.admin1 = admin1
        self.latitude = latitude; self.longitude = longitude; self.timeZone = timeZone
        self.population = population; self.aliases = aliases
    }
}

public enum CityCatalogError: Error, LocalizedError {
    case missingResources, invalidData
    public var errorDescription: String? {
        switch self {
        case .missingResources: return "Ugrađena baza gradova nije pronađena. Mjesto možete unijeti ručno."
        case .invalidData: return "Ugrađenu bazu gradova nije moguće otvoriti. Mjesto možete unijeti ručno."
        }
    }
}

/// Immutable offline GeoNames data. Decode/index once on a background task;
/// locking prevents concurrent searches from decoding the catalog repeatedly.
/// A newer IANA zone is retained even when this OS does not recognize it. The
/// picker checks the selected zone and never silently substitutes another one.
public final class CityCatalog: @unchecked Sendable {
    public static let shared = CityCatalog()
    public static var licenseNotice: String {
        guard let url = Bundle.module.url(forResource: "Cities", withExtension: nil)?.appendingPathComponent("NOTICE.txt"),
              let text = try? String(contentsOf: url, encoding: .utf8) else {
            return "Podaci gradova: GeoNames, https://www.geonames.org/ · CC BY 4.0, https://creativecommons.org/licenses/by/4.0/"
        }
        return text
    }

    private struct Entry {
        let city: City
        let primary: String
        let names: [String]
        let searchable: String
    }
    private struct Index {
        let entries: [Entry]
        let suggestions: [City]
    }
    private let lock = NSLock()
    private let resourceURL: URL?
    private var loaded: Result<Index, Error>?
    private static let locale = Locale(identifier: "hr_HR")
    private static let regionalCountries: Set<String> = ["HR", "BA", "RS", "SI", "ME", "MK", "XK"]

    private init() {
        resourceURL = Bundle.module.url(forResource: "Cities", withExtension: nil)?.appendingPathComponent("cities.json")
    }

    /// Internal initializer supports malformed/missing-resource tests without
    /// replacing the live application catalog or touching personal data.
    init(resourceURL: URL?) { self.resourceURL = resourceURL }

    private static func fold(_ value: String) -> String {
        // ASCII has no diacritics and Croatian case folding agrees with ordinary
        // lowercasing. Avoid an ICU transformation for the common alias case.
        if value.utf8.allSatisfy({ $0 < 128 }) { return value.lowercased() }
        return value.folding(options: [.caseInsensitive, .diacriticInsensitive], locale: locale)
    }
    private static func key(_ value: String) -> String {
        keyFromFolded(fold(value))
    }
    private static func keyFromFolded(_ value: String) -> String {
        let letters = value.replacingOccurrences(of: "đ", with: "d").replacingOccurrences(of: "ð", with: "d")
        return letters.components(separatedBy: CharacterSet.alphanumerics.inverted)
            .filter { !$0.isEmpty }.joined(separator: " ")
    }
    private static func nameKeys(_ value: String) -> [String] {
        let folded = fold(value)
        let ordinary = keyFromFolded(folded)
        guard folded.contains("đ") || folded.contains("ð") else { return [ordinary] }
        let digraph = keyFromFolded(folded.replacingOccurrences(of: "đ", with: "dj").replacingOccurrences(of: "ð", with: "dj"))
        return ordinary == digraph ? [ordinary] : [ordinary, digraph]
    }

    private func index() throws -> Index {
        lock.lock(); defer { lock.unlock() }
        if let loaded { return try loaded.get() }
        let result: Result<Index, Error>
        do {
            guard let resourceURL, FileManager.default.fileExists(atPath: resourceURL.path) else {
                throw CityCatalogError.missingResources
            }
            let cities: [City]
            do { cities = try JSONDecoder().decode([City].self, from: Data(contentsOf: resourceURL)) }
            catch { throw CityCatalogError.invalidData }
            guard !cities.isEmpty, Set(cities.map(\.id)).count == cities.count,
                  cities.allSatisfy({ city in
                      city.id > 0 && !city.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
                      city.countryCode.count == 2 && !city.timeZone.isEmpty && city.population >= 0 &&
                      city.latitude.isFinite && city.longitude.isFinite &&
                      city.latitude > -90 && city.latitude < 90 && (-180...180).contains(city.longitude)
                  }) else { throw CityCatalogError.invalidData }
            var countryKeys: [String: String] = [:]
            let english = Locale(identifier: "en_US")
            let entries = cities.sorted {
                $0.population == $1.population ? $0.id < $1.id : $0.population > $1.population
            }.map { city -> Entry in
                let names = Array(Set(([city.name] + city.aliases).flatMap(Self.nameKeys).filter { !$0.isEmpty }))
                let country: String
                if let cached = countryKeys[city.countryCode] { country = cached }
                else {
                    country = Self.key("\(city.countryCode) \(city.countryName) \(english.localizedString(forRegionCode: city.countryCode) ?? "")")
                    countryKeys[city.countryCode] = country
                }
                let searchable = " " + names.joined(separator: " ") + " " + country + " " + Self.key(city.admin1) + " "
                return Entry(city: city, primary: Self.key(city.name), names: names, searchable: searchable)
            }
            // Useful nearby names on an empty query, followed by major world cities.
            let regional = entries.filter { Self.regionalCountries.contains($0.city.countryCode) }.prefix(12).map(\.city)
            let regionalIDs = Set(regional.map(\.id))
            let world = entries.filter { !regionalIDs.contains($0.city.id) }.prefix(18).map(\.city)
            result = .success(Index(entries: entries, suggestions: regional + world))
        } catch { result = .failure(error) }
        loaded = result
        return try result.get()
    }

    /// Matches place names/aliases, country names/codes and subdivision codes.
    /// Exact names precede prefixes, with population then GeoNames ID as stable
    /// tie breakers. Diacritics and Croatian Đ/D/DJ variants are searchable.
    public func search(_ query: String, limit: Int = 30) throws -> [City] {
        guard limit > 0 else { return [] }
        try Task.checkCancellation()
        let catalog = try index()
        try Task.checkCancellation()
        let query = Self.key(query)
        if query.isEmpty { return Array(catalog.suggestions.prefix(limit)) }
        let tokens = query.split(separator: " ").map(String.init)
        var matches: [(Int, City)] = []
        for (offset, entry) in catalog.entries.enumerated() {
            if offset % 1024 == 0 { try Task.checkCancellation() }
            guard tokens.allSatisfy({ term in
                if term.count <= 2 {
                    return entry.searchable.contains(" \(term) ") || entry.names.contains(where: { $0.hasPrefix(term) })
                }
                return entry.searchable.contains(term)
            }) else { continue }
            let rank: Int
            if entry.primary == query { rank = 0 }
            else if entry.names.contains(query) { rank = 1 }
            else if entry.primary.hasPrefix(query) { rank = 2 }
            else if entry.names.contains(where: { $0.hasPrefix(query) }) { rank = 3 }
            else { rank = 4 }
            matches.append((rank, entry.city))
        }
        matches.sort { lhs, rhs in
            if lhs.0 != rhs.0 { return lhs.0 < rhs.0 }
            if lhs.1.population != rhs.1.population { return lhs.1.population > rhs.1.population }
            return lhs.1.id < rhs.1.id
        }
        return matches.prefix(limit).map(\.1)
    }
}
