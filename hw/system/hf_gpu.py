"""Next-byte predictions from a pretrained Hugging Face code model (default bigcode/tiny_starcoder_py).

The model works on BPE tokens; SPARK works on bytes. To compare them on the same task (predict the next
byte), the text is tokenized once and run through the model; at each token boundary we get the next-token
distribution P. For a byte that sits k bytes into the next token, the model's next-byte prediction is
  argmax_b  sum P(t)  over tokens t whose bytes start with the k bytes already seen and whose byte k is b.
Using the real tokenization to know where tokens start slightly favours the GPU model (it never has to
consider a token ending early), so it is a conservative baseline for SPARK.
"""
import numpy as np
import torch


def hf_next_byte_preds(data, name="bigcode/tiny_starcoder_py", window=1024, overlap=256, threads=2):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(threads)
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForCausalLM.from_pretrained(name, torch_dtype=torch.float32).eval()
    text = bytes(data).decode("latin-1")      # 1 char per byte, keeps offsets aligned with bytes
    enc = tok(text, return_offsets_mapping=True, add_special_tokens=False)
    ids, offs = enc["input_ids"], enc["offset_mapping"]
    vocab = [tok.convert_tokens_to_string([t]).encode("latin-1", errors="replace") for t in tok.convert_ids_to_tokens(range(len(tok)))]
    maxlen = max(len(v) for v in vocab)
    V = np.zeros((len(vocab), maxlen), dtype=np.int16) - 1
    for i, v in enumerate(vocab):
        V[i, :len(v)] = np.frombuffer(v, dtype=np.uint8)
    n_tok = len(ids)
    probs_at = [None] * (n_tok + 1)              # distribution for token j given tokens < j
    x = torch.tensor(ids)[None, :]
    start = 0
    with torch.no_grad():
        while start < n_tok:
            lo = max(0, start - overlap)
            hi = min(n_tok, lo + window)
            logits = model(x[:, lo:hi]).logits[0].float()
            p = torch.softmax(logits, -1).numpy()
            for j in range(max(start, lo + 1), hi + 1):
                if j - 1 - lo < p.shape[0] and probs_at[j] is None:
                    probs_at[j] = p[j - 1 - lo]
            start = hi
    preds = np.zeros(len(data), dtype=np.int64)
    first_tok_pred = None
    for j in range(n_tok):
        s, e = offs[j]
        P = probs_at[j]
        if P is None:                            # first token: no context, fall back to space
            preds[s:e] = 32
            continue
        cand = np.arange(len(vocab))
        for k in range(e - s):                   # predict byte s+k from bytes s..s+k-1 of this token
            pos = s + k - 1
            if k > 0:
                cand = cand[V[cand, k - 1] == data[s + k - 1]]
            nxt = V[cand, k]
            ok = nxt >= 0
            if pos >= 0 and ok.any():
                mass = np.bincount(nxt[ok], weights=P[cand[ok]], minlength=256)
                preds[pos] = int(mass.argmax())
    # last byte: no following token, predict newline
    preds[-1] = 10
    return preds
