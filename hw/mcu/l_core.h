/* L chip algorithm in portable C: see l_core.c */
#pragma once
#include <stdint.h>
typedef struct { int pred; int routed; int flag; int32_t margin; int32_t stage1_margin; int32_t scores[10]; } l_result;
/* img: 784 bytes (28 x 28, row major); reject_t: answers whose final margin is <= reject_t are flagged for a fallback */
void l_classify(const uint8_t *img, int32_t reject_t, l_result *r);
