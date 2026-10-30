/* PC check of the portable C core: classifies the test images and compares routed flag, all ten final scores and the prediction with the model's expected values (sys_exp.txt of hw/rtl/deep, the file the RTL checks use).
 * usage: ./l_pc test_images.bin sys_exp.txt N [reject_t]      prints mismatches, routed count, flagged count, mean time per image on this PC */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "l_core.h"
int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: %s test_images.bin sys_exp.txt N [reject_t]\n", argv[0]); return 2; }
    int N = atoi(argv[3]); int32_t rt = argc > 4 ? atoi(argv[4]) : 0; FILE *fi = fopen(argv[1], "rb"), *fe = fopen(argv[2], "r"); if (!fi || !fe) { perror("open"); return 2; }
    uint8_t *img = malloc(784 * (size_t)N); if (fread(img, 784, N, fi) != (size_t)N) { fprintf(stderr, "short image file\n"); return 2; }
    int bad = 0, routed = 0, flagged = 0; double t0 = (double)clock() / CLOCKS_PER_SEC;
    for (int i = 0; i < N; i++) {
        int er, ep; long es[10]; if (fscanf(fe, "%d", &er) != 1) return 2; for (int c = 0; c < 10; c++) if (fscanf(fe, "%ld", &es[c]) != 1) return 2; if (fscanf(fe, "%d", &ep) != 1) return 2;
        l_result r; l_classify(img + 784 * i, rt, &r); int ok = (r.routed == er) && (r.pred == ep); for (int c = 0; c < 10; c++) ok &= (r.scores[c] == es[c]);
        if (!ok) { bad++; if (bad <= 3) printf("MISMATCH image %d: routed %d/%d pred %d/%d\n", i, r.routed, er, r.pred, ep); }
        routed += r.routed; flagged += r.flag;
    }
    double dt = (double)clock() / CLOCKS_PER_SEC - t0; printf("%d images, routed %d, flagged %d, mismatches %d; %.2f ms per image on this PC\n%s\n", N, routed, flagged, bad, 1000 * dt / N, bad ? "FAIL" : "PASS"); return bad ? 1 : 0;
}
