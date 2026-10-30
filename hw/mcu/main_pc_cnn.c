/* PC check of the C CNN: predictions on the test images against the numpy int8 model (cnn_expected_pred.txt, one class per line) and the labels, plus time per image.
 * usage: ./cnn_pc test_images.bin cnn_expected_pred.txt N */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "cnn_core.h"
int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: %s test_images.bin cnn_expected_pred.txt N\n", argv[0]); return 2; }
    int N = atoi(argv[3]); FILE *fi = fopen(argv[1], "rb"), *fe = fopen(argv[2], "r"); if (!fi || !fe) { perror("open"); return 2; }
    uint8_t *img = malloc(784 * (size_t)N); if (fread(img, 784, N, fi) != (size_t)N) { fprintf(stderr, "short image file\n"); return 2; }
    int bad = 0; double t0 = (double)clock() / CLOCKS_PER_SEC;
    for (int i = 0; i < N; i++) { int e; if (fscanf(fe, "%d", &e) != 1) return 2; int p = cnn_classify(img + 784 * i, NULL); if (p != e) { bad++; if (bad <= 3) printf("MISMATCH image %d: %d vs %d\n", i, p, e); } }
    double dt = (double)clock() / CLOCKS_PER_SEC - t0; printf("%d images, mismatches against the numpy int8 model %d; %.2f ms per image on this PC\n%s\n", N, bad, 1000 * dt / N, bad ? "FAIL" : "PASS"); return bad ? 1 : 0;
}
