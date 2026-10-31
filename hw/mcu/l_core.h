/* L chip algorithm in portable C: see l_core.c */
#pragma once
#include <stdint.h>
typedef struct { int pred; int routed; int flag; int32_t margin; int32_t stage1_margin; int32_t scores[10]; } l_result;
/* img: 784 bytes (28 x 28, row major); reject_t: answers whose final margin is <= reject_t are flagged for a fallback */
void l_classify(const uint8_t *img, int32_t reject_t, l_result *r);
/* optional profiling (31 Oct 2026): set l_clock to a microsecond counter (e.g. micros on an ESP32); l_prof then accumulates the microseconds spent in the receptor map, the detectors, stage 1 (the counting table) and stage 2 (L Deep, routed images only) */
extern uint32_t (*l_clock)(void);
extern uint32_t l_prof[4];
