#ifndef JY_SWISS_BRIDGE_H
#define JY_SWISS_BRIDGE_H
void jy_set_path(const char *path);
const char *jy_version(void);
int jy_calc(double jd, int body, double *values, char *error);
int jy_ascendant(double jd, double latitude, double longitude, double *ascendant);
int jy_daytime(double jd, double latitude, double longitude, double *altitude, char *error);
int jy_rise_set(double jd, double latitude, double longitude, int is_rise, double *result, char *error);
#endif
