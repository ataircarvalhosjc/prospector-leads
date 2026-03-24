"""
Módulo de Qualificação - Analisa o código-fonte dos sites para detectar
pixels de marketing (Meta Pixel, Google Ads/Analytics).
"""

import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Padrões para detectar Meta Pixel (Facebook Pixel)
META_PIXEL_PATTERNS = [
    re.compile(r"fbq\s*\(\s*['\"]init['\"]", re.IGNORECASE),
    re.compile(r"connect\.facebook\.net.*fbevents\.js", re.IGNORECASE),
    re.compile(r"facebook\.com/tr\?", re.IGNORECASE),
    re.compile(r"Meta\s*Pixel", re.IGNORECASE),
]

# Padrões para detectar Google Analytics
GOOGLE_ANALYTICS_PATTERNS = [
    re.compile(r"gtag\s*\(\s*['\"]config['\"].*UA-", re.IGNORECASE),
    re.compile(r"gtag\s*\(\s*['\"]config['\"].*G-", re.IGNORECASE),
    re.compile(r"google-analytics\.com/analytics\.js", re.IGNORECASE),
    re.compile(r"googletagmanager\.com/gtag", re.IGNORECASE),
    re.compile(r"googletagmanager\.com/gtm\.js", re.IGNORECASE),
]

# Padrões para detectar Google Ads
GOOGLE_ADS_PATTERNS = [
    re.compile(r"gtag\s*\(\s*['\"]config['\"].*AW-", re.IGNORECASE),
    re.compile(r"googleads\.g\.doubleclick\.net", re.IGNORECASE),
    re.compile(r"google_conversion_id", re.IGNORECASE),
]


def qualify_company(empresa):
    """
    Qualifica uma empresa verificando a presença de pixels/tags de marketing.

    Args:
        empresa: Dicionário com dados da empresa (deve ter chave 'website').

    Returns:
        Dicionário atualizado com meta_pixel e google_ads_analytics.
    """
    empresa["meta_pixel"] = "Não"
    empresa["google_ads_analytics"] = "Não"

    website = empresa.get("website", "").strip()
    if not website:
        print(f"  [QUALIF] {empresa['nome']}: Sem website, pulando qualificação.")
        return empresa

    print(f"  [QUALIF] {empresa['nome']}: Verificando pixels/tags...")

    try:
        response = requests.get(website, headers=HEADERS, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            print(f"    -> Site retornou status {response.status_code}")
            return empresa

        html = response.text

        # Verificar Meta Pixel
        has_meta_pixel = any(pattern.search(html) for pattern in META_PIXEL_PATTERNS)
        if has_meta_pixel:
            empresa["meta_pixel"] = "Sim"

        # Verificar Google Analytics/Tag Manager
        has_ga = any(pattern.search(html) for pattern in GOOGLE_ANALYTICS_PATTERNS)

        # Verificar Google Ads
        has_gads = any(pattern.search(html) for pattern in GOOGLE_ADS_PATTERNS)

        if has_ga or has_gads:
            empresa["google_ads_analytics"] = "Sim"

        # Resumo
        tags = []
        if has_meta_pixel:
            tags.append("Meta Pixel")
        if has_ga:
            tags.append("Google Analytics/GTM")
        if has_gads:
            tags.append("Google Ads")

        if tags:
            print(f"    -> Detectado: {', '.join(tags)}")
        else:
            print(f"    -> Nenhum pixel/tag de marketing detectado.")

    except requests.RequestException as e:
        print(f"    -> Erro ao acessar site: {e}")

    return empresa
