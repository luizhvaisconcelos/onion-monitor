import requests

proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050',
}

try:
    r = requests.get('https://check.torproject.org/', proxies=proxies, timeout=10)
    if 'Congratulations. This browser is configured to use Tor' in r.text:
        print("✅ Conexão via Tor confirmada.")
    else:
        print("⚠️ Conectado, mas não via Tor.")
except Exception as e:
    print(f"❌ Erro na conexão via Tor: {e}")
