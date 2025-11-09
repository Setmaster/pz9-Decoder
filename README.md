# 🧩 pz9-decoder

A simple Python tool to decode `.pz9` and `.pa9` Pokémon data files from **Pokémon Legends: Z-A**.
It extracts core information such as species, nickname, original trainer, and trainer IDs.

---

## 🔍 Features

- Reads and decodes 344-byte `.pz9` and `.pa9` Pokémon records.
- Displays key trainer info:
  - **Species**
  - **Nickname**
  - **Original Trainer (OT)**
  - **TID (6-digit Trainer ID)**
  - **SID (4-digit SID7 for Gen 7+ games)**
- Optionally exports JSON output for each Pokémon.
- Automatically fetches a full species name list using [PokeAPI](https://pokeapi.co/).

---

## 🖥️ Usage

### Web version: **[ZA-Decoder Web](https://setmaster.github.io/ZA-Decoder/)**

### Python

The script will automatically find and process all `.pz9` and `.pa9` files in the current directory.

### 1. Basic (print summaries)
```bash
python pz9_decoder.py
```

Example output:
```
Species: Magikarp
Nick: Fish
OT: Set
TID: 021203
SID: 1341
------------------
Species: Pikachu
Nick: Sparky
OT: Ash
TID: 123456
SID: 7890
```

### 2. Save JSON output
Creates an `outdir/` folder containing a `.json` file for each `.pz9` or `.pa9` found.
```bash
python pz9_decoder.py --out
```

### 3. Custom output directory
```bash
python pz9_decoder.py --out results
```

---

## ⚙️ Requirements

- Python 3.9+
- [Requests](https://pypi.org/project/requests/)
  ```bash
  pip install requests
  ```

---

## 🧠 How It Works

- The script identifies `.pz9` and `.pa9` records as **344 bytes long**, representing one Pokémon entry.
- It extracts key data from fixed offsets:
  - `0x08–0x09` → **Species ID**
  - `0x0C–0x0F` → **TrainerID32**
- Trainer IDs are derived from the 32-bit `TrainerID32` value as follows:
  - **TID7** = `TrainerID32 % 1_000_000` → 6-digit in-game Trainer ID
  - **SID7** = `TrainerID32 // 1_000_000` → 4-digit Secret ID (Gen 7+ format)
- UTF-16LE encoded strings in the file are used to extract:
  - The Pokémon’s **nickname**
  - The **Original Trainer (OT)** name
- The script can optionally pull full Pokémon species names using [PokeAPI](https://pokeapi.co/), ensuring complete species coverage.
- Output can be printed directly to the console or exported as per-Pokémon JSON files for further analysis.