"""
gRPC vs REST 벤치마크 클라이언트

실행 전 proto 컴파일 필요:
  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. product.proto

실행:
  python run_bench.py [--n 100]

환경변수:
  GRPC_SERVER  (기본: grpc-server-svc:50051)
  REST_SERVER  (기본: http://rest-server-svc:8000)
"""
import os
import sys
import time
import argparse
import statistics

import urllib.request
import json
import grpc
import product_pb2
import product_pb2_grpc

GRPC_ADDR = os.environ.get("GRPC_SERVER", "grpc-server-svc:50051")
REST_BASE  = os.environ.get("REST_SERVER", "http://rest-server-svc:8000")


def bench_grpc(n: int):
    channel = grpc.insecure_channel(GRPC_ADDR)
    stub    = product_pb2_grpc.ProductServiceStub(channel)
    times, sizes = [], []
    for _ in range(n):
        t0  = time.perf_counter()
        res = stub.ListProducts(product_pb2.ListProductsRequest(target="best", page=1, page_size=20))
        times.append((time.perf_counter() - t0) * 1000)
        sizes.append(res.ByteSize())
    channel.close()
    return times, sizes


def bench_rest(n: int):
    url = f"{REST_BASE}/products?target=best&page=1&page_size=20"
    times, sizes = [], []
    for _ in range(n):
        t0  = time.perf_counter()
        with urllib.request.urlopen(url, timeout=10) as res:
            body = res.read()
        times.append((time.perf_counter() - t0) * 1000)
        sizes.append(len(body))
    return times, sizes


def print_result(label: str, times: list, sizes: list):
    print(f"\n  [{label}]")
    print(f"  평균    : {statistics.mean(times):.2f} ms")
    print(f"  중앙값  : {statistics.median(times):.2f} ms")
    print(f"  최소/최대: {min(times):.2f} / {max(times):.2f} ms")
    print(f"  처리량  : {len(times) / (sum(times) / 1000):.0f} req/s")
    print(f"  페이로드: {statistics.mean(sizes):,.0f} bytes")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    n = parser.parse_args().n

    sep = "=" * 52
    print(f"\n{sep}")
    print(f"  gRPC vs REST 벤치마크  ({n}회 반복)")
    print(f"  gRPC: {GRPC_ADDR}")
    print(f"  REST: {REST_BASE}")
    print(sep)

    print("\n측정 중...")

    try:
        g_times, g_sizes = bench_grpc(n)
        print_result("gRPC", g_times, g_sizes)
    except Exception as e:
        print(f"  [ERROR] gRPC 실패: {e}")
        sys.exit(1)

    try:
        r_times, r_sizes = bench_rest(n)
        print_result("REST", r_times, r_sizes)
    except Exception as e:
        print(f"  [ERROR] REST 실패: {e}")
        sys.exit(1)

    g_med = statistics.median(g_times)
    r_med = statistics.median(r_times)
    g_size = statistics.mean(g_sizes)
    r_size = statistics.mean(r_sizes)

    print(f"\n{'-' * 52}")
    if g_med < r_med:
        print(f"  gRPC가 REST 대비 {r_med / g_med:.1f}배 빠름 (중앙값 기준)")
    else:
        print(f"  REST가 gRPC 대비 {g_med / r_med:.1f}배 빠름 (중앙값 기준)")
    print(f"  페이로드: gRPC {g_size:,.0f}B  vs  REST {r_size:,.0f}B  ({r_size / g_size:.1f}배 차이)")
    print(f"{sep}\n")


if __name__ == "__main__":
    main()
