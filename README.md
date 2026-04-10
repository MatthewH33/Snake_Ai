# Minesweeper — Google Minesweeper screen assistant

Python tool that captures a fixed region of your screen, reads the **Google Minesweeper** grid with **OpenCV** (HSV color masks), runs a **constraint-based solver** (`google_minesweeper_solver.py`), and shows **safe / flag** suggestions on a live overlay and HUD.

The main entry script is `Snake.py` (historical filename).

## Requirements

- **Python 3.10+** (uses modern type hints)
- Windows (paths and capture coordinates in the script assume a typical desktop setup; adjust as needed)

## Install

```bash
cd Minesweapwe
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Dependencies: `mss`, `numpy`, `opencv-python`, `PyAutoGUI` (listed for the project; the live overlay uses `mss`, `numpy`, `opencv-python`).

## Run

```bash
python Snake.py
```

A window opens with:

- The captured region (with an optional green grid and move circles)
- A bottom panel: detected board, next moves, and key hints

Quit with **Q** or **Esc**.

## Controls

| Key | Action |
|-----|--------|
| **A** | Toggle auto-solve (recompute moves each frame when on) |
| **O** | Toggle move overlay on the capture |
| **Space** | Pause capture (freeze last frame) |
| **S** | Solve once from current detection |
| **P** | Print detected board and moves to the terminal |
| **Q** / **Esc** | Quit |

Overlay labels: **S** = safe (reveal), **F** = flag.

## Configure capture and grid

Edit `main()` in `Snake.py`:

- **`monitor_region`** — `left`, `top`, `width`, `height` passed to `mss` (must frame the game board tightly).
- **`grid_cols`**, **`grid_rows`** — must match the visible mine grid (default **10×8** in code).

Cell classification is tuned for **Google Minesweeper** colors (covered green tiles, blue/green/red number styling). If your theme or zoom differs, adjust the HSV ranges in `classify_cell()`.

## Standalone solver (no camera)

The solver module can be run from the command line with a manual board string; see its docstring in `google_minesweeper_solver.py` for the `--rows` / `--cols` / board format (`.` covered, `F` flag, digits revealed).

## Project layout

| File | Role |
|------|------|
| `Snake.py` | Screen grab, grid split, CV classification, HUD, overlay |
| `google_minesweeper_solver.py` | Board model, `solve()`, CLI |
| `requirements.txt` | Python dependencies |

## Disclaimer

This is an educational / personal automation aid. Only use it where allowed by the game’s terms and applicable rules. Coordinate and color tuning are **your** responsibility.
