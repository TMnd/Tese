`API version 1 - Author: João Amaral!`

**Introduction:**

API desenvolvida para a tese do tema "Recomendação de percursos com base de parâmetros e restrições multidimensionais" do mestrado de Engenharia de informatica da Universidade de Aveiro.

**Requisitos:**

-lazy<br>
-rtree<br>
-psycopg2<br>
-requests<br>
-flask<br>
-flask_cors<br>
-configparser<br>
-GDAL:<br>
&nbsp;&nbsp;&nbsp;-Debian:<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- apt-get install python3_gdal ou python3-gdal -- (para o python)<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- apt-get install gdal_bin     -- (para o script)<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;se = raise OSError("Could not find libspatialindex_c library file"):<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;apt-get install libspatialindex-dev<br>
-Flask-SQLAlchemy<br>
-flask_httpauth<br>
-passlib<br>

**Estrutura:**

Esta API esta dividida em 4 classes. Cada classe é sobre uma area do trabalho especifico.
- Inicialização da API (init.py):
    - A inicialização da API tem duplo objectivo, verificação/criação e preenchimento de dados. 
    No arranque a API irá efectuar um conjunto de verificações com o objectivo de garantir se as extensões encontram-se instaladas para depois 
    proceder a criação das tabelas e o preenchimento dos dados nas respectivas tabelas.

- Pois (POIS.py):
    - Esta classe concentra todos os metodos necessarios para o upload dos dados 
    dos pontos de interesse e selecção dos mesmos.
- Interação com o mapa (mapinteraction.py):
    - Esta classe concentra todos os metodos necessarios para o utilizador X poder interagir com o mapa,
    contém os metodos:
        - Inicialização da tabela do utilizador,
        - Selecionar o vertice mais perto das coordeadas selecionadas,
        - Bloquear estradas e vertices,
        - Carregamento dos vertices do grafo,
        - Carregamento das arestas do grafo,
        - Solução da tese proposta,
        - Solução do TSP.
- Função de custo (customCost.py):
    - Esta class contém todos os multiplicadores e irá alterar o custo do
    grafo em função das opções inseridas pelo utilizador.

**Metodos principais:**

Lista dos metodos que é possivel aceder directamente na api, eles encontram-se
divididos em 4 categorias:<br>
- Autenticação:<br>
    A autenticação é necessario para que seja possivel mais que uma pessoa possa utilizar a API ao mesmo tempo <br>
    O codigo utilizado foi originalmente adquirido no seguinte projecto:
    https://github.com/miguelgrinberg/REST-auth
    - POST **/api/v1/users**<br>
    Para registar um novo utilizador.<br>
    É adquirido hash da password usando a biblioteca PassLib que utiliza o algoritmo sha256_crypt.<br>
    É altamente recomendado que a API corra no protocolo https.<br>
    **Input:** Um objecto JSON que contanha a informação nos campos `username` e `password`.<br>
    **Return:** 
        - Sucess: Status code 201 e a informação do utilização recem criado.
        - Error:  Status code 400 (bad request).
    
    - GET  **/api/v1/token**<br>
    Metodo para adquirir o token de acesso do utilizador que se encontra a autenticar<br>
    **Input:** Autenticação utilizando a autenticação basica em HTTP <br>
    **Return:**   
        - Sucess: Retorna de um objecto JSON com o token e a duração do mesmo.
        - Error: Status code 401 (unauthorized).

    - GET  **/api/v1/resource**<br>
    Metodo que adquire a informação protegida do utilizador em base do token.<br>
    **Input:** O token adquirido<br>
    **Return:** 
        - Sucess: Retorna um objecto JSON com a informação do utilizador correspondente.<br>
        - Error: Status code 401 (unauthorized)
 
