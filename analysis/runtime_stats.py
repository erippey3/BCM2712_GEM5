from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional
import matplotlib.pyplot as plt


StatKey = Tuple[str, int, int]  
# (source, threads, problem_size)
# source ∈ {"hardware", "gem5"}


@dataclass
class RuntimeStats:
    name: str
    algorithm: str
    description: str

    # Main storage: (source, threads, problem_size) -> runtime
    runtimes: Dict[StatKey, float] = field(default_factory=dict)

    # Optional: store additional metrics later
    extra_stats: Dict[str, Dict[StatKey, float]] = field(default_factory=dict)

    # ----------------------------
    # Data insertion
    # ----------------------------
    def add_run(self, source: str, threads: int, problem_size: int, runtime: float):
        self.runtimes[(source, threads, problem_size)] = runtime

    def add_extra_stat(self, stat_name: str, source: str, threads: int, problem_size: int, value: float):
        if stat_name not in self.extra_stats:
            self.extra_stats[stat_name] = {}
        self.extra_stats[stat_name][(source, threads, problem_size)] = value

    # ----------------------------
    # Query helpers
    # ----------------------------
    def get_sources(self) -> List[str]:
        return sorted(set(k[0] for k in self.runtimes.keys()))

    def get_threads(self) -> List[int]:
        return sorted(set(k[1] for k in self.runtimes.keys()))

    def get_problem_sizes(self) -> List[int]:
        return sorted(set(k[2] for k in self.runtimes.keys()))

    def get_runtime(self, source: str, threads: int, problem_size: int) -> Optional[float]:
        return self.runtimes.get((source, threads, problem_size))

    # ----------------------------
    # Pretty print
    # ----------------------------
    def summary(self):
        print(f"\n=== {self.name} ({self.algorithm}) ===")
        print(self.description)
        print()

        for source in self.get_sources():
            print(f"[{source}]")
            for t in self.get_threads():
                row = []
                for p in self.get_problem_sizes():
                    val = self.get_runtime(source, t, p)
                    row.append(f"{val:.4f}" if val is not None else "----")
                print(f"t={t}: {row}")
            print()

    # ----------------------------
    # Plotting
    # ----------------------------
    def plot_vs_problem_size(self, threads: Optional[int] = None):
        plt.figure()

        thread_list = [threads] if threads is not None else self.get_threads()

        for source in self.get_sources():
            for t in thread_list:
                sizes = []
                runtimes = []

                for p in self.get_problem_sizes():
                    val = self.get_runtime(source, t, p)
                    if val is not None:
                        sizes.append(p)
                        runtimes.append(val)

                if sizes:
                    plt.plot(
                        sizes,
                        runtimes,
                        marker="o",
                        label=f"{source}, t={t}"
                    )

        plt.xlabel("Problem Size")
        plt.ylabel("Runtime (s)")

        if threads is None:
            plt.title(f"{self.name} - Runtime vs Problem Size, All Threads")
        else:
            plt.title(f"{self.name} - Runtime vs Problem Size, Threads={threads}")

        plt.legend()
        plt.grid(True)
        plt.savefig(f"{self.name}-runtime-v-problem-size.png", dpi=400)

    def plot_vs_threads(self, problem_size: Optional[int] = None):
        plt.figure()

        size_list = [problem_size] if problem_size is not None else self.get_problem_sizes()

        for source in self.get_sources():
            for p in size_list:
                threads = []
                runtimes = []

                for t in self.get_threads():
                    val = self.get_runtime(source, t, p)
                    if val is not None:
                        threads.append(t)
                        runtimes.append(val)

                if threads:
                    plt.plot(
                        threads,
                        runtimes,
                        marker="o",
                        label=f"{source}, size={p}"
                    )

        plt.xlabel("Threads")
        plt.ylabel("Runtime (s)")

        if problem_size is None:
            plt.title(f"{self.name} - Runtime vs Threads, All Problem Sizes")
        else:
            plt.title(f"{self.name} - Runtime vs Threads, Size={problem_size}")

        plt.legend()
        plt.grid(True)
        plt.savefig(f"{self.name}-runtime-v-threads.png", dpi=400)

    def plot_speedup(self, problem_size: int, baseline_threads: int = 1):
        plt.figure()

        for source in self.get_sources():
            threads = []
            speedups = []

            baseline = self.get_runtime(source, baseline_threads, problem_size)
            if baseline is None:
                continue

            for t in self.get_threads():
                val = self.get_runtime(source, t, problem_size)
                if val is not None:
                    threads.append(t)
                    speedups.append(baseline / val)

            plt.plot(threads, speedups, marker='o', label=source)

        plt.xlabel("Threads")
        plt.ylabel("Speedup")
        plt.title(f"{self.name} Speedup (Size={problem_size})")
        plt.legend()
        plt.grid(True)
        plt.show()