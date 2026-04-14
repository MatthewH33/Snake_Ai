from __future__ import annotations

import tkinter as tk

from PIL import Image, ImageGrab, ImageTk


LEFT = 300
RIGHT = 700
TOP = 315
BOTTOM = 622

WIDTH = RIGHT - LEFT
HEIGHT = BOTTOM - TOP

REFRESH_MS = 50
NUDGE_PX = 20
PREVIEW_SCALE = 0.5


def main() -> None:
    root = tk.Tk()
    # Keep Tk in 1:1 pixel mode; we scale the preview explicitly below.
    root.tk.call("tk", "scaling", 1.0)
    root.title("Live Capture")
    root.geometry(f"{int(WIDTH * PREVIEW_SCALE)}x{int(HEIGHT * PREVIEW_SCALE)}")
    root.resizable(False, False)

    label = tk.Label(root)
    label.pack(fill="both", expand=True)
    box = {
        "left": LEFT,
        "right": RIGHT,
        "top": TOP,
        "bottom": BOTTOM,
    }

    def move_box(dx: int, dy: int) -> None:
        box["left"] += dx
        box["right"] += dx
        box["top"] += dy
        box["bottom"] += dy

    def resize_box(dw: int, dh: int) -> None:
        # Grow/shrink from right and bottom edges while keeping top-left anchored.
        new_width = (box["right"] - box["left"]) + dw
        new_height = (box["bottom"] - box["top"]) + dh
        if new_width < 20 or new_height < 20:
            return
        box["right"] = box["left"] + new_width
        box["bottom"] = box["top"] + new_height
        root.geometry(
            f"{int(new_width * PREVIEW_SCALE)}x{int(new_height * PREVIEW_SCALE)}"
        )

    def update_frame() -> None:
        frame = ImageGrab.grab(
            bbox=(box["left"], box["top"], box["right"], box["bottom"]),
            all_screens=True,
        )
        if PREVIEW_SCALE != 1.0:
            frame = frame.resize(
                (int(frame.width * PREVIEW_SCALE), int(frame.height * PREVIEW_SCALE)),
                Image.Resampling.NEAREST,
            )
        photo = ImageTk.PhotoImage(frame)
        label.configure(image=photo)
        label.image = photo
        width = box["right"] - box["left"]
        height = box["bottom"] - box["top"]
        root.title(
            (
                f"Live Capture | x: {box['left']}..{box['right']} "
                f"y: {box['top']}..{box['bottom']} "
                f"size: {width}x{height}"
            )
        )
        root.after(REFRESH_MS, update_frame)

    root.bind("<Left>", lambda _e: move_box(-NUDGE_PX, 0))
    root.bind("<Right>", lambda _e: move_box(NUDGE_PX, 0))
    root.bind("<Up>", lambda _e: move_box(0, -NUDGE_PX))
    root.bind("<Down>", lambda _e: move_box(0, NUDGE_PX))
    root.bind("<Shift-Left>", lambda _e: move_box(-1, 0))
    root.bind("<Shift-Right>", lambda _e: move_box(1, 0))
    root.bind("<Shift-Up>", lambda _e: move_box(0, -1))
    root.bind("<Shift-Down>", lambda _e: move_box(0, 1))
    root.bind("a", lambda _e: resize_box(-NUDGE_PX, 0))
    root.bind("d", lambda _e: resize_box(NUDGE_PX, 0))
    root.bind("w", lambda _e: resize_box(0, -NUDGE_PX))
    root.bind("s", lambda _e: resize_box(0, NUDGE_PX))
    root.bind("A", lambda _e: resize_box(-1, 0))
    root.bind("D", lambda _e: resize_box(1, 0))
    root.bind("W", lambda _e: resize_box(0, -1))
    root.bind("S", lambda _e: resize_box(0, 1))
    root.bind("<Escape>", lambda _e: root.destroy())
    root.focus_force()

    update_frame()
    root.mainloop()


if __name__ == "__main__":
    main()