- UserData:<br>
    - GET  **/api/v1/readdata**<br> 
    Este método irá adquirir os valores das preferências do utilizador. <br>
    **Metodo usado:** checkDataBase from mapInteration.py<br> 
    **Parametros:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_id_: Identificação do utilizador<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Um objecto JSON com os dados recolhidos da base de dados.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `{"cover":{"coverage_rainprotected":false,"coverage_shape":false},"incli":{"helpmovement":false,"stairs":false},"roadMultiplier":{"cicleway":1,"dirt":5,"portugueswalkway_concrete":1,"tarmac":5,"woodenway_metalway":5},"security":{"allowbikes":false,"allowcars":true}}`   <br>
    
    - POST **/api/v1/updatedata**<br>
    Actualização das preferências utilizadas pela função de custo. <br>
    **Metodo usado:** addDataDatabase from mapInteration.py<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_id_:Identificação do utilizador. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_Calcadaportuguesa_Cimento_: Valor correspondente da preferencia. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_Alcatrao_: Valor correspondente da preferencia. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_Pistabicicleta_: Valor correspondente da preferencia. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_Terra_: Valor correspondente da preferencia. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_Passadicomadeira_metal_: Valor correspondente da preferencia. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_escadas_: Se as escadas sao relevantes. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_ajudamovimento_:  Se as ajudas pelo caminho sao relevantes. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_coverageshape_cover_:  Se a cobertuda do sol é relevante. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_coveragerainprotected_cover_:  Se a covertura da chuva é relevante. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_allowcars_security_: Se quer diminuir a relevancia de estradas utilizadas por carros. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_allowbikes_security_: Se quer diminuir a relevancia de estradas utilizadas por bicilcetas. <br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Confirmação que os dados foram atualizados. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `{"success":true}`<br>
    
- POIS:<br>
    - POST **/api/v1/addPois**<br>
    Método que lê um ficheiro CSV com a informação dos pois que se pretende adicionar no mapa, calcula também o vértice mais próximo das coordenadas fornecidas e gera o geom para que se possa ser representado no mapa. <br>
    **Metodo usado:** add from POIS.py <br>
    **Input:** Ficheiro CSV com a informação dos pontos de interesse com a seguinte estrutura: <br>
    `nome do poi, tipo do pois (se é um café, bar, igreja), latitude, longitude`<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Confirmação que os pois foram inseridos na base de dados.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `{"success":true}`<br>
    
    - GET  **/api/v1/loadPois**<br>
    Quando se visita a página para interagir com a API este método é ativado para carregar toda a informação dos pois que se encontram na base de dados. <br>
    **Metodo usado:** load from POIS.py<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_id_: Identificação do utilizador. <br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Informação sobre todos os pois existentes da base de dados para imprimir no mapa. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `{'cv_lat': '40.5749709', 'id': 81, 'latitude': '40.575006120376585', 'geom': '0101000020E610000086CD5BD0D6E420C06AD37DA598494440', 'selecionado': True, 'cv_long': '-8.4469514', 'tipo': 'cafe', 'nome': 'zeca', 'userid': 0, 'longitude': '-8.447102765884397'}`
    
    - POST **/api/v1/selectPoi**<br>
    Método de seleção dos pois, verifica o estado atual do poi alterando-o entre ativo e não ativo para que quando se executar o algoritmo ter em conta o poi em questão na lista que será criado pelo algoritmo de Simulated Annealing do pgRouting. <br>
    **Metodo usado:** select from POIS.py<br>
    **Input:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_userid_: Identificação do utilizador.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_long_: Valor de longitude do POI selecionado.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_lat_: Valor de latitude do POI selecionado.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_selec_: Valor booleano que determina se o poi se encontra selecionado ou nao.<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Confirmação da alteração do estado do POI.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `{ success: true }`
    
    - POST **/api/v1/removeallpoi**<br>
    Este método tem duas funcionalidades, uma é a remoção de todos os pois classificados como "custom" que foram inseridos pelo utilizado ou remover os pois individualmente. <br>
    **Metodo usado:** removePOI from POIS.py<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_long_: Valor de longitude do POI selecionado.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_lat_: Valor de latitude do POI selecionado.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_option_: Opção para determinar se é para apagar os pois na globalidade ou um poi individual.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_userid_: Indentificação do utilizador.<br>
    **Return:**<br> 
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: A confirmação da remoção do(s) pontos de interesse(s).<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `{ success: true }`
    
    - GET **/api/v1/geomCoord**<br>
    O metodo irá adquirir as coordenadas do geom.<br>
    **Metodo usado:** geomToCoord from POIS.py<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_geom_: O valor geografico do vertice desejado.<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: As coordenadas do vertice.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    
