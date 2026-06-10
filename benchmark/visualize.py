"""
gRPC vs REST 벤치마크 결과 시각화
run_bench.py 실행 후 측정 데이터를 받아 차트 4개 생성
실행: python visualize.py [--n 100]
"""
import sys
import os
import argparse
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
import matplotlib.patches as mpatches
import numpy as np

import grpc
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Backend", "product"))
import product_pb2
import product_pb2_grpc

REST_BASE = "http://localhost:50054"
GRPC_ADDR = "localhost:50051"
GRPC_MEM  = "localhost:50055"

BLUE   = "#4C8FE2"
ORANGE = "#F28C38"


def _bench_grpc(addr, n):
    ch    = grpc.insecure_channel(addr)
    stub  = product_pb2_grpc.ProductServiceStub(ch)
    times, sizes = [], []
    for _ in range(n):
        import time
        t0  = time.perf_counter()
        res = stub.ListProducts(product_pb2.ListProductsRequest(target="best", page=1, page_size=20))
        times.append((time.perf_counter() - t0) * 1000)
        sizes.append(res.ByteSize())
    ch.close()
    return times, sizes


def _bench_rest(url, n):
    import time
    client = httpx.Client(timeout=10.0)
    times, sizes = [], []
    for _ in range(n):
        t0  = time.perf_counter()
        res = client.get(url)
        times.append((time.perf_counter() - t0) * 1000)
        sizes.append(len(res.content))
    client.close()
    return times, sizes


def _bar_label(ax, bars, fmt="{:.2f}"):
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h * 1.03,
            fmt.format(h),
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )


def _rolling_mean(data, window=10):
    result = []
    for i in range(len(data)):
        start = max(0, i - window + 1)
        result.append(statistics.mean(data[start:i+1]))
    return result


def draw_chart(g1_t, r1_t, g1_s, r1_s, g2_t, r2_t, g2_s, r2_s, n, out="benchmark_result.png"):
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(f"gRPC vs REST Benchmark  (n={n})", fontsize=15, fontweight="bold")

    xs = list(range(1, n + 1))

    # ── 차트 1: 시나리오 1 요청별 응답 시간 ──────────────
    ax = axes[0][0]
    ax.plot(xs, g1_t, color=BLUE,   alpha=0.25, linewidth=0.8)
    ax.plot(xs, r1_t, color=ORANGE, alpha=0.25, linewidth=0.8)
    ax.plot(xs, _rolling_mean(g1_t), color=BLUE,   linewidth=2.0, label=f"gRPC  (중앙값 {statistics.median(g1_t):.2f}ms)")
    ax.plot(xs, _rolling_mean(r1_t), color=ORANGE, linewidth=2.0, label=f"REST  (중앙값 {statistics.median(r1_t):.2f}ms)")
    ax.set_title("시나리오 1 — DB 포함 응답 시간", fontweight="bold")
    ax.set_xlabel("요청 번호")
    ax.set_ylabel("응답 시간 (ms)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    # 이상치 제외한 y축 범위
    upper = sorted(r1_t)[int(n * 0.95)]
    ax.set_ylim(0, upper * 1.3)

    # ── 차트 2: 시나리오 2 요청별 응답 시간 ──────────────
    ax = axes[0][1]
    ax.plot(xs, g2_t, color=BLUE,   alpha=0.25, linewidth=0.8)
    ax.plot(xs, r2_t, color=ORANGE, alpha=0.25, linewidth=0.8)
    ax.plot(xs, _rolling_mean(g2_t), color=BLUE,   linewidth=2.0, label=f"gRPC  (중앙값 {statistics.median(g2_t):.2f}ms)")
    ax.plot(xs, _rolling_mean(r2_t), color=ORANGE, linewidth=2.0, label=f"REST  (중앙값 {statistics.median(r2_t):.2f}ms)")
    ax.set_title("시나리오 2 — In-memory 응답 시간", fontweight="bold")
    ax.set_xlabel("요청 번호")
    ax.set_ylabel("응답 시간 (ms)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    upper = sorted(r2_t)[int(n * 0.95)]
    ax.set_ylim(0, upper * 1.3)

    # ── 차트 3: 누적 평균 수렴 그래프 ────────────────────
    ax = axes[1][0]
    def cumulative_mean(data):
        return [statistics.mean(data[:i+1]) for i in range(len(data))]
    ax.plot(xs, cumulative_mean(g1_t), color=BLUE,              linewidth=2.0, label="gRPC DB")
    ax.plot(xs, cumulative_mean(r1_t), color=ORANGE,            linewidth=2.0, label="REST DB")
    ax.plot(xs, cumulative_mean(g2_t), color=BLUE,   linestyle="--", linewidth=1.5, label="gRPC Mem")
    ax.plot(xs, cumulative_mean(r2_t), color=ORANGE, linestyle="--", linewidth=1.5, label="REST Mem")
    ax.set_title("누적 평균 응답 시간 수렴", fontweight="bold")
    ax.set_xlabel("요청 번호")
    ax.set_ylabel("누적 평균 (ms)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

    # ── 차트 4: 페이로드 크기 비교 ───────────────────────
    ax = axes[1][1]
    series = [
        (r1_s, ORANGE, "-",  f"REST DB   ({statistics.mean(r1_s)/1024:.1f} KB)"),
        (r2_s, ORANGE, "--", f"REST Mem  ({statistics.mean(r2_s)/1024:.1f} KB)"),
        (g1_s, BLUE,   "-",  f"gRPC DB   ({statistics.mean(g1_s)/1024:.1f} KB)"),
        (g2_s, BLUE,   "--", f"gRPC Mem  ({statistics.mean(g2_s)/1024:.1f} KB)"),
    ]
    for data, color, ls, label in series:
        kb = [s / 1024 for s in data]
        ax.plot(xs, kb, color=color, linestyle=ls, linewidth=1.5, alpha=0.5)
        ax.axhline(y=statistics.mean(kb), color=color, linestyle=ls,
                   linewidth=2.2, label=label)

    ax.set_title("요청별 페이로드 크기", fontweight="bold")
    ax.set_xlabel("요청 번호")
    ax.set_ylabel("크기 (KB)")
    ax.set_ylim(0, statistics.mean(r1_s) / 1024 * 1.4)
    ax.legend(fontsize=9, loc="center right")
    ax.grid(alpha=0.3)

    fig.tight_layout()
    out_path = os.path.join(os.path.dirname(__file__), out)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\n차트 저장 완료: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    n = parser.parse_args().n

    print(f"측정 중... ({n}회 반복)")

    print("  gRPC DB...")
    g1_t, g1_s = _bench_grpc(GRPC_ADDR, n)
    print("  REST DB...")
    r1_t, r1_s = _bench_rest(f"{REST_BASE}/products?target=best&page=1&page_size=20", n)
    print("  gRPC In-memory...")
    g2_t, g2_s = _bench_grpc(GRPC_MEM, n)
    print("  REST In-memory...")
    r2_t, r2_s = _bench_rest(f"{REST_BASE}/products/inmemory", n)

    draw_chart(g1_t, r1_t, g1_s, r1_s, g2_t, r2_t, g2_s, r2_s, n)


if __name__ == "__main__":
    main()
