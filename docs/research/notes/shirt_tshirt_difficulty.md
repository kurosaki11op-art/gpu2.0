---
title: Research notes - shirt tshirt difficulty
tags: [l, research, notes]
---

# Why Shirt vs T-shirt (and Pullover/Coat) is hard in Fashion-MNIST, and what reduces it

Access note: arxiv.org, ar5iv, cleanlab.ai and mdpi.com were unreachable from the fetch tool (DNS failure). Only github.com/zalandoresearch/fashion-mnist was fetched in full. Every other figure below comes from web-search result summaries (page text not read in full), so treat them as "search-snippet level" and re-verify against the linked page before quoting. Nothing here is from memory unless marked UNVERIFIED.

## Highest published overall accuracy; best Shirt accuracy; is Shirt capped by label noise?

### Takeaway
The official benchmark table tops out at 96.7% (WRN40-4, crop+flip augmentation, no ensemble listed). One MDPI paper claims 99.65% with augmentation, which is an outlier I could not read. I found no source with a best-model per-class Shirt number; per-class Shirt figures found are all from weak models or student projects (61-80%) and show Shirt is the worst class everywhere. Whether a ceiling exists from label noise is not quantified for the test split.

### Cited Findings
- Official benchmark table, top entries: WRN40-4 (8.9M params) 0.967; WRN-28-10 + Random Erasing 0.963; WRN-28-10 0.959; Dual path net w/ WRN 28-10 0.957; DenseNet-BC 0.954; DENSER 0.953; ResNet18 0.949. Top four use mean/std normalization plus random crops and horizontal flips. Page says the page does not mention ensembles and that submissions are untested by the maintainers ("we haven't yet tested these results"). — [Fashion-MNIST GitHub README](https://github.com/zalandoresearch/fashion-mnist)
- A 2024 MDPI Mathematics paper (CNN-3-128 plus data augmentation) claims 99.65% Fashion-MNIST test accuracy, vs 99.1% for its cited predecessor. Not read in full; single-paper claim, far above the table's 96.7%, so possible train/test leakage or tuning on test cannot be ruled out. — [MDPI 12(20):3174](https://www.mdpi.com/2227-7390/12/20/3174) (via search summary)
- A community leaderboard lists roughly 96-97% (e.g. 96.3, 96.35). — [wizwand Fashion-MNIST](https://www.wizwand.com/dataset/fashion-mnist) (via search summary)
- Per-class results from weak or student models (not SOTA), all show Shirt as the worst class:
  - Blog (CNN): Shirt recall 67.7%; Shirt confused with T-shirt/top (98 images) and Coat (103); 169 Pullovers predicted as Coat. — [hashnode post](https://hashnode.com/posts/neural-network-from-scratch-mnist-fashion-mnist/6a9a81636e269aa076faab76)
  - VGG16-based model confusion row for Shirt: 104 to T-shirt, 52 to Pullover, 38 to Coat; GoogLeNet gets 670 of 1,000 Shirts and 759 Coats right. — [arXiv 2603.10731](https://arxiv.org/pdf/2603.10731)
  - Berkeley CS194-26 projects: Shirt 61% (T-shirt 84, Pullover 89, Coat 85) — [afk](https://inst.eecs.berkeley.edu/~cs194-26/sp20/upload/files/proj4/cs194-26-afk/); Shirt 0.693 (T-shirt 0.895, Pullover 0.877, Coat 0.916) and Shirt 0.728 (T-shirt 0.832, Pullover 0.904, Coat 0.838) and Shirt 0.80 (T-shirt 0.75, Pullover 0.80, Coat 0.83) — [Berkeley proj4 pages, same site](https://inst.eecs.berkeley.edu/~cs194-26/sp20/upload/files/proj4/cs194-26-aby/); Shirt 77.0% test vs trouser 98.8%, confusions with coat, dress, pullover — [Chelsea Ye project](https://inst.eecs.berkeley.edu/~cs194-26/sp20/upload/files/proj4/cs194-26-agb/Chelsea_Ye_proj4/); Shirt 70% — [agt](https://inst.eecs.berkeley.edu/~cs194-26/sp20/upload/files/proj4/cs194-26-agt/)
  - These models are ~87-90% overall while Shirt is 60-80% (search-engine summary). Individual numbers vary by model and are not comparable.
- Capsule-network paper error analysis calls some "T-shirt/top" vs "Shirt" mistakes genuinely ambiguous to humans. — [arXiv 2103.08074](https://arxiv.org/pdf/2103.08074) (via snippet)
- Tensor-based classification paper attributes Shirt being hardest to ambiguity in category definitions. — [arXiv 1910.02150](https://arxiv.org/pdf/1910.02150) (via snippet)

### Inferences
- With ~96.7% overall best published and 4 near-confusable upper-body classes, most remaining test errors plausibly sit in Shirt/T-shirt/Pullover/Coat, but no source I read gives the per-class table of a 96%+ model. Treat that as a hypothesis to test by training a strong CNN and printing its confusion matrix.
- Weak-model Shirt recall (60-80%) is not evidence of a ceiling; the SOTA Shirt recall is unknown to me.

### Gaps
- Per-class Shirt recall of any >95% model: not found. Arxiv/papers-with-code pages were unreachable.
- Whether 99.65% (MDPI) is legitimate: paper not readable.
- Ensemble-specific SOTA numbers: none found; table says nothing on ensembles.

## Label ambiguity and noise in Fashion-MNIST; fraction wrong/ambiguous

### Takeaway
No peer-reviewed fraction of wrong test labels for Fashion-MNIST was found. The only audit is a Cleanlab company blog on the full dataset (hundreds of issues, concentrated in Shirt to T-shirt/top and Dress). A small independent check found ~0.7% hard samples in 1,000.

### Cited Findings
- Cleanlab Studio audit ("Fashion MNIST ... contains Hundreds of Miscategorized Items"): >100 images labeled Shirt suggested to relabel as T-shirt/top, >40 as Dress; blog reasons that T-shirt/top covers both t-shirts and tops, so Shirt labels are inconsistent; some ambiguous images should be removed. Split-level (train vs test) breakdown not given in the material I saw; company blog, not peer reviewed. — [Cleanlab blog](https://cleanlab.ai/blog/learn/csa/csa-4/) (via search summary)
- Overhead MNIST paper reviewed 1,000 Fashion-MNIST samples and found 7 tough samples (0.7%), including images combining two categories (e.g. shirt and trousers). — [arXiv 2102.04266](https://arxiv.org/pdf/2102.04266) (via snippet)
- Northcutt, Athalye, Mueller, "Pervasive Label Errors in Test Sets": 10 datasets, ~3.3% average test label error (some sources 3.4%), ~51% (arXiv) / 54% (NeurIPS listing) of confident-learning candidates confirmed by crowd reviewers; MNIST 15 errors; ImageNet val ~2,916 (~6%). Error lists at labelerrors.com. I did not find Fashion-MNIST among the 10 datasets in what I saw (the ten are not enumerated in my sources); do not assume it was audited. — [ar5iv 2103.14749](https://ar5iv.arxiv.org/html/2103.14749), [AI Business](https://aibusiness.com/ml/machine-learning-benchmarks-revealed-to-contain-pervasive-labeling-errors) (the latter's CIFAR-100 attribution of 2,916 looks wrong)
- GitHub README of Fashion-MNIST does not discuss label noise; issue search for "label noise shirt" returned 0 results. — [repo](https://github.com/zalandoresearch/fashion-mnist)
- No "ReLabeled Fashion-MNIST" dataset found by search. Zalando paper (arXiv 1708.07747) could not be fetched, so its own statements on label construction are not verified here.

### Inferences
- Cleanlab's >100 Shirt-to-T-shirt flags are over 70,000 images (60k train+10k test), i.e. well under 1% of the dataset; if proportional in the test set that is on the order of tens of images (~0.2-0.5%), which cannot by itself explain 4-10 point Shirt recall loss. The semantic overlap (T-shirt/top includes top-like shirts) is a systematic definitional ambiguity, not random noise. This is my arithmetic, not a sourced figure.

### Gaps
- Test-split-only label error rate: not found. Zalando paper text: unreachable. Human per-class accuracy: not found. A figure of 83.5% crowd-sourced human accuracy on 1,000 examples appeared in one search summary but my follow-up search could not locate its source: UNVERIFIED.

## Specialist / hierarchical classifiers and other methods for the upper-body group

### Takeaway
No source found gives before/after numbers for a Shirt/T-shirt/Pullover/Coat specialist on Fashion-MNIST. Only generic hierarchical-CNN evidence (aggregate improvement) was found.

### Cited Findings
- Seo and Shin, Hierarchical CNN (VGG-based) for fashion images: reports lower loss and higher accuracy than a flat baseline; treats shirt-type garments as a coarse "tops" group refined by a second stage. No per-class numbers seen. — [Ewha repository](https://pure.ewha.ac.kr/en/publications/hierarchical-convolutional-neural-networks-for-fashion-image-clas/) (via snippet)
- Deep metric learning paper recovers a hierarchy where tops split by sleeve length rather than original garment label. — [arXiv 2004.06353](https://arxiv.org/pdf/2004.06353) (via snippet)
- Top benchmark entries rely on crops/flips and Random Erasing (+0.4 point: WRN-28-10 0.959 to 0.963). — [README](https://github.com/zalandoresearch/fashion-mnist)

### Inferences
- Random Erasing/crop+flip is the best-documented lever; effect on Shirt specifically is not shown.
- Specialist networks, mixup, TTA, ensembles, attention, higher resolution: no sourced numbers; need own experiments.

### Gaps
- All of the above technique-specific per-class numbers.

## Colour / high-resolution datasets where Shirt vs T-shirt is more separable

### Takeaway
Dataset facts found, but no per-class Shirt vs T-shirt accuracy on any of them.

### Cited Findings
- clothing-dataset-small (Grigorev): top-10 popular classes of a 5,000-image, 20-class set; Xception tutorial split 3,085 train / 372 val / 341 test. No accuracy or per-class result found. — [repo](https://github.com/alexeygrigorev/clothing-dataset-small), [Medium write-up](https://medium.com/@thebendu/clothing-image-classification-2476b1d20d92)
- Other Xception-style clothing results (different class sets, not comparable): 89.75% on 12 of 20 classes; 92.19% top-1 on 8 classes. — [rymshasaeed repo](https://github.com/rymshasaeed/Clothing-Classification), [Inderscience](https://www.inderscience.com/offer.php?id=111426)

### Inferences
- Not enough evidence to say separability is better in colour/high-res; plausible but unsupported.

### Gaps
- DeepFashion, Fashion Product Images, Fashionpedia: not searched or no data obtained within the tool budget (fetch tool could not reach most hosts).

Related: [Notes index](INDEX.md), [Report](../matrix_free_vs_cnn_report.md)