- Mapa:<br>
    - POST **/api/v1/initUser**<br>
    Método para criar as tabelas temporarias e restauro das tabelas caso elas ja se encontram criadas. <br>
    **Metodo usado:** initU from mapInteration.py<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_id_: Indentificação do utilizador.<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Confirmação da criação da tabela temporária do utilizador.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `{"UserData_Processed":true}`
    
    - GET **/api/v1/closedPoints**<br>
    Método que calcula o vértice mais perto das coordenadas adquiridas do mapa através do clique. <br>
    **Metodo usado:** closedP from mapInteration.py<br>
    **Input:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_longitude_: Valor da longitude na zona clicada do mapa.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_latitude_: Valor da latitude na zona clicada do mapa.<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Coordenadas do vértice mais perto.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `-8.4435497 40.5754472`
    
    - GET **/api/v1/teseSolucao**<br>
    Algoritmo desenvolvido para resolver o problema do _Traveling salesman_ que mostra o caminho a percorrer num mapa de uma determinada cidade passando por pontos de interesse intermédios.<br>
    **Metodo usado:** travelingSalemanSolução from mapInteration.py <br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_id_: Indentificador do utilizador actual.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_longitude_: Valor da longitude do ponto inicial.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_latitude_: Valor da latitude do ponto inicial.<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Caminho gerado pelo algoritmo em formato geoJSON.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `{ "type": "FeatureCollection", "features": [ {"type": "Feature", "geometry": {"type":"LineString","coordinates":[[-8.4450851,40.5774447],[-8.4455042,40.5774103]]}, "properties": {"0":""}},{"type": "Feature", "geometry": {"type":"LineString","coordinates":[[-8.4455042,40.5774103],[-8.4454981,40.5773402]]}, "properties": {"0":""}},{"type": "Feature", "geometry": {"type":"LineString","coordinates":[[-8.4454981,40.5773402],[-8.445418,40.5768687]]}, "properties": {"0":""}},{"type": "Feature", "geometry": {"type":"LineString","coordinates":[[-8.445418,40.5768687],[-8.4453545,40.5763719]]}, "properties": {"0":""}},{"type": "Feature", "geometry": {"type":"LineString","coordinates":[[-8.4453545,40.5763719],[-8.44511,40.5763606],[-8.4449521,40.5763587]]}, "properties": {"0":""}},{"type": "Feature", "geometry": {"type":"LineString","coordinates":[[-8.4449521,40.5763587],[-8.4449664,40.5764756],[-8.4450731,40.5773514]]}, "properties": {"0":""}},{"type": "Feature", "geometry": {"type":"LineString","coordinates":[[-8.4450731,40.5773514],[-8.4450851,40.5774447]]}, "properties": {"0":""}} ]}`
    
    - GET **/api/v1/soloteseSolucao**<br>
    Método que gera o caminho sem pontos de interesses intermedio. <br>
    **Metodo usado:** SolotravelingSalemanSolução from mapInteration. <br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_longitude:_: Valor da longitude do ponto inicial.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_latitude_: Valor da latitude do ponto inicial.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_id_: Indentificador do utilizador actual.<br> 
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_distanciaArea_: Valor do raio de pesquisa.<br> 
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Caminho gerado.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    
    - GET **/api/v1/tsp**<br>
    Método que gera a lista de pontos de interesse a visitar através da heurística do cálculo da distância euclidiana. <br>
    **Metodo usado:** tsp from mapInteration. <br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_list_: Lista dos ids dos vertices em que é para selecionar a ordem de visita. <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_initialPoint_: Id do vertice inicial do caminho. <br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: A lista de sequencia de pontos a visitar.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `[3468, 30240, 30464, 51783, 3468]`
    
    - GET **/api/v1/blockRoad**<br>
    Método utilizado para que o utilizador possa escolher uma aresta através do cálculo da distancia entre as coordenadas selecionadas no mapa e as diferentes coordenadas que constituem o valor geográfico das arestas, podendo selecionar a que esta mais perto.<br>
    **Metodo usado:** blockRoad from mapIteration.py <br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_lat_: Coordenada de latitude em que clicou no mapa.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_long_: Coordenada de longitude em que clicou no mapa.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_userid_: Indentificador do utilizador actual.<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Uma array com a informação em formato geoJSON com a estrada bloqueada e o identificador da estrada bloqueada.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `[ 276, "{ \"type\": \"FeatureCollection\", \"features\": [ {\"id\":276, \"type\": \"Feature\", \"geometry\": {\"type\":\"LineString\",\"coordinates\":[[-8.4450731,40.5773514],[-8.4449664,40.5764756],[-8.4449521,40.5763587]]}, \"properties\": {\"0\":\"\"}} ]}" ]`
        
    - GET **/api/v1/showPoints**<br>
    Método que carrega a informação de todos os vertices do grafo em uma determinada área.<br>
    **Metodo usado:** showPoints from mapInteration.py<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_long1_: Coordenada de longitude do limite superior esquerdo.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_lat1_: Coordenada de latitude do limite superior esquerdo.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_Long2_: Coordenada de longitude do limite superior direito.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_lat2_: Coordenada de latitude do limite superior direito.<br>
    **Return:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: A informação de todos os pontos dentro dessa área em formato JSON.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
       
    - GET **/api/v1/insertBlock**<br>
    Método que permite o utilizador escolher um vértice do grafo como um anti poi aumentando assim os custo a todas as arestas que se ligam a esse vértice.<br>
    **Metodo usado:** addunwantedpoi from mapInteration.py<br>
    **Input:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_userid_: Indentificador do utilizador actual.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_long_: Coordenada de longitude em que clicou no mapa<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_lat_: Coordenada de latitude em que clicou no mapa<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Array com as coordenadas do anti-poi e das arestas que se ligam ao anti-pois.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    **Exemplo da informação recebida:**<br>
    `[ 65, "-8.443555 40.576268", "{ \"type\": \"FeatureCollection\", \"features\": [ {\"type\": \"Feature\", \"geometry\": {\"type\":\"LineString\",\"coordinates\":[[-8.4427603,40.5762212],[-8.443555,40.576268]]}, \"properties\": {\"0\":\"\"}},{\"type\": \"Feature\", \"geometry\": {\"type\":\"LineString\",\"coordinates\":[[-8.4435728,40.5757589],[-8.443555,40.576268]]}, \"properties\": {\"0\":\"\"}},{\"type\": \"Feature\", \"geometry\": {\"type\":\"LineString\",\"coordinates\":[[-8.4444008,40.576346],[-8.4442143,40.5763188],[-8.443555,40.576268]]}, \"properties\": {\"0\":\"\"}} ]}" ]`
    
    - GET **/api/v1/showBlockedRoad**<br>
    Método que ao carregar o mapa carrega a informação das diferentes arestas bloqueadas relacionadas com o utilizador.<br>
    **Metodo usado:** showBlockedRoads from mapInteration.py<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_id_: Indentificador do utilizador actual.<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Os dados de todas as estradas bloqueadas.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    
    - GET **/api/v1/removeallBlockedRoad**<br>
    Método para remover todos os bloqueios no mapa e limpando a informação dos mesmos na base de dados.<br>
    **Metodo usado:** removeAllBlockedRoads from mapInteration.py<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_userid_: Identificação do utilizador actual.<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Confirmação da remoção de todos os bloqueios.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    
    - GET **/api/v1/unwantedPois**<br>
    Método que remove um anti poi individualmente  e restaura os custos originais das 
    arestas que se conectam com o vértice.<br>
    **Metodo usado:** removeunwantedpoi from mapInteration.py.<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_userid_: Identificação do utilizador que o anti-poi pertence.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_long_: Coordenada longitude do anti-poi.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_lat_: Coordenada latitude do anti-poi.<br>
    **Return:**<br> 
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: Confirmação da remoção do anti-poi.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    
    - GET **/api/v1/removeBlockedRoads**<br>
    Remove a aresta selecionada registada com o utilizador atual.<br>
    **Metodo usado:** removeblockroad from mapInteration.py.<br>
    **Input:** <br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_roadid_: Identificador da estrada.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-_id_: Identificador do utilizador actual.<br>
    **Return:**<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Sucess: A lista de sequencia de pontos a visitar.<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- Error: Erro de conexão à base de dados.<br>
    