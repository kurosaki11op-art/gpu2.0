/* Small reference CNN in portable C: see cnn_core.c */
#pragma once
#include <stdint.h>
/* img: 784 bytes (28 x 28, row major, 0..255); logits: 10 int32 or NULL; returns the predicted class */
int cnn_classify(const uint8_t *img, int32_t *logits);
