"""Explicit copy replacements only; keep persisted identifiers and manufacturer codes."""
import pathlib,json
PAIRS='''Troca de painel	Panel replacement
Service novo / upgrade	New service / upgrade
Service / entrada	Service entrance
Circuito dedicado	Dedicated circuit
Tomadas e switches	Receptacles and switches
Dados / Cat6	Data / Cat6
Dispositivos de fire alarm	Fire alarm devices
Painel e tampa compatíveis	Compatible panel and cover
Breakers por circuito	Breakers by circuit
Conectores para entradas	Entry connectors
Identificação dos circuitos	Circuit identification
Fabricante/modelo atual e novo	Existing and new manufacturer/model
Circuitos e polos; itens reaproveitados	Circuits and poles; reused items
Meter socket / meter-main aprovado	Approved meter socket / meter-main
Disconnect / painel conforme projeto	Disconnect / panel specified by the design
Condutores de entrada	Service conductors
Suportes e acessórios	Supports and accessories
Aéreo ou subterrâneo; requisitos da concessionária	Overhead or underground; utility requirements
Tensão, fases e capacidade definida; distâncias	Voltage, phases and specified capacity; distances
Subpanel e tampa	Subpanel and cover
Breaker do feeder compatível	Compatible feeder breaker
Feeder especificado	Specified feeder
Barras e acessórios	Bars and accessories
Painel de origem e especificação do subpanel	Source panel and subpanel specifications
Percurso e configuração do feeder	Feeder route and configuration
Breaker compatível	Compatible breaker
Cabo / condutores especificados	Specified cable / conductors
Caixa de conexão	Junction box
Tomada ou disconnect	Receptacle or disconnect
Equipamento e dados da placa/manual	Equipment and nameplate/manual data
Quantidade de circuitos; ponto final; percurso	Circuit count; endpoint; route
Tomadas por tipo	Receptacles by type
Switches / controles por tipo	Switches / controls by type
Placas por caixa	Cover plates by box
Caixas novas	New boxes
Conectores / pigtails	Connectors / pigtails
Troca ou instalação nova; quantidade por tipo	Replacement or new installation; quantity by type
Gangs; ambiente; proteção e controles	Gangs; location; protection and controls
Luminárias recessed	Recessed luminaires
Housing / trim se não incluso	Housing / trim if not included
Controle / dimmer compatível	Compatible control / dimmer
Cabo especificado	Specified cable
Conectores / caixas	Connectors / boxes
Quantidade e modelo; teto; ambiente	Quantity and model; ceiling; location
Acessórios inclusos; distribuição e percursos	Included accessories; layout and routes
Kit / luminária LED compatível	Compatible LED kit / luminaire
Driver se necessário	Driver if required
Etiquetas / adaptadores	Labels / adapters
Modelo das luminárias e ballast/driver existentes	Existing luminaire and ballast/driver models
Quantidade; troca completa ou kit; controle	Quantity; full replacement or kit; control
Breaker conforme placa/manual	Breaker specified by the nameplate/manual
Whip e conectores	Whip and connectors
Interligação quando no escopo	Interconnection when in scope
Modelo; placa; MCA/MOCP quando disponíveis	Model; nameplate; MCA/MOCP when available
Unidades; percurso; itens incluídos pelo fornecedor	Units; route; items included by supplier
Carregador quando fornecido	Charger when supplied
Receptáculo se indicado	Receptacle if specified
Montagem / acessórios	Mounting / accessories
Modelo/manual; hardwired ou receptáculo	Model/manual; hardwired or receptacle
Capacidade avaliada; corrente ajustada; percurso	Assessed capacity; adjusted current; route
Pontos e percurso; categoria e terminação	Endpoints and route; category and termination
Projeto; equipamento e conexões especificados	Design; specified equipment and connections
Dispositivos compatíveis por tipo	Compatible devices by type
Bases / backboxes se não inclusos	Bases / backboxes if not included
Cabo de fire alarm especificado	Specified fire alarm cable
Módulos conforme projeto	Modules specified by the design
Central, modelo, protocolo; adição ou troca	Panel, model, protocol; addition or replacement
Quantidade por tipo; compatibilidade; circuitos e percursos	Quantity by type; compatibility; circuits and routes
Definir especificação e quantidade; retirar itens não aplicáveis.	Specify product and quantity; remove items that do not apply.
Informe medidas positivas e margem válida.	Enter positive dimensions and a valid margin.
Adicione pelo menos um material.	Add at least one material.
Revise nome, unidade e quantidade positiva de todos os materiais.	Check the name, unit and positive quantity of every item.
Não foi possível salvar. Tente novamente.	Could not save. Try again.
Lista Guiada · versão 3	Guided Shopping · version 6
Como você quer montar sua lista?	How would you like to build your list?
Escolha o trabalho e marque materiais da sua biblioteca.	Choose the work and select products from your library.
Comece vazia, use a biblioteca ou adicione itens manualmente.	Start empty, use the library or add items manually.
Usar lista anterior	Reuse a previous list
Continuar rascunho	Continue draft
Rascunho inválido. Crie uma nova lista.	Invalid draft. Create a new list.
Crie uma nova compra com os mesmos materiais, inclusive itens manuais. A compra original será preservada.	Create a new purchase using the same materials, including manual items. The original purchase is preserved.
Buscar lista anterior	Search previous lists
Lista avulsa	Standalone list
Usar esta lista	Use this list
Nenhuma lista anterior encontrada.	No previous lists found.
nova compra	new purchase
Classificar usos do material	Classify material uses
Marque todos os trabalhos em que este produto pode ser usado. Essas etiquetas orientam as sugestões; confira as especificações antes de comprar.	Select the work types for this product. These tags guide suggestions; check specifications before purchasing.
Salvar classificação	Save classification
Classificação salva na biblioteca.	Classification saved in the library.
Qual trabalho você vai fazer?	What work will you do?
Marque um ou mais modelos. Depois você escolhe os materiais.	Select one or more templates, then choose materials.
Seu modelo personalizado	Your custom template
Modelo inicial · você escolhe os materiais	Starter template · you choose the products
Escolher materiais →	Choose materials →
Marque pelo menos um trabalho.	Select at least one work type.
Personalizar lista	Customize list
Montar lista de compras	Build shopping list
Nome da lista	List name
Alterar tipo de trabalho	Change work type
Detalhes do trabalho (opcional)	Work details (optional)
Descrição / situação	Description / situation
Instalação nova	New installation
Substituição	Replacement
Expansão	Expansion
Sua lista	Your list
Marque produtos abaixo ou adicione um material manualmente.	Select products below or add an item manually.
Novo material	New material
Da biblioteca	From library
Material manual	Manual item
Quantidade de	Quantity of
Editar nome, unidade e observações	Edit name, unit and notes
Nome do material manual	Manual item name
Nome do material	Material name
Observações / especificação	Notes / specifications
Compra já registrada — será preservada.	Purchase already recorded — will be preserved.
Remover da lista	Remove from list
Material manual adicionado.	Manual item added.
Adicionar material manualmente	Add an item manually
Quantidade manual	Manual quantity
Unidade manual	Manual unit
Observações do material manual	Manual item notes
Adicionar à lista	Add to list
Buscar na biblioteca	Search library
Nome, código ou modelo...	Name, code or model...
Sugestões da sua biblioteca por tipo de trabalho. Marque o que precisa e confira modelo, compatibilidade e quantidade.	Suggestions from your library by work type. Select what you need and check model, compatibility and quantity.
Sem código	No code
Na lista	In list
Sem usos definidos	No uses assigned
Editar usos	Edit uses
Nenhuma sugestão encontrada. Abra Biblioteca ou Material manual.	No suggestions found. Open Library or Manual item.
Nenhum material encontrado. Adicione manualmente.	No materials found. Add an item manually.
Ver mais produtos	Show more products
Estimar barras de conduíte	Estimate conduit sticks
Comprimento medido	Measured length
Comprimento da barra	Stick length
Unidade das medidas	Measurement unit
Margem (%)	Margin (%)
Adicionar estimativa manual	Add manual estimate
Conduíte — definir tipo e dimensão	Conduit — specify type and size
Revisar cortes e acessórios.	Review cuts and fittings.
Revisei os materiais, as especificações e as quantidades.	I reviewed the products, specifications and quantities.
Salvar rascunho	Save draft
Rascunho salvo nesta sessão do dispositivo.	Draft saved in this device session.
Salvar como novo modelo	Save as new template
Salvar alterações	Save changes
Criar lista de compras	Create shopping list
Informe o nome do modelo.	Enter the template name.
Escolha materiais antes de salvar o modelo.	Select materials before saving the template.
Novo modelo salvo na Lista Guiada.	New template saved in Guided Shopping.
Informe o nome da lista.	Enter the list name.
Confirme a revisão dos materiais antes de criar a lista.	Confirm your review before creating the list.
Lista salva. Você pode continuar personalizando.	List saved. You can continue customizing it.
Entre no sistema para criar listas.	Sign in to create lists.
Cadastro central de material	Central material record
Novo produto na biblioteca	New library product
Biblioteca central · código interno separado do modelo e dos códigos de cada loja.	Central library · internal code is separate from manufacturer and supplier codes.
Nome do produto	Product name
Código interno	Internal code
Gerado ao criar	Generated on creation
Modelo / referência do fabricante	Manufacturer part / model
UPC / código de barras	UPC / barcode
Unidade de compra	Purchase unit
Tipo de cadastro	Record type
Produto específico	Specific product
Família genérica — especificar antes da compra	Generic family — specify before purchasing
Não classificada	Unclassified
Fios e cabos	Wire and cable
Tomadas, switches e placas	Receptacles, switches and plates
Painéis e breakers	Panels and breakers
Fixações e acessórios	Fasteners and accessories
Quantidade por embalagem (opcional)	Pack quantity (optional)
Unidade da embalagem	Pack unit
Link da fonte / fabricante	Source / manufacturer link
URL da foto	Photo URL
Usos na lista guiada	Guided shopping uses
Códigos por fornecedor	Supplier codes
Código da loja 	Supplier code 
Link do produto 	Product link 
Unidade da loja 	Supplier unit 
Preço de referência 	Reference price 
Data do preço 	Price date 
Remover fornecedor	Remove supplier
Adicionar fornecedor	Add supplier
Informações técnicas e instalação	Technical and installation details
Salvar cadastro	Save record
Produto salvo na biblioteca central.	Product saved in the central library.
Informe nome e unidade.	Enter a name and unit.
Este código interno já existe.	This internal code already exists.
UPC precisa ter 12, 13 ou 14 dígitos. Código da loja deve ficar no fornecedor.	UPC must contain 12, 13 or 14 digits. Enter store codes under suppliers.
Este fabricante/modelo ou UPC já existe na biblioteca. Abra o cadastro existente.	This manufacturer/part or UPC already exists in the library. Open the existing record.
Informe uma quantidade de embalagem positiva.	Enter a positive pack quantity.
Informe o nome do fornecedor.	Enter the supplier name.
Use um link HTTPS válido para o produto.	Use a valid HTTPS product link.
Use uma URL HTTPS válida para a foto.	Use a valid HTTPS photo URL.
Use uma URL HTTPS válida para a fonte.	Use a valid HTTPS source URL.
Fornecedor da compra	Purchasing supplier
Mostrar todos os códigos	Show all codes
Copiar lista	Copy list
Lista copiada com os códigos.	List copied with codes.
Não foi possível copiar. Use o PDF.	Could not copy. Use the PDF.
Print / PDF inclui fotos e códigos. Para enviar esse PDF, salve-o e anexe ao e-mail ou WhatsApp.	Print / PDF includes photos and codes. Save the PDF and attach it to an email or WhatsApp message.
Lista Guiada / Personalizada	Guided / Custom list
Lista rápida	Quick list
Nova lista	New list
Cadastro completo	Full record
Somente o proprietário pode editar a biblioteca.	Only the owner can edit the library.
Entre novamente no sistema.	Sign in again.
Use até 200 materiais por lista nesta versão.	Use up to 200 materials per list in this version.
Esta lista foi removida.	This list was removed.
Outra pessoa alterou os dados da lista. Feche e abra novamente.	Another person changed the list. Close and reopen it.
A lista mudou. Feche e abra novamente antes de editar.	The list changed. Close and reopen it before editing.
Outra pessoa alterou esta lista. Feche e abra novamente para revisar.	Another person changed this list. Close and reopen it to review.
Adicionar	Add
Fechar	Close
Voltar	Back
Fabricante	Manufacturer
Fornecedor	Supplier
Categoria	Category
Família	Family
Conduítes	Conduit
Conexões	Fittings
Caixas	Boxes
Aterramento	Grounding
Iluminação	Lighting
Detecção	Detection
Notificação	Notification
Especificações	Specifications
Descrição	Description
Elétrica	Electrical
Outros	Other
Sem foto	No photo
Identificação	Identification
Conectores	Connectors
Biblioteca	Library
Sugestões	Suggestions
Lista Guiada	Guided list
Lista Personalizada	Custom list
Unidade	Unit
Obra	Project
Salvar	Save
materiais	materials
produtos	products
barra	stick
barras de	sticks of
margem	margin
 de 	 of 
OUTROS	OTHER'''
MAPPING=dict(line.split('\t',1) for line in PAIRS.splitlines())
def translate(text):
 for a,b in sorted(MAPPING.items(),key=lambda x:-len(x[0])):text=text.replace(a,b)
 return text
if __name__=='__main__':
 for path in ['public/central-catalog-v1.js','public/guided-shopping-v1.js','tests/central-catalog.cjs','tests/guided-shopping.cjs','tests/catalog-legacy-identities.cjs']:
  p=pathlib.Path(path);p.write_text(translate(p.read_text()))
 # Index has persisted keys and legacy multilingual matching. Only explicit phrases are replaced.
 p=pathlib.Path('public/index.html');s=p.read_text()
 for a,b in sorted(MAPPING.items(),key=lambda x:-len(x[0])):
  if len(a)>10 or a in {'OUTROS'}:s=s.replace(a,b)
 p.write_text(s)
