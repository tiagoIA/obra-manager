# Obra Manager / CrewNelo — mapa de continuidade

Auditoria base em 16/10/2026; atualização Estimates em 17/10/2026, America/New_York. Responsável pelo produto: Tiago Elias.

## Comece aqui, em qualquer chat novo

1. Leia este mapa inteiro. Consulte a versão mais recente em `tiagoIA/obra-manager`, branch `main`, arquivo `MAPA_DO_PROJETO.md`. Se GitHub estiver inacessível, use a cópia entregue pelo usuário.
2. Não confunda a branch padrão com a versão em produção. `main` estava atrasada nesta auditoria. O HTML ao vivo corresponde exatamente a `feature/purchase-suggestions-2026-10-16`, commit `9534a413b3f08fe9e64701da1464feb3cbb7002b`; diversos módulos preservados em Hosting vêm de outras branches.
3. Abra `/app.html` para o sistema. A raiz `/` é a apresentação pública CrewNelo. Obra Manager e CrewNelo são nomes presentes na mesma aplicação.
4. Confirme separadamente: GitHub, login do aplicativo, console Firebase, leitura do Firestore, Storage e permissões de publicação. Uma conexão não comprova todas as outras.
5. Antes de editar, compare o arquivo atual de produção, a branch e os hashes. Preserve assets fora do escopo. Consulte o inventário de arquivos ao final.
6. Retome o pedido atual do usuário; não refaça módulos concluídos só porque um resumo antigo os descreve como proposta.

Este documento transfere instruções e evidências, não transfere sessão, senha ou permissões. Acesso pode expirar. Não alegue acesso sem verificar. Não prometa memória automática entre chats.

## Endereços e ambientes

| Destino | Identificação / caminho | Situação nesta auditoria |
|---|---|---|
| Repositório | https://github.com/tiagoIA/obra-manager | Público; leitura e permissões push/admin retornadas pela conexão |
| Página pública | https://obra-manager-4ecc7.web.app/ | CrewNelo; HTTP 200 e interface observada |
| Sistema | https://obra-manager-4ecc7.web.app/app.html | Login concluído; obras e dados reais carregados |
| Firebase produção | https://console.firebase.google.com/project/obra-manager-4ecc7/overview | Console autenticado; projeto `obra-manager`; plano Blaze observado |
| Firestore produção | Produto Firestore no console de produção | Banco `(default)`, região `nam5`; coleções e documento existentes lidos |
| Storage produção | `obra-manager-4ecc7.firebasestorage.app` | Bucket configurado no código; upload/gravação não testados nesta auditoria |
| Firebase teste | Projeto `obra-manager-teste`, nome “Obra Manager Teste” | Console acessível; Spark; Firestore mostra “Criar banco de dados”; Auth mostra “Vamos começar” |
| Piloto empresas | Branch `feature/company-registration-2026-10-16`, pasta `pilot/` | Código e documentação inspecionados; PR #3 aberto; não tratar como implantação pronta |

## Como obter e conferir os acessos

### GitHub

Usar primeiro a conexão GitHub disponível no chat. Operações verificadas: `get_repo` com `repository_full_name: tiagoIA/obra-manager`; `fetch` para árvores, branches e PRs; `fetch_file` para arquivos. A consulta direta pelo nome encontrou o repositório. Uma lista vazia não prova ausência de acesso.

Para checkout local de leitura, `git clone https://github.com/tiagoIA/obra-manager.git` funcionou sem credenciais por ser público. Isso não fornece autenticação de escrita ao terminal. Para gravação, usar a conexão autenticada ou uma configuração git já autorizada. Não extrair credenciais do navegador.

`fetch_file` retorna conteúdo e blob SHA. `update_file` exige o SHA atual; `create_file` só serve para caminho inexistente. Em múltiplas alterações, preservar o pai/HEAD e evitar sobrescrever trabalho concorrente. Conferir a árvore inteira e quaisquer `AGENTS.md` antes da edição.

### Sistema

Na página pública, “Log in” abre `/app.html`. O formulário oferece Email, Password e Enter. O aplicativo usa Firebase Auth `signInWithEmailAndPassword`; o login do Google no console é separado. Um erro “Invalid email or password” foi resolvido por nova tentativa solicitada pelo usuário; não foi necessário recriar conta nem alterar permissões.

Se a sessão não estiver disponível no novo chat, usar o fluxo seguro de autenticação oferecido pelo navegador. Não pedir senhas/códigos em mensagens, não copiá-los para Markdown, Issues, commits ou capturas. Após entrar, verificar perfil e obras carregados; envio do formulário sozinho não confirma sucesso.

### Firebase

Abrir o console do projeto exato. O acesso foi recuperado pelo fluxo seguro de login Google da conta do proprietário; em seguida o console exibiu o projeto e o Firestore. Usar o seletor de projetos para alternar entre produção e “Obra Manager Teste”. Não fazer alterações de cobrança para apenas investigar.

Credenciais de automação são referenciadas pelo nome do secret GitHub `FIREBASE_SERVICE_ACCOUNT`. Os workflows injetam seu valor como `FIREBASE_SA`; não imprimir o valor nem criar cópias em arquivos entregáveis. Os scripts conferem `project_id`. O fato de o secret ser referenciado no YAML não prova que o próximo chat possa lê-lo ou usá-lo localmente.

## Arquitetura e mapa de dados

Frontend vanilla HTML/CSS/JavaScript, PWA, Firebase Web SDK 10.12.0. `app.html` contém grande parte da interface, listeners, autenticação e funções globais. As funcionalidades recentes também usam módulos ES externos. Há service worker e persistência local/IndexedDB; preservar filas de mídia e trabalho não sincronizado.

O código referencia `claudeProxy` na região `us-central1`, projeto de produção, para recursos assistidos. Sua presença no cliente não comprova disponibilidade, autorização, custo nem versão atual do backend. Não trocar o provedor nem criar nova chave de IA como parte da retomada.

Coleções vistas no Firestore de produção:

