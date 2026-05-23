# Guia de Implantação no Google Sites

Este documento fornece as instruções necessárias para visualizar e incorporar o seu novo **Dashboard Interativo do Nós na Rede Alagoas** no **Google Sites**.

O arquivo do dashboard foi gerado em dois locais convenientes no seu computador:
1. **Pasta do Projeto**: `/Users/tiagosobraldelima/Documents/New project/nos_na_rede_dashboard_live/index.html`
2. **Pasta de Downloads**: `/Users/tiagosobraldelima/Downloads/dashboard_nos_na_rede.html`

---

## Atualização Automática dos Dados

Esta versão usa como base a planilha publicada em CSV:

`https://docs.google.com/spreadsheets/d/e/2PACX-1vR1Zb8Ljbb9fB7BFQpC85FOPQ0QtJARSNt2y8hpbTlV4yrKJFmbuNEBVeThbS-JMSCkTIID2Qe6Kc6J/pub?gid=973871607&single=true&output=csv`

O dashboard mantém uma cópia inicial dos dados dentro do HTML para abrir rapidamente, mas também possui um gatilho de atualização no navegador:

* busca a planilha publicada ao carregar a página;
* verifica novamente a cada 60 segundos;
* verifica novamente quando a aba/janela volta a ficar ativa;
* reaplica filtros, tabela e gráficos sempre que detectar mudança no CSV.

Observação: em páginas HTML estáticas incorporadas no Google Sites, o Google Sheets não envia um evento em tempo real para o iframe. Por isso, o gatilho foi implementado por verificação periódica da planilha publicada, que é o comportamento compatível com incorporação estática.

---

## 1. Visualização Local (Teste Rápido)

Para testar o dashboard imediatamente em seu computador:
1. Abra a sua pasta de **Downloads**.
2. Dê um duplo-clique no arquivo `dashboard_nos_na_rede.html`.
3. O dashboard abrirá no seu navegador padrão (Safari, Chrome ou Firefox) com total interatividade:
   * Experimente alterar os filtros (Gênero, Raça/Etnia, Escolaridade, Vínculo, PCD, Região de Saúde, Município).
   * Digite termos na barra de busca (como o nome de uma pessoa ou cargo).
   * Alterne entre o **Modo Claro** e o **Modo Escuro** clicando no ícone de sol/lua no cabeçalho.
   * Clique no botão **"Exportar CSV"** para baixar a lista de acordo com os filtros selecionados.

---

## 2. Como Incorporar no Google Sites (Passo a Passo)

Como o dashboard é um arquivo HTML único e 100% auto-contido, a sua incorporação no **Google Sites** é extremamente simples e não requer hospedagem externa de banco de dados.

Siga os passos abaixo:

### Passo A: Copiar o Código do Dashboard
1. Abra o arquivo `dashboard_nos_na_rede.html` em um editor de texto (como o **TextEdit** do Mac, VS Code, Sublime Text, ou qualquer outro de sua preferência).
   * *Dica no Mac*: Você também pode abrir o terminal e rodar `cat ~/Downloads/dashboard_nos_na_rede.html | pbcopy` para copiar o código diretamente para a área de transferência.
2. Selecione todo o código (`Cmd + A` no Mac) e copie (`Cmd + C`).

### Passo B: Inserir no Google Sites
1. Acesse o [Google Sites](https://sites.google.com/) e abra o site onde deseja inserir o painel em modo de edição.
2. No menu lateral direito, clique na aba **"Inserir"** (Insert).
3. Selecione a opção **"Incorporar"** (Embed) — o ícone se parece com `< >`.
4. Na janela popup que se abre, clique na aba **"Incorporar código"** (Embed code).
5. Cole o código copiado na caixa de texto (`Cmd + V`).
6. Clique em **"Próximo"** (Next). O Google Sites carregará uma pré-visualização em tempo real do dashboard.
7. Clique em **"Inserir"** (Insert).

### Passo C: Ajustar a Visualização
1. O bloco do dashboard agora estará na sua página. Use as alças azuis nas bordas do bloco para redimensioná-lo:
   * **Largura**: Estenda o bloco horizontalmente até o limite da sua página para que a tabela e os gráficos fiquem bem espaçados.
   * **Altura**: Puxe a borda inferior do bloco para baixo para que a página inteira fique visível sem barras de rolagem duplas desnecessárias dentro do iframe.
2. Clique no botão azul **"Publicar"** (Publish) no canto superior direito do Google Sites para salvar as alterações e disponibilizar o dashboard para o público.
