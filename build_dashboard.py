# -*- coding: utf-8 -*-
import csv
import json
import os

CSV_PATH = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR1Zb8Ljbb9fB7BFQpC85FOPQ0QtJARSNt2y8hpbTlV4yrKJFmbuNEBVeThbS-JMSCkTIID2Qe6Kc6J/pub?gid=973871607&single=true&output=csv'
PROJECT_DIR = '/Users/tiagosobraldelima/Documents/New project/nos_na_rede_dashboard_live'
OUTPUT_DIR = '/Users/tiagosobraldelima/Downloads'
SCRATCH_OUTPUT = os.path.join(PROJECT_DIR, 'index.html')


def capitalize_portuguese(text):
    if not text:
        return ""
    words = text.split()
    capitalized_words = []
    for i, w in enumerate(words):
        w_lower = w.lower()
        if w_lower.startswith("d'"):
            parts = w_lower.split("'")
            if len(parts) > 1:
                w = "d'" + parts[1].capitalize()
            else:
                w = w_lower
        elif '-' in w_lower:
            w = "-".join(part.capitalize() for part in w_lower.split('-'))
        elif w_lower in ["de", "da", "do", "das", "dos", "e", "com", "na", "no", "nas", "nos", "ao", "aos", "para"]:
            w = w_lower if i > 0 else w.capitalize()
        else:
            w = w.capitalize()
        capitalized_words.append(w)
    return " ".join(capitalized_words)


def load_and_clean_data(source_path):
    import io

    print(f"Lendo dados de: {source_path}")

    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Arquivo CSV local não encontrado em: {source_path}")

    with open(source_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        csv_content = f.read()

    records = []
    f_like = io.StringIO(csv_content)

    sample = csv_content[:300]
    delimiter = ';' if ';' in sample else ','

    reader = csv.DictReader(f_like, delimiter=delimiter)

    for idx, row in enumerate(reader):
        cleaned_row = {}
        for k, v in row.items():
            if k is None:
                continue
            k_clean = k.lstrip('\ufeff').strip()
            v_clean = v.strip() if v else ''
            cleaned_row[k_clean] = v_clean

        if not cleaned_row.get('NOME COMPLETO') and not cleaned_row.get('CPF'):
            continue

        raca = cleaned_row.get('RAÇA/ETNIA', 'NÃO DECLARADO').upper()
        if not raca or raca == '':
            raca = 'NÃO DECLARADO'

        escolaridade_raw = cleaned_row.get('NÍVEL DE FORMAÇÃO', 'Não Informado')
        if not escolaridade_raw or escolaridade_raw.strip() == '':
            escolaridade_raw = 'Não Informado'
        escolaridade = capitalize_portuguese(escolaridade_raw.strip())

        vinculo = cleaned_row.get('VÍNCULO PROFISSIONAL', 'NÃO INFORMADO').upper()
        if not vinculo or vinculo == '':
            vinculo = 'NÃO INFORMADO'

        genero = cleaned_row.get('IDEN. GÊNERO', 'NÃO DECLARADO').upper()
        if not genero or genero == '':
            genero = 'NÃO DECLARADO'

        pcd = cleaned_row.get('PCD', 'NÃO').upper()
        if not pcd or pcd == '':
            pcd = 'NÃO'
        elif 'SIM' in pcd:
            pcd = 'SIM'
        elif 'NÃO' in pcd:
            pcd = 'NÃO'

        status = cleaned_row.get('STATUS DA INSCRIÇÃO', 'INSCRITO').upper()

        record = {
            'id': idx + 1,
            'nome': capitalize_portuguese(cleaned_row.get('NOME COMPLETO', '')),
            'nome_social': capitalize_portuguese(cleaned_row.get('NOME SOCIAL', '')),
            'status': status,
            'local': cleaned_row.get('NOME DO LOCAL/SERVIÇO DE ATUAÇÃO', 'Não Informado'),
            'turma': cleaned_row.get('TURMA', 'Não Informada'),
            'municipio': capitalize_portuguese(cleaned_row.get('MUNICÍPIO', 'Não Informado').split(',')[0].strip()),
            'regiao': cleaned_row.get('REGIÃO DE SAÚDE', 'Não Informada'),
            'escolaridade': escolaridade,
            'cargo': capitalize_portuguese(cleaned_row.get('CARGO/FUNÇÃO', 'Não Informado')),
            'vinculo': vinculo,
            'raca': raca,
            'genero': genero,
            'pcd': pcd,
            'acoes_afirmativas': cleaned_row.get('AÇÕES AFIRMATIVAS', 'NÃO')
        }
        records.append(record)

    return records


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR" class="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Indicações - Nós na Rede Alagoas</title>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&family=Slackey&display=swap" rel="stylesheet">

    <!-- Tailwind CSS (via Play CDN) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        outfit: ['Outfit', 'sans-serif'],
                    },
                    colors: {
                        brand: {
                            deep: '#1a1a1a',
                            blue: '#2F80C1',
                            teal: '#33A6D9',
                            coral: '#E94B3C',
                            emerald: '#78BD43',
                            purple: '#ED4F9A',
                        }
                    }
                }
            }
        }
    </script>

    <!-- FontAwesome for Premium Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <!-- Animate.css for entrance animations -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        .has-slackey-font-family {
            font-family: 'Slackey', cursive;
        }
        .has-text-align-left {
            text-align: left;
        }
        .has-text-primary-color {
            color: #003366;
        }
        .dark .has-text-primary-color {
            color: #38bdf8;
        }
        .has-large-font-size {
            font-size: 1.25rem;
            font-weight: 700;
        }
        @media (max-width: 640px) {
            .has-large-font-size {
                font-size: 0.95rem;
            }
        }
        .transition-all {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(226, 232, 240, 0.8);
        }
        .dark .glass-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(51, 65, 85, 0.25);
        }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 9999px; }
        .dark ::-webkit-scrollbar-thumb { background: #475569; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }


        :root {
            --nr-bg: #eaeaea;
            --nr-ink: #1a1a1a;
            --nr-muted: #5f646d;
            --nr-blue: #2f80c1;
            --nr-cyan: #33a6d9;
            --nr-pink: #ed4f9a;
            --nr-yellow: #f2cf43;
            --nr-red: #e94b3c;
            --nr-green: #78bd43;
            --nr-card: #fbfbfb;
            --nr-line: #d8dde5;
        }
        html { background: var(--nr-bg); }
        body {
            background: var(--nr-bg) !important;
            color: var(--nr-ink) !important;
            letter-spacing: 0;
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background:
                linear-gradient(110deg, transparent 0 18%, rgba(47,128,193,.12) 18.1% 18.35%, transparent 18.45% 100%),
                linear-gradient(155deg, transparent 0 62%, rgba(237,79,154,.12) 62.1% 62.35%, transparent 62.45% 100%),
                linear-gradient(30deg, transparent 0 76%, rgba(242,207,67,.16) 76.1% 76.35%, transparent 76.45% 100%);
            opacity: .75;
            z-index: -1;
        }
        .glass-card {
            background: rgba(251, 251, 251, .96) !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border: 1px solid var(--nr-line) !important;
            border-radius: 8px !important;
            box-shadow: 0 18px 44px rgba(21, 31, 46, .08) !important;
        }
        .dark .glass-card {
            background: rgba(18, 24, 34, .94) !important;
            border-color: rgba(123, 136, 154, .24) !important;
        }
        header.glass-card {
            position: relative;
            overflow: hidden;
            border-top: 6px solid transparent !important;
            border-image: linear-gradient(90deg, var(--nr-blue), var(--nr-cyan), var(--nr-pink), var(--nr-yellow), var(--nr-green)) 1;
            border-radius: 18px !important;
            min-height: 118px;
        }
        header h1 {
            background: none !important;
            color: var(--nr-ink) !important;
            -webkit-text-fill-color: var(--nr-ink) !important;
            text-shadow: none;
        }
        .dark header h1 {
            color: #f8fafc !important;
            -webkit-text-fill-color: #f8fafc !important;
        }
        .has-large-font-size {
            color: var(--nr-ink) !important;
            font-size: 1.42rem;
            line-height: 1.22 !important;
            max-width: 760px;
        }
        .dark .has-large-font-size { color: #f8fafc !important; }
        select, input, button {
            border-radius: 8px !important;
        }
        select, input[type="text"] {
            background: #fff !important;
            border-color: #d9dee6 !important;
        }
        .dark select, .dark input[type="text"] {
            background: rgba(15,23,42,.86) !important;
            border-color: rgba(100,116,139,.35) !important;
        }

        .active-filter label {
            color: var(--nr-blue) !important;
        }
        .active-filter .multi-dropdown-button,
        #tableSearch.active-filter-input {
            background: linear-gradient(180deg, rgba(47,128,193,.12), rgba(51,166,217,.08)) !important;
            border-color: var(--nr-blue) !important;
            color: var(--nr-ink) !important;
            box-shadow: 0 0 0 3px rgba(47,128,193,.14), inset 4px 0 0 var(--nr-blue) !important;
            font-weight: 700;
        }
        .active-filter .multi-dropdown-button:focus,
        #tableSearch.active-filter-input:focus {
            box-shadow: 0 0 0 4px rgba(237,79,154,.18), inset 4px 0 0 var(--nr-pink) !important;
            border-color: var(--nr-pink) !important;
        }
        .active-filter::after {
            display: inline-flex;
            width: max-content;
            margin-top: .25rem;
            padding: .18rem .45rem;
            border-radius: 999px;
            background: rgba(47,128,193,.12);
            color: var(--nr-blue);
            font-size: .64rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .02em;
        }

        .multi-filter-select {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        .multi-dropdown {
            position: relative;
        }
        .multi-dropdown-button {
            width: 100%;
            min-height: 2.75rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: .75rem;
            padding: .7rem .85rem;
            background: #fff;
            border: 1px solid #d9dee6;
            color: var(--nr-ink);
            font-size: .875rem;
            text-align: left;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,.45);
        }
        .multi-dropdown-button span {
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .multi-dropdown-button i {
            color: var(--nr-muted);
            transition: transform .18s ease;
        }
        .multi-dropdown.open .multi-dropdown-button i {
            transform: rotate(180deg);
        }
        .multi-dropdown-menu {
            display: none;
            position: absolute;
            z-index: 50;
            top: calc(100% + .35rem);
            left: 0;
            right: 0;
            max-height: 18rem;
            overflow-y: auto;
            padding: .45rem;
            background: #fff;
            border: 1px solid #d9dee6;
            border-radius: 8px;
            box-shadow: 0 18px 42px rgba(21, 31, 46, .16);
        }
        .multi-dropdown.open .multi-dropdown-menu {
            display: block;
        }
        .multi-dropdown-option {
            width: 100%;
            display: flex;
            align-items: center;
            gap: .55rem;
            padding: .48rem .55rem;
            border: 0;
            background: transparent;
            color: var(--nr-ink);
            font-size: .82rem;
            text-align: left;
            cursor: pointer;
        }
        .multi-dropdown-option:hover {
            background: rgba(47,128,193,.08);
        }
        .multi-dropdown-check {
            width: 1rem;
            height: 1rem;
            flex: 0 0 auto;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            color: transparent;
            font-size: .68rem;
        }
        .multi-dropdown-option.selected .multi-dropdown-check {
            background: var(--nr-blue);
            border-color: var(--nr-blue);
            color: #fff;
        }
        .multi-dropdown-option.all-option {
            font-weight: 800;
            border-bottom: 1px solid #edf0f4;
            margin-bottom: .25rem;
            color: var(--nr-blue);
        }
        .active-filter .multi-dropdown-button {
            background: linear-gradient(180deg, rgba(47,128,193,.12), rgba(51,166,217,.08)) !important;
            border-color: var(--nr-blue) !important;
            box-shadow: 0 0 0 3px rgba(47,128,193,.14), inset 4px 0 0 var(--nr-blue) !important;
            font-weight: 800;
        }
        .dark .multi-dropdown-button,
        .dark .multi-dropdown-menu {
            background: rgba(15,23,42,.96);
            border-color: rgba(100,116,139,.35);
            color: #f8fafc;
        }
        .dark .multi-dropdown-option {
            color: #f8fafc;
        }
        .dark .multi-dropdown-option:hover {
            background: rgba(47,128,193,.2);
        }
        .active-filter::after {
            content: attr(data-active-label);
        }

        .dark .active-filter .multi-dropdown-button,
        .dark #tableSearch.active-filter-input {
            background: rgba(47,128,193,.22) !important;
            color: #f8fafc !important;
        }

        section.glass-card, footer.glass-card { border-top-width: 0 !important; }
        section.glass-card h2, section.glass-card h3 {
            color: var(--nr-ink);
        }
        .dark section.glass-card h2, .dark section.glass-card h3 { color: #f8fafc; }
        .nr-section-accent {
            height: 4px;
            background: linear-gradient(90deg, var(--nr-blue), var(--nr-cyan), var(--nr-pink), var(--nr-yellow), var(--nr-green));
            border-radius: 999px;
        }
        #exportCsv {
            background: var(--nr-blue) !important;
            box-shadow: 0 10px 24px rgba(47,128,193,.18) !important;
        }
        #exportCsv:hover { background: #246fae !important; }
        .rounded-2xl, .rounded-3xl, .rounded-xl, .rounded-lg { border-radius: 8px !important; }
        header.rounded-3xl { border-radius: 18px !important; }
        @media (max-width: 760px) {
            header.glass-card::after { display: none; }
            header h1 { font-size: 2.45rem !important; }
            .has-large-font-size { font-size: 1.05rem; }
        }

    </style>