| Coleção | Papel no código / observação |
|---|---|
| projects | Obras; nome/endereço e campos associados |
| rooms | Unidades/ambientes, vinculados por `projectId` |
| tasks | Tarefas com `projectId`, `roomId`, conclusão, fotos e subtarefas |
| roomNotes | Notas e evidências por ambiente |
| materials | Biblioteca central e registros legados de tarefas/materiais |
| productDB | Base legada de produtos; não presumir equivalência com `materials` |
| shoppingLists | Cabeçalhos/listas e modelos conforme código atual |
| shoppingItems | Itens vinculados à lista e ao material |
| invoices | Cabeçalho de compras/notas, status e anexos |
| invoiceItems | Linhas de compra e vínculo de material |
| jobs | Trabalhos/jobs e acompanhamento |
| clockEntries | Entradas de horas, clock-in/out e pausas |
| reminders | Lembretes |
| users | Perfis; não publicar dados de pessoas |
| userLocations | Localização; não copiar histórico de localização para documentação pública |
| automationBackups | Backups de operações específicas |
| maintenanceOperations | Controle de operações/manutenção e idempotência |

Relação central: `projects` → `rooms.projectId` → `tasks.roomId/projectId`. Nem todos os campos são subcoleções; várias consultas da aplicação usam coleções globais. O piloto multiempresa usa outro modelo. Não instalar as regras do piloto em produção: a documentação alerta que elas negam as coleções legadas.

Um documento de backup existente foi aberto no console, mostrando tarefas e subtarefas com IDs preservados, `done`, `doneAt`, `photos`, `sortOrder`, `createdAt` e `updatedAt`. Isso comprova leitura do banco, não uma restauração integral testada. Não tratar um backup de duas tarefas como backup total do projeto.

## Onde editar cada função

| Área | Arquivos / pontos de entrada |
|---|---|
| Login, Home, obras, unidades, tarefas, Planning, Timeline, horas, navegação | `public/app.html`; localizar handlers antes de editar |
| Página pública CrewNelo | `public/index.html`, `crewnelo.js`, `crewnelo.css`, marca SVG |
| PWA/mobile | `sw.js`, `manifest.json`, `mobile-layout.css`; conferir cache e versões |
| Catálogo e identidade de produtos | `central-catalog-v1.js`, `product-library.js`, `product-search.js`, `product-enrichment.js`, `material-attributes.js` |
| Categorias/filtros e seleção de compras | `shopping-catalog.js`, `shopping-picker-core.js` |
| Compras e Lista Guiada | `shopping-view-v3.js`, `guided-shopping-v2.js`, integração em `app.html` |
| Sugestões de acessórios | `purchase-suggestions.js`, `purchase-suggestions-ui.js` |
| Nota fiscal e custos | `purchasing-core.js`, `invoice-store.js`, `receipt-review.js`, `costs-dashboard.js` |
| Fotos/notas e fila de mídia | `field-media.js`, `note-photos.js` e integração no HTML |
| Resumo de obra e retornos | `project-brief.js`, `unit-followup.js`, `unit-report-language.js`, `unit-report-structure.js` |
| Fotos por Unidade 2.0 e PDF direto | `photo-report.js`, `photo-report-pdf.js`, `photo-report-cover.js`, `report-photo-order.js`, `work-progress.js`, `vendor/pdf-lib.esm.min.js` |
| Empresas/cadastro/convites | Branch do piloto; `pilot/site/`, `pilot/functions/`, regras e testes em `pilot/`; `public/company-scope.js` como base de integração |
| Importação de catálogo | `catalog-expansion/`, `scripts/import_catalog_expansion.py`, `import_box_catalog.py`; scripts com gravação, não simples auditorias |

Handlers úteis em `app.html`: `doLogin`, `openHomePage`, `switchProject`, `openRoom`, `saveTaskEdit`, `toggleTask`, `toggleSubtask`, `renderPlanningPage`, `saveDailyAssignments`, `completeDailyTask`, `openSiteSchedule`, `saveSiteSchedule`, `toggleClockInOut`, `confirmClockIn`, `toggleBreak`, `openChangeJob`, `exportTimesheetCSV`, `generateReport`, `generateShopPDF`, `saveRoomNote`, `saveQuickCapture`.

Localização prática: `rg -n 'nomeDoHandler|nomeDoModulo' public/app.html public/`. Evitar reescrever o HTML inteiro para uma alteração localizada. Conferir imports e dependências, não apenas o arquivo modificado.

## Produção versus branches

| Referência | Uso correto |
|---|---|
| `main` em `168c0143e986ce0c1fa4394eb4c87a77329aa6c5` antes deste mapa | Histórico antigo; não publicar seus assets como se fossem a versão atual |
| `feature/purchase-suggestions-2026-10-16` em `9534a413b3f08fe9e64701da1464feb3cbb7002b` | HTML de produção e módulos recentes de catálogo/compras; melhor ponto inicial para essas áreas |
| `work/catalog-expansion-2026-10-16` em `7948b58998a978b7846b64628373d7cf612292a9` | Manifestos de importação, expansão e filtros; predecessor das sugestões |
| `feature/company-registration-2026-10-16` em `95d3b7174ab03c562b05247b950c127b26fce72a` | Cadastro/convites isolados; PR #3 aberto para `feature/company-isolation-pilot-2026-10-13` |
| `feature/unit-followup-2026-10-09` em `0d50496e3a72f8af08dfdd685745628ddd06dfed` | Código de retornos/brief e auditorias de compras; não representa sozinho toda a produção atual |
| `ops/melrose-progress-2026-10-16` em `123e11e36c6593f13630cef84ea3cb537f7fed40` | Scripts operacionais de atualização/anexos; não executar de novo só para conhecer o sistema |
| `fix/compact-photo-pdf-2026-10-15` | Correções do exportador compacto e paginação |
| `feature/compact-home-selection-2026-10-15` / `fix/pdf-export-followup-2026-10-15` | Referências para service worker e seleção compacta |

O Hosting contém uma composição de arquivos preservados em publicações sucessivas. A branch de sugestões não contém todos os módulos preservados com os mesmos bytes. O inventário abaixo identifica correspondências exatas. Antes de consolidar branches, comparar cada arquivo ao vivo; não usar merge indiscriminado.

## Editar, testar e publicar com segurança

