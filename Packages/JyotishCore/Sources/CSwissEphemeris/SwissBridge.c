#include "include/SwissBridge.h"
#include "swephexp.h"

void jy_set_path(const char *path) {
    swe_set_ephe_path((char *)path);
    swe_set_sid_mode(SE_SIDM_LAHIRI, 0, 0);
}
const char *jy_version(void) {
    static char version[256];
    return swe_version(version);
}
int jy_calc(double jd, int body, double *values, char *error) {
    return swe_calc_ut(jd, body, SEFLG_SIDEREAL | SEFLG_SWIEPH | SEFLG_SPEED, values, error);
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