</head>
<body class="bg-slate-50 dark:bg-[#0a0f1d] text-slate-800 dark:text-slate-100 font-sans min-h-screen transition-colors duration-300">

    <div class="max-w-[1600px] mx-auto p-4 sm:p-6 lg:p-8 space-y-6">

        <!-- Header -->
        <header class="glass-card rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between shadow-xl shadow-slate-100/50 dark:shadow-none transition-all gap-4 border-t-4 border-t-brand-blue">
            <div class="flex items-center gap-4">
                <div class="h-16 w-16 rounded-2xl flex items-center justify-center bg-white dark:bg-slate-900 overflow-hidden shadow-lg p-1.5 border border-slate-200/30 dark:border-slate-800/30">
                    <img src="<!-- LOGO_PLACEHOLDER -->" class="h-full w-full object-contain" alt="Logo Nós na Rede">
                </div>
                <div>
                    <h1 class="wp-block-heading has-text-align-left animate__animated animate__fadeInDown has-slackey-font-family text-slate-950 dark:text-white" style="margin-right:0;margin-bottom:0;margin-left:0;font-size:3.3rem">Nós na Rede</h1>
                    <p class="has-text-align-left animate__animated animate__fadeInDown has-text-primary-color has-text-color has-large-font-size wp-block-paragraph" style="padding-top:0;padding-right:0;padding-bottom:0;padding-left:0;line-height:1.3">Educação Permanente para a Rede de Atenção Psicossocial no SUS</p>
                    <p class="text-[11px] font-medium text-slate-400 dark:text-slate-500">
                        Dashboard de Indicações • 2º Ciclo Formativo • Alagoas
                    </p>
                </div>
            </div>

            <div class="flex flex-wrap items-center gap-3">
                <!-- Data Status Badge -->
                <div class="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-teal-50 dark:bg-teal-950/30 text-brand-teal border border-teal-100 dark:border-teal-900/30 text-xs font-semibold">
                    <span class="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
                    Planilha Online
                </div>

                <!-- Theme Switcher -->
                <button id="themeToggle" class="h-11 w-11 rounded-2xl flex items-center justify-center glass-card hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-all focus:outline-none focus:ring-2 focus:ring-brand-teal">
                    <i class="fa-solid fa-moon text-lg dark:hidden"></i>
                    <i class="fa-solid fa-sun text-lg hidden dark:block"></i>
                </button>
            </div>
        </header>

        <!-- Filters Panel -->
        <section class="glass-card rounded-3xl p-6 shadow-xl shadow-slate-100/50 dark:shadow-none transition-all space-y-4 border-t-4 border-t-slate-300 dark:border-t-slate-700">
            <div class="flex items-center justify-between border-b border-slate-200/50 dark:border-slate-800/50 pb-4">
                <div class="flex items-center gap-2">
                    <i class="fa-solid fa-sliders text-brand-teal text-lg"></i>
                    <h2 class="text-lg font-outfit font-bold">Filtros Avançados</h2>
                </div>
                <button id="clearFilters" class="text-xs font-semibold text-brand-coral hover:underline flex items-center gap-1 focus:outline-none">
                    <i class="fa-solid fa-rotate-left"></i> Limpar Filtros
                </button>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <div class="space-y-1.5">
                    <label for="filterGender" class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Gênero</label>
                    <select id="filterGender" multiple size="4" class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all multi-filter-select">
                        <option value="ALL" selected>Selecionar todas as opções</option>
                    </select>
                </div>
                <div class="space-y-1.5">
                    <label for="filterRaca" class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Raça / Etnia</label>
                    <select id="filterRaca" multiple size="4" class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all multi-filter-select">
                        <option value="ALL" selected>Selecionar todas as opções</option>
                    </select>
                </div>
                <div class="space-y-1.5">
                    <label for="filterEscolaridade" class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Escolaridade</label>
                    <select id="filterEscolaridade" multiple size="4" class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all multi-filter-select">
                        <option value="ALL" selected>Selecionar todas as opções</option>
                    </select>
                </div>
                <div class="space-y-1.5">
                    <label for="filterVinculo" class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Vínculo Profissional</label>
                    <select id="filterVinculo" multiple size="4" class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all multi-filter-select">
                        <option value="ALL" selected>Selecionar todas as opções</option>
                    </select>
                </div>
                <div class="space-y-1.5">
                    <label for="filterPcd" class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Pessoa com Deficiência</label>
                    <select id="filterPcd" multiple size="4" class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all multi-filter-select">
                        <option value="ALL" selected>Selecionar todas as opções</option>
                        <option value="SIM">Sim</option>
                        <option value="NÃO">Não</option>
                    </select>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div class="space-y-1.5">
                    <label for="filterRegiao" class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Região de Saúde</label>
                    <select id="filterRegiao" multiple size="4" class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all multi-filter-select">
                        <option value="ALL" selected>Selecionar todas as opções</option>
                    </select>
                </div>
                <div class="space-y-1.5">
                    <label for="filterMunicipio" class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Município</label>
                    <select id="filterMunicipio" multiple size="4" class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all multi-filter-select">
                        <option value="ALL" selected>Selecionar todas as opções</option>
                    </select>
                </div>
                <div class="space-y-1.5">
                    <label for="filterStatus" class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status Inscrição</label>
                    <select id="filterStatus" multiple size="4" class="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl py-2.5 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all multi-filter-select">
                        <option value="ALL" selected>Selecionar todas as opções</option>
                        <option value="INSCRITO">Inscrito</option>
                        <option value="EDIÇÃO LIBERADA">Edição Liberada</option>
                        <option value="DESISTENTE">Desistente</option>
                    </select>
                </div>
            </div>
        </section>

        <!-- Key Metrics Cards -->
        <div class="nr-section-accent"></div>
        <section class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div class="glass-card rounded-2xl p-5 shadow-lg shadow-slate-100/30 dark:shadow-none flex flex-col justify-between hover:-translate-y-1 hover:shadow-xl transition-all duration-300 border-t-4 border-t-brand-blue">
                <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Total Indicados</span>
                <div class="flex items-baseline gap-2 mt-2">
                    <span id="metricTotal" class="text-3xl font-outfit font-extrabold text-slate-900 dark:text-white">-</span>
                    <span class="text-xs text-slate-400">ind.</span>
                </div>
                <div class="mt-4 flex items-center gap-1.5 text-xs text-brand-blue dark:text-slate-200 font-medium">
                    <i class="fa-solid fa-users"></i> Geral
                </div>
            </div>

            <div class="glass-card rounded-2xl p-5 shadow-lg shadow-slate-100/30 dark:shadow-none flex flex-col justify-between hover:-translate-y-1 hover:shadow-xl transition-all duration-300 border-t-4 border-t-pink-500">
                <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">% Gênero Feminino</span>
                <div class="flex items-baseline gap-2 mt-2">
                    <span id="metricMulheres" class="text-3xl font-outfit font-extrabold text-pink-500">-</span>
                    <span class="text-xs text-pink-500/80 font-bold">%</span>
                </div>
                <div class="mt-4 flex items-center gap-1.5 text-xs text-pink-500 font-medium">
                    <i class="fa-solid fa-venus"></i> Mulheres Cis e Trans
                </div>
            </div>

            <div class="glass-card rounded-2xl p-5 shadow-lg shadow-slate-100/30 dark:shadow-none flex flex-col justify-between hover:-translate-y-1 hover:shadow-xl transition-all duration-300 border-t-4 border-t-amber-700 dark:border-t-amber-500">
                <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">% População Negra</span>
                <div class="flex items-baseline gap-2 mt-2">
                    <span id="metricNegros" class="text-3xl font-outfit font-extrabold text-amber-700 dark:text-amber-500">-</span>
                    <span class="text-xs text-amber-600 font-bold">%</span>
                </div>
                <div class="mt-4 flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-500 font-medium">
                    <i class="fa-solid fa-circle-nodes"></i> Pretos e Pardos
                </div>
            </div>

            <div class="glass-card rounded-2xl p-5 shadow-lg shadow-slate-100/30 dark:shadow-none flex flex-col justify-between hover:-translate-y-1 hover:shadow-xl transition-all duration-300 border-t-4 border-t-brand-coral">
                <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">% População Indígena</span>
                <div class="flex items-baseline gap-2 mt-2">
                    <span id="metricIndigenas" class="text-3xl font-outfit font-extrabold text-orange-600 dark:text-orange-500">-</span>
                    <span class="text-xs text-orange-600 font-bold">%</span>
                </div>
                <div class="mt-4 flex items-center gap-1.5 text-xs text-orange-500 font-medium">
                    <i class="fa-solid fa-leaf"></i> Povos Originários
                </div>
            </div>

            <div class="glass-card rounded-2xl p-5 shadow-lg shadow-slate-100/30 dark:shadow-none flex flex-col justify-between hover:-translate-y-1 hover:shadow-xl transition-all duration-300 border-t-4 border-t-blue-500">
                <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Pessoas com Defic.</span>
                <div class="flex items-baseline gap-2 mt-2">
                    <span id="metricPcd" class="text-3xl font-outfit font-extrabold text-blue-500">-</span>
                    <span class="text-xs text-blue-400 font-bold">pess.</span>
                </div>
                <div class="mt-4 flex items-center gap-1.5 text-xs text-blue-500 font-medium">
                    <i class="fa-solid fa-wheelchair"></i> PCD Atendidas
                </div>
            </div>

            <div class="glass-card rounded-2xl p-5 shadow-lg shadow-slate-100/30 dark:shadow-none flex flex-col justify-between hover:-translate-y-1 hover:shadow-xl transition-all duration-300 border-t-4 border-t-brand-teal">
                <span class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">% Contrato Temp.</span>
                <div class="flex items-baseline gap-2 mt-2">
                    <span id="metricContratos" class="text-3xl font-outfit font-extrabold text-emerald-600">-</span>
                    <span class="text-xs text-emerald-500 font-bold">%</span>
                </div>
                <div class="mt-4 flex items-center gap-1.5 text-xs text-emerald-500 font-medium">
                    <i class="fa-solid fa-briefcase"></i> Vínculo Contratual
                </div>
            </div>
        </section>

        <!-- Charts Grid Layout -->
        <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="glass-card rounded-3xl p-6 shadow-xl shadow-slate-100/50 dark:shadow-none transition-all flex flex-col justify-between min-h-[380px] border-t-4 border-t-brand-coral">
                <div class="flex items-center gap-2 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">
                    <i class="fa-solid fa-earth-americas text-brand-coral"></i>
                    <h3 class="text-base font-outfit font-bold">Recortes Étnicos e Raciais</h3>
                </div>
                <div class="relative flex-grow flex items-center justify-center">
                    <canvas id="chartRaca" class="max-h-[280px] w-full"></canvas>
                </div>
            </div>

            <div class="glass-card rounded-3xl p-6 shadow-xl shadow-slate-100/50 dark:shadow-none transition-all flex flex-col justify-between min-h-[380px] border-t-4 border-t-brand-purple">
                <div class="flex items-center gap-2 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">
                    <i class="fa-solid fa-graduation-cap text-brand-purple"></i>
                    <h3 class="text-base font-outfit font-bold">Nível de Escolaridade (Formação)</h3>
                </div>
                <div class="relative flex-grow flex items-center justify-center">
                    <canvas id="chartEscolaridade" class="max-h-[280px] w-full"></canvas>
                </div>
            </div>

            <div class="glass-card rounded-3xl p-6 shadow-xl shadow-slate-100/50 dark:shadow-none transition-all flex flex-col justify-between min-h-[380px] border-t-4 border-t-brand-teal">
                <div class="flex items-center gap-2 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">
                    <i class="fa-solid fa-id-card text-brand-teal"></i>
                    <h3 class="text-base font-outfit font-bold">Tipo de Vínculo Profissional</h3>
                </div>
                <div class="relative flex-grow flex items-center justify-center">
                    <canvas id="chartVinculo" class="max-h-[280px] w-full"></canvas>
                </div>
            </div>

            <div class="glass-card rounded-3xl p-6 shadow-xl shadow-slate-100/50 dark:shadow-none transition-all flex flex-col justify-between min-h-[380px] border-t-4 border-t-pink-500">
                <div class="flex items-center gap-2 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">
                    <i class="fa-solid fa-venus-mars text-pink-500"></i>
                    <h3 class="text-base font-outfit font-bold">Identidade de Gênero</h3>
                </div>
                <div class="relative flex-grow flex items-center justify-center">
                    <canvas id="chartGenero" class="max-h-[280px] w-full"></canvas>
                </div>
            </div>
        </section>

        <!-- Regional Analysis Section -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-1 glass-card rounded-3xl p-6 shadow-xl shadow-slate-100/50 dark:shadow-none flex flex-col justify-between min-h-[380px] border-t-4 border-t-brand-teal">
                <div>
                    <div class="flex items-center gap-2 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">
                        <i class="fa-solid fa-hospital-user text-brand-teal"></i>
                        <h3 class="text-base font-outfit font-bold">Regiões Sanitárias</h3>
                    </div>
                    <div id="regionsList" class="space-y-3 max-h-[280px] overflow-y-auto pr-1">
                    </div>
                </div>
            </div>

            <div class="lg:col-span-2 glass-card rounded-3xl p-6 shadow-xl shadow-slate-100/50 dark:shadow-none flex flex-col justify-between min-h-[380px] border-t-4 border-t-brand-emerald">
                <div>
                    <div class="flex items-center gap-2 mb-4 border-b border-slate-100 dark:border-slate-800 pb-2">
                        <i class="fa-solid fa-map-location-dot text-brand-emerald"></i>
                        <h3 class="text-base font-outfit font-bold">Top 10 Municípios em Indicações</h3>
                    </div>
                    <div class="grid grid-cols-2 gap-4 mt-2" id="municipalitiesGrid">
                    </div>
                </div>
            </div>
        </section>

        <!-- Detailed Data Table Section -->
        <section class="glass-card rounded-3xl p-6 shadow-xl shadow-slate-100/50 dark:shadow-none transition-all space-y-4 border-t-4 border-t-brand-blue">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/50 dark:border-slate-800/50 pb-4">
                <div class="flex items-center gap-2">
                    <i class="fa-solid fa-list-check text-brand-teal text-lg"></i>
                    <div>
                        <h2 class="text-lg font-outfit font-bold">Fichas de Indicações</h2>
                        <p class="text-xs text-slate-500">Visualização em tempo real de acordo com filtros ativos</p>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <div class="relative w-full sm:w-64">
                        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                            <i class="fa-solid fa-magnifying-glass text-xs"></i>
                        </span>
                        <input type="text" id="tableSearch" placeholder="Buscar por nome, cargo ou município..."
                               class="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-brand-teal transition-all">
                    </div>
                    <button id="exportCsv" class="px-4 py-2 bg-gradient-to-r from-brand-teal to-brand-emerald text-white rounded-xl text-xs font-semibold shadow-md shadow-brand-teal/10 hover:shadow-lg hover:shadow-brand-teal/20 transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-file-arrow-down"></i> Exportar CSV
                    </button>
                </div>
            </div>

            <div class="overflow-x-auto rounded-2xl border border-slate-100 dark:border-slate-900">
                <table class="w-full text-left text-xs border-collapse">
                    <thead>
                        <tr class="bg-slate-50 dark:bg-slate-950/40 text-slate-500 border-b border-slate-100 dark:border-slate-900">
                            <th class="p-3.5 font-bold uppercase tracking-wider">Nº</th>
                            <th class="p-3.5 font-bold uppercase tracking-wider">Nome Completo</th>
                            <th class="p-3.5 font-bold uppercase tracking-wider">Município</th>
                            <th class="p-3.5 font-bold uppercase tracking-wider">Região de Saúde</th>
                            <th class="p-3.5 font-bold uppercase tracking-wider">Cargo / Função</th>
                            <th class="p-3.5 font-bold uppercase tracking-wider">Vínculo</th>
                            <th class="p-3.5 font-bold uppercase tracking-wider">Raça/Etnia</th>
                            <th class="p-3.5 font-bold uppercase tracking-wider">Gênero</th>
                            <th class="p-3.5 font-bold uppercase tracking-wider text-center">PCD</th>
                            <th class="p-3.5 font-bold uppercase tracking-wider text-center">Status</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                    </tbody>
                </table>
            </div>

            <div class="flex flex-col sm:flex-row items-center justify-between pt-2 gap-4 text-xs font-medium text-slate-500 dark:text-slate-400">
                <span id="tablePaginationInfo">Mostrando 0-0 de 0 registros</span>
                <div class="flex items-center gap-2">
                    <button id="btnPrevPage" class="px-3 py-1.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-all disabled:opacity-50 disabled:pointer-events-none">
                        <i class="fa-solid fa-angle-left"></i> Anterior
                    </button>
                    <div id="pagesList" class="flex gap-1"></div>
                    <button id="btnNextPage" class="px-3 py-1.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-all disabled:opacity-50 disabled:pointer-events-none">
                        Próximo <i class="fa-solid fa-angle-right"></i>
                    </button>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="glass-card rounded-3xl p-6 shadow-xl shadow-slate-100/50 dark:shadow-none transition-all flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-slate-500 dark:text-slate-400 border-t-4 border-t-brand-blue">
            <div class="space-y-1 text-center md:text-left">
                <p class="font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">Iniciativa do Ministério da Saúde</p>
                <p>Em parceria com a Fundação Oswaldo Cruz (Fiocruz Brasília), com as Escolas Técnicas do SUS (ETSUS) e com as Escolas de Saúde Pública (ESP).</p>
                <p class="font-bold text-slate-600 dark:text-slate-400 mt-2">Projeto Nós na Rede • 2º Ciclo Formativo</p>
            </div>
            <div class="flex items-center justify-center bg-white rounded-2xl p-3 shadow-md border border-slate-100 dark:border-slate-800 w-full md:w-auto md:max-w-[400px] shrink-0">
                <img src="<!-- REGUA_PLACEHOLDER -->" class="h-10 w-auto object-contain" alt="Assinatura Institucional Fiocruz Brasília e Ministério da Saúde">
            </div>
        </footer>

    </div>

    <!-- DATA INJECTED BY PYTHON SCRIPT -->
    <script>
        let RAW_DATA = <!-- DATA_PLACEHOLDER -->;

        // Active Filter States
        const FILTER_CONFIG = {
            filterGender: 'gender', filterRaca: 'raca', filterEscolaridade: 'escolaridade',
            filterVinculo: 'vinculo', filterPcd: 'pcd', filterRegiao: 'regiao',
            filterMunicipio: 'municipio', filterStatus: 'status'
        };

        let filters = {
            gender: [], raca: [], escolaridade: [], vinculo: [], pcd: [], regiao: [],
            municipio: [], status: [], search: ''
        };

        let currentPage = 1;
        const rowsPerPage = 10;
        let filteredRecords = [...RAW_DATA];

        let chartRacaInstance = null;
        let chartEscolaridadeInstance = null;
        let chartVinculoInstance = null;
        let chartGeneroInstance = null;

        // Dark Mode — com proteção para iframes com localStorage bloqueado
        const themeToggleBtn = document.getElementById('themeToggle');
        let isDarkMode = false;
        try {
            isDarkMode = localStorage.getItem('color-theme') === 'dark' ||
                (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
        } catch (e) {
            isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        if (isDarkMode) document.documentElement.classList.add('dark');
        else document.documentElement.classList.remove('dark');

        themeToggleBtn.addEventListener('click', function () {
            if (document.documentElement.classList.contains('dark')) {
                document.documentElement.classList.remove('dark');
                try { localStorage.setItem('color-theme', 'light'); } catch (e) {}
            } else {
                document.documentElement.classList.add('dark');
                try { localStorage.setItem('color-theme', 'dark'); } catch (e) {}
            }
            updateChartsData();
        });

        // Capitalização em português
        function capitalizePortuguese(text) {
            if (!text) return "";
            const prepositions = ['de','da','do','das','dos','e','com','na','no','nas','nos','ao','aos','para'];
            return text.toLowerCase().split(/\\s+/).map((w, idx) => {
                if (w.startsWith("d'")) return "d'" + (w.charAt(2) ? w.charAt(2).toUpperCase() + w.slice(3) : '');
                if (w.includes('-')) return w.split('-').map(p => p.charAt(0).toUpperCase() + p.slice(1)).join('-');
                if (prepositions.includes(w) && idx > 0) return w;
                return w.charAt(0).toUpperCase() + w.slice(1);
            }).join(' ');
        }

        const SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR1Zb8Ljbb9fB7BFQpC85FOPQ0QtJARSNt2y8hpbTlV4yrKJFmbuNEBVeThbS-JMSCkTIID2Qe6Kc6J/pub?gid=973871607&single=true&output=csv';
        const AUTO_REFRESH_INTERVAL_MS = 60000;
        let lastCsvSignature = '';
        let isRefreshingData = false;
        window.__dashboardDataRefresh = { status: 'pending', records: RAW_DATA.length, lastCheckedAt: null };

        function parseCsv(text) {
            const rows = [];
            let row = [];
            let value = '';
            let inQuotes = false;

            for (let i = 0; i < text.length; i++) {
                const ch = text[i];
                const next = text[i + 1];

                if (ch === '"') {
                    if (inQuotes && next === '"') {
                        value += '"';
                        i++;
                    } else {
                        inQuotes = !inQuotes;
                    }
                } else if ((ch === ',' || ch === ';') && !inQuotes) {
                    row.push(value);
                    value = '';
                } else if ((ch === String.fromCharCode(10) || ch === String.fromCharCode(13)) && !inQuotes) {
                    if (ch === String.fromCharCode(13) && next === String.fromCharCode(10)) i++;
                    row.push(value);
                    rows.push(row);
                    row = [];
                    value = '';
                } else {
                    value += ch;
                }
            }

            if (value || row.length) {
                row.push(value);
                rows.push(row);
            }

            const headers = (rows.shift() || []).map(h => h.replace(/^\uFEFF/, '').trim());
            return rows
                .filter(cols => cols.some(col => col && col.trim()))
                .map(cols => Object.fromEntries(headers.map((h, idx) => [h, (cols[idx] || '').trim()])));
        }

        function normalizeRecord(row, idx) {
            const normalizeUpper = (value, fallback) => {
                const normalized = (value || fallback || '').trim().toUpperCase();
                return normalized || fallback;
            };
            let pcd = normalizeUpper(row['PCD'], 'NÃO');
            if (pcd.includes('SIM')) pcd = 'SIM';
            else if (pcd.includes('NÃO')) pcd = 'NÃO';

            return {
                id: idx + 1,
                nome: capitalizePortuguese(row['NOME COMPLETO'] || ''),
                nome_social: '',
                status: normalizeUpper(row['STATUS DA INSCRIÇÃO'], 'INSCRITO'),
                local: row['NOME DO LOCAL/SERVIÇO DE ATUAÇÃO'] || 'Não Informado',
                turma: row['TURMA'] || 'Não Informada',
                municipio: capitalizePortuguese((row['MUNICÍPIO'] || 'Não Informado').split(',')[0].trim()),
                regiao: row['REGIÃO DE SAÚDE'] || 'Não Informada',
                escolaridade: capitalizePortuguese(row['NÍVEL DE FORMAÇÃO'] || 'Não Informado'),
                cargo: capitalizePortuguese(row['CARGO/FUNÇÃO'] || 'Não Informado'),
                vinculo: normalizeUpper(row['VÍNCULO PROFISSIONAL'], 'NÃO INFORMADO'),
                raca: normalizeUpper(row['RAÇA/ETNIA'], 'NÃO DECLARADO'),
                genero: normalizeUpper(row['IDEN. GÊNERO'], 'NÃO DECLARADO'),
                pcd,
                acoes_afirmativas: normalizeUpper(row['AÇÕES AFIRMATIVAS'], 'NÃO')
            };
        }

        function resetInvalidFilterValues() {
            const allowed = {
                gender: new Set(RAW_DATA.map(r => r.genero)),
                raca: new Set(RAW_DATA.map(r => r.raca)),
                escolaridade: new Set(RAW_DATA.map(r => r.escolaridade)),
                vinculo: new Set(RAW_DATA.map(r => r.vinculo)),
                pcd: new Set(['SIM', 'NÃO']),
                regiao: new Set(RAW_DATA.map(r => r.regiao)),
                municipio: new Set(RAW_DATA.map(r => r.municipio)),
                status: new Set([...RAW_DATA.map(r => r.status), 'INSCRITO', 'EDIÇÃO LIBERADA', 'DESISTENTE', 'CADASTRO RESERVA', 'INDEFERIDO'])
            };
            Object.keys(allowed).forEach(key => {
                filters[key] = normalizeFilterValues(filters[key]).filter(value => allowed[key].has(value));
            });
        }

        async function refreshDashboardData(force = false) {
            if (isRefreshingData) return;
            isRefreshingData = true;
            try {
                const url = SHEET_CSV_URL + '&_=' + Date.now();
                const response = await fetch(url, { cache: 'no-store' });
                if (!response.ok) throw new Error('HTTP ' + response.status);
                const csvText = await response.text();
                const signature = String(csvText.length) + ':' + csvText.slice(0, 200) + ':' + csvText.slice(-200);
                if (!force && signature === lastCsvSignature) return;

                const rows = parseCsv(csvText);
                const nextData = rows
                    .filter(row => row['NOME COMPLETO'] || row['CPF'])
                    .map(normalizeRecord);

                if (!nextData.length) return;
                RAW_DATA = nextData;
                lastCsvSignature = signature;
                window.__dashboardDataRefresh = { status: 'updated', records: RAW_DATA.length, lastCheckedAt: new Date().toISOString() };
                resetInvalidFilterValues();
                populateFilterOptions();
                Object.entries(FILTER_CONFIG).forEach(([id, key]) => {
                    setSelectedValues(id, filters[key]);
                });
                filterDataset();
            } catch (err) {
                window.__dashboardDataRefresh = { status: 'error', records: RAW_DATA.length, lastCheckedAt: new Date().toISOString(), message: err.message };
                console.warn('Não foi possível atualizar dados da planilha publicada. Mantendo dados locais.', err);
            } finally {
                isRefreshingData = false;
            }
        }

        // Popula selects de filtro
        function populateFilterOptions() {
            const genres = new Set(), racas = new Set(), levels = new Set(),
                  vinculos = new Set(), regions = new Set(), cities = new Set();
            RAW_DATA.forEach(r => {
                if (r.genero) genres.add(r.genero);
                if (r.raca) racas.add(r.raca);
                if (r.escolaridade) levels.add(r.escolaridade);
                if (r.vinculo) vinculos.add(r.vinculo);
                if (r.regiao) regions.add(r.regiao);
                if (r.municipio) cities.add(r.municipio);
            });
            populateSelect('filterGender', [...genres].sort());
            populateSelect('filterRaca', [...racas].sort());
            populateSelect('filterEscolaridade', [...levels].sort());
            populateSelect('filterVinculo', [...vinculos].sort());
            populateSelect('filterRegiao', [...regions].sort());
            populateSelect('filterMunicipio', [...cities].sort());
        }

        function populateSelect(id, opts) {
            const sel = document.getElementById(id);
            const first = sel.options[0];
            sel.innerHTML = '';
            first.selected = true;
            sel.appendChild(first);
            opts.sort((a, b) => capitalizePortuguese(a).localeCompare(capitalizePortuguese(b), 'pt-BR', { sensitivity: 'base' }));
            opts.forEach(v => {
                if (!v || !v.trim()) return;
                const opt = document.createElement('option');
                opt.value = v;
                opt.textContent = capitalizePortuguese(v);
                sel.appendChild(opt);
            });
            updateMultiDropdown(id);
        }



        function sortSelectOptions(select) {
            const allOption = Array.from(select.options).find(option => option.value === 'ALL');
            const options = Array.from(select.options)
                .filter(option => option.value !== 'ALL')
                .sort((a, b) => a.textContent.localeCompare(b.textContent, 'pt-BR', { sensitivity: 'base' }));
            select.innerHTML = '';
            if (allOption) select.appendChild(allOption);
            options.forEach(option => select.appendChild(option));
        }

        function getSelectedValuesFromState(id) {
            const key = FILTER_CONFIG[id];
            return key ? normalizeFilterValues(filters[key]) : [];
        }

        function updateMultiDropdown(id) {
            const select = document.getElementById(id);
            const dropdown = document.getElementById(id + 'Dropdown');
            if (!select || !dropdown) return;
            sortSelectOptions(select);

            const selectedValues = new Set(getSelectedValuesFromState(id));
            const buttonText = dropdown.querySelector('.multi-dropdown-label');
            const menu = dropdown.querySelector('.multi-dropdown-menu');
            const selectedOptions = Array.from(select.options).filter(option => selectedValues.has(option.value));

            if (buttonText) {
                if (selectedOptions.length === 0) buttonText.textContent = select.options[0]?.textContent || 'Todas as opções';
                else if (selectedOptions.length === 1) buttonText.textContent = selectedOptions[0].textContent;
                else buttonText.textContent = selectedOptions.length + ' opções selecionadas';
            }

            menu.innerHTML = '';
            Array.from(select.options).forEach(option => {
                const isAll = option.value === 'ALL';
                const isSelected = isAll ? selectedValues.size === 0 : selectedValues.has(option.value);
                const row = document.createElement('button');
                row.type = 'button';
                row.className = 'multi-dropdown-option' + (isSelected ? ' selected' : '') + (isAll ? ' all-option' : '');
                row.dataset.value = option.value;
                row.innerHTML = '<span class="multi-dropdown-check"><i class="fa-solid fa-check"></i></span><span>' + option.textContent + '</span>';
                row.addEventListener('click', event => {
                    event.stopPropagation();
                    toggleMultiSelectOption(id, option);
                });
                menu.appendChild(row);
            });
        }

        function createMultiDropdown(id) {
            const select = document.getElementById(id);
            if (!select || document.getElementById(id + 'Dropdown')) return;
            const dropdown = document.createElement('div');
            dropdown.id = id + 'Dropdown';
            dropdown.className = 'multi-dropdown';
            dropdown.innerHTML = '<button type="button" class="multi-dropdown-button" aria-haspopup="listbox" aria-expanded="false"><span class="multi-dropdown-label"></span><i class="fa-solid fa-chevron-down text-xs"></i></button><div class="multi-dropdown-menu" role="listbox"></div>';
            select.insertAdjacentElement('afterend', dropdown);
            dropdown.querySelector('.multi-dropdown-button').addEventListener('click', event => {
                event.stopPropagation();
                document.querySelectorAll('.multi-dropdown.open').forEach(openDropdown => {
                    if (openDropdown !== dropdown) {
                        openDropdown.classList.remove('open');
                        openDropdown.querySelector('.multi-dropdown-button')?.setAttribute('aria-expanded', 'false');
                    }
                });
                const isOpen = dropdown.classList.toggle('open');
                dropdown.querySelector('.multi-dropdown-button').setAttribute('aria-expanded', String(isOpen));
            });
            updateMultiDropdown(id);
        }

        function createAllMultiDropdowns() {
            Object.keys(FILTER_CONFIG).forEach(createMultiDropdown);
        }

        function closeMultiDropdownsOnOutsideClick(event) {
            if (event.target.closest('.multi-dropdown')) return;
            document.querySelectorAll('.multi-dropdown.open').forEach(dropdown => {
                dropdown.classList.remove('open');
                dropdown.querySelector('.multi-dropdown-button')?.setAttribute('aria-expanded', 'false');
            });
        }

        function normalizeFilterValues(value) {
            if (Array.isArray(value)) return value.filter(v => v && v !== 'ALL');
            return value && value !== 'ALL' ? [value] : [];
        }

        function setSelectedValues(id, values) {
            const select = document.getElementById(id);
            if (!select) return;
            const selectedValues = new Set(normalizeFilterValues(values));
            let hasSelectedOption = false;
            Array.from(select.options).forEach(option => {
                const isSelected = selectedValues.has(option.value);
                option.selected = isSelected;
                if (isSelected) hasSelectedOption = true;
            });
            const allOption = Array.from(select.options).find(option => option.value === 'ALL');
            if (allOption) allOption.selected = !hasSelectedOption;
            updateMultiDropdown(id);
        }

        function syncFilterFromSelect(id) {
            const select = document.getElementById(id);
            const key = FILTER_CONFIG[id];
            if (!select || !key) return;
            const values = Array.from(select.selectedOptions)
                .map(option => option.value)
                .filter(value => value !== 'ALL');
            filters[key] = values;
            setSelectedValues(id, values);
        }

        function toggleMultiSelectOption(id, option) {
            const select = document.getElementById(id);
            const key = FILTER_CONFIG[id];
            if (!select || !key || !option) return;

            if (option.value === 'ALL') {
                filters[key] = [];
                setSelectedValues(id, []);
            } else {
                const values = new Set(normalizeFilterValues(filters[key]));
                if (values.has(option.value)) values.delete(option.value);
                else values.add(option.value);
                filters[key] = [...values];
                setSelectedValues(id, filters[key]);
            }
            filterDataset();
        }

        function matchesAnyFilter(selectedValues, recordValue) {
            const values = normalizeFilterValues(selectedValues);
            return values.length === 0 || values.includes(recordValue);
        }

        function updateActiveFilterStyles() {
            Object.entries(FILTER_CONFIG).forEach(([id, key]) => {
                const select = document.getElementById(id);
                const wrapper = select ? select.parentElement : null;
                if (!select || !wrapper) return;
                const selectedValues = normalizeFilterValues(filters[key]);
                wrapper.classList.toggle('active-filter', selectedValues.length > 0);
                wrapper.dataset.activeLabel = selectedValues.length === 1
                    ? '1 opção selecionada'
                    : selectedValues.length + ' opções selecionadas';
            });

            const searchInput = document.getElementById('tableSearch');
            if (searchInput) {
                searchInput.classList.toggle('active-filter-input', searchInput.value.trim().length > 0);
            }
        }

        // Filtro de dados
        function filterDataset() {
            filteredRecords = RAW_DATA.filter(r => {
                const mG = matchesAnyFilter(filters.gender, r.genero);
                const mR = matchesAnyFilter(filters.raca, r.raca);
                const mE = matchesAnyFilter(filters.escolaridade, r.escolaridade);
                const mV = matchesAnyFilter(filters.vinculo, r.vinculo);
                const mP = matchesAnyFilter(filters.pcd, r.pcd);
                const mReg = matchesAnyFilter(filters.regiao, r.regiao);
                const mM = matchesAnyFilter(filters.municipio, r.municipio);
                const mS = matchesAnyFilter(filters.status, r.status);
                let mSrch = true;
                if (filters.search.trim()) {
                    const s = filters.search.toLowerCase();
                    mSrch = r.nome.toLowerCase().includes(s) ||
                            r.cargo.toLowerCase().includes(s) ||
                            r.municipio.toLowerCase().includes(s) ||
                            (r.nome_social && r.nome_social.toLowerCase().includes(s));
                }
                return mG && mR && mE && mV && mP && mReg && mM && mS && mSrch;
            });
            currentPage = 1;
            updateActiveFilterStyles();
            updateMetrics();
            renderTable();
            updateChartsData();
            renderRegionalData();
        }

        // Cartões de métricas
        function updateMetrics() {
            const total = filteredRecords.length;
            document.getElementById('metricTotal').textContent = total;
            if (total === 0) {
                ['metricMulheres','metricNegros','metricIndigenas','metricPcd','metricContratos']
                    .forEach(id => document.getElementById(id).textContent = '0');
                return;
            }
            const women = filteredRecords.filter(r => r.genero.includes('MULHER') || r.genero === 'FEMININO').length;
            document.getElementById('metricMulheres').textContent = ((women / total) * 100).toFixed(0);

            const blacks = filteredRecords.filter(r => ['PARDA','PRETA','QUILOMBOLA'].includes(r.raca)).length;
            document.getElementById('metricNegros').textContent = ((blacks / total) * 100).toFixed(0);

            const ind = filteredRecords.filter(r => r.raca === 'INDÍGENA').length;
            document.getElementById('metricIndigenas').textContent = ((ind / total) * 100).toFixed(0);

            const pcdCount = filteredRecords.filter(r => r.pcd === 'SIM').length;
            document.getElementById('metricPcd').textContent = pcdCount;

            const contracts = filteredRecords.filter(r => r.vinculo === 'CONTRATO').length;
            document.getElementById('metricContratos').textContent = ((contracts / total) * 100).toFixed(0);
        }

        // Tabela paginada
        function renderTable() {
            const tableBody = document.getElementById('tableBody');
            tableBody.innerHTML = '';
            const total = filteredRecords.length;
            if (total === 0) {
                tableBody.innerHTML = `<tr><td colspan="10" class="p-8 text-center text-slate-400 dark:text-slate-500 font-medium">
                    <i class="fa-solid fa-circle-exclamation text-2xl mb-2 block text-brand-coral"></i>
                    Nenhum registro encontrado com os filtros ativos.</td></tr>`;
                document.getElementById('tablePaginationInfo').textContent = 'Mostrando 0 registros';
                document.getElementById('btnPrevPage').disabled = true;
                document.getElementById('btnNextPage').disabled = true;
                document.getElementById('pagesList').innerHTML = '';
                return;
            }
            const startIndex = (currentPage - 1) * rowsPerPage;
            const endIndex = Math.min(startIndex + rowsPerPage, total);
            filteredRecords.slice(startIndex, endIndex).forEach((r, idx) => {
                const tr = document.createElement('tr');
                tr.className = "border-b border-slate-100 dark:border-slate-900 hover:bg-slate-100/40 dark:hover:bg-slate-900/30 transition-colors";
                const pcdBadge = r.pcd === 'SIM'
                    ? '<span class="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-bold text-[10px]">SIM</span>'
                    : '<span class="text-slate-400 dark:text-slate-600">-</span>';
                let sColor = "bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400";
                if (r.status === 'DESISTENTE') sColor = "bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400";
                else if (r.status === 'EDIÇÃO LIBERADA') sColor = "bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400";
                const statusBadge = `<span class="inline-block px-2 py-0.5 rounded-full font-bold text-[9px] uppercase ${sColor}">${r.status}</span>`;
                const displayNome = r.nome_social
                    ? `<div>${r.nome_social} <span class="text-[10px] text-slate-400 block font-normal">Civil: ${r.nome}</span></div>`
                    : `<div>${r.nome}</div>`;
                tr.innerHTML = `
                    <td class="p-3.5 text-slate-400 font-bold">${startIndex + idx + 1}</td>
                    <td class="p-3.5 font-semibold text-slate-900 dark:text-white">${displayNome}</td>
                    <td class="p-3.5 font-medium">${r.municipio}</td>
                    <td class="p-3.5 text-slate-500">${r.regiao}</td>
                    <td class="p-3.5 font-medium">${r.cargo}</td>
                    <td class="p-3.5 text-slate-500">${r.vinculo.toLowerCase()}</td>
                    <td class="p-3.5 text-slate-500">${r.raca.toLowerCase()}</td>
                    <td class="p-3.5 text-slate-500">${r.genero.toLowerCase()}</td>
                    <td class="p-3.5 text-center">${pcdBadge}</td>
                    <td class="p-3.5 text-center">${statusBadge}</td>`;
                tableBody.appendChild(tr);
            });
            document.getElementById('tablePaginationInfo').textContent = `Mostrando ${startIndex + 1}-${endIndex} de ${total} registros`;
            const totalPages = Math.ceil(total / rowsPerPage);
            document.getElementById('btnPrevPage').disabled = currentPage === 1;
            document.getElementById('btnNextPage').disabled = currentPage === totalPages;
            const pagesList = document.getElementById('pagesList');
            pagesList.innerHTML = '';
            let startPage = Math.max(1, currentPage - 2);
            let endPage = Math.min(totalPages, startPage + 4);
            if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);
            for (let p = startPage; p <= endPage; p++) {
                const btn = document.createElement('button');
                btn.className = `w-7 h-7 rounded-lg border text-xs font-semibold transition-all ${p === currentPage
                    ? 'bg-brand-teal text-white border-brand-teal'
                    : 'bg-slate-100 dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:bg-slate-200 dark:hover:bg-slate-800'}`;
                btn.textContent = p;
                btn.addEventListener('click', () => { currentPage = p; renderTable(); });
                pagesList.appendChild(btn);
            }
        }

        // Análise regional
        function renderRegionalData() {
            const regionsCount = {};
            filteredRecords.forEach(r => { regionsCount[r.regiao] = (regionsCount[r.regiao] || 0) + 1; });
            const sorted = Object.entries(regionsCount).sort((a, b) => b[1] - a[1]);
            const regionsList = document.getElementById('regionsList');
            regionsList.innerHTML = '';
            if (sorted.length === 0) {
                regionsList.innerHTML = '<p class="text-xs text-slate-400">Nenhum dado regional.</p>';
            } else {
                const maxCount = sorted[0][1];
                sorted.forEach(([region, count]) => {
                    if (!region || region === 'Não Informada') return;
                    const pct = ((count / filteredRecords.length) * 100).toFixed(0);
                    const w = maxCount > 0 ? (count / maxCount) * 100 : 0;
                    const el = document.createElement('div');
                    el.className = 'space-y-1';
                    el.innerHTML = `
                        <div class="flex items-center justify-between text-xs font-medium">
                            <span class="truncate pr-2">${region}</span>
                            <span class="text-slate-400">${count} (${pct}%)</span>
                        </div>
                        <div class="h-1.5 w-full bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                            <div class="h-full bg-brand-teal rounded-full" style="width:${w}%"></div>
                        </div>`;
                    regionsList.appendChild(el);
                });
            }
            const citiesCount = {};
            filteredRecords.forEach(r => { citiesCount[r.municipio] = (citiesCount[r.municipio] || 0) + 1; });
            const sortedCities = Object.entries(citiesCount).sort((a, b) => b[1] - a[1]).slice(0, 10);
            const grid = document.getElementById('municipalitiesGrid');
            grid.innerHTML = '';
            if (sortedCities.length === 0) {
                grid.innerHTML = '<p class="text-xs text-slate-400 col-span-2">Nenhum dado de município.</p>';
            } else {
                sortedCities.forEach(([city, count]) => {
                    const card = document.createElement('div');
                    card.className = 'flex items-center justify-between p-3 bg-slate-100/40 dark:bg-slate-950/20 border border-slate-200/30 dark:border-slate-800/30 rounded-xl';
                    card.innerHTML = `
                        <span class="text-xs font-bold text-slate-700 dark:text-slate-300 truncate max-w-[120px]">${city}</span>
                        <span class="px-2 py-0.5 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-brand-teal font-extrabold text-xs border border-teal-100/40 dark:border-teal-900/40">${count}</span>`;
                    grid.appendChild(card);
                });
            }
        }

        // Exportar CSV
        function exportToCSV() {
            if (filteredRecords.length === 0) return;
            let csv = "data:text/csv;charset=utf-8,\\ufeff";
            csv += "ID;Nome Completo;Nome Social;Status;Local de Atuacao;Turma;Municipio;Regiao de Saude;Escolaridade;Cargo;Vinculo;Raca/Etnia;Genero;PCD\\r\\n";
            filteredRecords.forEach(r => {
                csv += [r.id, `"${r.nome}"`, `"${r.nome_social}"`, r.status, `"${r.local}"`,
                        `"${r.turma}"`, `"${r.municipio}"`, `"${r.regiao}"`, `"${r.escolaridade}"`,
                        `"${r.cargo}"`, `"${r.vinculo}"`, `"${r.raca}"`, `"${r.genero}"`, r.pcd
                ].join(";") + "\\r\\n";
            });
            const link = document.createElement("a");
            link.setAttribute("href", encodeURI(csv));
            link.setAttribute("download", "indicacoes_filtradas_nos_na_rede.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        // Cores dos gráficos
        function getChartColors() {
            const dark = document.documentElement.classList.contains('dark');
            return {
                text: dark ? '#cbd5e1' : '#5f646d',
                grid: dark ? '#263244' : '#dde3ea',
                raca: ['rgba(233,75,60,.88)','rgba(47,128,193,.88)','rgba(51,166,217,.88)','rgba(242,207,67,.92)','rgba(120,189,67,.88)','rgba(237,79,154,.88)','rgba(95,100,109,.74)'],
                racaBorders: ['#E94B3C','#2F80C1','#33A6D9','#F2CF43','#78BD43','#ED4F9A','#5F646D'],
                levels: ['rgba(47,128,193,.88)','rgba(51,166,217,.88)','rgba(120,189,67,.88)','rgba(242,207,67,.92)','rgba(237,79,154,.88)','rgba(233,75,60,.88)'],
                levelsBorders: ['#2F80C1','#33A6D9','#78BD43','#F2CF43','#ED4F9A','#E94B3C'],
                vinculos: ['rgba(47,128,193,.88)','rgba(120,189,67,.88)','rgba(242,207,67,.92)','rgba(233,75,60,.88)','rgba(237,79,154,.88)'],
                vinculosBorders: ['#2F80C1','#78BD43','#F2CF43','#E94B3C','#ED4F9A'],
                genders: ['rgba(237,79,154,.88)','rgba(47,128,193,.88)','rgba(95,100,109,.70)','rgba(242,207,67,.92)'],
                gendersBorders: ['#ED4F9A','#2F80C1','#5F646D','#F2CF43']
            };
        }

        // Atualiza / cria gráficos Chart.js
        function updateChartsData() {
            if (typeof Chart === 'undefined') {
                console.warn("Chart.js não carregado. Gráficos indisponíveis.");
                return;
            }
            try {
                const c = getChartColors();

                // --- RAÇA / ETNIA ---
                const racaCounts = {};
                filteredRecords.forEach(r => { racaCounts[r.raca] = (racaCounts[r.raca] || 0) + 1; });
                const racaLabels = Object.keys(racaCounts);
                const racaData = Object.values(racaCounts);
                if (chartRacaInstance) {
                    chartRacaInstance.data.labels = racaLabels.map(l => capitalizePortuguese(l));
                    chartRacaInstance.data.datasets[0].data = racaData;
                    chartRacaInstance.data.datasets[0].backgroundColor = c.raca;
                    chartRacaInstance.data.datasets[0].borderColor = c.racaBorders;
                    chartRacaInstance.options.scales.x.grid.color = c.grid;
                    chartRacaInstance.options.scales.y.grid.color = c.grid;
                    chartRacaInstance.options.scales.x.ticks.color = c.text;
                    chartRacaInstance.options.scales.y.ticks.color = c.text;
                    chartRacaInstance.update();
                } else {
                    chartRacaInstance = new Chart(document.getElementById('chartRaca').getContext('2d'), {
                        type: 'bar',
                        data: { labels: racaLabels.map(l => capitalizePortuguese(l)), datasets: [{ label: 'Indicações', data: racaData, backgroundColor: c.raca, borderColor: c.racaBorders, borderWidth: 1.5, borderRadius: 8 }] },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { padding: 12, borderRadius: 12 } }, scales: { x: { grid: { color: c.grid }, ticks: { color: c.text, font: { family: 'Inter', weight: '500' } } }, y: { grid: { color: c.grid }, ticks: { color: c.text, stepSize: 10 } } } }
                    });
                }

                // --- ESCOLARIDADE ---
                const escCounts = {};
                filteredRecords.forEach(r => { escCounts[r.escolaridade] = (escCounts[r.escolaridade] || 0) + 1; });
                const sortedEsc = Object.entries(escCounts).sort((a, b) => b[1] - a[1]);
                const escLabels = sortedEsc.map(x => x[0]);
                const escData = sortedEsc.map(x => x[1]);
                if (chartEscolaridadeInstance) {
                    chartEscolaridadeInstance.data.labels = escLabels;
                    chartEscolaridadeInstance.data.datasets[0].data = escData;
                    chartEscolaridadeInstance.data.datasets[0].backgroundColor = c.levels;
                    chartEscolaridadeInstance.data.datasets[0].borderColor = c.levelsBorders;
                    chartEscolaridadeInstance.options.scales.x.grid.color = c.grid;
                    chartEscolaridadeInstance.options.scales.y.grid.color = c.grid;
                    chartEscolaridadeInstance.options.scales.x.ticks.color = c.text;
                    chartEscolaridadeInstance.options.scales.y.ticks.color = c.text;
                    chartEscolaridadeInstance.update();
                } else {
                    chartEscolaridadeInstance = new Chart(document.getElementById('chartEscolaridade').getContext('2d'), {
                        type: 'bar',
                        data: { labels: escLabels, datasets: [{ label: 'Indicações', data: escData, backgroundColor: c.levels, borderColor: c.levelsBorders, borderWidth: 1.5, borderRadius: 8 }] },
                        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { padding: 12, borderRadius: 12 } }, scales: { x: { grid: { color: c.grid }, ticks: { color: c.text } }, y: { grid: { display: false }, ticks: { color: c.text, font: { family: 'Inter', size: 10 } } } } }
                    });
                }

                // --- VÍNCULO ---
                const vinCounts = {};
                filteredRecords.forEach(r => { vinCounts[r.vinculo] = (vinCounts[r.vinculo] || 0) + 1; });
                const vinLabels = Object.keys(vinCounts);
                const vinData = Object.values(vinCounts);
                if (chartVinculoInstance) {
                    chartVinculoInstance.data.labels = vinLabels.map(l => capitalizePortuguese(l));
                    chartVinculoInstance.data.datasets[0].data = vinData;
                    chartVinculoInstance.data.datasets[0].backgroundColor = c.vinculos;
                    chartVinculoInstance.data.datasets[0].borderColor = c.vinculosBorders;
                    if (chartVinculoInstance.options.plugins.legend && chartVinculoInstance.options.plugins.legend.labels)
                        chartVinculoInstance.options.plugins.legend.labels.color = c.text;
                    chartVinculoInstance.update();
                } else {
                    chartVinculoInstance = new Chart(document.getElementById('chartVinculo').getContext('2d'), {
                        type: 'doughnut',
                        data: { labels: vinLabels.map(l => capitalizePortuguese(l)), datasets: [{ data: vinData, backgroundColor: c.vinculos, borderColor: c.vinculosBorders, borderWidth: 2, hoverOffset: 12 }] },
                        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'right', labels: { color: c.text, usePointStyle: true, font: { family: 'Inter', size: 11 } } }, tooltip: { padding: 12, borderRadius: 12 } } }
                    });
                }

                // --- GÊNERO ---
                const genCounts = {};
                filteredRecords.forEach(r => { genCounts[r.genero] = (genCounts[r.genero] || 0) + 1; });
                const genLabels = Object.keys(genCounts);
                const genData = Object.values(genCounts);
                if (chartGeneroInstance) {
                    chartGeneroInstance.data.labels = genLabels.map(l => capitalizePortuguese(l));
                    chartGeneroInstance.data.datasets[0].data = genData;
                    chartGeneroInstance.data.datasets[0].backgroundColor = c.genders;
                    chartGeneroInstance.data.datasets[0].borderColor = c.gendersBorders;
                    if (chartGeneroInstance.options.plugins.legend && chartGeneroInstance.options.plugins.legend.labels)
                        chartGeneroInstance.options.plugins.legend.labels.color = c.text;
                    chartGeneroInstance.update();
                } else {
                    chartGeneroInstance = new Chart(document.getElementById('chartGenero').getContext('2d'), {
                        type: 'pie',
                        data: { labels: genLabels.map(l => capitalizePortuguese(l)), datasets: [{ data: genData, backgroundColor: c.genders, borderColor: c.gendersBorders, borderWidth: 2, hoverOffset: 12 }] },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: c.text, usePointStyle: true, font: { family: 'Inter', size: 11 } } }, tooltip: { padding: 12, borderRadius: 12 } } }
                    });
                }
            } catch (err) {
                console.error("Erro ao renderizar gráficos:", err);
            }
        }

        // Inicialização e eventos
        window.addEventListener('DOMContentLoaded', () => {
            populateFilterOptions();

            createAllMultiDropdowns();
            document.addEventListener('click', closeMultiDropdownsOnOutsideClick);

            document.getElementById('tableSearch').addEventListener('input', e => { filters.search = e.target.value; filterDataset(); });

            document.getElementById('clearFilters').addEventListener('click', () => {
                filters = { gender:[], raca:[], escolaridade:[], vinculo:[], pcd:[], regiao:[], municipio:[], status:[], search:'' };
                Object.keys(FILTER_CONFIG).forEach(id => setSelectedValues(id, []));
                document.getElementById('tableSearch').value = '';
                filterDataset();
            });

            document.getElementById('btnPrevPage').addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderTable(); } });
            document.getElementById('btnNextPage').addEventListener('click', () => {
                const totalPages = Math.ceil(filteredRecords.length / rowsPerPage);
                if (currentPage < totalPages) { currentPage++; renderTable(); }
            });

            document.getElementById('exportCsv').addEventListener('click', exportToCSV);

            filterDataset();
            refreshDashboardData(true);
            setInterval(() => refreshDashboardData(false), AUTO_REFRESH_INTERVAL_MS);
            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) refreshDashboardData(false);
            });
        });
    </script>
