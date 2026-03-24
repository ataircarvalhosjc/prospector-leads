"""
Agente de Prospecção de Clientes - Gestão de Tráfego
====================================================
Agente autônomo que busca, enriquece e qualifica leads
para profissionais de gestão de tráfego.

Uso:
    python main.py
    python main.py --api-key SUA_CHAVE_SERPAPI

Sem API key, o sistema roda em modo demonstração com dados simulados.
Para obter uma chave gratuita: https://serpapi.com (100 buscas/mês grátis)
"""

import argparse
import os
import sys
import time

from modules.input_module import get_user_input
from modules.search_module import search_google_maps
from modules.enrichment_module import enrich_company
from modules.qualification_module import qualify_company
from modules.output_module import export_to_csv


def main():
    parser = argparse.ArgumentParser(description="Agente de Prospecção de Clientes")
    parser.add_argument("--api-key", type=str, help="Chave da SerpApi (ou defina SERPAPI_KEY no ambiente)")
    parser.add_argument("--output", type=str, help="Diretório de saída para o CSV")
    parser.add_argument("--max-results", type=int, default=20, help="Número máximo de resultados (padrão: 20)")
    args = parser.parse_args()

    # Etapa 1: Entrada do usuário
    user_input = get_user_input()
    if not user_input:
        sys.exit(1)

    # Etapa 2: Busca no Google Maps
    print("\n" + "=" * 60)
    print("  ETAPA 1/3 - BUSCANDO EMPRESAS")
    print("=" * 60)
    api_key = args.api_key or os.environ.get("SERPAPI_KEY")
    empresas = search_google_maps(user_input["query"], api_key=api_key, num_results=args.max_results)

    if not empresas:
        print("Nenhuma empresa encontrada. Tente outro nicho ou localização.")
        sys.exit(1)

    # Etapa 3: Enriquecimento
    print("\n" + "=" * 60)
    print("  ETAPA 2/3 - ENRIQUECENDO DADOS")
    print("=" * 60)
    for i, empresa in enumerate(empresas):
        print(f"\n[{i+1}/{len(empresas)}]")
        enrich_company(empresa, delay=1.5)

    # Etapa 4: Qualificação
    print("\n" + "=" * 60)
    print("  ETAPA 3/3 - QUALIFICANDO LEADS")
    print("=" * 60)
    for i, empresa in enumerate(empresas):
        print(f"\n[{i+1}/{len(empresas)}]")
        qualify_company(empresa)

    # Etapa 5: Exportação
    print("\n" + "=" * 60)
    print("  EXPORTANDO RESULTADOS")
    print("=" * 60)
    output_dir = args.output or os.path.dirname(os.path.abspath(__file__))
    filepath = export_to_csv(empresas, output_dir=output_dir)

    if filepath:
        print(f"\nProspecção concluída com sucesso!")
        print(f"Abra o arquivo CSV no Excel para visualizar os leads.")


if __name__ == "__main__":
    main()
