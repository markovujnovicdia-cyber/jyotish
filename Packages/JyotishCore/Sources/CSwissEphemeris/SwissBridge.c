#include "include/SwissBridge.h"
#include "swephexp.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

int jy_max_path_bytes(void) {
    /* Match swe_set_ephe_path's actual bound, including filename allowance. */
    return AS_MAXCH - 1 - 13;
}
int jy_set_path(const char *path) {
    const char *override = getenv("SE_EPHE_PATH");
    if (path == NULL || *path == '\0' || strlen(path) > (size_t)jy_max_path_bytes()) return -1;
    /* Do not silently let a developer environment override the bundled data. */
    if (override != NULL && *override != '\0' &&
        strlen(override) <= (size_t)jy_max_path_bytes() && strcmp(override, path) != 0) return -2;
    swe_set_ephe_path(path);
    swe_set_sid_mode(SE_SIDM_LAHIRI, 0, 0);
    return 0;
}
const char *jy_version(void) {
    static char version[256];
    return swe_version(version);
}
int jy_calc(double jd, int body, double *values, char *error) {
    return swe_calc_ut(jd, body, SEFLG_SIDEREAL | SEFLG_SWIEPH | SEFLG_SPEED, values, error);
}
int jy_mean_node_true_ayanamsa(double jd, double *values, char *error) {
    double ayanamsha, before, after;
    if (!isfinite(jd)) {
        strcpy(error, "Non-finite Julian day for mean node");
        return -1;
    }
    int result = swe_calc_ut(jd, SE_MEAN_NODE,
                             SEFLG_SWIEPH | SEFLG_SPEED | SEFLG_NONUT, values, error);
    if (result < 0) return result;
    if (!(result & SEFLG_SWIEPH)) {
        strcpy(error, "Swiss ephemeris flag missing from mean node result");
        return -1;
    }
    int status = swe_get_ayanamsa_ex_ut(jd, SEFLG_SWIEPH, &ayanamsha, error);
    if (status < 0) return status;
    if (!(status & SEFLG_SWIEPH)) {
        strcpy(error, "Swiss ephemeris flag missing from true ayanamsha");
        return -1;
    }
    /* Symmetric one-day difference gives a speed in degrees per civil day.
     * The circular difference remains defined if ayanamsha crosses zero. */
    status = swe_get_ayanamsa_ex_ut(jd - 0.5, SEFLG_SWIEPH, &before, error);
    if (status < 0) return status;
    if (!(status & SEFLG_SWIEPH)) {
        strcpy(error, "Swiss ephemeris flag missing from prior ayanamsha");
        return -1;
    }
    status = swe_get_ayanamsa_ex_ut(jd + 0.5, SEFLG_SWIEPH, &after, error);
    if (status < 0) return status;
    if (!(status & SEFLG_SWIEPH)) {
        strcpy(error, "Swiss ephemeris flag missing from subsequent ayanamsha");
        return -1;
    }
    if (!isfinite(ayanamsha) || !isfinite(before) || !isfinite(after)) {
        strcpy(error, "Non-finite true ayanamsha");
        return -1;
    }
    values[0] = swe_degnorm(values[0] - ayanamsha);
    values[3] -= swe_difdeg2n(after, before);
    for (int index = 0; index < 6; index++) {
        if (!isfinite(values[index])) {
            strcpy(error, "Non-finite mean node result");
            return -1;
        }
    }
    return result;
}
int jy_ascendant(double jd, double latitude, double longitude, double *ascendant) {
    double cusps[13], ascmc[10];
    int result = swe_houses_ex(jd, SEFLG_SIDEREAL | SEFLG_SWIEPH | SEFLG_SPEED,
                               latitude, longitude, 'W', cusps, ascmc);
    *ascendant = ascmc[0];
    return result;
}
int jy_daytime(double jd, double latitude, double longitude, double *altitude, char *error) {
    double solar[6], geographic[3] = {longitude, latitude, 0}, horizontal[3];
    int result = swe_calc_ut(jd, SE_SUN, SEFLG_SWIEPH | SEFLG_SPEED, solar, error);
    if (result < 0) return result;
    swe_azalt(jd, SE_ECL2HOR, geographic, 0, 15, solar, horizontal);
    *altitude = horizontal[1];
    return result;
}
int jy_rise_set(double jd, double latitude, double longitude, int is_rise, double *result, char *error) {
    double geographic[3] = {longitude, latitude, 0}, times[10];
    int status = swe_rise_trans(jd, SE_SUN, NULL, SEFLG_SWIEPH,
                                is_rise ? SE_CALC_RISE : SE_CALC_SET,
                                geographic, 0, 0, times, error);
    *result = times[0];
    return status;
}
