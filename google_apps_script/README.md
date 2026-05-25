# Endpoint sem cache via Google Apps Script

Este Web App entrega os dados da planilha como JSON para reduzir o atraso do link CSV publicado do Google Sheets.

## Publicação

1. Abra a planilha base no Google Sheets.
2. Acesse `Extensões > Apps Script`.
3. Cole o conteúdo de `Code.gs`.
4. Se o script estiver vinculado à própria planilha, deixe `SPREADSHEET_ID` vazio.
5. Se quiser usar um script avulso, preencha `SPREADSHEET_ID` com o ID real da planilha.
6. Clique em `Implantar > Nova implantação`.
7. Tipo: `App da Web`.
8. Executar como: `Eu`.
9. Quem tem acesso: `Qualquer pessoa`.
10. Copie a URL gerada do Web App.

Depois, cole a URL em `APPS_SCRIPT_URL` no `build_dashboard.py` e rode:

```bash
python3 build_dashboard.py
```

O dashboard usará o Apps Script automaticamente. Se `APPS_SCRIPT_URL` ficar vazio, ele continua usando o CSV publicado como fallback.