1. Atualizar leitura de HEAD/árvore e dos assets de produção. Guardar hash SHA-256 dos bytes originais e versão/release do Hosting, se a alteração envolver publicação.
2. Criar branch de trabalho apropriada sem descartar os módulos preservados em Hosting. Não colocar produção antiga de `main` por cima da atual.
3. Fazer patch localizado. Para alterações de dados, primeiro ler os documentos alvo, preservar IDs/relações e preparar operação idempotente com backup dos campos afetados.
4. Executar testes pertinentes à área, não todos os scripts operacionais. Teste local não é prova de escrita online nem de publicação.
5. Ler o workflow antes do push: várias branches publicam ou gravam no banco automaticamente ao alterar caminhos específicos. Um commit pode produzir efeitos externos.
6. Publicar somente o escopo autorizado. Os scripts recentes clonam a versão atual do Hosting, substituem um conjunto explícito de arquivos, validam preview e depois live; preservam outros assets e interrompem se o baseline mudou. Não remover essas proteções.
7. Conferir conclusão do workflow, resultado/artifact e os bytes live. Verificar também a tela pertinente. Registrar commit, run, release, dados alterados e limitações no mapa.

Fluxo concreto recente: `.github/workflows/purchase_suggestions.yml` é acionado por push na branch `feature/purchase-suggestions-2026-10-16` quando mudam `public/**`, testes `suggestions*`, manifesto ou o próprio workflow. Roda testes Node/browser e `scripts/publish_suggestions.py`. Usa `scripts/suggestion-publication.json`, com hashes esperados de origem e baseline. O script verifica `app.html` e módulos, clona a versão live, publica preview, verifica, publica live e pode restaurar a versão anterior se a verificação falhar. Concurrency usa `obra-manager-hosting-publication`.

Outros fluxos: `catalog_expansion.yml`, `box_catalog.yml`, `product_library.yml`, `compact_pdf.yml`, `photo_unit_progress.yml`, `partial_progress.yml`, `company_pilot.yml`, `melrose_progress.yml`; localizar na branch correspondente. Alguns importam dados ou executam manutenção. Não disparar todos para “testar acesso”.

O `publish_ui.py` da `main` é antigo, compara a raiz com backup de 09/10 e substitui `/index.html`; não é o método adequado para atualizar o atual `/app.html`. Seu bloqueio por baseline não deve ser contornado para forçar publicação.

### Testes existentes para orientar a retomada

- Catálogo/variantes: `tests/product-core.mjs`, `tests/attributes-core.cjs`, `tests/box-variants.mjs`, testes browser de biblioteca/boxes/catalog.
- Sugestões: `tests/suggestions-core.mjs`, `tests/suggestions-browser.cjs`.
- Relatórios: `scripts/check-direct-photo-pdf.cjs`, `check-photo-pdf-node.cjs`, `check-photo-pdf-layout.py`, `check-compact.cjs`, `check-unit-progress.cjs` nas branches de relatório.
- Planejamento e retornos: `check-schedule.cjs`, `check-schedule-layout.cjs`, `check-unit-followup.cjs`, `check-unit-followup-ui.cjs` na branch de follow-up.
- Piloto: `pilot/test-registration.mjs`, `test-invitations.mjs`, `test-isolation.mjs`, `test-consumption.mjs` e `scripts/check-company-signup.cjs`. Usar emuladores conforme README; não apontar scripts de fixtures a produção.

Nesta auditoria documental não foram reexecutadas suítes de produto nem realizados uploads, clocks, convites, compras, novas tarefas ou mudanças de regras. A validação realizada foi leitura do código, comparação de bytes e navegação autenticada.

## Funcionalidades e resultados observados

| Área | Evidência atual | O que não concluir automaticamente |
|---|---|---|
| Home e obras | Perfil autenticado e seletor de obras carregados | Sessão permanente entre chats |
| Biblioteca | UI: 3.339 produtos ativos; 3.208 Electrical, 121 Fire alarm, 10 Other; categorias e renderização inicial de 24 cards | Que todos os metadados ou fotos estão corretos |
| Compras | Tela com busca, filtros por obra/unidade/loja/status, 4 listas e indicação de PDF | Compra/pagamento automático ou teste de todas as listas |
| Planning | Manager e My Schedule abriram; dia 16/10 sem tarefas/obra atribuídas ao perfil observado | Que o módulo não existe por estar vazio; nem que todas as operações de gravação foram testadas |
| Relatórios | Opções Fotos por Unidade 2.0, Gerar PDF, CSV, WhatsApp e formatos Resumido/Completo presentes | Compartilhamento no iPhone e exportação real testados nesta auditoria |
| Clock/time | Código e coleção `clockEntries` presentes; entrada My Time na Home | Recurso ainda por criar só porque há pedido antigo; nem validação de clock-in real nesta auditoria |
| Multiempresa | Piloto e PR aberto, testes anteriores documentados | Produção já isolada por empresa |

### Catálogo e sugestões: atualização que supera os resumos antigos

`catalog-expansion/completion.json` documenta importação em 16/10: 2.792 novos produtos, piloto de 50 e lote posterior de 2.742; 3.000 produtos identificados por fabricante/modelo, 3.288 registros ativos naquele momento, sem alteração/exclusão de registros existentes. Workflows registrados: 38904694520 e 38904929658. Os totais desse manifesto são históricos e não substituem os 3.339 exibidos agora após expansões posteriores.

Preferência de fornecedores recuperada e documentada: Electric Supply Center (ESC) e Granite City Electric. Não confundir ESC com City Electric Supply. Códigos de loja, modelos e embalagem só por fonte exata. Fotos são referências HTTPS de fornecedores; fotos de referência não comprovam variante. Preços não registrados não são zero.

Os escopos antigos “Escopo-Biblioteca-Produtos.txt”, “Escopo-Sugestoes-de-Compra.txt” e “Lista_Guiada_Plano_Para_Aprovacao.md” eram propostas nas datas em que foram escritos. Hoje há código publicado de busca/filtros, Guided Shopping v2 e sugestões determinísticas de acessórios. Não recomeçar essas funcionalidades do zero. Comparar cada critério da proposta com a implementação antes de dizer que está totalmente concluído.

### Multiempresa: situação exata

Código para CFC Electric e PNV Electric em ambiente isolado, cadastro via callable transacional, convites vinculados a e-mail verificado, token com hash e expiração, aceitação idempotente e revogação. Não envia e-mail de convite automaticamente. README documenta testes anteriores: 23 de cadastro, 33 de convites, 28 de isolamento, 35 browser e 7 cenários de consumo; não reexecutados nesta auditoria.

