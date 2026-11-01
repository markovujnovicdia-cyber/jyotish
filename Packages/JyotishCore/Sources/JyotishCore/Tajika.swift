import Foundation

public enum TajikaError: Error, LocalizedError {
    case invalidPlanet(String), missingPlanet(String), invalidCoordinate, invalidSign
    public var errorDescription: String? {
        switch self {
        case .invalidPlanet(let name): return "Planet nije dio sedam klasičnih Tajika planeta: \(name)."
        case .missingPlanet(let name): return "Nedostaje položaj planeta \(name)."
        case .invalidCoordinate: return "Tajika zahtijeva konačne koordinate i brzine."
        case .invalidSign: return "Indeks znaka mora biti između 0 i 11."
        }
    }
}

/// The Python pair-yoga module predates its ephemeris-speed aspect API.
/// Its mean-speed convention remains explicit and is the default for pair yogas.
public enum TajikaSpeedConvention: String, Codable, Sendable {
    case ephemeris, legacyMean
}

public struct TajikaRelation: Codable, Equatable, Sendable, Identifiable {
    public let planetA: String
    public let planetB: String
    public let faster: String
    public let slower: String
    public let aspect: String?
    public let orbDifference: Double
    public let combinedOrb: Double
    public let withinOrb: Bool
    public let isApplying: Bool
    public let isExact: Bool
    public let isSeparating: Bool
    public let relativeSpeed: Double
    public var id: String { planetA + "/" + planetB }
}

/// A detected geometric condition. No predictive or interpretive text is stored.
public struct TajikaYoga: Codable, Equatable, Sendable, Identifiable {
    public let name: String
    public let found: Bool
    public let participants: [String]
    public let applicable: Bool
    public var id: String { name }
    public init(name: String, found: Bool, participants: [String] = [], applicable: Bool = true) {
        self.name = name
        self.found = found
        self.participants = participants
        self.applicable = applicable
    }
}

/// Ports core/tajika.py and the numerical predicates in core/karyesha_yogas.py.
public enum Tajika {
    public static let planets = ["Mjesec", "Merkur", "Venera", "Sunce", "Mars", "Jupiter", "Saturn"]
    public static let deeptamsha: [String: Double] = [
        "Sunce": 15, "Mjesec": 12, "Mars": 8, "Merkur": 7,
        "Jupiter": 9, "Venera": 7, "Saturn": 9
    ]
    private static let meanSpeeds: [String: Double] = [
        "Mjesec": 13.176, "Merkur": 1.20, "Venera": 1.18, "Sunce": 0.986,
        "Mars": 0.524, "Jupiter": 0.083, "Saturn": 0.034
    ]
    private static let aspectBySignDistance = [
        0: "konjunkcija", 2: "sekstil", 10: "sekstil", 3: "kvadrat", 9: "kvadrat",
        4: "trigon", 8: "trigon", 6: "opozicija"
    ]
    private static let exactAngles: [String: Double] = [
        "konjunkcija": 0, "sekstil": 60, "kvadrat": 90, "trigon": 120, "opozicija": 180
    ]

    public static func aspect(signA: Int, signB: Int) -> String? {
        guard (0..<12).contains(signA), (0..<12).contains(signB) else { return nil }
        return aspectBySignDistance[((signB - signA) % 12 + 12) % 12]
    }

    public static func residual(longitudeA: Double, longitudeB: Double, aspect: String) -> Double {
        guard let angle = exactAngles[aspect] else { return 999 }
        let targets: [Double] = angle == 0 ? [0] : (angle == 180 ? [180] : [angle, -angle])
        let direction = Astro.signedDifference(longitudeB - longitudeA)
        // Python min(..., key=abs) retains the first target on a tie.
        var result = Astro.signedDifference(direction - targets[0])
        for target in targets.dropFirst() {
            let candidate = Astro.signedDifference(direction - target)
            if abs(candidate) < abs(result) { result = candidate }
        }
        return result
    }

