"""
Módulo de Entrada - Coleta as especificações do usuário para prospecção.
"""


def get_user_input():
    """Coleta nicho e localização do usuário via terminal."""
    print("=" * 60)
    print("  AGENTE DE PROSPECÇÃO DE CLIENTES")
    print("  Gestão de Tráfego")
    print("=" * 60)
    print()

    nicho = input("Digite o nicho desejado (ex: Clínicas de Estética, Academias): ").strip()
    if not nicho:
        print("Erro: O nicho não pode ser vazio.")
        return None

    localizacao = input("Digite a localização (ex: São Paulo, SP): ").strip()
    if not localizacao:
        print("Erro: A localização não pode ser vazia.")
        return None

    print(f"\nBuscando: '{nicho}' em '{localizacao}'...\n")

    return {
        "nicho": nicho,
        "localizacao": localizacao,
        "query": f"{nicho} em {localizacao}"
    }
