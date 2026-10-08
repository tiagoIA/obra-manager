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