    public static func analyze(_ a: PlanetPosition, _ b: PlanetPosition,
                               speedConvention: TajikaSpeedConvention = .ephemeris) throws -> TajikaRelation {
        guard a.name != b.name else { throw TajikaError.invalidPlanet(a.name) }
        guard let rankA = planets.firstIndex(of: a.name),
              let rankB = planets.firstIndex(of: b.name),
              let orbA = deeptamsha[a.name], let orbB = deeptamsha[b.name] else {
            throw TajikaError.invalidPlanet(!planets.contains(a.name) ? a.name : b.name)
        }
        guard a.longitude.isFinite, b.longitude.isFinite, a.speed.isFinite, b.speed.isFinite,
              (0..<360).contains(a.longitude), (0..<360).contains(b.longitude) else {
            throw TajikaError.invalidCoordinate
        }
        let faster = rankA < rankB ? a.name : b.name
        let slower = rankA < rankB ? b.name : a.name
        let combinedOrb = (orbA + orbB) / 2
        guard let aspectName = aspect(signA: a.signIndex, signB: b.signIndex) else {
            return TajikaRelation(planetA: a.name, planetB: b.name, faster: faster, slower: slower,
                                  aspect: nil, orbDifference: 999, combinedOrb: combinedOrb,
                                  withinOrb: false, isApplying: false, isExact: false,
                                  isSeparating: false, relativeSpeed: 0)
        }
        let residual = residual(longitudeA: a.longitude, longitudeB: b.longitude, aspect: aspectName)
        let orb = abs(residual)
        let exact = orb < 1e-8
        let speedA = speedConvention == .ephemeris ? a.speed : meanSpeeds[a.name]! * (a.isRetrograde ? -1 : 1)
        let speedB = speedConvention == .ephemeris ? b.speed : meanSpeeds[b.name]! * (b.isRetrograde ? -1 : 1)
        let relativeSpeed = speedB - speedA
        return TajikaRelation(planetA: a.name, planetB: b.name, faster: faster, slower: slower,
                              aspect: aspectName, orbDifference: orb, combinedOrb: combinedOrb,
                              withinOrb: orb <= combinedOrb + 1e-10,
                              isApplying: residual * relativeSpeed < -1e-10 && !exact,
                              isExact: exact,
                              isSeparating: residual * relativeSpeed > 1e-10 && !exact,
                              relativeSpeed: relativeSpeed)
    }

    public static func relations(positions: [String: PlanetPosition],
                                 speedConvention: TajikaSpeedConvention = .ephemeris) throws -> [TajikaRelation] {
        let names = planets.filter { positions[$0] != nil }
        var result: [TajikaRelation] = []
        for (index, name) in names.enumerated() {
            for other in names.dropFirst(index + 1) {
                result.append(try analyze(positions[name]!, positions[other]!, speedConvention: speedConvention))
            }
        }
        return result
    }

    public static func ithasala(positions: [String: PlanetPosition]) throws -> [TajikaRelation] {
        try relations(positions: positions).filter { $0.aspect != nil && $0.withinOrb && $0.isApplying }
    }

    public static func isarapha(positions: [String: PlanetPosition]) throws -> [TajikaRelation] {
        try relations(positions: positions).filter { $0.aspect != nil && $0.withinOrb && $0.isSeparating }
    }

