#ifndef JY_SWISS_BRIDGE_H
#define JY_SWISS_BRIDGE_H
int jy_max_path_bytes(void);
/* 0 success; -1 invalid/overlong path; -2 conflicting SE_EPHE_PATH override. */
int jy_set_path(const char *path);
const char *jy_version(void);
int jy_calc(double jd, int body, double *values, char *error);
/* Mean tropical node (without nutation) minus true Lahiri ayanamsha.
 * Applies the corresponding ayanamsha derivative to longitudinal speed. */
int jy_mean_node_true_ayanamsa(double jd, double *values, char *error);
int jy_ascendant(double jd, double latitude, double longitude, double *ascendant);
int jy_daytime(double jd, double latitude, double longitude, double *altitude, char *error);
int jy_rise_set(double jd, double latitude, double longitude, int is_rise, double *result, char *error);
#endif
