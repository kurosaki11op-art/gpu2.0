// L decision on a microcontroller: add the table rows of the active input bits, take the largest class. No multiply, no float.
#pragma once
#include "l_table.h"
static inline int l_decide(int img, int32_t *score_out) {
    int32_t s[L_CLASSES] = {0};
    for (uint32_t k = L_OFF[img]; k < L_OFF[img + 1]; k++) {
        const int8_t *r = L_ROWS[L_ACT[k]];
        for (int c = 0; c < L_CLASSES; c++) s[c] += r[c];
    }
    int best = 0;
    for (int c = 1; c < L_CLASSES; c++) if (s[c] > s[best]) best = c;
    if (score_out) *score_out = s[best];
    return best;
}
