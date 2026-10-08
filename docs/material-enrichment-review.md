# Revisão dos materiais existentes — 8 de outubro de 2026

Biblioteca auditada: **495 materiais**, inicialmente **193 sem foto**.

Atualização verificada: **26 cadastros existentes**, **nenhum novo cadastro**. Foram acrescentadas informações confirmadas em nove registros, corrigidos 17 campos UPC que continham IDs de fornecedor e adicionada uma foto de referência. Restam **192 cadastros sem foto**.

## Cadastros enriquecidos

| Código interno preservado | Material | Informação acrescentada |
|---|---|---|
| MAT-004 | Fusível TRS15R | Mersen, modelo, UPC 782001748821, especificações, Grainger 4YZL3 e foto de referência da série TRS-R |
| MAT-003 | Fusível TRS15R | Mesma identidade verificada; foto anterior preservada |
| MAT-008 | DPS QSPD2A035B | Siemens, modelo e especificações do manual; foto e UPC continuam pendentes |
| FIRE-046 / FIRE-008 | Mircom FX-2000 | Identificação como família; referência completa do painel ainda necessária |
| 1049101 | Fita preta WW-732 | NSI, modelo, UPC 662381367167 e especificações |
| 1037923 | Fita preta WW-832 | NSI, modelo, UPC 662381367150 e especificações |
| 1033407 | Fita preta WW-716 | NSI, modelo, UPC 662381367365 e especificações |
| 1083231 | Fita anticorrosão WW-CP-401 | NSI, modelo, UPC 662381994189 e especificações |

Os códigos internos acima não foram renumerados. Os dois cadastros TRS15R já existiam; ambos foram preservados, inclusive seus vínculos e histórico. A edição de registros antigos com identidade repetida continua permitida, mas a criação de novas duplicatas é bloqueada.

## Correção de códigos

17 produtos importados tinham um número de 6 ou 7 dígitos do distribuidor no campo UPC. Esses números continuam em `suppliers.code`; somente a cópia incorreta em `upc` foi removida. A coleta e importação passaram a rejeitar esse formato como UPC. O formulário também orienta a usar o campo do fornecedor.

## Pendências reais

As famílias genéricas não receberam marca, código ou imagem de uma variante escolhida arbitrariamente. Tomadas, disjuntores, caixas, cabos e detectores precisam de modelo, medida, cor ou sistema compatível conforme o produto.

Há nomes que exigem conferência da etiqueta/nota, por exemplo QA1154FC, HP362N, R977LCCAR, B300-16 e SMICO-210. Resultados para modelos parecidos não foram tratados como confirmação.

FX-2000 identifica uma família e possui aviso de fim de vida do fabricante; não foi convertido em uma referência de compra específica.

## Fontes e verificação

Referências públicas do fabricante: Mersen TRS15R, manual Siemens QSPD2A035B, páginas NSI das quatro fitas e aviso Mircom FX-2000. Foto de referência: página Grainger TRS15R (4YZL3), com indicação nos detalhes de que é da série TRS-R.

Backup dos materiais e coleções vinculadas: `backups/material-enrichment/37851755467/`. O relatório privado `pending-identification.json` registra os 192 materiais sem foto. A gravação foi atômica, com condições de versão para impedir sobrescrever uma edição posterior à leitura. IDs e campos fora da atualização foram comparados depois da gravação.

Testes: identidade exata, rejeição de conflito de fabricante/modelo, preservação de estoque e metadados do fornecedor, prevenção de novas duplicatas, edição de duplicatas antigas e validação do formato de UPC.

Publicação verificada: somente os arquivos de validação da biblioteca e cache foram atualizados; 74 arquivos do site preservados, sem gravações adicionais no Firestore. Testes de edição, busca nas tasks/listas, PDF e layout móvel passaram. Backup da interface: `backups/catalog-guards/37852263957/`.

## Segundo lote — aplicado e verificado

Execução `37855143847`: 21 cadastros existentes atualizados, uma foto nova, 495 IDs preservados. Total atual: 304 com foto e 191 sem foto. Estoques, códigos internos, fornecedores, imagens anteriores e campos fora da atualização preservados. Nenhum produto novo criado.

| Código interno | Material/modelo | Atualização |
|---|---|---|
| 1049108 | WW-732-BL | Marca, modelo, UPC e especificações |
| 1049103 | WW-732-BN | Marca, modelo, UPC e especificações |
| 1049107 | WW-732-GN | Marca, modelo, UPC e especificações |
| 1049110 | WW-732-GY | Marca, modelo, UPC e especificações |
| 1049105 | WW-732-OR | Marca, modelo, UPC e especificações |
| 1049104 | WW-732-RD | Marca, modelo, UPC e especificações |
| 1049109 | WW-732-VT | Marca, modelo, UPC e especificações |
| 1049112 | WW-732-WT | Marca, modelo, UPC e especificações |
| 1049106 | WW-732-YL | Marca, modelo, UPC e especificações |
| 1049098 | WW-716-BL | Marca, modelo, UPC e especificações |
| 1049096 | WW-716-BN | Marca, modelo, UPC e especificações |
| 1030075 | WW-716-GN | Marca, modelo, UPC e especificações |
| 1036160 | WW-716-GY | Marca, modelo, UPC e especificações |
| 1030096 | WW-716-OR | Marca, modelo, UPC e especificações |
| 1033236 | WW-716-RD | Marca, modelo, UPC e especificações |
| 1049099 | WW-716-VT | Marca, modelo, UPC e especificações |
| 1028022 | WW-716-WT | Marca, modelo, UPC e especificações |
| 1049097 | WW-716-YL | Marca, modelo, UPC e especificações |
| MAT-009 | 300HS | Marca, modelo e especificações; UPC pendente |
| MAT-010 | 400HS | Marca, modelo e especificações; UPC pendente |
| MAT-008 | Siemens QSPD2A035B | Foto exata, rótulo conferido no PDF Siemens |

Fontes do fabricante registradas individualmente em `material-enrichment-v2.json` e em `catalogProvenance`, preservando a URL e o código GCE. A imagem Siemens foi extraída do PDF público do fabricante hospedado pela City Electric Supply; hashes do documento e da imagem conferidos antes da gravação.

Backup completo das coleções vinculadas: `backups/material-enrichment/37855143847/`. Gravação atômica com condição de versão; comparação dos IDs e campos protegidos após a gravação passou. Testes de identidade, conflito, preservação de estoque/fotos e metadados de fornecedores passaram. Nenhuma alteração de Hosting foi necessária: dados e foto já estão na biblioteca usada pelo site.

Pendência adicional: EWDT-8 tem cadastro de 55 yd e referência atual do fabricante com 60 yd. O UPC e a medida não foram preenchidos sem confirmar a embalagem. Austin 400HS ainda sem foto exata obtida; materiais genéricos e modelos possivelmente digitados incorretamente continuam no levantamento de identificação.
