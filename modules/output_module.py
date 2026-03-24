"""
Módulo de Saída - Exporta os leads qualificados para arquivo CSV.
"""

import os
import pandas as pd
from datetime import datetime


CSV_COLUMNS = [
    "Nome da Empresa",
    "Endereço",
    "Telefone",
    "Website",
    "Avaliação",
    "Nº Avaliações",
    "E-mail de Contato",
    "URL do LinkedIn",
    "URL do Instagram",
    "URL do Facebook",
    "Meta Pixel Detectado",
    "Google Ads/Analytics Detectado",
]

FIELD_MAP = {
    "nome": "Nome da Empresa",
    "endereco": "Endereço",
    "telefone": "Telefone",
    "website": "Website",
    "avaliacao": "Avaliação",
    "num_avaliacoes": "Nº Avaliações",
    "email": "E-mail de Contato",
    "linkedin": "URL do LinkedIn",
    "instagram": "URL do Instagram",
    "facebook": "URL do Facebook",
    "meta_pixel": "Meta Pixel Detectado",
    "google_ads_analytics": "Google Ads/Analytics Detectado",
}


def export_to_csv(empresas, output_dir=None, filename=None):
    """
    Exporta a lista de empresas para um arquivo CSV.

    Args:
        empresas: Lista de dicionários com dados das empresas.
        output_dir: Diretório de saída. Se None, usa o diretório atual.
        filename: Nome do arquivo. Se None, gera automaticamente com timestamp.

    Returns:
        Caminho completo do arquivo CSV gerado.
    """
    if not empresas:
        print("[SAÍDA] Nenhuma empresa para exportar.")
        return None

    # Preparar dados renomeando as colunas
    rows = []
    for emp in empresas:
        row = {}
        for key_internal, col_name in FIELD_MAP.items():
            row[col_name] = emp.get(key_internal, "")
        rows.append(row)

    df = pd.DataFrame(rows, columns=CSV_COLUMNS)

    # Definir caminho do arquivo
    if output_dir is None:
        output_dir = os.getcwd()

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"leads_prospeccao_{timestamp}.csv"

    filepath = os.path.join(output_dir, filename)

    # Exportar
    df.to_csv(filepath, index=False, encoding="utf-8-sig", sep=";")

    print(f"\n[SAÍDA] Arquivo CSV gerado com sucesso!")
    print(f"[SAÍDA] Local: {filepath}")
    print(f"[SAÍDA] Total de leads: {len(empresas)}")

    # Resumo de qualificação
    with_pixel = sum(1 for e in empresas if e.get("meta_pixel") == "Sim")
    with_google = sum(1 for e in empresas if e.get("google_ads_analytics") == "Sim")
    with_email = sum(1 for e in empresas if e.get("email"))

    print(f"\n--- Resumo ---")
    print(f"  Com Meta Pixel:           {with_pixel}/{len(empresas)}")
    print(f"  Com Google Ads/Analytics:  {with_google}/{len(empresas)}")
    print(f"  Com e-mail de contato:     {with_email}/{len(empresas)}")

    return filepath