`pilot/CONSUMPTION.md` já identifica `obra-manager-teste`. Guards antigos aceitam prefixo `obra-company-staging*`; precisam ser ajustados explicitamente para o novo teste sem permitir produção. Firestore e Auth de teste ainda não inicializados, como confirmado no console. Publicação de Functions, permissões e faturamento continuam pré-requisitos separados; não habilitados aqui.

Bloqueios documentados de release: integrar todas as queries/listeners/filas ao escopo de empresa; entrega privada de mídia; permissões operacionais internas; onboarding completo e testes hospedados. Nunca usar regras do piloto em produção nem presumir que testes de emulador comprovam isolamento comercial completo.

## Pendências e sinais encontrados nesta auditoria

1. Consolidar a origem de produção: `main` está atrasada e há módulos servidos por Hosting preservados de branches diferentes. Esta auditoria documenta a composição, mas não faz merge/publicação do produto.
2. Qualidade de atributos: a biblioteca exibiu títulos CANTEX “.5 in.” e “.75 in.” com atributos “5 in.” e “75 in.”; cabos 4/0 também exibiram configuração suspeita “0/4”. Registrar como defeito observado e investigar parser/fonte antes de corrigir. Nenhum cadastro alterado aqui.
3. Indicadores de progresso da obra selecionada mostraram 100% com 20/21 concluídas e uma pendência. Pode envolver subtarefas/arredondamento/regra de agregação; verificar `work-progress.js` e tarefa pendente, sem marcar trabalho físico como concluído por inferência.
4. My Schedule vazio em 16/10 não confirma falha: Manager também não mostrou atribuições naquele dia. Validar atribuição persistida se a próxima tarefa for atualizar agenda.
5. Piloto de empresas ainda requer configuração e publicação isoladas; não é um sistema comercial hospedado pronto.
6. Regras atuais completas de Firestore/Storage, IAM efetivo de deploy, backup/restore integral, backend completo e todos os critérios históricos não foram auditados exaustivamente. Se a próxima tarefa depender deles, inspecionar os recursos pertinentes. Acesso de leitura ao console não é prova de qualquer permissão de escrita.

## Como manter a continuidade

Ao terminar uma etapa, registrar: data/fuso; pedido; código/branch/commit; dados tocados (IDs apenas em cópia privada quando necessário); testes executados e resultado; publicação/run/release; pendências; próximo passo. Distinguir pedido, implementação, teste local, persistência online e implantação. Atualizar o mapa principal e a cópia de passagem quando mudar um caminho ou decisão.

O repositório é público. Manter aqui apenas documentação técnica apropriada; detalhes operacionais privados, credenciais e anexos de clientes não pertencem a este arquivo público. A cópia entregue ao usuário pode acrescentar contexto operacional sem publicá-lo no GitHub. Novos registros devem preservar esse limite.

Mensagem de retomada: “Continue o Obra Manager/CrewNelo pelo MAPA_DO_PROJETO.md de tiagoIA/obra-manager, main. Confirme a versão mais recente e os acessos. Não use main como baseline dos assets sem comparar com produção. Preserve dados e módulos existentes e retome o pedido pendente.”

Se GitHub estiver indisponível, anexar a cópia Markdown. Se também faltar acesso ao sistema, usar a cópia para preparar o trabalho e identificar a dependência concreta; não pedir que Tiago reconte o projeto inteiro. Senhas e sessões continuam sendo tratadas pelos fluxos seguros.

## Inventário verificável de assets

Os hashes e referências abaixo são um retrato de 16/10/2026, não uma autorização para restaurá-los sobre alterações futuras. Cada correspondência foi comparada byte a byte por SHA-256 com o Git, além do código HTML em produção. Revalidar antes de publicar.