    public static func karyeshaYogas(lagnesha: String, karyesha: String,
                                     positions: [String: PlanetPosition], ascendantSign: Int,
                                     speedConvention: TajikaSpeedConvention = .legacyMean) throws -> [TajikaYoga] {
        guard (0..<12).contains(ascendantSign) else { throw TajikaError.invalidSign }
        try requireAll(positions)
        guard planets.contains(lagnesha), planets.contains(karyesha) else {
            throw TajikaError.invalidPlanet(!planets.contains(lagnesha) ? lagnesha : karyesha)
        }
        let pairNames = ["Ithasala", "Isarapha", "Nakta", "Yamaya", "Manau", "Kambula", "Radda", "Duparikutha", "Durupha"]
        if lagnesha == karyesha {
            // The original Python returns these nine (rather than eleven) for a same-planet pair.
            return pairNames.map { TajikaYoga(name: $0, found: false, participants: [lagnesha], applicable: false) }
        }
        let l = positions[lagnesha]!, k = positions[karyesha]!
        let direct = try analyze(l, k, speedConvention: speedConvention)
        let hasIthasala = direct.aspect != nil && direct.withinOrb && direct.isApplying
        // Preserve Python's pair-yoga predicate, including its exact/stationary edge convention.
        let hasIsarapha = direct.aspect != nil && direct.withinOrb && !direct.isApplying
        var result = [TajikaYoga(name: "Ithasala", found: hasIthasala, participants: [lagnesha, karyesha]),
                      TajikaYoga(name: "Isarapha", found: hasIsarapha, participants: [lagnesha, karyesha])]
        var nakta: String?, yamaya: String?
        if !hasIthasala && !hasIsarapha {
            let rankL = planets.firstIndex(of: lagnesha)!, rankK = planets.firstIndex(of: karyesha)!
            for (rankP, name) in planets.enumerated() where name != lagnesha && name != karyesha {
                let p = positions[name]!
                let relL = try analyze(p, l, speedConvention: speedConvention)
                let relK = try analyze(p, k, speedConvention: speedConvention)
                if relL.aspect != nil && relL.withinOrb && relK.aspect != nil && relK.withinOrb {
                    if rankP < rankL && rankP < rankK && nakta == nil { nakta = name }
                    else if rankP > rankL && rankP > rankK && yamaya == nil { yamaya = name }
                }
            }
        }
        result.append(TajikaYoga(name: "Nakta", found: nakta != nil, participants: [lagnesha, karyesha] + (nakta.map { [$0] } ?? [])))
        result.append(TajikaYoga(name: "Yamaya", found: yamaya != nil, participants: [lagnesha, karyesha] + (yamaya.map { [$0] } ?? [])))
        var blockers: [String] = []
        if hasIthasala {
            for name in ["Mars", "Saturn"] where name != lagnesha && name != karyesha {
                if abs(Astro.signedDifference(positions[name]!.longitude - positions[direct.faster]!.longitude)) <= deeptamsha[name]! {
                    blockers.append(name)
                }
            }
        }
        result.append(TajikaYoga(name: "Manau", found: !blockers.isEmpty, participants: [lagnesha, karyesha] + blockers))
        var kambula = false
        if hasIthasala && lagnesha != "Mjesec" && karyesha != "Mjesec" {
            for p in [l, k] {
                let r = try analyze(positions["Mjesec"]!, p, speedConvention: speedConvention)
                if r.aspect != nil && r.withinOrb && r.isApplying { kambula = true }
            }
        }
        result.append(TajikaYoga(name: "Kambula", found: kambula, participants: [lagnesha, karyesha, "Mjesec"]))
        let sun = positions["Sunce"]!
        let combustL = isCombust(l, sunLongitude: sun.longitude)
        let combustK = isCombust(k, sunLongitude: sun.longitude)
        let radda = hasIthasala && (l.isRetrograde || k.isRetrograde || combustL || combustK)
        result.append(TajikaYoga(name: "Radda", found: radda, participants: [lagnesha, karyesha]))
        let dignityL = PlanetDignity.classify(planet: lagnesha, signIndex: l.signIndex)
        let dignityK = PlanetDignity.classify(planet: karyesha, signIndex: k.signIndex)
        let strong: Set<String> = ["uzvišen", "vlastiti"]
        let weak: Set<String> = ["pad", "neprijateljski"]
        let slowerDignity = direct.slower == lagnesha ? dignityL : dignityK
        let fasterDignity = direct.faster == lagnesha ? dignityL : dignityK
        let duparikutha = hasIthasala && strong.contains(slowerDignity) && !strong.contains(fasterDignity)
        result.append(TajikaYoga(name: "Duparikutha", found: duparikutha, participants: [direct.slower, direct.faster]))
        let houseL = Astro.house(sign: l.signIndex, ascendantSign: ascendantSign)
        let houseK = Astro.house(sign: k.signIndex, ascendantSign: ascendantSign)
        let dusthana: Set<Int> = [6, 8, 12]
        let durupha = hasIthasala && dusthana.contains(houseL) && dusthana.contains(houseK)
            && (weak.contains(dignityL) || l.isRetrograde) && (weak.contains(dignityK) || k.isRetrograde)
        result.append(TajikaYoga(name: "Durupha", found: durupha, participants: [lagnesha, karyesha]))
        let bothWeak = (weak.contains(dignityL) || l.isRetrograde || combustL)
            && (weak.contains(dignityK) || k.isRetrograde || combustK)
        var helper: String?
        if bothWeak {
            for name in planets where name != lagnesha && name != karyesha {
                let p = positions[name]!
                for weakPlanet in [l, k] {
                    let relation = try analyze(p, weakPlanet, speedConvention: speedConvention)
                    if relation.aspect != nil && relation.withinOrb && relation.isApplying
                        && strong.contains(PlanetDignity.classify(planet: name, signIndex: p.signIndex)) {
                        helper = name
                        break
                    }
                }
                if helper != nil { break }
            }
        }
        result.append(TajikaYoga(name: "Duttota", found: helper != nil, participants: [lagnesha, karyesha] + (helper.map { [$0] } ?? [])))
        let faster = positions[direct.faster]!
        let tambira = hasIthasala && strong.contains(fasterDignity) && faster.degree >= 27
        result.append(TajikaYoga(name: "Tambira", found: tambira, participants: [direct.faster]))
        return result
    }

