#!/usr/bin/env python3
"""
Flexible matplotlib plotting for combined hardware/gem5 statistics CSVs.

Example inputs are rows like:
    algorithm,backend,iteration,problem_size,threads,ipc,runtime_sec,...

Typical usage:

  # One backend/iteration, one line, x = problem size
  python3 plot_combined_stats.py combined_stats.csv \
      --algorithm GEMM --run gem5:i2 \
      --x problem_size --y ipc --where threads=4 \
      --output gemm_gem5_i2_ipc_vs_size_t4.png

  # Multiple backends/iterations, one line per run
  python3 plot_combined_stats.py combined_stats.csv \
      --algorithm GEMM --run hardware --run gem5:i1 --run gem5:i2 \
      --x problem_size --y runtime_sec --where threads=4 \
      --series run --output gemm_runtime_compare_t4.png

  # One backend/iteration, one line per thread
  python3 plot_combined_stats.py combined_stats.csv \
      --algorithm FFT --run gem5:i2 \
      --x problem_size --y ipc --series threads \
      --output fft_gem5_i2_ipc_by_threads.png

  # One backend/iteration, one line per problem size
  python3 plot_combined_stats.py combined_stats.csv \
      --algorithm BFS --run hardware \
      --x threads --y runtime_sec --series problem_size \
      --output bfs_hw_runtime_by_size.png
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_DPI = 400
META_COLUMNS = {
    "algorithm",
    "backend",
    "iteration",
    "problem_size",
    "threads",
    "source_path",
}


def split_csv_values(values: Optional[Iterable[str]]) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for value in values:
        for part in str(value).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def parse_value_token(token: str):
    """Convert CLI string tokens into int/float when that is clearly safe."""
    token = token.strip()
    if re.fullmatch(r"[-+]?\d+", token):
        return int(token)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\d*\.\d+)([eE][-+]?\d+)?", token) or re.fullmatch(
        r"[-+]?\d+[eE][-+]?\d+", token
    ):
        return float(token)
    return token


def parse_where(expr: str) -> tuple[str, list[object]]:
    """Parse COL=VALUE[,VALUE...] filters."""
    if "=" not in expr:
        raise ValueError(f"--where expects COL=VALUE[,VALUE...], got: {expr!r}")
    col, raw_values = expr.split("=", 1)
    col = col.strip()
    values = [parse_value_token(v) for v in raw_values.split(",") if v.strip()]
    if not col or not values:
        raise ValueError(f"Bad --where filter: {expr!r}")
    return col, values


def make_run_label(backend: object, iteration: object) -> str:
    backend_s = str(backend)
    iteration_s = str(iteration)
    if backend_s == "hardware" or iteration_s in {"", "none", "nan", "None", "NaN"}:
        return backend_s
    return f"{backend_s}:{iteration_s}"


def parse_run_selector(selector: str) -> tuple[str, Optional[str]]:
    """
    Parse backend[:iteration].

    Examples:
      hardware     -> (hardware, None)
      hardware:none-> (hardware, none)
      gem5:i1      -> (gem5, i1)
      gem5:*       -> (gem5, *)
    """
    selector = selector.strip()
    if ":" not in selector:
        return selector, None
    backend, iteration = selector.split(":", 1)
    return backend.strip(), iteration.strip()


def filter_runs(df: pd.DataFrame, selectors: list[str]) -> pd.DataFrame:
    if not selectors:
        return df

    mask = pd.Series(False, index=df.index)
    for selector in selectors:
        backend, iteration = parse_run_selector(selector)
        this = df["backend"].astype(str).eq(backend)
        if iteration is not None and iteration != "*":
            this &= df["iteration"].astype(str).eq(iteration)
        mask |= this
    return df[mask]


def natural_key(value: object):
    """Sort numbers numerically and mixed strings naturally."""
    if pd.isna(value):
        return (2, "")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return (0, float(value))
    s = str(value)
    try:
        return (0, float(s))
    except ValueError:
        parts = re.split(r"(\d+)", s)
        key = tuple(int(p) if p.isdigit() else p.lower() for p in parts)
        return (1, key)


def coerce_numeric_if_possible(series: pd.Series) -> pd.Series:
    converted = pd.to_numeric(series, errors="coerce")
    # Use numeric only if every non-null value converted successfully.
    if converted.notna().sum() == series.notna().sum():
        return converted
    return series


def choose_auto_series(df: pd.DataFrame, x_col: str) -> str:
    """
    Pick a sensible default line grouping.

    Preference:
      1. run, if multiple backend/iteration combos are present
      2. threads/problem_size, whichever is not x, if multiple values exist
      3. algorithm, if multiple algorithms are present
      4. none
    """
    if "run" in df and df["run"].nunique(dropna=True) > 1:
        return "run"

    other = "threads" if x_col == "problem_size" else "problem_size"
    if other in df and df[other].nunique(dropna=True) > 1:
        return other

    if "algorithm" in df and df["algorithm"].nunique(dropna=True) > 1:
        return "algorithm"

    return "none"


def aggregate_for_plot(df: pd.DataFrame, x_col: str, y_col: str, series_col: str, agg: str) -> pd.DataFrame:
    group_cols = [x_col] if series_col == "none" else [series_col, x_col]

    if agg == "first":
        out = df.groupby(group_cols, dropna=False, as_index=False)[y_col].first()
    else:
        out = df.groupby(group_cols, dropna=False, as_index=False)[y_col].agg(agg)

    return out


def error_data(
    original: pd.DataFrame,
    grouped: pd.DataFrame,
    x_col: str,
    y_col: str,
    series_col: str,
    mode: str,
) -> dict[tuple[object, object], tuple[float, float]]:
    """
    Return asymmetric yerr keyed by (series, x). For mode=minmax/std.
    Values are (lower_error, upper_error).
    """
    if mode == "none":
        return {}

    group_cols = [x_col] if series_col == "none" else [series_col, x_col]
    stats = original.groupby(group_cols, dropna=False)[y_col]

    result: dict[tuple[object, object], tuple[float, float]] = {}
    for key, vals in stats:
        vals = pd.to_numeric(vals, errors="coerce").dropna()
        if vals.empty:
            continue
        if series_col == "none":
            series_value = "__single__"
            x_value = key
        else:
            series_value, x_value = key

        mean = vals.mean()
        if mode == "std":
            if len(vals) < 2:
                low = high = 0.0
            else:
                sd = vals.std(ddof=1)
                low = high = float(sd)
        elif mode == "minmax":
            low = float(mean - vals.min())
            high = float(vals.max() - mean)
        else:
            low = high = 0.0
        result[(series_value, x_value)] = (low, high)
    return result


def safe_filename_part(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.:-]+", "_", value.strip())
    return value.strip("_") or "plot"


def default_output_name(args: argparse.Namespace, series_col: str) -> str:
    alg = "all" if not args.algorithm else "-".join(split_csv_values(args.algorithm))
    runs = "allruns" if not args.run else "-".join(split_csv_values(args.run))
    name = f"{alg}_{runs}_{args.y}_vs_{args.x}_by_{series_col}.png"
    return safe_filename_part(name)


def apply_common_plot_formatting(ax, args: argparse.Namespace, x_col: str, y_col: str, series_col: str):
    ax.set_xlabel(args.xlabel or x_col)
    ax.set_ylabel(args.ylabel or y_col)

    if args.title:
        ax.set_title(args.title)
    else:
        title = f"{y_col} vs {x_col}"
        if series_col != "none":
            title += f" by {series_col}"
        ax.set_title(title)

    ax.grid(True, which="both", alpha=0.3)

    if args.logx:
        ax.set_xscale("log")
    if args.logy:
        ax.set_yscale("log")


def plot_lines(df: pd.DataFrame, args: argparse.Namespace) -> Path:
    x_col = args.x
    y_col = args.y

    if x_col not in df.columns:
        raise SystemExit(f"X column {x_col!r} was not found. Available columns include: {', '.join(df.columns[:30])}")
    if y_col not in df.columns:
        useful = [c for c in df.columns if c not in META_COLUMNS]
        raise SystemExit(f"Y/stat column {y_col!r} was not found. Useful stat columns include: {', '.join(useful[:40])}")

    df = df.copy()
    df["run"] = [make_run_label(b, it) for b, it in zip(df["backend"], df["iteration"])]
    df[x_col] = coerce_numeric_if_possible(df[x_col])
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
    df = df.dropna(subset=[x_col, y_col])

    if df.empty:
        raise SystemExit("No rows remain after filtering and dropping non-numeric/missing plot values.")

    series_col = args.series
    if series_col == "auto":
        series_col = choose_auto_series(df, x_col)
    if series_col != "none" and series_col not in df.columns:
        raise SystemExit(f"Series column {series_col!r} was not found in the CSV.")

    grouped = aggregate_for_plot(df, x_col, y_col, series_col, args.agg)
    grouped = grouped.sort_values(by=[series_col, x_col] if series_col != "none" else [x_col], key=lambda s: s.map(natural_key))

    yerr_lookup = error_data(df, grouped, x_col, y_col, series_col, args.error)

    fig, ax = plt.subplots(figsize=tuple(args.figsize))

    if series_col == "none":
        g = grouped.sort_values(x_col, key=lambda s: s.map(natural_key))
        if args.error == "none":
            ax.plot(g[x_col], g[y_col], marker=args.marker, linewidth=args.linewidth, label=None)
        else:
            lows, highs = [], []
            for x in g[x_col]:
                low, high = yerr_lookup.get(("__single__", x), (0.0, 0.0))
                lows.append(low)
                highs.append(high)
            ax.errorbar(g[x_col], g[y_col], yerr=[lows, highs], marker=args.marker, linewidth=args.linewidth, capsize=3)
    else:
        for series_value in sorted(grouped[series_col].dropna().unique(), key=natural_key):
            g = grouped[grouped[series_col] == series_value].sort_values(x_col, key=lambda s: s.map(natural_key))
            label = str(series_value)
            if args.error == "none":
                ax.plot(g[x_col], g[y_col], marker=args.marker, linewidth=args.linewidth, label=label)
            else:
                lows, highs = [], []
                for x in g[x_col]:
                    low, high = yerr_lookup.get((series_value, x), (0.0, 0.0))
                    lows.append(low)
                    highs.append(high)
                ax.errorbar(
                    g[x_col],
                    g[y_col],
                    yerr=[lows, highs],
                    marker=args.marker,
                    linewidth=args.linewidth,
                    capsize=3,
                    label=label,
                )
        ax.legend(title=series_col)

    # If x was not fully numeric, force ticks to the available values.
    if not pd.api.types.is_numeric_dtype(grouped[x_col]):
        values = sorted(grouped[x_col].dropna().unique(), key=natural_key)
        ax.set_xticks(range(len(values)))
        ax.set_xticklabels([str(v) for v in values], rotation=45, ha="right")

    apply_common_plot_formatting(ax, args, x_col, y_col, series_col)
    fig.tight_layout()

    output = Path(args.output or default_output_name(args, series_col))
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=args.dpi)
    plt.close(fig)
    return output


def load_and_filter(args: argparse.Namespace) -> pd.DataFrame:
    df = pd.read_csv(args.csv)

    required = {"algorithm", "backend", "iteration", "problem_size", "threads"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Input CSV is missing required metadata columns: {', '.join(missing)}")

    algorithms = split_csv_values(args.algorithm)
    if algorithms:
        df = df[df["algorithm"].astype(str).isin(algorithms)]

    runs = split_csv_values(args.run)
    df = filter_runs(df, runs)

    for expr in args.where or []:
        col, values = parse_where(expr)
        if col not in df.columns:
            raise SystemExit(f"--where column {col!r} was not found in the CSV.")
        # Compare as strings and parsed values to make filters robust for CSV dtype inference.
        raw = df[col]
        value_strings = {str(v) for v in values}
        mask = raw.isin(values) | raw.astype(str).isin(value_strings)
        df = df[mask]

    if args.drop_zero:
        if args.y in df.columns:
            y_numeric = pd.to_numeric(df[args.y], errors="coerce")
            df = df[y_numeric != 0]

    if df.empty:
        raise SystemExit("No rows matched the requested filters.")

    return df


def list_columns(args: argparse.Namespace) -> None:
    df = pd.read_csv(args.csv, nrows=10)
    numericish = []
    for col in df.columns:
        if col in META_COLUMNS:
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().any():
            numericish.append(col)

    print("Metadata columns:")
    for col in [c for c in df.columns if c in META_COLUMNS]:
        print(f"  {col}")

    print("\nNumeric/stat columns:")
    for col in numericish:
        print(f"  {col}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Flexible matplotlib plotting for combined hardware/gem5 stats CSVs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("csv", type=Path, help="Combined stats CSV produced by stats_aggregator.py")

    p.add_argument("--algorithm", action="append", help="Algorithm filter. Can repeat or comma-separate, e.g. GEMM,FFT")
    p.add_argument(
        "--run",
        action="append",
        help="Run/backend selector. Can repeat. Examples: hardware, hardware:none, gem5:i1, gem5:i2, gem5:*",
    )
    p.add_argument(
        "--where",
        action="append",
        help="Extra filter as COL=VALUE[,VALUE...]. Examples: threads=4, problem_size=256,512",
    )

    p.add_argument("--x", default="problem_size", choices=["problem_size", "threads"], help="X-axis column")
    p.add_argument("--y", required=False, help="Stat column to plot")
    p.add_argument(
        "--series",
        default="auto",
        choices=["auto", "none", "run", "backend", "iteration", "problem_size", "threads", "algorithm"],
        help="Column used to create separate lines",
    )

    p.add_argument("--agg", default="mean", choices=["mean", "median", "min", "max", "first"], help="Aggregation if filters leave multiple rows per x/series")
    p.add_argument("--error", default="none", choices=["none", "std", "minmax"], help="Optional error bars when multiple rows exist per x/series")
    p.add_argument("--drop-zero", action="store_true", help="Drop rows where the selected y stat is zero")

    p.add_argument("--title", help="Plot title")
    p.add_argument("--xlabel", help="X-axis label")
    p.add_argument("--ylabel", help="Y-axis label")
    p.add_argument("--output", "-o", help="Output image path. Defaults to an auto-generated PNG name")
    p.add_argument("--dpi", type=int, default=DEFAULT_DPI, help="DPI passed to plt.savefig")
    p.add_argument("--figsize", type=float, nargs=2, default=(8.0, 5.0), metavar=("W", "H"), help="Figure size in inches")
    p.add_argument("--marker", default="o", help="Matplotlib marker style")
    p.add_argument("--linewidth", type=float, default=2.0, help="Line width")
    p.add_argument("--logx", action="store_true", help="Use log scale for x-axis")
    p.add_argument("--logy", action="store_true", help="Use log scale for y-axis")

    p.add_argument("--list-stats", action="store_true", help="List available numeric/stat columns and exit")

    return p


def main() -> None:
    args = build_parser().parse_args()

    if args.list_stats:
        list_columns(args)
        return

    if not args.y:
        raise SystemExit("--y is required unless --list-stats is used.")

    df = load_and_filter(args)
    output = plot_lines(df, args)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
