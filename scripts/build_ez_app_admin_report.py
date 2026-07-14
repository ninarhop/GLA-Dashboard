from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG = ROOT / "config" / "data_sources.local.json"
EXAMPLE_CONFIG = ROOT / "config" / "data_sources.example.json"
COLUMN_MAP = ROOT / "config" / "source_columns.json"

DETAIL_FILENAME = "GLA_EZ_APP_MATCH_DETAIL_CURRENT.csv"
SUMMARY_FILENAME = "GLA_EZ_APP_MATCH_SUMMARY_CURRENT.json"


