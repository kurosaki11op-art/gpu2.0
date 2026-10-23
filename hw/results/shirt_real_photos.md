---
title: Shirt against T-shirt on real colour photos (24 Oct 2026)
tags: [l, clothing, limits, results]
---

# With real extra evidence (colour), does L separate Shirt from T-shirt? No label is used at test time. (SIMULATED on a real photo data set, 5 random splits)

Data: the Grigorev clothing dataset (photos taken by volunteers, colour, 400+ px, github `alexeygrigorev/clothing-dataset`; list in `clothing_photos_images.csv`, images fetched to `/tmp/clothing`, not stored in the repo). Used: T-Shirt 984, Shirt 372, Longsleeve 661, Outwear 277 after dropping children's items and files that failed. Pictures are padded to a square and resized; **backgrounds are NOT removed** (unlike Fashion-MNIST), labels come from the volunteers.
Script `hw/brain/experiments/month5/shirt_real_photos.py`, log `shirt_real_photos.log`. Same images, same random 75/25 splits (5) for every model. L = integer slow-table model, stride-1 detector code; for colour the three colour planes are coded separately and the codes concatenated (3 x 4,608 bits). CNN = small backprop ruler (flip augmentation, 40 epochs), never part of the chip.

**Shirt against T-shirt (2 classes, 1,356 images; always answering T-shirt scores 72.6%)**

| Model and input | T-Shirt recall | Shirt recall | Accuracy |
|---|---|---|---|
| L, grey 28 x 28 | 93.2 | 61.0 | 83.7 |
| **L, colour 28 x 28** | 94.1 | **79.6** | **89.8** |
| CNN, grey 28 x 28 | 94.0 | 79.8 | 89.9 |
| CNN, colour 28 x 28 | 93.9 | 74.8 | 88.4 |
| CNN, colour 56 x 56 | 96.6 | 73.4 | 89.8 |

**Four garments (T-Shirt, Shirt, Longsleeve, Outwear; 2,294 images)**

| Model and input | T-Shirt | Shirt | Longsleeve | Outwear | Accuracy |
|---|---|---|---|---|---|
| L, grey 28 | 86.0 | 61.3 | 53.7 | 51.5 | 67.8 |
| L, colour 28 | 89.8 | 58.0 | 56.3 | 54.7 | 70.2 |
| CNN, grey 28 | 91.9 | 50.6 | 65.2 | 51.6 | 71.9 |
| CNN, colour 28 | 89.6 | 54.0 | 69.1 | 52.1 | 72.7 |
| CNN, colour 56 | 88.6 | 56.2 | 69.7 | 55.1 | 73.2 |

**Reading.**
- On the pair you asked about, **colour is real independent evidence and L uses it**: Shirt recall 61.0 to 79.6 (+18.6), accuracy 83.7 to 89.8, level with the CNN ruler, with no label at test time. This is a legitimate second source, unlike the spoken-name test.
- **It does not generalise to the 4-way task**: Shirt recall is flat (61.3 to 58.0); overall +2.4. Colour helps tell a plain shirt from a printed T-shirt, not shirt from long-sleeve.
- **Resolution did not help the CNN** (56 x 56 against 28 x 28: no consistent gain). What is missing is not pixels but cleaner data; these photos have backgrounds, folds, hangers and noisy volunteer labels. Even the CNN is at 73% on 4 garments.
- Honest comparison with Fashion-MNIST: different data (photos, small, unbalanced), so these numbers must not be set next to the 63 to 74% Fashion-MNIST Shirt recall as if the same test.

**Limits and risks (read before quoting).** Small data (1,356 and 2,294 images), 5 splits of the same pool (no independent test set); classes unbalanced; **colour may help partly through data-set bias** (volunteers' shirts and T-shirts differ in typical colour), which is a real cue here but may not hold elsewhere; the L colour code is three times the table rows (13,824 bits, not on the chip's 4,608-bit design); no tuning of either model; labels are noisy.

**Next.** Balanced and repeated tests with a held-out volunteer group; colour-opponent cells (cheaper than three full planes); a cleaner source (background removed) for fair comparison with Fashion-MNIST.

Related: [Results index](INDEX.md), [Specialist for Shirt/T-shirt](shirt_specialist.md), [Second-sense correction](shirt_second_sense.md), [Where L loses on clothing](clothing_confusion.md), [Journal](../../docs/journal.md)