| Asset | SHA-256 | Uma branch com os mesmos bytes |
|---|---|---|
| `app.html` | `825b1f89c37399054e4fb9884882a749e4a4fb57a08d99dd20b10aa6c2f81aae` | `feature/purchase-suggestions-2026-10-16` |
| `central-catalog-v1.js` | `81a1160588174850b85f0121e3b13bbe8d56865a6a239be7c6a84baba375272b` | `feature/purchase-suggestions-2026-10-16` |
| `costs-dashboard.js` | `e2c50bef074b388056332987f44e48930eefa62fbc385fe4a9d92cf4ad2112df` | `feature/purchase-suggestions-2026-10-16` |
| `crewnelo.css` | `6a08751e436663da2f4c83f5611d16c91cfc639f2c3c41b237c7788ec7c7010d` | `feature/compact-home-selection-2026-10-15` |
| `crewnelo.js` | `07f7ae921cb1372282f8defd9bb8412d023190f590b9d604885a63a03d300bb4` | `feature/compact-home-selection-2026-10-15` |
| `field-media.js` | `ad902cefc2b616d591529445493929f6d364db078076090d1bc46ae64376f4e9` | `feature/unit-followup-2026-10-09` |
| `guided-shopping-v2.js` | `d8cf494ff05b2909dc5846ec5bd80e24c9a266b01dcb014e3292b4350fd391c4` | `feature/purchase-suggestions-2026-10-16` |
| `invoice-store.js` | `fd30bb81fd0773751f26c18ad04714ed32d9c97e314a0a7fa8cefeb94a5d3bb9` | `feature/purchase-suggestions-2026-10-16` |
| `material-attributes.js` | `ab203d4f3a0a95e5d66684ed4e4e4bc9327211500159d14e5cc0ab572b2b2636` | `feature/purchase-suggestions-2026-10-16` |
| `mobile-layout.css` | `7dee8296f8449bbbbde567e3ab817bae238c264808a834927420f51b3a1bfbfd` | `feature/unit-followup-2026-10-09` |
| `note-photos.js` | `9bedda9c12ce9e2d251f5759055311b1cc06bdf4221dc062ad5f1b51c77e9db8` | `feature/unit-followup-2026-10-09` |
| `photo-report-cover.js` | `2cebf159c87986262ba678b477307b83e33f88bce6b7d3df1ed4a08de39221d8` | `feature/purchase-suggestions-2026-10-16` |
| `photo-report-pdf.js` | `8c53667d36b5c8be87cdf1f8688eb01c96e9b7dd67bf434e03c9e75a2efef1e8` | `feature/purchase-suggestions-2026-10-16` |
| `photo-report.js` | `d952f9d57fa9ac5d6351ce1d6af143372cbea93e9d721299c0a1c29bb15e28d8` | `feature/purchase-suggestions-2026-10-16` |
| `product-enrichment.js` | `2c37998a1f63c3b787c696b3403762a854aa4f6151271d458c04deb3ab0ae04b` | `feature/purchase-suggestions-2026-10-16` |
| `product-library.js` | `a1783f09c884dab8a90581f478f2f873ecc78e4d9a96b52385768201e8fd49b4` | `feature/purchase-suggestions-2026-10-16` |
| `product-search.js` | `b366478d7fe97637dc2cadb9f6eedecb8a19c2590f2919f28ff88cef2282d837` | `feature/purchase-suggestions-2026-10-16` |
| `project-brief.js` | `fa1e021cbca78e2725607de9e39dd7e3f03c00164518afba0634c1e6980aa2bd` | `feature/unit-followup-2026-10-09` |
| `purchase-suggestions-ui.js` | `9de9b29cdf8d3bfc195e7ee8fe874bd80e900ee268d0e8d7347869c6b5dc2cef` | `feature/purchase-suggestions-2026-10-16` |
| `purchase-suggestions.js` | `04666e9855bbfda5893bdd6b449e2645893414f8f4e8d03ac53bbba582f9b654` | `feature/purchase-suggestions-2026-10-16` |
| `purchasing-core.js` | `e5274d321c802715b41b24ba5f1785a358c1b0f306f5d89030d0381660a8d340` | `feature/purchase-suggestions-2026-10-16` |
| `receipt-review.js` | `3dad8accce1c63fed20f3ce91ce0c04dd4e3088161a680c3111870c4380ca216` | `feature/purchase-suggestions-2026-10-16` |
| `report-photo-order.js` | `75594d9f8b6df66ed7b5f42e9268a5d8115394a36ec308a034b9ae2a72fcfc3b` | `feature/purchase-suggestions-2026-10-16` |
| `shopping-catalog.js` | `e1f38ca5bfe37deb97b7035df702c7224e7b0d54c1957588f674db8214d710b1` | `feature/purchase-suggestions-2026-10-16` |
| `shopping-picker-core.js` | `b08bef3eae2b75b4debc44255b7e495e960d0a06b075281aafa6275650327019` | `feature/purchase-suggestions-2026-10-16` |
| `shopping-view-v3.js` | `53d93cdbdd6210b31708be8307729372168e9b2fa05f55b4bd878c3f8719e6cd` | `feature/purchase-suggestions-2026-10-16` |
| `sw.js` | `99ae77f8286049ab22387180b0f1ea0c092113791c6271da70f9f7cb8b19d55c` | `feature/compact-home-selection-2026-10-15` |
| `unit-followup.js` | `c69ba1d5c1c0ad949bcd2d247155165a659180a502e046912d85590f7eac36c7` | `feature/unit-followup-2026-10-09` |
| `unit-report-language.js` | `231a89c5ef9be4ea88e5853f505f77cc5def87757cbc6614d9cf5e0ba9278922` | `feature/unit-followup-2026-10-09` |
| `unit-report-structure.js` | `b07fea52af306207e64b4013cb7fe66ee2c30a8e1b7ddefba1ffcdec8b5493a2` | `feature/compact-home-selection-2026-10-15` |
| `work-progress.js` | `5b1be71bf2fe24d6c97bb96f64b40dad5ed1a382bc46a1832be7bd2ebfe3e189` | `feature/purchase-suggestions-2026-10-16` |

## Índice de branches disponíveis na auditoria

