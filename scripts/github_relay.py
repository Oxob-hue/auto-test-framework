"""临时本地 TLS 中继：绕过被 Steam++/Watt Toolkit 写坏的 hosts 解析。

背景：本机 hosts 中有一段工具写入的重定向，把 github.com / api.github.com /
raw.githubusercontent.com 等域名指向 127.0.0.1，导致 git push、抓取仓库文件全部失败。
真实 IP 可直连（DoH 解析验证 20.205.243.166:443 可建连）。

原理：监听 127.0.0.1:443，按 TLS ClientHello 中的 SNI 判断目标域名，
经 DoH（AliDNS / doh.pub）解析真实 IP 后转发原始 TLS 流量（证书仍由 GitHub 提供，SNI 不变）。

用法（临时，用完可 Ctrl+C 或结束进程）：
    python scripts/github_relay.py

注意：这是应急通道。根治办法是关闭 Steam++/Watt Toolkit 的加速（或清理其写入 hosts 的条目）。
"""
import select
import socket
import socketserver
import sys
import threading
import time

import requests

DEFAULT_HOST = "github.com"
_cache: dict = {}
_cache_lock = threading.Lock()

DOH_ENDPOINTS = (
    "https://223.5.5.5/resolve?name={host}&type=A",
    "https://doh.pub/dns-query?name={host}&type=A",
)

# 已知的 GitHub 地址族（按实测可达性排序；DoH 结果可能命中被限流的 IP，故放在其后兜底）
FALLBACK_IPS = {
    "github.com": ["140.82.112.3", "140.82.112.4", "140.82.113.3", "140.82.113.4",
                   "20.27.177.113", "20.29.134.23", "20.200.245.247", "20.205.243.166"],
    "api.github.com": ["20.205.243.168", "140.82.112.6", "140.82.113.6"],
    "codeload.github.com": ["140.82.112.9", "20.205.243.165"],
    "objects.githubusercontent.com": ["185.199.108.133", "185.199.109.133"],
    "raw.githubusercontent.com": ["185.199.108.133", "185.199.109.133"],
}
_fail_cache: dict = {}
_last_good: dict = {}
_bad_until: dict = {}
CONNECT_TIMEOUT = 3.0
BAD_COOLDOWN = 60.0


def resolve_all(host: str):
    """返回候选 IP 列表：上次可用 > 已知可达 > DoH 解析结果。"""
    ips = []

    def add(ip):
        if ip and ip not in ips:
            ips.append(ip)

    add(_last_good.get(host))
    for ip in FALLBACK_IPS.get(host, []):
        add(ip)
    with _cache_lock:
        add(_cache.get(host))
    for endpoint in DOH_ENDPOINTS:
        try:
            resp = requests.get(endpoint.format(host=host), timeout=6,
                                headers={"accept": "application/dns-json"})
            for a in resp.json().get("Answer", []):
                if a.get("type") == 1:
                    add(a["data"])
        except Exception as exc:  # noqa: BLE001
            print(f"[relay] DoH 失败 {endpoint.split('/')[2]}: {exc}", flush=True)
    if not ips:
        raise RuntimeError(f"无法解析域名: {host}")
    # 跳过冷却期内的坏 IP
    now = time.time()
    usable = [ip for ip in ips if _bad_until.get(ip, 0) < now]
    return usable or ips


def connect_upstream(host: str) -> socket.socket:
    """依次尝试候选 IP，返回首个可建连的 socket（失败 IP 进入冷却名单）。"""
    last_error = None
    for ip in resolve_all(host):
        try:
            sock = socket.create_connection((ip, 443), timeout=CONNECT_TIMEOUT)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            _bad_until.pop(ip, None)
            if _last_good.get(host) != ip:
                _last_good[host] = ip
                with _cache_lock:
                    _cache[host] = ip
                print(f"[relay] {host} -> {ip} (可用)", flush=True)
            return sock
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _bad_until[ip] = time.time() + BAD_COOLDOWN
            _fail_cache[ip] = _fail_cache.get(ip, 0) + 1
            print(f"[relay] {host} via {ip} 失败: {exc}", flush=True)
    raise RuntimeError(f"所有候选 IP 均不可达: {host} ({last_error})")


def resolve(host: str) -> str:
    """兼容旧调用：返回首选 IP。"""
    return resolve_all(host)[0]


def parse_sni(data: bytes):
    """从 TLS ClientHello 中解析 SNI 主机名（最小实现）。"""
    if len(data) < 5 or data[0] != 0x16:
        return None
    record_len = int.from_bytes(data[3:5], "big")
    hs = data[5:5 + record_len]
    if len(hs) < 4 or hs[0] != 0x01:
        return None
    i = 4 + 2 + 32                                   # handshake 头 + 版本 + random
    if i >= len(hs):
        return None
    i += 1 + hs[i]                                   # session id
    if i + 2 > len(hs):
        return None
    i += 2 + int.from_bytes(hs[i:i + 2], "big")      # cipher suites
    if i >= len(hs):
        return None
    i += 1 + hs[i]                                   # compression methods
    if i + 2 > len(hs):
        return None
    ext_end = min(len(hs), i + 2 + int.from_bytes(hs[i:i + 2], "big"))
    i += 2
    while i + 4 <= ext_end:
        etype = int.from_bytes(hs[i:i + 2], "big")
        elen = int.from_bytes(hs[i + 2:i + 4], "big")
        i += 4
        if etype == 0 and i + 5 <= ext_end:          # server_name
            nlen = int.from_bytes(hs[i + 3:i + 5], "big")
            return hs[i + 5:i + 5 + nlen].decode("ascii", "ignore")
        i += elen
    return None


class RelayHandler(socketserver.BaseRequestHandler):
    def handle(self):
        client = self.request
        client.settimeout(10)
        try:
            head = client.recv(4096)
            if not head:
                return
            host = parse_sni(head) or DEFAULT_HOST
            upstream = connect_upstream(host)
            upstream.sendall(head)
        except Exception as exc:  # noqa: BLE001
            print(f"[relay] 建立上游失败: {exc}", flush=True)
            return

        client.settimeout(None)
        upstream.settimeout(None)
        socks = [client, upstream]
        try:
            while True:
                readable, _, errored = select.select(socks, [], socks, 60)
                if errored or not readable:
                    break
                for src in readable:
                    data = src.recv(65536)
                    if not data:
                        return
                    (upstream if src is client else client).sendall(data)
        except Exception:  # noqa: BLE001
            pass
        finally:
            upstream.close()


class ThreadingServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> int:
    try:
        server = ThreadingServer(("127.0.0.1", 443), RelayHandler)
    except OSError as exc:
        print(f"[relay] 无法监听 127.0.0.1:443 -> {exc}")
        return 1
    print("[relay] 已启动：127.0.0.1:443 -> 按 SNI 转发到真实 GitHub（绕过 hosts 污染）", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[relay] 已停止", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
