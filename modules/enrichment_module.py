"""
Módulo de Enriquecimento - Coleta informações adicionais dos sites das empresas.
Extrai emails, links de redes sociais (LinkedIn, Instagram, Facebook).
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Regex para encontrar emails
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Padrões de URLs de redes sociais
SOCIAL_PATTERNS = {
    "linkedin": re.compile(r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[^\s\"'<>]+", re.IGNORECASE),
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/[^\s\"'<>/?]+", re.IGNORECASE),
    "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[^\s\"'<>/?]+", re.IGNORECASE),
}

# Emails genéricos para ignorar
IGNORE_EMAILS = {
    "example@example.com", "email@email.com", "seu@email.com",
    "sentry@sentry.io", "wixpress@gmail.com",
}


def enrich_company(empresa, delay=1.5):
    """
    Enriquece os dados de uma empresa visitando seu website.

    Args:
        empresa: Dicionário com dados da empresa (deve ter chave 'website').
        delay: Tempo de espera entre requisições (em segundos).

    Returns:
        Dicionário atualizado com email, linkedin, instagram, facebook.
    """
    empresa["email"] = ""
    empresa["linkedin"] = ""
    empresa["instagram"] = ""
    empresa["facebook"] = ""

    website = empresa.get("website", "").strip()
    if not website:
        print(f"  [ENRIQ] {empresa['nome']}: Sem website, pulando.")
        return empresa

    print(f"  [ENRIQ] {empresa['nome']}: Analisando {website}...")

    # Páginas para verificar
    pages_to_check = _get_pages_to_check(website)

    all_emails = set()
    all_socials = {"linkedin": set(), "instagram": set(), "facebook": set()}

    for url in pages_to_check:
        try:
            html = _fetch_page(url)
            if not html:
                continue

            # Extrair emails
            emails = _extract_emails(html)
            all_emails.update(emails)

            # Extrair redes sociais
            socials = _extract_social_links(html)
            for key, values in socials.items():
                all_socials[key].update(values)

            time.sleep(delay)

        except Exception as e:
            print(f"    [ENRIQ] Erro ao acessar {url}: {e}")
            continue

    # Atribuir o primeiro resultado encontrado
    if all_emails:
        empresa["email"] = sorted(all_emails)[0]

    for key in ["linkedin", "instagram", "facebook"]:
        if all_socials[key]:
            empresa[key] = sorted(all_socials[key])[0]

    _print_enrichment_result(empresa)
    return empresa


def _get_pages_to_check(website):
    """Retorna lista de URLs para verificar (home + páginas comuns de contato)."""
    base = website.rstrip("/")
    pages = [base]

    contact_paths = ["/contato", "/contact", "/fale-conosco", "/sobre", "/about"]
    for path in contact_paths:
        pages.append(base + path)

    return pages


def _fetch_page(url, timeout=10):
    """Faz requisição HTTP e retorna o HTML da página."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        pass
    return None


def _extract_emails(html):
    """Extrai emails válidos do HTML."""
    found = EMAIL_PATTERN.findall(html)
    valid = set()
    for email in found:
        email = email.lower().strip(".")
        if email not in IGNORE_EMAILS and not email.endswith((".png", ".jpg", ".gif", ".svg", ".webp")):
            valid.add(email)
    return valid


def _extract_social_links(html):
    """Extrai links de redes sociais do HTML."""
    results = {"linkedin": set(), "instagram": set(), "facebook": set()}

    for platform, pattern in SOCIAL_PATTERNS.items():
        matches = pattern.findall(html)
        for match in matches:
            clean = match.rstrip("/")
            # Ignorar links genéricos
            if clean.lower() not in (
                "https://www.instagram.com/p",
                "https://www.facebook.com/sharer",
                "https://www.facebook.com/share",
                "https://www.linkedin.com/shareArticle",
            ):
                results[platform].add(clean)

    return results


def _print_enrichment_result(empresa):
    """Imprime resumo do enriquecimento."""
    found = []
    if empresa["email"]:
        found.append(f"Email: {empresa['email']}")
    if empresa["linkedin"]:
        found.append("LinkedIn")
    if empresa["instagram"]:
        found.append("Instagram")
    if empresa["facebook"]:
        found.append("Facebook")

    if found:
        print(f"    -> Encontrado: {', '.join(found)}")
    else:
        print(f"    -> Nenhum dado adicional encontrado.")