- `origin` — `168c0143e986ce0c1fa4394eb4c87a77329aa6c5`
- `backup/antes-biblioteca-central-2026-10-08` — `01437c6112bc078955313349a01fdcb0dff3ad43`
- `backup/antes-cadastro-central-2026-10-08` — `01437c6112bc078955313349a01fdcb0dff3ad43`
- `backup/antes-classificacao-listas-2026-10-08` — `c7c12d46ac6f2c2eb80e37d7126cd5ce5e834057`
- `backup/antes-layout-mobile-2026-10-10` — `4848b8a00f4abd4cf5ed7168216fb09028307d14`
- `backup/antes-lista-guiada-2026-10-08` — `e254ab89459f2454a82933cfc3ccabde0e44f47b`
- `backup/antes-restaurar-pdf-compras-2026-10-10` — `b6f1c67f3cc2e69b3684a10457c039505c005e0c`
- `backup/before-photo-report-2026-10-13` — `5831d76950c900506280302e1e6f199606321dcc`
- `backup/before-summary-format-2026-10-13` — `5e49fc534238fc4d28138fa1ef46265fabb2ac50`
- `backup/copia-1.0-2026-10-08` — `e254ab89459f2454a82933cfc3ccabde0e44f47b`
- `backup/lista-guiada-v1-antes-interface-2026-10-08` — `6aded5f7ff0499355720080c7c0c3cdfa2b2e13e`
- `backup/lista-guiada-v2-antes-classificacao-2026-10-08` — `c7c12d46ac6f2c2eb80e37d7126cd5ce5e834057`
- `backup/live-before-multiempresa-2026-10-15` — `ad00eb62d647541b535ef87d76ec09afeca36061`
- `backup/photo-report-2.0-before-client-refinement-2026-10-13` — `c4efacb8d631a4123f3c1419e583ad488daadc8c`
- `backup/verificacao-2026-10-08` — `3b8dfeaa254e5e50400bfe952007fb147688f989`
- `feature/compact-home-selection-2026-10-15` — `1f513e5bd63cc56bf53261633ea325fe61de0dfc`
- `feature/company-isolation-pilot-2026-10-13` — `78c276a8a9a08c886bf1bb25af871c42f08b6de8`
- `feature/company-registration-2026-10-16` — `95d3b7174ab03c562b05247b950c127b26fce72a`
- `feature/crewnelo-public-page-2026-10-13` — `5831d76950c900506280302e1e6f199606321dcc`
- `feature/daily-schedule-2026-10-09` — `331c74975fef80304c06042226f2be37973b67fb`
- `feature/lista-guiada-v1` — `9a343f4add00421ea8af9f9a7e554128d3bfbeeb`
- `feature/material-lists-2026-10-09` — `759ff8bb2fd0fac6ffc9c171d08c030ed74c179c`
- `feature/optional-work-types-2026-10-15` — `c582df9e6b7a3a32a20f6e7d4b09da6866d18b2a`
- `feature/photo-cover-2026-10-15` — `4985026315bd3532b91fabf163d8352c39b311fd`
- `feature/photo-unit-progress-2026-10-15` — `abb71f24d2987269752ce6441480458df93d0845`
- `feature/product-dimensions-2026-10-16` — `fbbd33b5a04bd65915ae551f77b031eed78fdb66`
- `feature/product-library-2026-10-16` — `fbbd33b5a04bd65915ae551f77b031eed78fdb66`
- `feature/project-facade-2026-10-15` — `1cf1168861e33567eae8c3b7ea28a9d6ed7be3ea`
- `feature/project-facade-followup-2026-10-15` — `f4aa3c37be323505de9e1504d9cf98d3b1d55957`
- `feature/purchase-suggestions-2026-10-16` — `9534a413b3f08fe9e64701da1464feb3cbb7002b`
- `feature/purchasing-costs-2026-10-09` — `071c312c859cbd208b4d856763c938209b83e6fd`
- `feature/shopping-catalog-2026-10-15` — `62b252777384058c0abfe9fa3bb568f83e75a7dd`
- `feature/shopping-simplification-2026-10-15` — `0b71e74a02d353f7b16557d9717ba76f983c3916`
- `feature/unit-followup-2026-10-09` — `0d50496e3a72f8af08dfdd685745628ddd06dfed`
- `fix/arlington-project-name-2026-10-08` — `567d8123bb17f04bbec97b5ac265e7f3e1ca8390`
- `fix/arlington-report-layout-2026-10-15` — `8b0b7e72e0cc63e7dd4eefb080a4408eb52fec30`
- `fix/compact-photo-pdf-2026-10-15` — `4f62cdb9e5a39bf5cf1dc55946d13d2d8624c722`
- `fix/compact-unit-details-2026-10-12` — `3a983af7dfb20f5834d2b6e971b10518294f98c9`
- `fix/direct-photo-pdf-2026-10-15` — `198454cc73b7ab985e4151b3543c42d71b42cbe9`
- `fix/home-photo-zoom-2026-10-09` — `3912bf318d23f1cbcdab65f012ee1b99fbd9fff8`
- `fix/pdf-export-followup-2026-10-15` — `e0d6ad4bed554799ca80fe4ee4fa2a66272f36b6`
- `fix/photo-report-2026-10-13` — `bb00d2254e839f74452d294ca524604ab99aff2e`
- `fix/report-pdf-names-2026-10-15` — `4c4004fdd493258017b82489031076b60badf432`
- `fix/subtask-progress-2026-10-15` — `8dedd75d2b6bd8a1d6bf88f138395826c1f7b7ab`
- `main` — `168c0143e986ce0c1fa4394eb4c87a77329aa6c5`
- `ops/melrose-progress-2026-10-16` — `123e11e36c6593f13630cef84ea3cb537f7fed40`
- `review/materials-2026-10-08` — `2c82ee30b851c7dd5e77f45dde92e6c565b68e72`
- `setup/firebase-access-check-2026-10-08` — `a7e09ea665b2ce684d361d23884ddf32d8b90059`
- `setup/hosting-preview-test-2026-10-08` — `8836f9b68ca97973fa40eeb88428c8177fa325ca`
- `task/arlington-condensers-2026-10-13` — `efc819ab11a3ad54bd7b5ca0f5c3bdbcf7afc2a1`
- `task/basement-2026-10-15` — `d9b4776161a50db318143203f68c34812991cb3e`
- `task/basement-details-2026-10-15` — `5f4eae9ec9c0ecfaa28ee817063bed7780403e63`
- `task/fire-alarm-guided-20261014` — `b3564612862d04e8cc3a7e1fcdbf0536b6f67d01`
- `task/schedule-2026-10-12` — `46400a724c9e8d97044edb706bd2362a1c3ee051`
- `work/catalog-expansion-2026-10-16` — `7948b58998a978b7846b64628373d7cf612292a9`


## Decisao de produto — Estimates (16/10/2026)

Nova necessidade solicitada: guardar planta/PDF e suas revisoes, fotos, videos e relatos da visita por orcamento; ajudar a levantar pontos e escopo antes de precificar. Ainda em definicao/piloto documental, nao implementado como modulo novo nesta etapa. Nao confundir com invoices existentes de fornecedores.

Permitir escolhas independentes: somente mao de obra ou material e mao de obra; por hora, empreita ou combinacao por linha. Manter materiais internos mesmo quando fornecidos pelo contractor. Separar quantidade desenhada, complemento de escopo e quantidade aprovada; cada item deve apontar folha/pagina ou evidencia. Delimitar existente versus adicao antes de contar; excluir simbolos de legendas e evitar duplicacao entre fotos e plantas. Comandos graficos nao definem automaticamente tipo/SKU; percursos e circuitos precisam de definicao propria.

Pesquisa de referencias concluida: Countfire, Togal, STACK (takeoff), Handoff (arquivos/visita para rascunho de estimate), magicplan (documentacao por ambiente). Pesquisa de funcoes oficiais nao equivale a teste desses produtos ou acesso ao codigo deles. Piloto em planta do usuario iniciado e consolidado em arquivo privado de levantamento; detalhes de obra permanecem na copia privada. Nao ha valor final calculado nem proposta enviada ao cliente. Proximo passo depende do pedido atual: definir precificacao do piloto ou implementar o modulo, sem pressupor que o levantamento visual ja e um detector automatico.


## Estimates — implementado e publicado em 17/10/2026

Esta atualização supera o estado de proposta/piloto documental descrito anteriormente para este módulo.

