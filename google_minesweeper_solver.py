"""
Minesweeper solver logic only (no detection/capture/clicking).

Usage:
  python google_minesweeper_solver.py --rows 9 --cols 9 --manual "..2......|...etc..."

Row chars:
  . = covered, F = flag, 0-8 = revealed number
Rows are separated by '|'.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterator

import numpy as np


class Cell(IntEnum):
    COVERED = -2
    FLAG = -1
    SAFE = -4  # internal marker for deduced safe cells


@dataclass(frozen=True)
class Move:
    row: int
    col: int
    flag: bool  # True=flag mine, False=reveal safe


def neighbors(r: int, c: int, rows: int, cols: int) -> Iterator[tuple[int, int]]:
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield nr, nc


def parse_manual(s: str, rows: int, cols: int) -> np.ndarray:
    s = s.strip().replace(" ", "")
    parts = s.split("|")
    if len(parts) != rows:
        raise ValueError(f"Expected {rows} rows separated by |, got {len(parts)}")
    board = np.full((rows, cols), Cell.COVERED, dtype=np.int8)
    for ri, row in enumerate(parts):
        if len(row) != cols:
            raise ValueError(f"Row {ri} length {len(row)} != cols {cols}")
        for ci, ch in enumerate(row):
            if ch == ".":
                board[ri, ci] = Cell.COVERED
            elif ch in "fF":
                board[ri, ci] = Cell.FLAG
            elif ch.isdigit():
                board[ri, ci] = int(ch)
            else:
                raise ValueError(f"Bad char {ch!r} at row {ri} col {ci}")
    return board


def board_to_str(board: np.ndarray) -> str:
    rows, cols = board.shape
    lines: list[str] = []
    for r in range(rows):
        chars: list[str] = []
        for c in range(cols):
            v = int(board[r, c])
            if v == Cell.COVERED:
                chars.append(".")
            elif v == Cell.FLAG:
                chars.append("F")
            else:
                chars.append(str(v))
        lines.append("".join(chars))
    return "\n".join(lines)


def solve(board: np.ndarray) -> list[Move]:
    """Return safe flags and reveals (deterministic only, no guessing)."""
    rows, cols = board.shape
    moves: list[Move] = []
    seen_set: set[tuple[int, int, bool]] = set()
    work = board.copy()

    def add(r: int, c: int, flag: bool) -> bool:
        key = (r, c, flag)
        if key in seen_set:
            return False
        seen_set.add(key)
        moves.append(Move(r, c, flag))
        work[r, c] = Cell.FLAG if flag else Cell.SAFE
        return True

    def collect_numbered() -> list[tuple[int, int, int, list[tuple[int, int]]]]:
        numbered: list[tuple[int, int, int, list[tuple[int, int]]]] = []
        for r in range(rows):
            for c in range(cols):
                v = int(work[r, c])
                if v < 0 or v > 8:
                    continue
                unk: list[tuple[int, int]] = []
                flags = 0
                for nr, nc in neighbors(r, c, rows, cols):
                    cell = int(work[nr, nc])
                    if cell == Cell.FLAG:
                        flags += 1
                    elif cell == Cell.COVERED:
                        unk.append((nr, nc))
                need = v - flags
                if unk:
                    numbered.append((r, c, need, unk))
        return numbered

    changed = True
    while changed:
        changed = False

        for r in range(rows):
            for c in range(cols):
                v = int(work[r, c])
                if v < 0 or v > 8:
                    continue
                unk: list[tuple[int, int]] = []
                flags = 0
                for nr, nc in neighbors(r, c, rows, cols):
                    cell = int(work[nr, nc])
                    if cell == Cell.FLAG:
                        flags += 1
                    elif cell == Cell.COVERED:
                        unk.append((nr, nc))
                need = v - flags
                if need < 0 or need > len(unk):
                    continue
                if need == len(unk) and unk:
                    for nr, nc in unk:
                        if add(nr, nc, True):
                            changed = True
                if need == 0 and unk:
                    for nr, nc in unk:
                        if add(nr, nc, False):
                            changed = True

        numbered = collect_numbered()
        for i, (_, _, need_a, unk_a) in enumerate(numbered):
            set_a = set(unk_a)
            for _, _, need_b, unk_b in numbered[i + 1 :]:
                set_b = set(unk_b)
                if set_a <= set_b and set_b > set_a:
                    diff = list(set_b - set_a)
                    n_diff = need_b - need_a
                    if n_diff == 0:
                        for nr, nc in diff:
                            if add(nr, nc, False):
                                changed = True
                    elif n_diff == len(diff):
                        for nr, nc in diff:
                            if add(nr, nc, True):
                                changed = True
                elif set_b <= set_a and set_a > set_b:
                    diff = list(set_a - set_b)
                    n_diff = need_a - need_b
                    if n_diff == 0:
                        for nr, nc in diff:
                            if add(nr, nc, False):
                                changed = True
                    elif n_diff == len(diff):
                        for nr, nc in diff:
                            if add(nr, nc, True):
                                changed = True

    return moves


def main() -> None:
    p = argparse.ArgumentParser(description="Minesweeper solver logic only")
    p.add_argument("--rows", type=int, required=True)
    p.add_argument("--cols", type=int, required=True)
    p.add_argument(
        "--manual",
        type=str,
        required=True,
        help='Board string, e.g. "1..|...|..."',
    )
    args = p.parse_args()

    board = parse_manual(args.manual, args.rows, args.cols)
    moves = solve(board)
    print("Board:")
    print(board_to_str(board))
    print(f"Moves: {len(moves)}")
    for m in moves:
        print(f"  {'FLAG' if m.flag else 'REVEAL'} ({m.row},{m.col})")


if __name__ == "__main__":
    main()
