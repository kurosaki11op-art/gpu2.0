# Virtual space for the chip-vs-GPU benchmark (22 Oct 2026). The chip runs as its RTL design in Icarus Verilog; the GPU side uses your GPU through the NVIDIA container runtime.
FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime
RUN apt-get update && apt-get install -y --no-install-recommends iverilog git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy numba nvidia-ml-py
WORKDIR /work
COPY . /work
ENTRYPOINT ["python", "virtual_space/benchmark.py", "/data"]