- Pedido: implementar o protótipo diretamente no Obra Manager; usuário autorizou testar e publicar no sistema habitual, sem revisão prévia em ambiente separado.
- Fonte: branch feature/estimates-2026-10-17, commit 8d3e166a6afe55a828e365852b7922632ba4b435. Arquivo principal em produção corresponde a esta branch; main continua sendo a referência do mapa, não o baseline dos assets.
- Arquivos: public/estimates.js; integração localizada em public/app.html (entrada Owner na Home e bridge Firebase). Outros módulos foram preservados pela clonagem da versão live. Não reimplantar toda a árvore da branch como substituta do Hosting.
- Entregue: lista e cadastro de estimates independentes de obra contratada; vínculo opcional a projeto; ambientes; notas de visita; gravação de áudio quando suportada; upload de PDF/imagem/vídeo/áudio até 50 MB; revisão de serviços/quantidades/fontes; preço por unidade, hora ou verba; materiais do cliente ou da empresa; PDF marcado DRAFT; histórico de revisões e proteção contra sobrescrita concorrente.
- Acesso nesta primeira versão: Owner; registros privados em users/{uid}/estimates/{estimateId}; mídia em estimateFiles/{uid}/{estimateId}/{fileId}. Novas regras Firestore isolam por uid e perfil administrativo. Storage restringe o novo prefixo por uid, tipo e tamanho; comportamento dos demais caminhos preservado. Nenhuma migração ou alteração de tarefas/compras/obras existentes foi executada.
- Upload não é análise por IA. A IA de vídeo/planta ainda NÃO está conectada; não há contagem automática validada. Referência de origem dos serviços é preenchida manualmente. PDF é rascunho e não é enviado ao cliente. Status é controle manual. Impostos não são calculados. Histórico registra metadados, não restauração de versões completas.
- Validação: testes de interface em 390px/1440px com host simulado (cadastro, salvar/reabrir, notas, escopo aprovado, preço ausente, subtotal, PDF e falha de persistência); regressão suggestions-core com sintaxe do app; Firebase emuladores com regras derivadas das atuais (isolamento de usuário, bloqueio anônimo/worker, revisão e mídia privada, preservação de tarefas/fotos legadas). PDF de QA extraído/renderizado. Teste autenticado na conta real do usuário ainda não realizado: navegador desta sessão estava no login; não alegar salvamento real de um estimate de cliente.
- Publicação verificada: workflow 39046702992; Hosting sites/obra-manager-4ecc7/versions/72c80d10e55af0ff; release sites/obra-manager-4ecc7/releases/1792252234854000. SHA-256 app.html 1b2a2db3af1405deb90366c0371179074f452f7e52e3e914ca6360f423a3620a; estimates.js a2cf8e16e019b33f72eacad1f06c9308ce867976cf868b6579a1a57ceb259621. Regras Firestore e Storage publicadas e seus releases conferidos pela API.
- Entrada: https://obra-manager-4ecc7.web.app/app.html, Home → ESTIMATES, perfil Owner; recarregar a página para obter o HTML atualizado. Navegação de app.html usa network first no service worker observado.
- Publicador: scripts/publish_estimates.py e scripts/estimate-publication.json; prepara preview, confere bytes e baseline, aplica regras testadas via release_estimate_rules.py e publica preservando demais assets. Proteção contra mudança concorrente. Antes de repetir, ler os scripts e atualizar o baseline; o preparador de regras foi feito para adicionar a estrutura ao estado anterior, não para ser reexecutado indiscriminadamente depois da publicação.
- Próximo passo: usuário testar criação, salvar/reabrir, anexar e baixar no próprio login; corrigir observações. Depois, integrar análise assistida aproveitando o backend existente somente após verificar sua configuração. Não criar provedor/chave nova por inferência.


## Atualização de permissões Estimates — Supervisor coleta; Owner precifica e aprova (17/10/2026)

Esta seção supera a versão inicial Owner/Master e a proposta intermediária de acesso completo para Supervisor. Pedido final explícito de Tiago: Supervisor visita a obra, grava/envia vídeos/fotos/áudio e informações; somente o dono da empresa vê preços e faz a aprovação final.

- Publicado no app habitual em https://obra-manager-4ecc7.web.app/app.html. Código: feature/estimates-2026-10-17, commit 0b9646f4de12a4bf342781326cc2e73b3dc02ecc; workflow 39047471871 concluído com sucesso. Hosting sites/obra-manager-4ecc7/versions/b1c1c99a6dffe405, release sites/obra-manager-4ecc7/releases/1792252887440000. SHA-256 app.html 40af30e3fc30e26f2e91f6a326164b0c149ff7a60d36331510b0c2215e9acd66; estimates.js fcfadf423c9bcf7ea57b7384ed47f382c126faeb4dec03736425eb5a2b4ea014. Import do módulo atualizado para v=20261017-field-3 para invalidar cache.
- Supervisor: acesso Estimates na Home, modo de coleta de visita, ambientes/notas/mídia e escopo/quantidades. Escolhe explicitamente Company Owner responsible e encaminha com Send visit to Owner. Sem campos de taxa, totais, condições financeiras, PDF de proposta ou aprovação final.
- Capturas separadas em users/{uid}/estimateCaptures/{captureId}; a serialização de coleta não inclui preços, totais ou condições financeiras. Capturas podem ter somente status Draft ou Submitted. Encaminhamento gera referência em users/{owner}/estimateIntake/{sourceUid}~{captureId}. Owner recebe seção Visits from your team e usa Prepare estimate; depois do primeiro salvamento, Open estimate aponta ao orçamento já importado.
- Valores permanecem em users/{owner}/estimates/{estimateId}, com leitura/escrita restritas ao próprio uid E role exata owner nas regras. Supervisor não lê esses documentos nem pela API. Master/admin não têm exceção financeira nesta versão: usam o modo de coleta se não forem role owner. Não alegar herança de valores de Owner para Master.
- Owner importa uma cópia do levantamento para um estimate próprio, preenche valores e condições e usa Approve estimate. Aprovação exige serviços revisados, quantidades e taxas completas. Revisão de quantidade pelo Supervisor NÃO é aprovação comercial. Salvar modificações retorna o estimate a Draft. PDF aprovado é identificado como OWNER APPROVED - CLIENT ACCEPTANCE PENDING; não equivale à aceitação do cliente nem envio automático.
- Anexos em estimateFiles continuam pertencendo ao autor; no encaminhamento, metadata reviewOwner concede leitura ao Owner explicitamente selecionado. Supervisor não recebe anexos do orçamento financeiro. Outros caminhos e políticas legadas de tarefas/mídia preservados. Nenhuma migração de dados existentes.
- Vínculo multiempresa automático ainda não foi concluído na produção: NÃO inferir o dono da empresa por nome ou escolher o primeiro Owner. O responsável é selecionado explicitamente na visita; demais Owners não recebem acesso ao levantamento. Não confundir com isolamento multiempresa comercial integral.
- Validação: interface Owner em mobile/desktop, fluxo de visita Supervisor sem controles financeiros, ausência de rate no item salvo pelo fixture; regras em emuladores: Supervisor cadastra coleta, encaminha e é bloqueado em documento financeiro, inclusive na própria pasta; status Approved e campo total rejeitados em captura; Owner designado lê levantamento/inbox; outro Owner e Worker bloqueados; mídia compartilhada apenas com destinatário escolhido. Regressão de suggestions-core/sintaxe do app passou. Publicação de ambos os arquivos e releases de regras conferida. Validação autenticada em conta real continua pendente; usuário testará no sistema.
- IA de análise de planta/vídeo continua não integrada. Próximo passo é o teste do usuário nos perfis reais e correções específicas. Não ampliar valores ao Supervisor por inferência.
- Publicador/regra preparadora usam hashes das regras e assets anteriores como proteção: antes de nova publicação, atualizar os baselines após leitura da versão live; não reexecutar contra estado diferente ignorando guards.

