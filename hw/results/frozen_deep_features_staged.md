---
title: Frozen deep gate features plus counting table in staged learning
tags: [l, accelerator, continual-learning, gate-network, shirt]
---

# Frozen deep gate features under L's counting table, learned in stages (25 Oct 2026)

Stage A: the hard-gate integer learner ([boolean_error_transport](boolean_error_transport.md); error passed down, trained once) on L's 4,608-bit code, base classes 0-5 only, 2,000 + 2,000 + 600 gates, 4 epochs (6-way base accuracy 86.1%), then frozen. Stage B: the counting table (CortexSlow) reads classes 0-5, then the new classes 6-9 (Shirt, Sneaker, Bag, Boot) in a second stage, no rehearsal. SIMULATED, Fashion-MNIST, one seed. Scripts: [bool_frozen_features.py](../brain/experiments/month5/bool_frozen_features.py), [bool_frozen_tables.py](../brain/experiments/month5/bool_frozen_tables.py); logs: [features](../brain/experiments/month5/bool_frozen_features.log), [tables](../brain/experiments/month5/bool_frozen_tables.log).

| Table reads | Bits | Base 6-way after stage 1 | Old (after stage 2) | New | All 10 | Cluster | Shirt recall | Shirt AP |
|---|---|---|---|---|---|---|---|---|
| L's code only | 4,608 | 93.2 | 81.9 | 91.6 | **85.8** | 78.0 | 0.749 | **0.640** |
| frozen gate layers only | 4,600 | 91.6 | 82.2 | 86.5 | 83.9 | 75.2 | 0.588 | 0.580 |
| L's code + frozen gate layers | 9,208 | 92.6 | 79.5 | 88.7 | 83.2 | 76.4 | 0.665 | 0.611 |

## Reading
- **Fails.** Frozen deep gate features trained on the base classes do not help the table: alone they are worse than L's own code (83.9 against 85.8), added to it they are worse still (83.2, Shirt AP 0.611 against 0.640).
- Cause (hypothesis, consistent with the earlier runs): the features were trained to separate classes 0-5 only, so they carry little about the new classes; Shirt is the class most like the base T-shirt, Pullover and Coat and was never contrasted with them.
- Reference: with Shirt absent from the first stage, L's code gives Shirt AP 0.640 (0.753 when all classes are trained together): the cost of staged learning for the confusable class is about 0.11 AP.
- So neither error passing (base training) nor local error nor neurogenesis has produced features that help Shirt or staged learning on top of L's own code in these tests.

Related: [Results index](INDEX.md), [Local layers and neurogenesis](local_growth_staged.md), [Boolean error transport](boolean_error_transport.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
