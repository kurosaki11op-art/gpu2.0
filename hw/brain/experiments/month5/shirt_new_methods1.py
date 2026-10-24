"""24 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. Method 1: flip augmentation of the table training (train-time only, no chip cost). Method 2: test-time flip (adds a second view)."""
from shirt_new_methods_setup import *
W0 = train_table(ctr, ytr); report("baseline L (single view)", cte.astype(np.int32) @ W0)
W1 = train_table(np.concatenate([ctr, ctrf]), np.concatenate([ytr, ytr])); report("M1 table trained with flipped copies", cte.astype(np.int32) @ W1)
report("M2 baseline + test-time flip", cte.astype(np.int32) @ W0 + ctef.astype(np.int32) @ W0)
report("M1+M2 both", cte.astype(np.int32) @ W1 + ctef.astype(np.int32) @ W1)
