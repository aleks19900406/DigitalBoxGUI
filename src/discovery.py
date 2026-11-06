import socket
import paramiko
from PyQt6.QtCore import QObject, pyqtSignal
from concurrent.futures import ThreadPoolExecutor, as_completed


class NetworkScanner(QObject):
    found = pyqtSignal(str)         # emit each alive ip
    finished = pyqtSignal()         # emit when done
    progress = pyqtSignal(int, int) # (found_count, total_scanned)

    def __init__(self, subnet_prefix=None, timeout_ms=200, max_workers=60):
        super().__init__()
        self._running = True
        self.timeout_ms = timeout_ms
        self.max_workers = max_workers
        self.subnet_prefix = subnet_prefix or self._guess_subnet_prefix()

    def stop(self):
        self._running = False

    def _guess_subnet_prefix(self):
        # Try get local IP then take first 3 octets
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            parts = local_ip.split(".")
            if len(parts) == 4:
                return ".".join(parts[:3])
        except Exception:
            pass
        # fallback
        return "192.168.1"

    def _ping(self, ip):
        """Fast alive check via TCP port 22."""
        if not self._running:
            return False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)  # 500ms timeout
            sock.connect((ip, 22))  # SSH port
            sock.close()
            return True
        except:
            return False
        
    def run(self):
        """Main scan loop: ping .1..254 on the guessed subnet in parallel"""
        prefix = self.subnet_prefix
        ips = [f"{prefix}.{i}" for i in range(1, 255)]
        found_count = 0
        scanned = 0
        # use ThreadPoolExecutor for parallel pings
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = {ex.submit(self._ping, ip): ip for ip in ips}
            for fut in as_completed(futures):
                if not self._running:
                    break
                scanned += 1
                ip = futures[fut]
                try:
                    alive = fut.result()
                except Exception:
                    alive = False
                if alive:
                    found_count += 1
                    self.found.emit(ip)
                self.progress.emit(found_count, scanned)
        self.finished.emit()

def get_local_subnet_prefix():
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        parts = local_ip.split('.')
        if len(parts) == 4:
            return '.'.join(parts[:3])
    except Exception:
        pass
    return '192.168.1'

class ScanWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(str)

    def __init__(self, base_ip, start, end, password=''):
        super().__init__()
        self.base_ip = base_ip
        self.start = start
        self.end = end
        self.password = password
        self._running = True

    def stop(self):
        self._running = False

    def _scan_ip(self, ip):
        if not self._running:
            return None
        ssh = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                ip, username="pi", password=self.password, timeout=0.5,
                banner_timeout=2, auth_timeout=2,
                allow_agent=False, look_for_keys=False,
            )
            if not self._running:
                return None
            stdin, stdout, stderr = ssh.exec_command("hostname", timeout=2)
            name = stdout.read().decode().strip()
            return f"{name}@{ip}"
        except Exception:
            return None
        finally:
            if ssh is not None:
                ssh.close()

    def run(self):
        results = {}
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = {
                executor.submit(self._scan_ip, f"{self.base_ip}.{index}"): index
                for index in range(self.start, self.end + 1)
                if self._running
            }
            scanned = 0
            for future in as_completed(futures):
                if not self._running:
                    for pending in futures:
                        pending.cancel()
                    break
                result = future.result()
                if result is not None:
                    results[futures[future]] = result
                scanned += 1
                self.progress.emit(f"Scanning network... {scanned}/{len(futures)}")

        self.finished.emit([results[index] for index in sorted(results)])

def get_scan_config(ip):
    #print("🌐 Local IP detected:", ip)

    # ✅ LOCAL LAN
    if ip.startswith("192.168"):
        return "192.168.88", 10, 30

    # ✅ VPN
    if ip.startswith("10.0"):
        return "10.0.10", 100, 130

    # ✅ fallback
    return "192.168.1", 10, 30

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "192.168.88.1"
