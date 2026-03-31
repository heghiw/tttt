from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import math
import statistics
import time

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.storage import TournamentState


@dataclass(frozen=True)
class Series:
    label: str
    x: list[int]
    y_ms: list[float]


def measure_ms(fn, repeats: int) -> float:
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        end = time.perf_counter()
        samples.append((end - start) * 1000.0)
    return statistics.median(samples)


def benchmark_assign_groups(ns: list[int], repeats: int) -> Series:
    y = []
    for n in ns:
        s = TournamentState()
        s.setup(serves_per_match=11, player_count=n, service_change_interval=3)
        y.append(measure_ms(s.assign_groups, repeats=repeats))
    return Series("assign_groups (expected ~O(n))", ns, y)


def benchmark_leaderboard_sort(ns: list[int], repeats: int) -> Series:
    y = []
    for n in ns:
        s = TournamentState()
        s.setup(serves_per_match=11, player_count=n, service_change_interval=3)
        for idx, p in enumerate(s.players):
            if idx % 2 == 0:
                p.eliminated = True
                p.total_score = (idx * 7) % 1000
        y.append(measure_ms(s.leaderboard, repeats=repeats))
    return Series("leaderboard sorting (expected ~O(n log n))", ns, y)


def benchmark_report_match(ns: list[int], repeats: int) -> Series:
    y = []
    for n in ns:
        s = TournamentState()
        s.setup(serves_per_match=11, player_count=n, service_change_interval=3)
        matches = s.assign_groups()
        mid = matches[0].id

        def report_once():
            s.report_match(mid, 11, 7)

        y.append(measure_ms(report_once, repeats=repeats))
    return Series("report_match (expected ~O(1))", ns, y)


def plot_theoretical(out_path: Path) -> None:
    n = np.linspace(1, 200, 200)
    o1 = np.ones_like(n)
    on = n
    onlogn = n * np.log2(n + 1e-9)
    on2 = n**2

    def norm(arr):
        return arr / np.max(arr)

    plt.figure(figsize=(10, 6), dpi=160)
    plt.plot(n, norm(o1), label="O(1)")
    plt.plot(n, norm(on), label="O(n)")
    plt.plot(n, norm(onlogn), label="O(n log n)")
    plt.plot(n, norm(on2), label="O(n^2)")
    plt.title("Theoretical time-complexity curves (normalized)")
    plt.xlabel("n (input size)")
    plt.ylabel("relative time (normalized)")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()


def plot_empirical(series: list[Series], out_path: Path) -> None:
    plt.figure(figsize=(10, 6), dpi=160)
    for s in series:
        plt.plot(s.x, s.y_ms, marker="o", linewidth=1.8, label=s.label)
    plt.title("Empirical runtime (median of repeats)")
    plt.xlabel("number of players (n)")
    plt.ylabel("time (ms)")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()


def main() -> None:
    repo_root = REPO_ROOT
    assets = repo_root / "report_assets"
    ns = [8, 16, 32, 64, 128, 256, 512, 1024]
    repeats = 15

    empirical = [
        benchmark_report_match(ns, repeats=repeats),
        benchmark_assign_groups(ns, repeats=repeats),
        benchmark_leaderboard_sort(ns, repeats=repeats),
    ]

    plot_theoretical(assets / "complexity_theoretical.png")
    plot_empirical(empirical, assets / "complexity_empirical.png")

    print(f"Wrote {assets / 'complexity_theoretical.png'}")
    print(f"Wrote {assets / 'complexity_empirical.png'}")


if __name__ == "__main__":
    main()
