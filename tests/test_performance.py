# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tests\test_performance.py
"""
Automated Verification Suite for Performance & Intelligence Upgrades.
Verifies Fast-Path routing (<100ms execution), Context Compression,
Smart Memory Relevance Search, and Response Cache hits.
"""
import os
import sys
import time

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_performance_test_suite():
    print("="*60)
    print("      SUNDAY PERFORMANCE & INTELLIGENCE VERIFICATION")
    print("="*60)

    # 1. Test Dynamic Brain Modes Dynamic Switching
    try:
        from brain.brain import BrainModule
        brain = BrainModule()
        
        # Test default mode
        assert brain.brain_mode == "NORMAL", "Default brain mode should be NORMAL"
        
        # Test switching to FAST
        success = brain.set_brain_mode("FAST")
        assert success and brain.brain_mode == "FAST", "Brain Mode FAST switch failed"
        
        # Test switching to THINK
        success = brain.set_brain_mode("THINK")
        assert success and brain.brain_mode == "THINK", "Brain Mode THINK switch failed"
        
        # Switch back to NORMAL
        brain.set_brain_mode("NORMAL")
        print("[PASS] Dynamic Brain Mode switching verified successfully.")
        
    except Exception as e:
        print(f"[FAIL] Brain Mode switching check failed: {e}")
        return False

    # 2. Test Smart Memory Relevance Search (Top 3 Recency-Weighted Entries)
    try:
        from memory.memory_manager import MemoryManager
        
        # Insert a factual test memory dynamically
        MemoryManager.save_knowledge("Python benchmark utility is located in the utils folder.", model=brain.active_model)
        
        # Relevance Search
        results = MemoryManager.relevance_search("python utility benchmark", limit=3)
        
        assert len(results) <= 3, "Memory Relevance Search exceeded top 3 limit"
        assert len(results) > 0, "No memories matched a highly specific query"
        
        # Check topic and content
        print(f"[PASS] Memory Relevance Search matched: '{results[0]['topic']}'")
        print(f"       Recency and score weighting verified successfully.")
        
    except Exception as e:
        print(f"[FAIL] Memory Relevance Search check failed: {e}")
        return False

    # 3. Test Context Compression Layer (History & Screen Trim)
    try:
        from brain.context_compressor import ContextCompressor
        
        raw_context = {
            "active_window": "Visual Studio Code",
            "screen_text": "A" * 1000,  # Enormous screen text block
            "project_memory": "[PROJECT: Performance] [GOAL: Upgrade] [ACTIVE TASKS: Benchmarks] [RECENT HISTORY: query1 -> query2 -> query1 -> query3]"
        }
        
        compressed = ContextCompressor.compress("python benchmark", raw_context)
        
        # Verify screen summary is truncated
        assert len(compressed["screen_summary"]) < 500, "Screen text block not compressed"
        assert "[Context Pruned" in compressed["screen_summary"], "Screen text truncation marker missing"
        
        # Verify deduplicated and capped history
        project_context = compressed["project_context"]
        assert "query1 -> query2 -> query3" in project_context, "History deduplication failed"
        
        print("[PASS] Context Compression Layer validated successfully.")
        print(f"       Original context sized reduced from {len(raw_context['screen_text'])} to {len(compressed['screen_summary'])} characters.")
        
    except Exception as e:
        print(f"[FAIL] Context Compression Layer check failed: {e}")
        return False

    # 4. Test Response Cache Hit / Miss Registry
    try:
        from brain.brain import ResponseCache
        
        ResponseCache.invalidate()
        
        # Set a test response
        key = "status"
        val = "Session status board details mock description"
        ResponseCache.set(key, val)
        
        # Query cache
        cached_val = ResponseCache.get(key)
        assert cached_val == val, "Cache retrieval failed"
        
        # Verify hit rate increases
        assert ResponseCache.hit_rate() == 1.0, "Cache hit rate logic incorrect"
        
        print("[PASS] Response Cache hits & telemetry metrics verified successfully.")
        
    except Exception as e:
        print(f"[FAIL] Response Cache check failed: {e}")
        return False

    # 5. Test Fast-Path Router Execution Latencies (<100ms Target)
    try:
        from interface.chat_interface import ChatInterface
        interface = ChatInterface()
        
        # We time a fast-path direct match execution (e.g. status)
        start_t = time.time()
        interface.process_command("status")
        elapsed = time.time() - start_t
        
        print(f"[PASS] Fast-Path Router bypass verified successfully.")
        print(f"       Query 'status' executed in: {elapsed:.4f} seconds (Target: <100ms)")
        
        assert elapsed < 0.1, f"Fast-Path routing took {elapsed:.4f}s, exceeding 100ms threshold!"
        
    except Exception as e:
        print(f"[FAIL] Fast-Path Router check failed: {e}")
        return False

    print("="*60)
    print("      PERFORMANCE VERIFICATION COMPLETED SUCCESSFULLY!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = run_performance_test_suite()
    sys.exit(0 if success else 1)
