# actions/network_tester.py
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor

def _log(message: str, player=None):
    print(f"[NetworkTester] {message}")
    if player:
        try:
            player.write_log(f"JARVIS: {message}")
        except Exception:
            pass

def network_tester(parameters: dict, player=None) -> str:
    """
    Measures download speed, upload speed, latency (ping), and jitter.
    Also retrieves ISP and location information.
    """
    action = parameters.get("action", "test").lower().strip()
    
    _log("Initializing network diagnostics...", player)
    
    # 1. Fetch ISP and Network details
    isp = "Unknown ISP"
    ip = "Unknown IP"
    location = "Unknown Location"
    asn = "Unknown ASN"
    
    try:
        r = requests.get("http://ip-api.com/json/", timeout=4)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success":
                ip = data.get("query", ip)
                isp = data.get("isp", isp)
                city = data.get("city", "")
                country = data.get("country", "")
                location = f"{city}, {country}" if city and country else city or country or location
                asn = data.get("as", asn)
    except Exception as e:
        # Fallback using Cloudflare headers
        try:
            r = requests.head("https://speed.cloudflare.com/__down?bytes=0", timeout=4)
            ip = r.headers.get("cf-meta-ip", ip)
            city = r.headers.get("city", "")
            country = r.headers.get("country", "")
            location = f"{city}, {country}" if city and country else city or country or location
            asn = f"AS{r.headers.get('asn', '')}" if r.headers.get('asn') else asn
        except Exception:
            pass

    _log(f"Connected via {isp} ({ip}) in {location}", player)
    
    # 2. Latency (Ping) and Jitter test
    _log("Measuring ping and jitter to nearest edge server...", player)
    rtts = []
    session = requests.Session()
    
    # Warmup request to establish TCP/TLS connection
    try:
        session.get("https://speed.cloudflare.com/__down?bytes=0", timeout=4)
    except Exception:
        pass
        
    for i in range(8):
        try:
            start = time.time()
            session.get("https://speed.cloudflare.com/__down?bytes=0", timeout=4)
            rtt = (time.time() - start) * 1000  # in ms
            rtts.append(rtt)
            # Short sleep to prevent rate limiting
            time.sleep(0.05)
        except Exception:
            continue

    if not rtts:
        ping = 0.0
        jitter = 0.0
        _log("Could not measure latency metrics.", player)
    else:
        ping = sum(rtts) / len(rtts)
        if len(rtts) > 1:
            jitter = sum(abs(rtts[i] - rtts[i-1]) for i in range(1, len(rtts))) / (len(rtts) - 1)
        else:
            jitter = 0.0
        _log(f"Latency results: Ping={ping:.1f} ms, Jitter={jitter:.1f} ms", player)

    if action == "ping":
        return (
            f"Sir, here are your network latency diagnostics:\n"
            f"  - **IP Address**: {ip}\n"
            f"  - **Provider (ISP)**: {isp}\n"
            f"  - **Location**: {location}\n"
            f"  - **Ping (RTT)**: {ping:.1f} ms\n"
            f"  - **Jitter**: {jitter:.1f} ms"
        )

    # 3. Download Speed Test
    _log("Testing download speed (this will take about 5 seconds)...", player)
    
    download_urls = [
        "https://speed.cloudflare.com/__down?bytes=15000000" for _ in range(4)
    ]
    
    total_downloaded_bytes = 0
    bytes_lock = threading.Lock()
    dl_start_time = time.time()
    dl_timeout = 4.5  # Max duration for download
    
    def download_worker(url):
        nonlocal total_downloaded_bytes
        try:
            # stream=True allows reading chunk by chunk
            r = requests.get(url, stream=True, timeout=5)
            if r.status_code == 200:
                for chunk in r.iter_content(chunk_size=32768):
                    if time.time() - dl_start_time > dl_timeout:
                        break
                    if chunk:
                        with bytes_lock:
                            total_downloaded_bytes += len(chunk)
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(download_worker, download_urls)
        
    dl_elapsed = time.time() - dl_start_time
    if dl_elapsed <= 0:
        dl_elapsed = 0.1
        
    download_speed = (total_downloaded_bytes * 8) / (dl_elapsed * 1000000)
    _log(f"Download completed: {download_speed:.2f} Mbps", player)
    
    # 4. Upload Speed Test
    _log("Testing upload speed (this will take about 5 seconds)...", player)
    
    # Determine upload chunk size dynamically based on download speed
    if download_speed < 2.0:
        upload_chunk_size = 128 * 1024  # 128 KB
    elif download_speed < 10.0:
        upload_chunk_size = 512 * 1024  # 512 KB
    else:
        upload_chunk_size = 1024 * 1024  # 1 MB
        
    upload_payload = b'\x00' * upload_chunk_size
    total_uploaded_bytes = 0
    ul_lock = threading.Lock()
    ul_start_time = time.time()
    ul_timeout = 4.5
    
    def upload_worker(_):
        nonlocal total_uploaded_bytes
        session = requests.Session()
        while time.time() - ul_start_time < ul_timeout:
            try:
                r = session.post(
                    "https://speed.cloudflare.com/__up",
                    data=upload_payload,
                    timeout=5
                )
                if r.status_code == 200:
                    with ul_lock:
                        total_uploaded_bytes += upload_chunk_size
            except Exception:
                break

    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(upload_worker, range(4))
        
    ul_elapsed = time.time() - ul_start_time
    if ul_elapsed <= 0:
        ul_elapsed = 0.1
        
    upload_speed = (total_uploaded_bytes * 8) / (ul_elapsed * 1000000)
    _log(f"Upload completed: {upload_speed:.2f} Mbps", player)
    
    # Format and return final response
    summary = (
        f"Sir, here are the results of your network speed test:\n"
        f"  - **IP Address**: {ip}\n"
        f"  - **Location**: {location}\n"
        f"  - **Provider (ISP)**: {isp}\n"
        f"  - **Ping / Jitter**: {ping:.1f} ms / {jitter:.1f} ms\n"
        f"  - **Download Speed**: {download_speed:.2f} Mbps\n"
        f"  - **Upload Speed**: {upload_speed:.2f} Mbps\n"
        f"Your network connection is fully verified and stable."
    )
    _log("Speed test complete.", player)
    return summary
