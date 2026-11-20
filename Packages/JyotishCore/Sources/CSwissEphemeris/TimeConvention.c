#include "include/SwissBridge.h"
#include "swephexp.h"
#include <math.h>

/* Historical future Delta T forecast, not a fitted offset.
 * Source: Astrodienst Swiss Ephemeris swephlib.c, deltat_aa(), commit
 * cb7971a07d166ff8768e22247f63568718f2cd66 (official repository).
 * https://github.com/aloistr/swisseph/blob/cb7971a07d166ff8768e22247f63568718f2cd66/swephlib.c
 * Source SHA-256:
 * af3bd16fb4213eae201c146f156df0cd6421b0cdecb20a9258cde4132393ac9f
 * Its table ends at fractional year 2019 with 69.50 seconds; the future
 * branch blends to the Stephenson (1997) quadratic over the next century.
 * Earlier observational epochs deliberately retain the current Swiss model.
 * The source's tag labels and embedded version differ, hence the commit pin.
 */
double jy_historical_2019_forecast_seconds(double jd) {
    if (!isfinite(jd)) return NAN;
    double year = 2000.0 + (jd - 2451545.0) / 365.2425;
    if (year <= 2019.0) return NAN;
    double b = 0.01 * (year - 1820.0);
    double seconds = -20.0 + 31.0 * b * b;
    if (year <= 2119.0) {
        double b2 = 0.01 * (2019.0 - 1820.0);
        double at_table_end = -20.0 + 31.0 * b2 * b2;
        seconds += (at_table_end - 69.50) * (year - 2119.0) * 0.01;
    }
    return seconds;
}

int jy_set_time_convention(double jd, int historical_forecast) {
    /* Reset on every call so an alternate forecast cannot leak into the
     * current model or an earlier observational epoch. The Swift caller owns
     * the process-wide ephemeris lock for this and the dependent calculation. */
    swe_set_delta_t_userdef(SE_DELTAT_AUTOMATIC);
    if (!isfinite(jd) || (historical_forecast != 0 && historical_forecast != 1)) return -1;
    if (historical_forecast) {
        double year = 2000.0 + (jd - 2451545.0) / 365.2425;
        if (year > 2019.0) {
            double seconds = jy_historical_2019_forecast_seconds(jd);
            if (!isfinite(seconds)) return -1;
            swe_set_delta_t_userdef(seconds / 86400.0);
        }
    }
    return 0;
}
