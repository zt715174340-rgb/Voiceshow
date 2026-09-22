from __future__ import annotations

import json
import sys

from .graph import run_agent


def main() -> None:
    query = " ".join(sys.argv[1:]).strip() or "我想买一双适合跑步的鞋，预算500以内，轻一点"
    result = run_agent(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
