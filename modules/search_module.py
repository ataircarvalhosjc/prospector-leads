"""
Módulo de Busca - Busca empresas no Google Maps via SerpApi.
"""

import os
import requests


SERPAPI_URL = "https://serpapi.com/search"


def search_google_maps(query, api_key=None, num_results=40):
    """
    Busca empresas no Google Maps usando SerpApi com paginação.

    Args:
        query: Termo de busca (ex: "Clínicas de Estética em São Paulo, SP")
        api_key: Chave da SerpApi. Se None, tenta usar variável de ambiente.
        num_results: Número máximo de resultados (20 por página).

    Returns:
        Lista de dicionários com dados das empresas.
    """
    api_key = api_key or os.environ.get("SERPAPI_KEY")

    if not api_key:
        print("[BUSCA] Sem chave SerpApi. Usando modo de demonstracao com dados simulados.")
        return _demo_results(query)

    results = []
    pages = (num_results + 19) // 20  # Calcula quantas páginas precisamos

    try:
        for page in range(pages):
            start = page * 20
            print(f"[BUSCA] Pagina {page + 1}/{pages} - Consultando Google Maps para: '{query}'...")

            params = {
                "engine": "google_maps",
                "q": query,
                "type": "search",
                "api_key": api_key,
                "hl": "pt-br",
                "num": 20,
                "start": start,
            }

            response = requests.get(SERPAPI_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            page_results = data.get("local_results", [])
            if not page_results:
                print(f"[BUSCA] Pagina {page + 1}: sem mais resultados.")
                break

            for place in page_results:
                empresa = {
                    "nome": place.get("title", ""),
                    "endereco": place.get("address", ""),
                    "telefone": place.get("phone", ""),
                    "website": place.get("website", ""),
                    "categoria": place.get("type", ""),
                    "avaliacao": place.get("rating", ""),
                    "num_avaliacoes": place.get("reviews", ""),
                }
                results.append(empresa)

            print(f"[BUSCA] Pagina {page + 1}: {len(page_results)} empresas encontradas.")

            if len(results) >= num_results:
                break

        # Remove duplicatas por nome
        seen = set()
        unique = []
        for emp in results:
            if emp["nome"] not in seen:
                seen.add(emp["nome"])
                unique.append(emp)
        results = unique[:num_results]

        print(f"[BUSCA] Total: {len(results)} empresas unicas encontradas.")
        return results

    except requests.RequestException as e:
        print(f"[BUSCA] Erro na requisicao: {e}")
        if results:
            print(f"[BUSCA] Retornando {len(results)} resultados parciais.")
            return results
        print("[BUSCA] Usando dados de demonstracao como fallback.")
        return _demo_results(query)


def _demo_results(query):
    """Retorna dados simulados para demonstração quando não há API key."""
    print("[BUSCA] Gerando dados de demonstração...")
    demo_data = [
        {
            "nome": "Studio Belle Estética",
            "endereco": "Rua Augusta, 1500 - Consolação, São Paulo - SP",
            "telefone": "(11) 3456-7890",
            "website": "https://www.studiobelle.com.br",
            "categoria": "Clínica de Estética",
            "avaliacao": "4.5",
            "num_avaliacoes": "128",
        },
        {
            "nome": "Clínica Renova Estética",
            "endereco": "Av. Paulista, 2200 - Bela Vista, São Paulo - SP",
            "telefone": "(11) 2345-6789",
            "website": "https://www.clinicarenova.com.br",
            "categoria": "Clínica de Estética",
            "avaliacao": "4.8",
            "num_avaliacoes": "256",
        },
        {
            "nome": "Espaço Vida Saudável",
            "endereco": "Rua Oscar Freire, 800 - Jardins, São Paulo - SP",
            "telefone": "(11) 9876-5432",
            "website": "https://www.espacovidasaudavel.com.br",
            "categoria": "Clínica de Estética",
            "avaliacao": "4.2",
            "num_avaliacoes": "89",
        },
        {
            "nome": "Beauty Center SP",
            "endereco": "Rua Haddock Lobo, 595 - Cerqueira César, São Paulo - SP",
            "telefone": "(11) 3333-4444",
            "website": "https://www.beautycentersp.com.br",
            "categoria": "Clínica de Estética",
            "avaliacao": "4.6",
            "num_avaliacoes": "192",
        },
        {
            "nome": "Derma Clinic",
            "endereco": "Rua Bela Cintra, 1200 - Consolação, São Paulo - SP",
            "telefone": "(11) 5555-6666",
            "website": "https://www.dermaclinic.com.br",
            "categoria": "Clínica de Estética",
            "avaliacao": "4.7",
            "num_avaliacoes": "310",
        },
    ]
    print(f"[BUSCA] {len(demo_data)} empresas de demonstração geradas.")
    return demo_data