    public static func globalYogas(positions: [String: PlanetPosition], ascendantSign: Int,
                                   speedConvention: TajikaSpeedConvention = .legacyMean) throws -> [TajikaYoga] {
        guard (0..<12).contains(ascendantSign) else { throw TajikaError.invalidSign }
        try requireAll(positions)
        let apoklima: Set<Int> = [3, 6, 9, 12]
        let houses = planets.map { Astro.house(sign: positions[$0]!.signIndex, ascendantSign: ascendantSign) }
        var khallasara = true
        for name in planets where name != "Mjesec" {
            let r = try analyze(positions["Mjesec"]!, positions[name]!, speedConvention: speedConvention)
            if r.aspect != nil && r.withinOrb && r.isApplying { khallasara = false; break }
        }
        return [TajikaYoga(name: "Ishkavala", found: houses.allSatisfy { !apoklima.contains($0) }, participants: planets),
                TajikaYoga(name: "Induvara", found: houses.allSatisfy { apoklima.contains($0) }, participants: planets),
                TajikaYoga(name: "Khallasara", found: khallasara, participants: ["Mjesec"])]
    }

    public static func isCombust(_ planet: PlanetPosition, sunLongitude: Double) -> Bool {
        let orbs: [String: Double] = ["Mjesec": 12, "Mars": 17, "Merkur": 14, "Jupiter": 11, "Venera": 10, "Saturn": 15]
        guard var orb = orbs[planet.name] else { return false }
        if planet.isRetrograde && planet.name == "Merkur" { orb = 12 }
        if planet.isRetrograde && planet.name == "Venera" { orb = 8 }
        return abs(Astro.signedDifference(planet.longitude - sunLongitude)) <= orb
    }

    private static func requireAll(_ positions: [String: PlanetPosition]) throws {
        for name in planets {
            guard let p = positions[name] else { throw TajikaError.missingPlanet(name) }
            guard p.name == name else { throw TajikaError.invalidPlanet(p.name) }
            guard p.longitude.isFinite, p.speed.isFinite, (0..<360).contains(p.longitude) else { throw TajikaError.invalidCoordinate }
        }
    }
}