</body>
</html>
"""


def generate_dashboard():
    try:
        import base64

        print("Lendo e higienizando os dados do arquivo CSV local...")
        records = load_and_clean_data(CSV_PATH)
        print(f"Total de registros carregados com sucesso: {len(records)}")

        json_data = json.dumps(records, ensure_ascii=False, indent=2)

        # Logo principal
        logo_path = '/Users/tiagosobraldelima/Desktop/NÓS NA REDE_LOGO.png'
        logo_base64 = ""
        if os.path.exists(logo_path):
            print("Carregando e codificando a logo em base64...")
            with open(logo_path, "rb") as img_file:
                logo_base64 = "data:image/png;base64," + base64.b64encode(img_file.read()).decode('utf-8')
        else:
            print("Logo não encontrada na Área de Trabalho. Usando fallback...")
            logo_base64 = "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=128"

        # Régua de assinatura
        ruler_path = '/Users/tiagosobraldelima/Desktop/regua-assinatura-fio-brasilia.png'
        ruler_base64 = ""
        if os.path.exists(ruler_path):
            print("Carregando e codificando a régua de logos em base64...")
            with open(ruler_path, "rb") as img_file:
                ruler_base64 = "data:image/png;base64," + base64.b64encode(img_file.read()).decode('utf-8')
        else:
            print("Régua de logos não encontrada na Área de Trabalho. Usando fallback...")
            ruler_base64 = "https://brasilia.fiocruz.br/nosnarede/wp-content/uploads/sites/10/2025/10/regua-assinatura-fio-brasilia.png"

        compiled_html = HTML_TEMPLATE.replace("<!-- DATA_PLACEHOLDER -->", json_data)
        compiled_html = compiled_html.replace("<!-- LOGO_PLACEHOLDER -->", logo_base64)
        compiled_html = compiled_html.replace("<!-- REGUA_PLACEHOLDER -->", ruler_base64)

        os.makedirs(os.path.dirname(SCRATCH_OUTPUT), exist_ok=True)
        print(f"Escrevendo arquivo HTML compilado em: {SCRATCH_OUTPUT}...")
        with open(SCRATCH_OUTPUT, mode='w', encoding='utf-8') as f:
            f.write(compiled_html)

        downloads_html = os.path.join(OUTPUT_DIR, 'dashboard_nos_na_rede.html')
        print(f"Escrevendo cópia em Downloads: {downloads_html}...")
        with open(downloads_html, mode='w', encoding='utf-8') as f:
            f.write(compiled_html)

        print("Dashboard compilado com absoluto sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro no processamento: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    generate_dashboard()
