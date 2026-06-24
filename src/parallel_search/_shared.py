from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# ─── User-Agent ──────────────────────────────────────────────────
_HEADERS = {
    "User-Agent": "ReasonixCognitiveSearch/5.8 (fangtaocai041@gmail.com)",
    "Accept": "application/json",
}

_TIMEOUT_S = 15  # per-provider timeout
