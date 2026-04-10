import cv2
import mss
import numpy as np

from google_minesweeper_solver import Cell, Move, solve


def classify_cell(cell_bgr: np.ndarray) -> str:
    """Classify one Minesweeper cell using robust HSV color masks."""
    hsv = cv2.cvtColor(cell_bgr, cv2.COLOR_BGR2HSV)
    h, w = cell_bgr.shape[:2]

    # Ignore a small border to avoid green grid edges.
    pad_x = max(1, w // 8)
    pad_y = max(1, h // 8)
    roi = hsv[pad_y : h - pad_y, pad_x : w - pad_x]

    if roi.size == 0:
        roi = hsv

    # Covered tile (green shades).
    covered_mask = cv2.inRange(roi, (35, 40, 80), (90, 255, 255))
    covered_ratio = float(np.count_nonzero(covered_mask)) / covered_mask.size
    if covered_ratio > 0.45:
        return "."

    # Number color masks.
    blue_mask = cv2.inRange(roi, (90, 50, 40), (140, 255, 255))
    green_mask = cv2.inRange(roi, (35, 50, 40), (85, 255, 255))
    red_mask1 = cv2.inRange(roi, (0, 60, 40), (12, 255, 255))
    red_mask2 = cv2.inRange(roi, (165, 60, 40), (179, 255, 255))
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    blue_count = int(np.count_nonzero(blue_mask))
    green_count = int(np.count_nonzero(green_mask))
    red_count = int(np.count_nonzero(red_mask))
    number_count = max(blue_count, green_count, red_count)

    # If no number color is present, treat as opened empty.
    min_number_pixels = max(10, (roi.shape[0] * roi.shape[1]) // 40)
    if number_count < min_number_pixels:
        return "0"

    if blue_count >= green_count and blue_count >= red_count:
        return "1"
    if green_count >= blue_count and green_count >= red_count:
        return "2"
    return "3"


def detected_to_solver_board(board_chars: np.ndarray) -> np.ndarray:
    rows, cols = board_chars.shape
    board = np.full((rows, cols), Cell.COVERED, dtype=np.int8)
    for r in range(rows):
        for c in range(cols):
            ch = str(board_chars[r, c])
            if ch == ".":
                board[r, c] = Cell.COVERED
            elif ch == "F":
                board[r, c] = Cell.FLAG
            elif ch.isdigit():
                board[r, c] = int(ch)
            else:
                board[r, c] = Cell.COVERED
    return board


def board_to_lines(board_chars: np.ndarray) -> list[str]:
    return ["".join(str(ch) for ch in row) for row in board_chars]


def detect_board(frame_bgr: np.ndarray, rows: int, cols: int) -> np.ndarray:
    h, w = frame_bgr.shape[:2]
    x_edges = np.linspace(0, w, cols + 1, dtype=int)
    y_edges = np.linspace(0, h, rows + 1, dtype=int)
    board = np.full((rows, cols), ".", dtype="<U1")

    for r in range(rows):
        for c in range(cols):
            x0, x1 = x_edges[c], x_edges[c + 1]
            y0, y1 = y_edges[r], y_edges[r + 1]
            cell = frame_bgr[y0:y1, x0:x1]
            if cell.size == 0:
                continue
            board[r, c] = classify_cell(cell)
    return board


def render_board_panel(board: np.ndarray, moves: list[Move], cell_px: int = 30) -> np.ndarray:
    rows, cols = board.shape
    panel_h = rows * cell_px
    panel_w = cols * cell_px
    panel = np.full((panel_h, panel_w, 3), 35, dtype=np.uint8)

    num_colors = {
        "1": (255, 120, 0),
        "2": (40, 180, 70),
        "3": (40, 60, 220),
    }
    move_map = {(m.row, m.col): m for m in moves if 0 <= m.row < rows and 0 <= m.col < cols}

    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * cell_px, r * cell_px
            x1, y1 = x0 + cell_px, y0 + cell_px
            val = board[r, c]

            if val == ".":
                fill = (80, 160, 80)
                text = ""
            elif val == "0":
                fill = (205, 185, 160)
                text = ""
            else:
                fill = (220, 205, 180)
                text = val

            cv2.rectangle(panel, (x0, y0), (x1, y1), fill, thickness=-1)
            border_color = (25, 25, 25)
            if (r, c) in move_map:
                border_color = (0, 165, 255) if move_map[(r, c)].flag else (80, 255, 80)
            cv2.rectangle(panel, (x0, y0), (x1, y1), border_color, thickness=2 if (r, c) in move_map else 1)

            if text:
                color = num_colors.get(text, (0, 0, 0))
                cv2.putText(
                    panel,
                    text,
                    (x0 + cell_px // 3, y0 + (cell_px * 3) // 4),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2,
                    lineType=cv2.LINE_AA,
                )

    return panel


def draw_moves_overlay(frame_bgr: np.ndarray, moves: list[Move], rows: int, cols: int) -> None:
    h, w = frame_bgr.shape[:2]
    x_edges = np.linspace(0, w, cols + 1, dtype=int)
    y_edges = np.linspace(0, h, rows + 1, dtype=int)

    for m in moves:
        if not (0 <= m.row < rows and 0 <= m.col < cols):
            continue
        x0, x1 = x_edges[m.col], x_edges[m.col + 1]
        y0, y1 = y_edges[m.row], y_edges[m.row + 1]
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2
        rad = max(6, min(x1 - x0, y1 - y0) // 4)
        color = (0, 165, 255) if m.flag else (80, 255, 80)
        label = "F" if m.flag else "S"
        cv2.circle(frame_bgr, (cx, cy), rad, color, 2, lineType=cv2.LINE_AA)
        cv2.putText(
            frame_bgr,
            label,
            (cx - rad // 2, cy + rad // 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
            lineType=cv2.LINE_AA,
        )


def render_bottom_hud(
    board: np.ndarray,
    moves: list[Move],
    frame_width: int,
    solver_auto: bool,
    show_overlay: bool,
    paused: bool,
) -> np.ndarray:
    rows, cols = board.shape
    board_panel = render_board_panel(board, moves, cell_px=30)

    hud_h = board_panel.shape[0] + 92
    hud = np.full((hud_h, frame_width, 3), 22, dtype=np.uint8)

    title = f"Detected board {cols}x{rows}  |  moves: {len(moves)}"
    cv2.putText(hud, title, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1, cv2.LINE_AA)

    mode_line = f"[A] auto-solve: {'ON' if solver_auto else 'OFF'}   [O] overlay: {'ON' if show_overlay else 'OFF'}   [Space] pause: {'ON' if paused else 'OFF'}"
    cv2.putText(hud, mode_line, (10, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 220, 200), 1, cv2.LINE_AA)

    key_line = "[S] solve now   [P] print board+moves   [Q/Esc] quit"
    cv2.putText(hud, key_line, (10, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 220), 1, cv2.LINE_AA)

    board_w = board_panel.shape[1]
    y0 = 86
    hud[y0 : y0 + board_panel.shape[0], 0:board_w] = board_panel

    info_x = min(board_w + 10, frame_width - 140)
    cv2.putText(hud, "Next moves:", (info_x, y0 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)
    for i, m in enumerate(moves[:9]):
        line = f"{i + 1}. {'FLAG' if m.flag else 'SAFE'} ({m.row},{m.col})"
        cv2.putText(
            hud,
            line,
            (info_x, y0 + 45 + i * 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 180, 255) if m.flag else (120, 255, 120),
            1,
            cv2.LINE_AA,
        )

    return hud


def main() -> None:
    # Region requested: x:-1166..-716, y:210..570, size 450x360
    monitor_region = {
        "left": -1166,
        "top": 210,
        "width": 450,
        "height": 360,
    }

    window_name = "Live Screen View (q to quit)"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    grid_cols = 10
    grid_rows = 8
    auto_solve = True
    show_overlay = True
    paused = False
    detected_board = np.full((grid_rows, grid_cols), ".", dtype="<U1")
    moves: list[Move] = []
    frozen_frame_bgr: np.ndarray | None = None

    with mss.mss() as sct:
        while True:
            if not paused:
                frame = np.array(sct.grab(monitor_region))
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                frozen_frame_bgr = frame_bgr.copy()
            else:
                # Reuse last captured frame while paused.
                if frozen_frame_bgr is None:
                    frame = np.array(sct.grab(monitor_region))
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    frozen_frame_bgr = frame_bgr.copy()
                else:
                    frame_bgr = frozen_frame_bgr.copy()

            # Draw an evenly spaced 10x8 grid overlay.
            h, w = frame_bgr.shape[:2]
            grid_color = (0, 255, 0)
            thickness = 1

            # Draw all boundaries (including outer border) for accurate counts:
            # 10 columns => 11 vertical lines, 8 rows => 9 horizontal lines.
            vertical_x = np.linspace(0, w - 1, grid_cols + 1, dtype=int)
            horizontal_y = np.linspace(0, h - 1, grid_rows + 1, dtype=int)

            for x in vertical_x:
                cv2.line(frame_bgr, (x, 0), (x, h - 1), grid_color, thickness)

            for y in horizontal_y:
                cv2.line(frame_bgr, (0, y), (w - 1, y), grid_color, thickness)

            if not paused:
                detected_board = detect_board(frame_bgr, grid_rows, grid_cols)
                if auto_solve:
                    solver_board = detected_to_solver_board(detected_board)
                    moves = solve(solver_board)

            if show_overlay:
                draw_moves_overlay(frame_bgr, moves, grid_rows, grid_cols)

            bottom_panel = render_bottom_hud(
                board=detected_board,
                moves=moves,
                frame_width=frame_bgr.shape[1],
                solver_auto=auto_solve,
                show_overlay=show_overlay,
                paused=paused,
            )
            combined = np.vstack([frame_bgr, bottom_panel])

            cv2.imshow(window_name, combined)

            # Keybinds.
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break
            if key == ord("a"):
                auto_solve = not auto_solve
            elif key == ord("o"):
                show_overlay = not show_overlay
            elif key == ord(" "):
                paused = not paused
            elif key == ord("s"):
                solver_board = detected_to_solver_board(detected_board)
                moves = solve(solver_board)
            elif key == ord("p"):
                lines = board_to_lines(detected_board)
                print("\nDetected board:")
                for line in lines:
                    print(line)
                print(f"Moves: {len(moves)}")
                for i, m in enumerate(moves[:30]):
                    action = "FLAG" if m.flag else "SAFE"
                    print(f"  {i + 1:02d}. {action} ({m.row},{m.col})")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