## Cadastro e projetos por empresa — trabalho em 17/10/2026

Prioridade explícita: novas empresas devem cadastrar-se e usar projetos próprios, sem enxergar outras empresas. Produção ainda NÃO está comercialmente isolada. Não abrir seu cadastro público usando coleções globais legadas.

- Implementação separada em feature/company-workspace-2026-10-17, commit 8cd50a1dc2aa0d46d251c38a7b52ecc5f287b38f, baseada no piloto 95d3b7174ab03c562b05247b950c127b26fce72a. Não publicada.
- pilot/functions/company-projects.cjs: callable saveCompanyProject deriva empresa do índice e valida membership owner no servidor. Criação, edição e arquivamento lógico, revisão otimista e retries idempotentes. Cliente não fornece companyId. pilot/site/projects.js integra lista por empresa e formulário Owner; limpa listener/estado ao trocar conta. UI ainda precisa teste browser hospedado.
- Regras pilot/firestore.rules bloqueiam gravação direta em projects; leitura exige associação à empresa. Demais coleções do piloto ainda precisam auditoria de permissões internas. Não instalar essas regras sobre produção legada.
- CI run 39048905297 concluído com sucesso: 23 verificações de cadastro, 33 de convites, 31 de projetos e 7 cenários de consumo. Somente emulador. Primeira execução 39048719026 falhou por import relativo do teste e foi corrigida; não era falha comprovada de isolamento.
- Acesso Google ao console de teste recuperado nesta sessão. Firestore (default) Standard, nam5 criado no projeto obra-manager-teste com regras iniciais deny-all. Firebase Auth inicializado e E-mail/senha ativado. Não houve importação de dados reais, upgrade ou publicação.
- Bloqueio atual confirmado no console Functions: plano Spark exige upgrade de faturamento para usar Functions. Upgrade NÃO realizado; é decisão financeira do usuário. Credencial de automação existente retornou 403 para recursos de teste na auditoria 39048333065, mas acessou produção. Login humano não concede automaticamente acesso ao CI.
- Próximo: usuário concluir eventual ativação Blaze no ambiente de teste; conferir/conceder apenas permissões necessárias à publicação, com confirmação aplicável; registrar app web/Hosting, publicar backend/regras/frontend e validar cadastro real e duas empresas isoladas. Migração dos módulos operacionais legados, mídia privada, filas/cache e vínculos de perfis continua pendente antes de comercializar o app completo.

## Mudança autorizada de destino e bloqueio exato — 17/10/2026

Tiago autorizou explicitamente usar o projeto atual obra-manager-4ecc7 (já Blaze) para testar com a própria equipe, sem ativar cobrança do segundo projeto. Pediu aviso imediato quando sua intervenção for necessária.

- Branch feature/company-production-2026-10-17, HEAD a505a85595d9ae27796f5151ccb7ca39a49e6cdb. Backend preparado com codebase company-workspace, preservando demais codebases. Contas que já têm perfil legado são impedidas de cadastrar nova empresa automaticamente.
- Tentativa de publicação 39049368469: testes de cadastro (23), convites (33) e projetos (31) aprovados. Deploy PAROU antes de publicar: falta iam.serviceAccounts.ActAs na conta runtime obra-manager-4ecc7@appspot.gserviceaccount.com para a identidade de publicação firebase-adminsdk-fbsvc@obra-manager-4ecc7.iam.gserviceaccount.com. Não afirmar que outras permissões de deploy já passaram.
- Concessão mínima a preparar: papel Service Account User (roles/iam.serviceAccountUser), no recurso da conta runtime acima, para a identidade de publicação acima. Não conceder Owner nem ampliar permissões de faturamento. Concessão ainda NÃO realizada.
- A página oficial indicada pelo Firebase CLI, https://console.cloud.google.com/iam-admin/iam?project=obra-manager-4ecc7, retornou Site Unavailable neste navegador, inclusive uma recarga. Não é prova de bloqueio por bot. Usuário precisa abrir a página em seu navegador e conceder o acesso; login em navegador externo não recupera a sessão deste navegador.
- company-production/firestore.rules e storage.rules são candidatas NÃO publicadas. Bloqueiam contas novas, pendentes e multiempresa em coleções/mídia legadas; conservam acesso dos perfis legados existentes. Nova empresa usa companies/{company}/projects e membership. Importante: não confundir essas candidatas com regras já em produção.
- Workflow 39049460909 concluiu com sucesso: 194 verificações em emuladores de preservação do app legado, bloqueio das coleções globais e mídia para contas novas, consultas por empresa, e bloqueio mesmo com perfil legado acidental. Nenhuma alteração nas regras de produção.
- company-production/site prepara página própria em /companies/ com projetos por empresa; UI publicada e teste browser integrado ainda pendentes. Não publicar esta branch antiga sobre app.html ou landing atuais.
- Próximo: liberar a permissão precisa; repetir somente deploy necessário, resolver eventual próximo erro com evidência; validar UI; publicar regras testadas e /companies/* mediante preservação do Hosting atual e hashes; testar duas empresas reais. Ainda falta levar módulos operacionais legados ao escopo de empresa para comercialização completa. Não declarar tarefa concluída.
