// PC check of the same code the ESP32 runs: gcc -Iesp32_l_test host_check.c -o host_check && ./host_check
#include <stdio.h>
#include "l_decide.h"
int main(void) {
    int bad = 0, ok = 0;
    for (int i = 0; i < L_NIMG; i++) { int p = l_decide(i, 0); if (p != L_EXPECT[i]) bad++; if (p == L_LABEL[i]) ok++; }
    printf("%d images, %d differ from the Python model, accuracy %d/%d\n", L_NIMG, bad, ok, L_NIMG);
    printf(bad ? "LOGIC FAIL\n" : "LOGIC PASS\n"); return bad != 0;
}
