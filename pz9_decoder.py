#!/usr/bin/env python3
r"""
pz9_decoder_v2.py
A simple "dumb-proof" decoder for 344-byte Legends Z-A `.pz9` Pokémon records.

Default behavior (no args):
    - Scans the current directory for all .pz9 files
    - Prints a compact summary for each file:
        Species: <SpeciesName>
        Nick:    <Nickname>
        OT:      <OriginalOT>
        TID:     <6-digit TID7>
        SID:     <4-digit SID7>

Optional:
    --out [DIR]
        - Writes per-file JSON output into DIR (default: "outdir")
        - JSON contains species, OT, TID7, SID7, etc.

This code uses PokeAPI to build a full species map on first run.
"""

import argparse
import json
import re
import sys
import glob
from pathlib import Path
from typing import Any, Dict, List
import requests  # Requires the "requests" library to fetch from PokeAPI

POKEAPI_SPECIES_URL = "https://pokeapi.co/api/v2/pokemon-species/?limit=10000"

_species_map: Dict[int, str] = {}

def load_species_map() -> None:
    """Loads the species‐ID → name map from PokeAPI."""
    global _species_map
    try:
        resp = requests.get(POKEAPI_SPECIES_URL)
        resp.raise_for_status()
        data = resp.json()
        for entry in data["results"]:
            # entry["url"] ends in “/.../pokemon-species/<id>/”
            # we extract the id from the URL
            url = entry["url"]
            match = re.search(r"/pokemon-species/(\d+)/?$", url)
            if match:
                sid = int(match.group(1))
                name = entry["name"].capitalize()
                _species_map[sid] = name
    except Exception as e:
        print(f"[!] Warning: failed to load species map from PokeAPI: {e}", file=sys.stderr)

def species_name_from_id(sid: int) -> str:
    if not _species_map:
        load_species_map()
    return _species_map.get(sid, f"SpeciesID {sid}")

def u16(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o+2], "little")

def u32(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o+4], "little")

def find_utf16le_strings(data: bytes, min_chars: int = 2) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for offset in (0, 1):
        try:
            s = data[offset:].decode("utf-16le", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r"[A-Za-z0-9 _\-\.\'\!\?\:\;\&\(\)\/]{%d,}" % min_chars, s):
            out.append({"offset": offset + m.start()*2, "string": m.group(0)})
    seen, uniq = set(), []
    for ent in sorted(out, key=lambda x: x["offset"]):
        key = (ent["offset"], ent["string"])
        if key not in seen:
            seen.add(key)
            uniq.append(ent)
    return uniq

def decode_pz9(p: Path) -> Dict[str, Any]:
    raw = p.read_bytes()
    if len(raw) != 344:
        raise ValueError(f"{p.name}: expected 344 bytes, got {len(raw)}")

    species_id = u16(raw, 0x08)
    trainer_id32 = u32(raw, 0x0C)

    tid7 = trainer_id32 % 1_000_000
    tid7_str = f"{tid7:06d}"
    sid7 = trainer_id32 // 1_000_000

    strings = find_utf16le_strings(raw)
    nickname = strings[0]["string"] if len(strings) >= 1 else ""
    original_ot = strings[-1]["string"] if len(strings) >= 3 else (strings[-1]["string"] if strings else "")

    return {
        "file": p.name,
        "species_id": species_id,
        "species_name": species_name_from_id(species_id),
        "nickname": nickname,
        "original_ot": original_ot,
        "TID7": tid7_str,
        "SID7": sid7,
    }

def print_summary(entry: Dict[str, Any]) -> None:
    print(f"Species: {entry['species_name']}")
    print(f"Nick:    {entry['nickname']}")
    print(f"OT:      {entry['original_ot']}")
    print(f"TID:     {entry['TID7']}")
    print(f"SID:     {entry['SID7']}")

def gather_inputs() -> List[Path]:
    return [Path(m) for m in sorted(glob.glob("*.pz9"))]

def main():
    parser = argparse.ArgumentParser(description="Simple .pz9 decoder (shows SID7 only).")
    parser.add_argument("--out", nargs="?", const="outdir", default=None,
                        help="Write detailed JSON per .pz9 to this directory.")
    args = parser.parse_args()

    inputs = gather_inputs()
    if not inputs:
        print("No .pz9 files found in this directory.", file=sys.stderr)
        sys.exit(1)

    outdir: Path | None = None
    if args.out is not None:
        outdir = Path(args.out)
        outdir.mkdir(parents=True, exist_ok=True)

    for i, p in enumerate(inputs):
        try:
            dec = decode_pz9(p)
            print_summary(dec)
            if i < len(inputs) - 1:
                print("-" * 18)
            if outdir:
                out_file = outdir / f"{p.stem}_decoded.json"
                out_file.write_text(json.dumps(dec, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[!] Error decoding {p.name}: {e}", file=sys.stderr)
            if outdir:
                err = {"file": p.name, "error": str(e)}
                (outdir / f"{p.stem}_error.json").write_text(json.dumps(err, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
