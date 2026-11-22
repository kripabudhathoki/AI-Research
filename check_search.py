"""Run: python check_search.py   (shows exactly what works on THIS computer)"""
from workflow import _wikipedia, find_in_directory

print("1. Sample directory (works offline):")
for q in ["Nepal Telecom", "ncel", "banking", "Foodmandu", "coffee"]:
    entry, score = find_in_directory(q)
    print(f"   {q!r:16} ->", entry["name"] if entry else "NOT FOUND")

print("2. Live web search (needs internet):")
try:
    pages = _wikipedia("Himalayan Bank")
    print("   OK:", [p["title"] for p in pages])
except Exception as exc:
    print("   FAILED:", type(exc).__name__, exc)
    print("   -> Internet/firewall/SSL issue. Sample directory still works; use Auto or Sample mode.")