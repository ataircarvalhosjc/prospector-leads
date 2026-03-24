"""
Servidor Web - Interface web para o Agente de Prospecção de Clientes.
Roda com FastAPI + Uvicorn na porta 8000.
"""

import os
import io
import sys
import json
from dotenv import load_dotenv
from datetime import datetime

# Fix encoding do Windows para evitar UnicodeEncodeError nos print()
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from modules.search_module import search_google_maps
from modules.enrichment_module import enrich_company
from modules.qualification_module import qualify_company
from modules.output_module import FIELD_MAP, CSV_COLUMNS

app = FastAPI(title="Agente de Prospecção de Clientes")

# Armazena os leads da última busca para exportação
last_leads: list = []


def _build_dataframe(leads: list) -> pd.DataFrame:
    """Converte a lista de leads em DataFrame com colunas em português."""
    rows = []
    for emp in leads:
        row = {}
        for key_internal, col_name in FIELD_MAP.items():
            row[col_name] = emp.get(key_internal, "")
        rows.append(row)
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prospecção de Clientes</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
  .container { max-width: 960px; margin: 0 auto; padding: 2rem; }
  h1 { text-align: center; font-size: 1.8rem; margin-bottom: 0.5rem; color: #38bdf8; }
  .subtitle { text-align: center; color: #94a3b8; margin-bottom: 2rem; }
  .form-card { background: #1e293b; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; border: 1px solid #334155; }
  label { display: block; font-weight: 600; margin-bottom: 0.4rem; color: #cbd5e1; }
  input[type="text"] { width: 100%; padding: 0.7rem 1rem; border-radius: 8px; border: 1px solid #475569;
    background: #0f172a; color: #e2e8f0; font-size: 1rem; margin-bottom: 1rem; }
  input[type="text"]:focus { outline: none; border-color: #38bdf8; }
  .btn-primary { background: #2563eb; color: white; border: none; padding: 0.8rem 2rem; border-radius: 8px;
    font-size: 1rem; cursor: pointer; font-weight: 600; width: 100%; }
  .btn-primary:hover { background: #1d4ed8; }
  .btn-primary:disabled { background: #475569; cursor: not-allowed; }
  .status { text-align: center; margin: 1.5rem 0; color: #38bdf8; font-size: 1.1rem; }
  .spinner { display: inline-block; width: 18px; height: 18px; border: 3px solid #475569;
    border-top-color: #38bdf8; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 8px; vertical-align: middle; }
  @keyframes spin { to { transform: rotate(360deg); } }
  table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.85rem; }
  th { background: #2563eb; color: white; padding: 0.6rem; text-align: left; position: sticky; top: 0; }
  td { padding: 0.5rem 0.6rem; border-bottom: 1px solid #334155; }
  tr:hover td { background: #1e293b; }
  .tag-sim { background: #22c55e; color: #000; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
  .tag-nao { background: #475569; color: #94a3b8; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
  a { color: #38bdf8; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .results-wrap { overflow-x: auto; background: #1e293b; border-radius: 12px; padding: 1rem; border: 1px solid #334155; }
  .summary { display: flex; gap: 1rem; justify-content: center; margin: 1rem 0; flex-wrap: wrap; }
  .summary-card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 1rem 1.5rem; text-align: center; min-width: 140px; }
  .summary-card .num { font-size: 1.8rem; font-weight: 700; color: #38bdf8; }
  .summary-card .label { font-size: 0.8rem; color: #94a3b8; }

  /* Export buttons */
  .export-bar { display: flex; gap: 0.8rem; justify-content: center; margin: 1.5rem 0; flex-wrap: wrap; }
  .btn-export { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.6rem 1.5rem; border-radius: 8px;
    border: 2px solid; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.2s; background: transparent; }
  .btn-csv { color: #22c55e; border-color: #22c55e; }
  .btn-csv:hover { background: #22c55e; color: #000; }
  .btn-excel { color: #10b981; border-color: #10b981; }
  .btn-excel:hover { background: #10b981; color: #000; }
  .btn-json { color: #38bdf8; border-color: #38bdf8; }
  .btn-json:hover { background: #38bdf8; color: #000; }

  .export-bar.hidden { display: none; }
</style>
</head>
<body>
<div class="container">
  <h1>Agente de Prospecção de Clientes</h1>
  <p class="subtitle">Gestão de Tráfego — Encontre e qualifique leads automaticamente</p>

  <div class="form-card">
    <label for="nicho">Nicho</label>
    <input type="text" id="nicho" placeholder="Ex: Clínicas de Estética, Academias, Restaurantes...">
    <label for="localizacao">Localização</label>
    <input type="text" id="localizacao" placeholder="Ex: São Paulo, SP">
    <button class="btn-primary" id="btn" onclick="prospect()">Iniciar Prospecção</button>
  </div>

  <div id="status"></div>
  <div id="summary"></div>

  <div id="exportBar" class="export-bar hidden">
    <button class="btn-export btn-csv" onclick="exportar('csv')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
      Exportar CSV
    </button>
    <button class="btn-export btn-excel" onclick="exportar('excel')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
      Exportar Excel
    </button>
    <button class="btn-export btn-json" onclick="exportar('json')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
      Exportar JSON
    </button>
  </div>

  <div id="results"></div>
</div>
<script>
let currentLeads = [];

async function prospect() {
  const nicho = document.getElementById('nicho').value.trim();
  const loc = document.getElementById('localizacao').value.trim();
  if (!nicho || !loc) { alert('Preencha nicho e localização.'); return; }

  const btn = document.getElementById('btn');
  btn.disabled = true;
  document.getElementById('status').innerHTML = '<span class="spinner"></span> Buscando e qualificando leads...';
  document.getElementById('summary').innerHTML = '';
  document.getElementById('results').innerHTML = '';
  document.getElementById('exportBar').classList.add('hidden');

  try {
    const res = await fetch('/api/prospect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nicho, localizacao: loc })
    });
    const data = await res.json();

    if (data.error) { document.getElementById('status').textContent = 'Erro: ' + data.error; return; }

    currentLeads = data.leads;
    const leads = data.leads;
    const withPixel = leads.filter(l => l.meta_pixel === 'Sim').length;
    const withGoogle = leads.filter(l => l.google_ads_analytics === 'Sim').length;
    const withEmail = leads.filter(l => l.email).length;

    document.getElementById('status').textContent = '';
    document.getElementById('summary').innerHTML = `
      <div class="summary-card"><div class="num">${leads.length}</div><div class="label">Leads</div></div>
      <div class="summary-card"><div class="num">${withEmail}</div><div class="label">Com Email</div></div>
      <div class="summary-card"><div class="num">${withPixel}</div><div class="label">Meta Pixel</div></div>
      <div class="summary-card"><div class="num">${withGoogle}</div><div class="label">Google Ads</div></div>`;

    // Show export buttons
    document.getElementById('exportBar').classList.remove('hidden');

    let html = '<div class="results-wrap"><table><tr><th>Empresa</th><th>Telefone</th><th>Email</th><th>Redes Sociais</th><th>Meta Pixel</th><th>Google Ads</th></tr>';
    for (const l of leads) {
      const socials = [l.linkedin ? '<a href="'+l.linkedin+'" target="_blank">LI</a>' : '',
        l.instagram ? '<a href="'+l.instagram+'" target="_blank">IG</a>' : '',
        l.facebook ? '<a href="'+l.facebook+'" target="_blank">FB</a>' : ''].filter(Boolean).join(' ');
      html += `<tr>
        <td><strong>${l.nome}</strong><br><small style="color:#94a3b8">${l.endereco}</small></td>
        <td>${l.telefone||'-'}</td>
        <td>${l.email ? '<a href="mailto:'+l.email+'">'+l.email+'</a>' : '-'}</td>
        <td>${socials||'-'}</td>
        <td><span class="${l.meta_pixel==='Sim'?'tag-sim':'tag-nao'}">${l.meta_pixel}</span></td>
        <td><span class="${l.google_ads_analytics==='Sim'?'tag-sim':'tag-nao'}">${l.google_ads_analytics}</span></td>
      </tr>`;
    }
    html += '</table></div>';
    document.getElementById('results').innerHTML = html;
  } catch(e) {
    document.getElementById('status').textContent = 'Erro de conexão: ' + e.message;
  } finally { btn.disabled = false; }
}

function exportar(formato) {
  if (!currentLeads.length) { alert('Nenhum lead para exportar.'); return; }
  // Trigger download via the API
  window.location.href = '/api/export/' + formato;
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE


@app.post("/api/prospect")
async def prospect(request: Request):
    global last_leads
    body = await request.json()
    nicho = body.get("nicho", "").strip()
    localizacao = body.get("localizacao", "").strip()

    if not nicho or not localizacao:
        return JSONResponse({"error": "Nicho e localização são obrigatórios."}, status_code=400)

    query = f"{nicho} em {localizacao}"
    api_key = os.environ.get("SERPAPI_KEY")

    # Buscar
    empresas = search_google_maps(query, api_key=api_key, num_results=20)
    if not empresas:
        return JSONResponse({"error": "Nenhuma empresa encontrada."}, status_code=404)

    # Enriquecer e qualificar
    for empresa in empresas:
        enrich_company(empresa, delay=0.5)
        qualify_company(empresa)

    last_leads = empresas
    return {"leads": empresas, "total": len(empresas)}


@app.get("/api/export/csv")
async def export_csv():
    """Exporta leads em CSV para download."""
    if not last_leads:
        return JSONResponse({"error": "Nenhum lead disponível. Faça uma busca primeiro."}, status_code=404)

    df = _build_dataframe(last_leads)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig", sep=";")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"leads_{timestamp}.csv"

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/export/excel")
async def export_excel():
    """Exporta leads em Excel (.xlsx) para download."""
    if not last_leads:
        return JSONResponse({"error": "Nenhum lead disponível. Faça uma busca primeiro."}, status_code=404)

    df = _build_dataframe(last_leads)
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")

        # Auto-ajustar largura das colunas
        ws = writer.sheets["Leads"]
        for col_idx, col_name in enumerate(df.columns, 1):
            max_len = max(
                len(str(col_name)),
                df[col_name].astype(str).map(len).max() if len(df) > 0 else 0
            )
            ws.column_dimensions[chr(64 + col_idx) if col_idx <= 26 else "A"].width = min(max_len + 3, 40)

    buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"leads_{timestamp}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/export/json")
async def export_json():
    """Exporta leads em JSON para download."""
    if not last_leads:
        return JSONResponse({"error": "Nenhum lead disponível. Faça uma busca primeiro."}, status_code=404)

    content = json.dumps(last_leads, ensure_ascii=False, indent=2)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"leads_{timestamp}.json"

    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
