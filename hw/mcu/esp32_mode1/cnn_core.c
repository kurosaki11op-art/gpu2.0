/* Small reference CNN in portable C, int8 weights, uint8 activations, int32 accumulators, fixed-point requantisation (30 Oct 2026). A REFERENCE BASELINE for the microcontroller energy measurement, not a part of L.
 * conv 3x3 x32 + ReLU + 2x2 max pool, conv 3x3 x64 + ReLU + 2x2 max pool, fully connected 3,136 -> 10. About 3.9 million multiply-adds per image. Bit-exact with the numpy model of gen_cnn.py (checked by main_pc_cnn.c). */
#include <stdint.h>
#include "cnn_core.h"
#include "cnn_tables.h"
/* speed (31 Oct 2026): the Arduino ESP32 build uses -Os (small code); ask for speed for this file, the same as l_core.c, so both methods get the same treatment */
#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC optimize ("O3")
#endif

static uint8_t c1[32][28][28], p1[32][14][14], c2[64][14][14], p2[64][7][7];
static inline uint8_t rq(int32_t acc, int32_t m) { if (acc < 0) acc = 0; int64_t v = ((int64_t)acc * m + 32768) >> 16; return v > 255 ? 255 : (uint8_t)v; }

int cnn_classify(const uint8_t *img, int32_t *logits) {
    for (int o = 0; o < 32; o++) for (int y = 0; y < 28; y++) for (int x = 0; x < 28; x++) {
        int32_t acc = CNN_B1[o];
        for (int ky = 0; ky < 3; ky++) { int iy = y + ky - 1; if (iy < 0 || iy > 27) continue;
            for (int kx = 0; kx < 3; kx++) { int ix = x + kx - 1; if (ix < 0 || ix > 27) continue; acc += (int32_t)CNN_W1[o * 9 + ky * 3 + kx] * img[iy * 28 + ix]; } }
        c1[o][y][x] = rq(acc, CNN_M1);
    }
    for (int o = 0; o < 32; o++) for (int y = 0; y < 14; y++) for (int x = 0; x < 14; x++) {
        uint8_t a = c1[o][2 * y][2 * x], b = c1[o][2 * y][2 * x + 1], c = c1[o][2 * y + 1][2 * x], d = c1[o][2 * y + 1][2 * x + 1]; uint8_t m = a > b ? a : b; uint8_t n = c > d ? c : d; p1[o][y][x] = m > n ? m : n;
    }
    for (int o = 0; o < 64; o++) for (int y = 0; y < 14; y++) for (int x = 0; x < 14; x++) {
        int32_t acc = CNN_B2[o];
        for (int c = 0; c < 32; c++) for (int ky = 0; ky < 3; ky++) { int iy = y + ky - 1; if (iy < 0 || iy > 13) continue;
            for (int kx = 0; kx < 3; kx++) { int ix = x + kx - 1; if (ix < 0 || ix > 13) continue; acc += (int32_t)CNN_W2[((o * 32 + c) * 3 + ky) * 3 + kx] * p1[c][iy][ix]; } }
        c2[o][y][x] = rq(acc, CNN_M2);
    }
    for (int o = 0; o < 64; o++) for (int y = 0; y < 7; y++) for (int x = 0; x < 7; x++) {
        uint8_t a = c2[o][2 * y][2 * x], b = c2[o][2 * y][2 * x + 1], c = c2[o][2 * y + 1][2 * x], d = c2[o][2 * y + 1][2 * x + 1]; uint8_t m = a > b ? a : b; uint8_t n = c > d ? c : d; p2[o][y][x] = m > n ? m : n;
    }
    const uint8_t *f = &p2[0][0][0]; int best = 0; int32_t bv = INT32_MIN;
    for (int o = 0; o < 10; o++) { int32_t acc = CNN_B3[o]; for (int i = 0; i < 3136; i++) acc += (int32_t)CNN_W3[o * 3136 + i] * f[i]; if (logits) logits[o] = acc; if (acc > bv) { bv = acc; best = o; } }
    return best;
}
