#!/usr/bin/env python3
"""Verification test for Python multi-agent server."""

import os
import sys
import json
import time
import urllib.request
import threading
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import server

def run_tests():
    print("--- Starting Python Multi-Agent Server Tests ---")
    server.PORT = 4006
    httpd = server.HTTPServer(("127.0.0.1", 4006), server.ResearchHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    try:
        # 1. Test GET /
        print("[Python Test 1] Testing static GET / ...")
        with urllib.request.urlopen("http://127.0.0.1:4006/", timeout=5) as resp:
            content = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "MarketPulse" in content
            print("✅ [Python Test 1 Passed] Served index.html successfully.")

        # 2. Test GET /api/health
        print("[Python Test 2] Testing GET /api/health ...")
        with urllib.request.urlopen("http://127.0.0.1:4006/api/health", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert resp.status == 200
            assert data["status"] == "ok"
            print("✅ [Python Test 2 Passed] Health check OK.")

        # 3. Test POST /api/research
        print("[Python Test 3] Testing POST /api/research for 'Analyze the food delivery market in Nepal.' ...")
        payload = json.dumps({"query": "Analyze the food delivery market in Nepal.", "provider": "simulated"}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:4006/api/research", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            assert resp.status == 200
            assert res_data["success"] is True
            result = res_data["result"]
            print(f"📋 Entity: {result.get('entity')}")
            print(f"- SAM: {result.get('metrics', {}).get('sam')}")
            print(f"- Players: {[p['name'] for p in result.get('key_players', [])]}")
            assert "planner" in result["raw_agents"]
            assert "synthesis" in result["raw_agents"]
            print("✅ [Python Test 3 Passed] All agents executed successfully in Python!")

        print("\n🎉 ALL PYTHON MULTI-AGENT APP TESTS PASSED!\n")
        return 0
    except Exception as e:
        print(f"❌ Test failed: {e}", file=sys.stderr)
        return 1
    finally:
        httpd.server_close()

if __name__ == "__main__":
    sys.exit(run_tests())

