"""Train the 'GPU-side' model for the SPARK + GPU system simulation.

Model: nanoGPT (open-source GPT-2-style transformer, MIT licence, third_party/nanogpt/model.py,
unmodified) at byte level (vocab 256), so it predicts exactly the same thing as SPARK: the next byte.
Trained here on the same Python-source corpus split SPARK was trained on (first 90%); the test
slice (95%..) is never seen by either model.  Pretrained checkpoints (HuggingFace) are not
reachable from this sandbox, so the weights are trained locally from the open-source architecture.
"""
import argparse, json, os, sys, time
import numpy as np, torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "third_party", "nanogpt"))
sys.path.insert(0, os.path.join(HERE, "..", "train"))
from model import GPT, GPTConfig          # noqa: E402
import train_spark_v0 as tr               # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--embd", type=int, default=256)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--block", type=int, default=256)
    ap.add_argument("--batch", type=int, default=24)
    ap.add_argument("--minutes", type=float, default=12.0)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    torch.manual_seed(0)
    data = tr.load_corpus(3_000_000)
    n = len(data)
    train = torch.from_numpy(data[: int(n * 0.9)].astype(np.int64))
    val = torch.from_numpy(data[int(n * 0.9): int(n * 0.95)].astype(np.int64))
    cfg = GPTConfig(block_size=a.block, vocab_size=256, n_layer=a.layers, n_head=a.heads,
                    n_embd=a.embd, dropout=0.0, bias=False)
    m = GPT(cfg)
    opt = m.configure_optimizers(0.1, 1e-3, (0.9, 0.95), "cpu")

    def batch(src):
        ix = torch.randint(len(src) - a.block - 1, (a.batch,))
        x = torch.stack([src[i: i + a.block] for i in ix])
        y = torch.stack([src[i + 1: i + 1 + a.block] for i in ix])
        return x, y

    t0, it, log = time.time(), 0, []
    budget = a.minutes * 60
    while time.time() - t0 < budget:
        frac = (time.time() - t0) / budget
        lr = 1e-3 * min(1.0, (it + 1) / 100) * (0.1 + 0.9 * 0.5 * (1 + np.cos(np.pi * frac)))
        for g in opt.param_groups:
            g["lr"] = lr
        x, y = batch(train)
        _, loss = m(x, y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step()
        if it % 100 == 0:
            m.eval()
            with torch.no_grad():
                vl = float(np.mean([m(*batch(val))[1].item() for _ in range(4)]))
            m.train()
            log.append((it, round(time.time() - t0), loss.item(), vl))
            print(f"it {it} t {time.time()-t0:.0f}s train {loss.item():.3f} val {vl:.3f}", flush=True)
        it += 1
    os.makedirs(a.out, exist_ok=True)
    torch.save({"cfg": cfg.__dict__, "state": m.state_dict()}, os.path.join(a.out, "gpu_model.pt"))
    json.dump({"params": m.get_num_params(), "iters": it, "log": log, "args": vars(a)},
              open(os.path.join(a.out, "gpu_model_train.json"), "w"), indent=1)
    print("params", m.get_num_params(), "iters", it)


if __name__ == "__main__":
    main()
