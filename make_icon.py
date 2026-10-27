"""Generates icon.ico (PNG-compressed, multi-size). Replace icon.ico with your own to customise."""
import math
import struct
import sys

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QPolygonF

SIZES = [16, 32, 48, 64, 128, 256]


def render(size: int) -> bytes:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#14161a"))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(0, 0, size, size, size * 0.22, size * 0.22)
    pts = []
    for i in range(size + 1):
        x = i / size
        env = 0.5 * (math.sin(2 * math.pi * 7 * x) + math.sin(2 * math.pi * 8 * x))
        pts.append(QPointF(i, size / 2 - env * size * 0.32))
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor("#4a9cff"), max(1.5, size / 24)))
    p.drawPolyline(QPolygonF(pts))
    p.end()
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(data)


def main(out: str = "icon.ico") -> None:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)  # noqa: F841
    images = [(s, render(s)) for s in SIZES]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries, blobs = b"", b""
    for size, png in images:
        dim = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        blobs += png
        offset += len(png)
    with open(out, "wb") as f:
        f.write(header + entries + blobs)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
