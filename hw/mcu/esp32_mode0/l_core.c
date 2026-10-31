/* L chip algorithm in portable C (30 Oct 2026): the integer pipeline of the RTL (hw/rtl/deep/l_cortex_deep.v) for a microcontroller or a PC.
 * Stages: (1) the Cortex encoder (finer-grid option): four binary receptor channels, 5x5 windows at stride 1 over a 24 x 24 grid of spots, the winning detector of 32 per channel, 4 x 4 pooling into 6 x 6 cells = 4,608 code bits;
 * (2) stage 1: the counting table, the sum of table rows of the active code bits (adds only); (3) the dispatcher: margin = top minus runner-up, wake stage 2 when margin <= L_ROUTE_T;
 * (4) L Deep stage 2: the sum of the second table's code rows plus the rows of the clauses that fire (a clause is an AND of literals over the 4,608 code bits and the two raw-pixel threshold planes);
 * (5) the reject flag: the margin of the final scores <= reject_t. Bit-exact with the model (checked by main_pc.c). No multiplies in the pipeline; table memory 145 KB.
 * Written to be read: no tricks, and uses only integer operations. */
#include <stdint.h>
#include <string.h>
#include "l_core.h"
#include "l_tables.h"

#define NCODE 4608
#define NB 6176
static inline int pop25(uint32_t v) { return __builtin_popcount(v & 0x1FFFFFFu); }

/* receptor map: bit0 pixel > 50, bit1 pixel > 150, bit2 ON cell (pixel - (sum of 8 neighbours >> 3) > 8), bit3 OFF cell ((sum >> 3) - pixel > 8); image edges repeat the border pixel */
static void receptors(const uint8_t *img, uint8_t *bmap) {
    for (int y = 0; y < 28; y++) for (int x = 0; x < 28; x++) {
        int ctr = img[y * 28 + x], nsum = 0;
        for (int ky = -1; ky <= 1; ky++) for (int kx = -1; kx <= 1; kx++) {
            if (ky == 0 && kx == 0) continue;
            int cy = y + ky, cx = x + kx; cy = cy < 0 ? 0 : (cy > 27 ? 27 : cy); cx = cx < 0 ? 0 : (cx > 27 ? 27 : cx); nsum += img[cy * 28 + cx];
        }
        int avg = nsum >> 3;
        bmap[y * 28 + x] = (uint8_t)((ctr > 50) | ((ctr > 150) << 1) | (((ctr - avg) > 8) << 2) | (((avg - ctr) > 8) << 3));
    }
}

/* detectors: for every spot and channel, the template with the most agreeing bits wins (the first one on a tie); a window with fewer than 3 on bits stays silent; the code bit is set per pooled cell */
static void encode(const uint8_t *bmap, uint8_t *code) {
    memset(code, 0, NCODE);
    for (int si = 0; si < 24; si++) for (int sj = 0; sj < 24; sj++) {
        uint32_t p[4] = {0, 0, 0, 0};
        for (int gr = 0; gr < 5; gr++) for (int gc = 0; gc < 5; gc++) {
            uint8_t b = bmap[(si + gr) * 28 + (sj + gc)]; int g = gr * 5 + gc;
            for (int ch = 0; ch < 4; ch++) p[ch] |= (uint32_t)((b >> ch) & 1) << g;
        }
        for (int ch = 0; ch < 4; ch++) {
            if (pop25(p[ch]) < 3) continue;
            int best = -1, win = 0;
            for (int f = 0; f < 32; f++) { int a = pop25(~(p[ch] ^ L_TM[ch * 32 + f])); if (a > best) { best = a; win = f; } }
            code[ch * 1152 + ((si >> 2) * 6 + (sj >> 2)) * 32 + win] = 1;
        }
    }
}

static void top2(const int32_t *s, int *pred, int32_t *margin) {
    int32_t a = INT32_MIN, b = INT32_MIN; int p = 0;
    for (int c = 0; c < 10; c++) { if (s[c] > a) { b = a; a = s[c]; p = c; } else if (s[c] > b) b = s[c]; }
    *pred = p; *margin = a - b;
}

void l_classify(const uint8_t *img, int32_t reject_t, l_result *r) {
    uint8_t bmap[784], code[NCODE]; static uint8_t in[NB];
    receptors(img, bmap); encode(bmap, code);
    int32_t s1[10] = {0}, s2[10] = {0}, m1;
    for (int b = 0; b < NCODE; b++) if (code[b]) for (int c = 0; c < 10; c++) s1[c] += L_W1[b * 10 + c];
    int p1; top2(s1, &p1, &m1);
    r->routed = (m1 <= L_ROUTE_T); r->stage1_margin = m1;
    const int32_t *fin = s1;
    if (r->routed) {
        for (int b = 0; b < NCODE; b++) { in[b] = code[b]; if (code[b]) for (int c = 0; c < 10; c++) s2[c] += L_W2[b * 10 + c]; }
        for (int i = 0; i < 784; i++) { in[NCODE + i] = img[i] > 85; in[NCODE + 784 + i] = img[i] > 170; }
        for (int cl = 0; cl < L_NCL; cl++) {
            int n = L_HDR_N[cl]; if (n == 0) continue;
            int ok = 1; const uint16_t *lp = &L_LITS[L_HDR_START[cl]];
            for (int t = 0; t < n; t++) { uint16_t lit = lp[t]; int v = (lit < NB) ? in[lit] : !in[lit - NB]; if (!v) { ok = 0; break; } }
            if (ok) for (int c = 0; c < 10; c++) s2[c] += L_WCL[cl * 10 + c];
        }
        fin = s2;
    }
    int32_t mf; top2(fin, &r->pred, &mf); r->margin = mf; r->flag = (mf <= reject_t);
    for (int c = 0; c < 10; c++) r->scores[c] = fin[c];
}
