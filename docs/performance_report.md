# SUNDAY Local AI Models Performance Benchmark Report

Generated on: 2026-06-01 05:27:04

## Executive Performance Summary

This report compiles real-time execution speeds, prompt evaluation latencies, and token generation velocities for active local models running on Ollama.

| Model Tag | Warm-Start Latency (s) | Avg Total Response Time (s) | First-Token Latency (s) | Avg Token Speed (tokens/s) | Tokens Generated |
| --- | --- | --- | --- | --- | --- |
| `llama3.2:latest` | 17.5628s | 10.3330s | 1.4972s | 5.79 tokens/s | 49.0 tokens |
| `phi3:latest` | 17.3505s | 13.2731s | 1.4394s | 3.01 tokens/s | 35.0 tokens |
| `llama3:8b` | 33.1529s | 16.7612s | 2.8940s | 2.38 tokens/s | 32.5 tokens |
| `llama3.2:1b` | 15.8161s | 7.0824s | 0.4108s | 9.72 tokens/s | 63.7 tokens |


## Configured Routing Modes & Priorities

- **FAST Mode** $ightarrow$ `llama3.2:1b` (Ultra-High speed, minimal RAM footprint)
- **NORMAL Mode** $ightarrow$ `llama3.2:latest` (Llama 3.2 3B — Optimal balance on 8 GB RAM)
- **THINK Mode** $ightarrow$ `llama3:8b` (Deepest reasoning fallbacks)
- **CODE Mode** $ightarrow$ `phi3:latest` (Phi-3 3.8B — Specialized coding capabilities)
- **Automatic Downgrade Protection**: Fully active on query timeout, OOM, or server failure.

## Individual Run Analytics

### Model: `llama3.2:latest`
- **VRAM Warm-Start Latency**: 17.5628 seconds

#### Query 1: *"What is the capital of France?"*
- **Total Response Time (latency)**: 3.1840 seconds
- **First-Token Latency**: 1.4507 seconds
- **Token Velocity (speed)**: 5.89 tokens/sec
- **Tokens Generated**: 8 tokens

#### Query 2: *"Explain quantum computing in one sentence."*
- **Total Response Time (latency)**: 10.2657 seconds
- **First-Token Latency**: 1.4491 seconds
- **Token Velocity (speed)**: 5.50 tokens/sec
- **Tokens Generated**: 46 tokens

#### Query 3: *"Write a python function to check if a number is prime."*
- **Total Response Time (latency)**: 17.5493 seconds
- **First-Token Latency**: 1.5919 seconds
- **Token Velocity (speed)**: 5.97 tokens/sec
- **Tokens Generated**: 93 tokens

### Model: `phi3:latest`
- **VRAM Warm-Start Latency**: 17.3505 seconds

#### Query 1: *"Explain quantum computing in one sentence."*
- **Total Response Time (latency)**: 13.2731 seconds
- **First-Token Latency**: 1.4394 seconds
- **Token Velocity (speed)**: 3.01 tokens/sec
- **Tokens Generated**: 35 tokens

### Model: `llama3:8b`
- **VRAM Warm-Start Latency**: 33.1529 seconds

#### Query 1: *"What is the capital of France?"*
- **Total Response Time (latency)**: 7.4294 seconds
- **First-Token Latency**: 2.9866 seconds
- **Token Velocity (speed)**: 2.28 tokens/sec
- **Tokens Generated**: 8 tokens

#### Query 2: *"Explain quantum computing in one sentence."*
- **Total Response Time (latency)**: 26.0930 seconds
- **First-Token Latency**: 2.8015 seconds
- **Token Velocity (speed)**: 2.48 tokens/sec
- **Tokens Generated**: 57 tokens

### Model: `llama3.2:1b`
- **VRAM Warm-Start Latency**: 15.8161 seconds

#### Query 1: *"What is the capital of France?"*
- **Total Response Time (latency)**: 1.4923 seconds
- **First-Token Latency**: 0.3650 seconds
- **Token Velocity (speed)**: 8.78 tokens/sec
- **Tokens Generated**: 8 tokens

#### Query 2: *"Explain quantum computing in one sentence."*
- **Total Response Time (latency)**: 3.8443 seconds
- **First-Token Latency**: 0.4217 seconds
- **Token Velocity (speed)**: 10.42 tokens/sec
- **Tokens Generated**: 33 tokens

#### Query 3: *"Write a python function to check if a number is prime."*
- **Total Response Time (latency)**: 15.9105 seconds
- **First-Token Latency**: 0.4456 seconds
- **Token Velocity (speed)**: 9.97 tokens/sec
- **Tokens Generated**: 150 tokens

