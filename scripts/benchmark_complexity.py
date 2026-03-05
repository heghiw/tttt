"""
Generate small empirical timing graphs for the report.

This script measures how runtime changes as the number of players grows and writes:
- report_assets/benchmark_results.csv
- report_assets/complexity_setup.svg
- report_assets/complexity_assign_groups.svg
- report_assets/complexity_leaderboard.svg

No third-party plotting libraries are required (pure SVG output).
"""

from __future__ import annotations

import csv
import math
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from storage import TournamentState


@dataclass(frozen=True)
class BenchRow:
    players: int
    setup_ms: float
    assign_groups_ms: float
    leaderboard_ms: float


def _median_ms(samples_s: list[float]) -> float:
    return statistics.median(samples_s) * 1000.0


def _time_call(fn, repeats: int) -> float:
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return _median_ms(samples)


def _bench(players: int, repeats: int, seed: int) -> BenchRow:
    random.seed(seed)

    def setup_once() -> TournamentState:
        s = TournamentState()
        s.setup(serves_per_match=11, player_count=players, service_change_interval=3)
        return s

    setup_ms = _time_call(lambda: setup_once(), repeats=repeats)

    state = setup_once()
    assign_groups_ms = _time_call(lambda: state.assign_groups(), repeats=repeats)

    # Prepare a state with ~half eliminated to exercise filter + sort (k log k).
    state_for_lb = setup_once()
    k = players // 2
    for i, p in enumerate(state_for_lb.players):
        if i < k:
            p.eliminated = True
            p.total_score = random.randint(0, 500)
    leaderboard_ms = _time_call(lambda: state_for_lb.leaderboard(), repeats=repeats)

    return BenchRow(
        players=players,
        setup_ms=setup_ms,
        assign_groups_ms=assign_groups_ms,
        leaderboard_ms=leaderboard_ms,
    )


def _svg_line_chart(
    title: str,
    x_label: str,
    y_label: str,
    points: list[tuple[float, float]],
    out_path: Path,
) -> None:
    width, height = 900, 520
    pad_left, pad_right, pad_top, pad_bottom = 80, 30, 60, 70
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = 0.0, max(ys) * 1.1 if max(ys) > 0 else 1.0

    def sx(x: float) -> float:
        if max_x == min_x:
            return pad_left + plot_w / 2
        return pad_left + (x - min_x) / (max_x - min_x) * plot_w

    def sy(y: float) -> float:
        return pad_top + (1.0 - (y - min_y) / (max_y - min_y)) * plot_h

    # Simple tick selection.
    y_ticks = 6
    y_step = max_y / (y_ticks - 1)
    x_ticks = min(8, len(points))
    x_step = (max_x - min_x) / (x_ticks - 1) if x_ticks > 1 else 1

    def esc(t: str) -> str:
        return (
            t.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    poly = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in points)

    svg_lines: list[str] = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')
    svg_lines.append('<rect width="100%" height="100%" fill="white"/>')

    # Title
    svg_lines.append(
        f'<text x="{width/2:.1f}" y="28" text-anchor="middle" font-size="18" font-family="Segoe UI, Arial">'
        f"{esc(title)}</text>"
    )

    # Axes
    x0, y0 = pad_left, pad_top + plot_h
    x1, y1 = pad_left + plot_w, pad_top
    svg_lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#111" stroke-width="2"/>')
    svg_lines.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#111" stroke-width="2"/>')

    # Grid + ticks (Y)
    for i in range(y_ticks):
        y_val = i * y_step
        yy = sy(y_val)
        svg_lines.append(f'<line x1="{x0}" y1="{yy:.2f}" x2="{x1}" y2="{yy:.2f}" stroke="#eee"/>')
        svg_lines.append(
            f'<text x="{x0-10}" y="{yy+4:.2f}" text-anchor="end" font-size="12" '
            f'font-family="Segoe UI, Arial" fill="#333">{y_val:.2f}</text>'
        )

    # Grid + ticks (X)
    for i in range(x_ticks):
        x_val = min_x + i * x_step
        xx = sx(x_val)
        svg_lines.append(f'<line x1="{xx:.2f}" y1="{y0}" x2="{xx:.2f}" y2="{y1}" stroke="#f4f4f4"/>')
        svg_lines.append(
            f'<text x="{xx:.2f}" y="{y0+18}" text-anchor="middle" font-size="12" '
            f'font-family="Segoe UI, Arial" fill="#333">{int(round(x_val))}</text>'
        )

    # Labels
    svg_lines.append(
        f'<text x="{width/2:.1f}" y="{height-18}" text-anchor="middle" font-size="14" '
        f'font-family="Segoe UI, Arial">{esc(x_label)}</text>'
    )
    # Rotated Y label
    svg_lines.append(
        f'<text x="18" y="{height/2:.1f}" text-anchor="middle" font-size="14" '
        f'font-family="Segoe UI, Arial" transform="rotate(-90 18 {height/2:.1f})">{esc(y_label)}</text>'
    )

    # Line
    svg_lines.append(f'<polyline fill="none" stroke="#0b5" stroke-width="3" points="{poly}"/>')
    for x, y in points:
        svg_lines.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="4" fill="#0b5"/>')

    svg_lines.append("</svg>")
    out_path.write_text("\n".join(svg_lines), encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "report_assets"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Keep the benchmark small and fast.
    player_sizes = [8, 16, 32, 64, 96, 128, 160, 200]
    repeats = 25
    seed = 1337

    rows: list[BenchRow] = []
    for n in player_sizes:
        rows.append(_bench(players=n, repeats=repeats, seed=seed + n))

    # CSV
    csv_path = out_dir / "benchmark_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["players", "setup_ms_median", "assign_groups_ms_median", "leaderboard_ms_median"])
        for r in rows:
            w.writerow([r.players, f"{r.setup_ms:.6f}", f"{r.assign_groups_ms:.6f}", f"{r.leaderboard_ms:.6f}"])

    # SVG charts
    _svg_line_chart(
        title="Setup runtime vs number of players (median of repeats)",
        x_label="Players",
        y_label="Milliseconds (ms)",
        points=[(r.players, r.setup_ms) for r in rows],
        out_path=out_dir / "complexity_setup.svg",
    )
    _svg_line_chart(
        title="Round generation runtime vs number of players (median of repeats)",
        x_label="Players",
        y_label="Milliseconds (ms)",
        points=[(r.players, r.assign_groups_ms) for r in rows],
        out_path=out_dir / "complexity_assign_groups.svg",
    )
    _svg_line_chart(
        title="Leaderboard runtime vs number of players (median of repeats)",
        x_label="Players",
        y_label="Milliseconds (ms)",
        points=[(r.players, r.leaderboard_ms) for r in rows],
        out_path=out_dir / "complexity_leaderboard.svg",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
