"""
gRPC vs REST 벤치마크

시나리오 1 - DB 포함
  gRPC: product gRPC 서버 (localhost:50051) 직접 호출
  REST: FastAPI REST 서버 (localhost:50054) 호출 — 동일 MongoDB 쿼리

시나리오 2 - In-memory (순수 직렬화/전송 속도)
  gRPC: in-memory gRPC 서버 (localhost:50055)
  REST: /products/inmemory 엔드포인트

실행: python run_bench.py [--n 100]
"""
import sys
import os
import time
import statistics
import argparse

import httpx
import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Backend", "product"))

import product_pb2
import product_pb2_grpc

REST_BASE  = "http://localhost:50054"
GRPC_ADDR  = "localhost:50051"
GRPC_MEM   = "localhost:50055"


def _bench_grpc(addr: str, n: int) -> tuple[list, list]:
    channel = grpc.insecure_channel(addr)
    stub    = product_pb2_grpc.ProductServiceStub(channel)
    times, sizes = [], []
    for _ in range(n):
        t0  = time.perf_counter()
        res = stub.ListProducts(product_pb2.ListProductsRequest(target="best", page=1, page_size=20))
        times.append((time.perf_counter() - t0) * 1000)
        sizes.append(res.ByteSize())
    channel.close()
    return times, sizes


def _bench_rest(url: str, n: int) -> tuple[list, list]:
    client = httpx.Client(timeout=10.0)
    times, sizes = [], []
    for _ in range(n):
        t0  = time.perf_counter()
        res = client.get(url)
        times.append((time.perf_counter() - t0) * 1000)
        sizes.append(len(res.content))
    client.close()
    return times, sizes


def _print(label: str, times: list, sizes: list) -> None:
    avg  = statistics.mean(times)
    med  = statistics.median(times)
    tps  = len(times) / (sum(times) / 1000)
    size = statistics.mean(sizes)
    print(f"  {'평균 응답':<10} {avg:>8.2f} ms")
    print(f"  {'중앙값':<10} {med:>8.2f} ms")
    print(f"  {'최소/최대':<10} {min(times):>6.2f} / {max(times):.2f} ms")
    print(f"  {'처리량':<10} {tps:>8.0f} req/s")
    print(f"  {'페이로드':<10} {size:>8,.0f} bytes")


def _compare(grpc_times: list, rest_times: list) -> None:
    g = statistics.mean(grpc_times)
    r = statistics.mean(rest_times)
    if g < r:
        print(f"\n  ➜ gRPC가 REST 대비 {r/g:.1f}배 빠름  |  페이로드 절감은 위 bytes 비교 참고")
    else:
        print(f"\n  ➜ REST가 gRPC 대비 {g/r:.1f}배 빠름  (DB IO 병목 구간에서는 차이 미미할 수 있음)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100, help="반복 횟수 (기본 100)")
    n = parser.parse_args().n

    sep = "=" * 52

    print(f"\n{sep}")
    print(f"  gRPC vs REST 벤치마크  ({n}회 반복)")
    print(sep)

    # ── 시나리오 1: DB 포함 ──────────────────────────────
    print(f"\n[시나리오 1]  실제 MongoDB 쿼리 포함")
    print(f"\n  gRPC  (product 서버 직접, localhost:50051)")
    try:
        g1_t, g1_s = _bench_grpc(GRPC_ADDR, n)
        _print("gRPC DB", g1_t, g1_s)
    except Exception as e:
        print(f"  [ERROR] gRPC 연결 실패: {e}")
        g1_t = None

    print(f"\n  REST  (FastAPI + MongoDB, localhost:50054/products)")
    try:
        r1_t, r1_s = _bench_rest(f"{REST_BASE}/products?target=best&page=1&page_size=20", n)
        _print("REST DB", r1_t, r1_s)
    except Exception as e:
        print(f"  [ERROR] REST 연결 실패: {e}")
        r1_t = None

    if g1_t and r1_t:
        _compare(g1_t, r1_t)

    # ── 시나리오 2: In-memory ────────────────────────────
    print(f"\n{'-'*52}")
    print(f"\n[시나리오 2]  In-memory 고정 데이터 (순수 직렬화/전송)")
    print(f"\n  gRPC  (in-memory 서버, localhost:50055)")
    try:
        g2_t, g2_s = _bench_grpc(GRPC_MEM, n)
        _print("gRPC Memory", g2_t, g2_s)
    except Exception as e:
        print(f"  [ERROR] gRPC in-memory 서버 연결 실패: {e}")
        g2_t = None

    print(f"\n  REST  (in-memory, localhost:50054/products/inmemory)")
    try:
        r2_t, r2_s = _bench_rest(f"{REST_BASE}/products/inmemory", n)
        _print("REST Memory", r2_t, r2_s)
    except Exception as e:
        print(f"  [ERROR] REST 연결 실패: {e}")
        r2_t = None

    if g2_t and r2_t:
        _compare(g2_t, r2_t)

    print(f"\n{sep}\n")


if __name__ == "__main__":
    main()
