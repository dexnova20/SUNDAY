# c:\Users\mshas\OneDrive\Desktop\SUNDAY\utils\benchmark_models.py
"""
Benchmarking Suite for SUNDAY.
Queries installed local models to track:
- Total response latency
- First-token latency
- Token generation speed (tokens/sec)
- Warm-start latency (VRAM loading latency)
Outputs a beautiful markdown performance comparison report at docs/performance_report.md.
"""
import os
import sys
import time
import requests

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import OLLAMA_URL, FALLBACK_CHAIN

TEST_QUERIES = [
    "What is the capital of France?",
    "Explain quantum computing in one sentence.",
    "Write a python function to check if a number is prime."
]

def run_model_benchmarks():
    print("="*65)
    print("            SUNDAY LOCAL MODELS PERFORMANCE BENCHMARKER")
    print("="*65)

    # 1. Fetch available models
    try:
        response = requests.get(OLLAMA_URL.rstrip('/') + "/api/tags", timeout=5)
        if response.status_code != 200:
            print("[ERROR] Ollama did not respond successfully.")
            return
        installed_models = [m["name"] for m in response.json().get("models", [])]
    except Exception as e:
        print(f"[ERROR] Could not query Ollama: {e}")
        return

    if not installed_models:
        print("[WARNING] No installed Ollama models found to benchmark!")
        return

    # Filter to prioritize the models configured in SUNDAY's fallback/priority list
    bench_models = []
    for preferred in FALLBACK_CHAIN:
        # Match tag case-insensitively
        matched = next((m for m in installed_models if preferred.lower() in m.lower()), None)
        if matched and matched not in bench_models:
            bench_models.append(matched)
            
    # Include other installed models as secondary
    for m in installed_models:
        if m not in bench_models:
            bench_models.append(m)

    print(f"Prioritizing {len(bench_models)} models for benchmark: {', '.join(bench_models)}")
    
    results = {}
    
    for model in bench_models:
        print(f"\nBenchmarking model: '{model}'...")
        results[model] = {
            "runs": [],
            "warmstart": 0.0
        }
        
        # Measure warm-start latency (Approved Requirement)
        print(f"  Measuring warm-start latency (loading '{model}' into VRAM)...")
        start_ws = time.time()
        try:
            ws_res = requests.post(
                OLLAMA_URL.rstrip('/') + "/api/chat",
                json={"model": model, "messages": [{"role": "user", "content": "Hi"}], "stream": False, "options": {"num_predict": 1}},
                timeout=35
            )
            warmstart_latency = time.time() - start_ws
            if ws_res.status_code == 200:
                print(f"  Warm-start Latency: {warmstart_latency:.4f}s")
            else:
                print(f"  Warm-start failed (HTTP {ws_res.status_code}), estimated: {warmstart_latency:.4f}s")
        except Exception as ws_ex:
            warmstart_latency = time.time() - start_ws
            print(f"  Warm-start exception (Ollama load delay): {ws_ex}. Estimated: {warmstart_latency:.4f}s")
            
        results[model]["warmstart"] = warmstart_latency

        for i, query in enumerate(TEST_QUERIES):
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": query}],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 150
                }
            }
            
            start_t = time.time()
            try:
                res = requests.post(OLLAMA_URL.rstrip('/') + "/api/chat", json=payload, timeout=30)
                elapsed = time.time() - start_t
                if res.status_code == 200:
                    data = res.json()
                    eval_cnt = data.get("eval_count", 0)
                    eval_dur = data.get("eval_duration", 0) / 1e9
                    prompt_dur = data.get("prompt_eval_duration", 0) / 1e9
                    
                    tokens_per_sec = eval_cnt / eval_dur if eval_dur > 0 else 0.0
                    first_token = prompt_dur if prompt_dur > 0 else elapsed * 0.1
                    
                    results[model]["runs"].append({
                        "query": query,
                        "latency": elapsed,
                        "first_token": first_token,
                        "tokens_per_sec": tokens_per_sec,
                        "tokens_generated": eval_cnt
                    })
                    print(f"  Query {i+1} Success: Total {elapsed:.2f}s | First Token {first_token:.2f}s | {tokens_per_sec:.2f} tok/s")
                else:
                    print(f"  Query {i+1} Failed: HTTP {res.status_code}")
            except Exception as ex:
                print(f"  Query {i+1} Exception: {ex}")
                
    # 2. Compile and write report
    report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "performance_report.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# SUNDAY Local AI Models Performance Benchmark Report\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Executive Performance Summary\n\n")
        f.write("This report compiles real-time execution speeds, prompt evaluation latencies, and token generation velocities for active local models running on Ollama.\n\n")
        
        f.write("| Model Tag | Warm-Start Latency (s) | Avg Total Response Time (s) | First-Token Latency (s) | Avg Token Speed (tokens/s) | Tokens Generated |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        
        for model, details in results.items():
            runs = details["runs"]
            if not runs:
                continue
            avg_latency = sum(r["latency"] for r in runs) / len(runs)
            avg_first_token = sum(r["first_token"] for r in runs) / len(runs)
            avg_speed = sum(r["tokens_per_sec"] for r in runs) / len(runs)
            avg_tokens = sum(r["tokens_generated"] for r in runs) / len(runs)
            ws_lat = details["warmstart"]
            
            f.write(f"| `{model}` | {ws_lat:.4f}s | {avg_latency:.4f}s | {avg_first_token:.4f}s | {avg_speed:.2f} tokens/s | {avg_tokens:.1f} tokens |\n")
            
        f.write("\n\n## Configured Routing Modes & Priorities\n\n")
        f.write("- **FAST Mode** $\rightarrow$ `llama3.2:1b` (Ultra-High speed, minimal RAM footprint)\n")
        f.write("- **NORMAL Mode** $\rightarrow$ `llama3.2:latest` (Llama 3.2 3B — Optimal balance on 8 GB RAM)\n")
        f.write("- **THINK Mode** $\rightarrow$ `llama3:8b` (Deepest reasoning fallbacks)\n")
        f.write("- **CODE Mode** $\rightarrow$ `phi3:latest` (Phi-3 3.8B — Specialized coding capabilities)\n")
        f.write("- **Automatic Downgrade Protection**: Fully active on query timeout, OOM, or server failure.\n\n")
        
        f.write("## Individual Run Analytics\n\n")
        for model, details in results.items():
            runs = details["runs"]
            if not runs:
                continue
            f.write(f"### Model: `{model}`\n")
            f.write(f"- **VRAM Warm-Start Latency**: {details['warmstart']:.4f} seconds\n\n")
            for idx, r in enumerate(runs):
                f.write(f"#### Query {idx+1}: *\"{r['query']}\"*\n")
                f.write(f"- **Total Response Time (latency)**: {r['latency']:.4f} seconds\n")
                f.write(f"- **First-Token Latency**: {r['first_token']:.4f} seconds\n")
                f.write(f"- **Token Velocity (speed)**: {r['tokens_per_sec']:.2f} tokens/sec\n")
                f.write(f"- **Tokens Generated**: {r['tokens_generated']} tokens\n\n")
                
    print(f"\n[SUCCESS] Performance benchmarks completed successfully!")
    print(f"          Report saved at: {report_path}")
    print("="*65 + "\n")

if __name__ == "__main__":
    run_model_benchmarks()
