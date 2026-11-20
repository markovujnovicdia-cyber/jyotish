import Foundation

/// An explicit six-candidate monthly election: five annual-style roles applied
/// to the monthly chart, plus the separately determined lord of the year.
/// Public implementation reference for the candidate family:
/// https://github.com/naturalstupid/PyJHora/blob/f8c6de2f54338752bdb667384a8b0ca5791c5bdf/src/jhora/horoscope/transit/tajaka.py#L539
/// This helper does not import that implementation's approximate return dates,
/// candidate-index selection, or implicit Muntha derivation. Callers provide
/// the precise chart and the chosen Muntha sign explicitly. Six supplied PL9
/// months match this policy; those examples do not establish all PL9 defaults.
public enum MasaLord {
    public static func calculate(natalAscendantSign: Int, annualLord: String?,
                                  munthaSign: Int, chart: Chart,
                                  isDaytime: Bool) throws -> VarsheshwaraResult {
        guard (0..<12).contains(natalAscendantSign), (0..<12).contains(munthaSign) else {
            throw TajikaError.invalidSign
        }
        guard chart.ascendantLongitude.isFinite, (0..<360).contains(chart.ascendantLongitude) else {
            throw TajikaError.invalidCoordinate
        }
        let luminaryName = isDaytime ? "Sunce" : "Mjesec"
        guard let luminary = chart.positions[luminaryName] else {
            throw TajikaError.missingPlanet(luminaryName)
        }
        guard luminary.longitude.isFinite, (0..<360).contains(luminary.longitude) else {
            throw TajikaError.invalidCoordinate
        }
        var definitions = [
            ("Janma Lagna Pati", Astro.signLords[natalAscendantSign]),
            ("Muntha Pati", Astro.signLords[munthaSign]),
            ("Masa Lagna Pati", Astro.signLords[chart.ascendantSign]),
            ("Dina-Ratri Pati", Astro.signLords[luminary.signIndex]),
            ("Tri-Rashi Pati", (isDaytime ? Varsheshwara.triplicityDay : Varsheshwara.triplicityNight)[chart.ascendantSign])
        ]
        if let annualLord {
            guard Tajika.planets.contains(annualLord) else { throw TajikaError.invalidPlanet(annualLord) }
            definitions.append(("Varshesha", annualLord))
        }
        return try Varsheshwara.evaluate(definitions: definitions, chart: chart, convention: .signAspect)
    }
}
