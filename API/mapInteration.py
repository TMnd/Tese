from psycopg2 import sql
import psycopg2
import psycopg2.extras
import re
import json
import math
import configparser
import sys
import requests
from flask import jsonify,make_response

class mapInteration():
    host = ''
    user = ''
    dbname = ''
    password = ''
    #-------
    # Função de custo
    # variaveis do ficheiro ini
    roadMultiplier = {}
    cover = {}
    roadStatus = {}
    sidewalkWidth = {}
    pathInclination = {}
    wifi = {}
    security = {}
    # valores pre-definidos para calculo de preferencias de caminho
    # o utilizador pode nao querer usar um certo caminho mas a um caso extremo
    # poderá ser usado. O custo vai ser aumentado mas nao ao ponto de nao ser utilizado.
    roadValues = {
        "tarmac": [41, 21, 22, 31, 31, 42, 63],
        "dirt": [51],
        "portugueswalkway_concrete": [72, 62, 92],
    # a calçada portuguesa e o chao de betao estao dentro destas categorias.
        "cicleway": [81, 71],
        "woodenway_metalway": [91]  # as pontes de meta e de passadiços de metal têm o mesmo valor.
    }
    roadUsers = {
        "car": [21, 22, 31, 32, 41, 42, 43, 51, 63],
        "bike": [31, 32, 41, 42, 43, 51, 62, 63, 71, 72, 81],
        "foot": [63, 62, 71, 72, 91, 92, 81]
    }
    #----

    def __init__(self, host, user, dbname, password):
        self.host = host
        self.user = user
        self.dbname = dbname
        self.password = password
        # ------
        self.roadMultiplier = self.loadtomemory("roadMultiplier")
        self.cover = self.loadtomemory("cover")
        self.roadStatus = self.loadtomemory("roadStatus")
        self.sidewalkWidth = self.loadtomemory("sidewalkWidth")
        self.pathInclination = self.loadtomemory("pathInclination")
        self.wifi = self.loadtomemory("wifi")
        self.security = self.loadtomemory("security")

    #Done!
    def initU(self, userid):
        """
        Method for creating a temporary table for each user.
        :param id: user id which is connecting to the service.
        :return:
        """
        tabelaUso = 'tablep_'+str(userid)
        tabelaCusto = 'table_cost_'+str(userid)
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        cur.execute("SELECT to_regclass(%s)", (tabelaUso,))
        resulttable = cur.fetchone() #('*nome_tabela*',)
        cur.execute("SELECT to_regclass(%s)", (tabelaCusto,))
        resulttable_cost = cur.fetchone()
        if resulttable_cost[0] is None and resulttable[0] is None:
            print("copiar os dados da tabela original para as duas novas tabelas e adcionar o pk em cada nova tabela")
            #Tabela para os custos
            cur.execute(sql.SQL("SELECT * INTO {} FROM rede_viaria_bv").format(sql.Identifier(tabelaCusto)))
            cur.execute(sql.SQL("ALTER TABLE {} ADD PRIMARY KEY(id)").format(sql.Identifier(tabelaCusto)))
            conn.commit()
            self.runCostfuncton(userid,tabelaCusto)
            cur.execute("SELECT * INTO "+ str(tabelaUso) +" FROM "+ str(tabelaCusto))
            cur.execute(sql.SQL("ALTER TABLE {} ADD PRIMARY KEY(id)").format(sql.Identifier(tabelaUso)))
            conn.commit()
        else: # as tabelas existem porque o utilizador ja entrou pelo menos uma vez
            table = "tablep_"+str(userid)
            cur.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(table)))
            cur.execute("SELECT * INTO tablep_" + str(userid) + " FROM table_cost_" + str(userid)) #Todo: Tem de ser verificada!
            cur.execute(sql.SQL("ALTER TABLE {} ADD PRIMARY KEY(id);").format(sql.Identifier(table)))
            conn.commit()
        cur.close()
        conn.close()
        return jsonify({'UserData_Processed': True})

    #Done!
    def closedP(self, longitude, latitude): #é preciso
        """
        Method to get the point closest to the coordinates clicked on the map.
        :param longitude: longitude value from the start point
        :param latitude: latitude value from the start point
        :return: The closest vertex from the coordinates clicked on the map
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        pointCoord = "POINT(" + longitude + " " + latitude + ")"
        cur.execute("SELECT geom_vertex FROM rede_viaria_bv_vertex ORDER BY geom_vertex <-> ST_GeometryFromText(%s,4326) LIMIT 1;", (str(pointCoord),))
        row = str(cur.fetchone())
        geom = re.search('\((.*),\)', row)
        cur.execute("SELECT ST_AsText(geom_vertex) FROM rede_viaria_bv_vertex where geom_vertex=" + geom.group(1))
        row2 = str(cur.fetchone())
        closestCoord = re.search('\(\'POINT\((.*)\)\',\)', row2)
        return closestCoord.group(1)

    def SolotravelingSalemanSolução(self, longitude, latitude, id, distanciaArea):
        """

        :param longitude:
        :param latitude:
        :param id:
        :param distanciaArea:
        :return:
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        tabela = "table_cost_"+str(id)
        tabelapessoa = "tablep_"+str(id)
        cur = conn.cursor()
        pointInfo = 'POINT('+longitude+' '+latitude+')'
        cur.execute("SELECT id, geom_vertex from rede_viaria_bv_vertex where geom_vertex=ST_GeomFromText(%s,4326)", (pointInfo,))
        getId = cur.fetchone()
        selectPointId = getId[0]
        selectPointGeom = getId[1]
        cur.execute("SELECT id FROM rede_viaria_bv_vertex as t where ST_DWithin(%s,t.geom_vertex,%s,true)",(selectPointGeom, distanciaArea))
        result = cur.fetchall()
        inputList = [] #para conter os vertex especiais e efectuar o tsp
        inputList.append(selectPointId)
        print(tabelapessoa)
        #iterar os vertices adquiridos anteriormente
        for x in result:
            if x[0]!=selectPointId:
                #vertices especiais com 2 ou mais vias de acesso
                cur.execute(sql.SQL("SELECT id,km FROM {} where source=%s or target=%s").format(sql.Identifier(tabelapessoa)), (x[0],x[0],))
                resultAuditWayId = cur.fetchall()
                print(x)
                if len(resultAuditWayId) >= 2:
                    print(resultAuditWayId)
                    print("tamanho: " + str(len(resultAuditWayId)))
                    contatudorDeEstradasValidas = len(resultAuditWayId)
                    for w in resultAuditWayId:
                        if w[1] == 1000:
                            contatudorDeEstradasValidas -= 1
                    print("numero de estrdas sem estarem bloquedas: " + str(contatudorDeEstradasValidas))
                    if contatudorDeEstradasValidas >= 3:
                        inputList.append(x[0])
                    print("----------------------")
                else:
                    print("nada")
        print(inputList)
        inputList = sorted(inputList)
        print(inputList)
                #aqui dentro verificar o valor do custo  or target=%s
                #cur.execute(sql.SQL("SELECT km FROM {} where source=%s").format(sql.Identifier(tabelapessoa)), [x[0],])
                #resultkm = cur.fetchall()
                #for i in resultkm:
                #    print(i)
                #inputList.append(x[0])
        inputListlist = str(inputList).replace("[", "").replace("]", "")
        tspresult = self.tsp(inputListlist,selectPointId)
        tspSequence = []
        for x in tspresult:
            tspSequence.append(x[1])
        print(tspSequence)
    ###cur.execute("SELECT st_asgeojson(geom) AS geojson FROM pgr_deaparabkm2(%s,%s)", (str(tabela), tspSequence,))
    ###cur.execute("SELECT st_asgeojson(geom) AS geojson FROM pgr_deaparabkmtsp(%s,%s)", (str(tabela), tspSequence,))
        cur.execute("SELECT st_asgeojson(geom) AS geojson FROM pgr_deaparabkm2_5(%s,%s)", (str(tabela), tspSequence,))
        rows = cur.fetchall()
        geojson = self.createGeoJSON(rows, 1, 0)
        resultadosolopoint = {}
        resultadosolopoint["TypeRoute"] = "SoloPoint"
        #resultadosolopoint["geojson"] = ""
        resultadosolopoint["geojson"] = geojson
        cur.close()
        conn.close()
        return resultadosolopoint

    #Done!
    def travelingSalemanSolução(self,longitude,latitude,id):
        """
        Method that solves the problem at hand
        :param longitude: longitude value from the start point
        :param latitude: latitude value from the start point
        :param id: User id
        :return: The path generated
        """
        sequence = [] #para a sequencia de pois a visitar
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        cur.execute("SELECT id from rede_viaria_bv_vertex where geom_vertex=ST_GeomFromText('POINT("+longitude+" "+latitude+")',4326)")
        reslt1 = cur.fetchone()
        sequence.append(reslt1[0])
        print(id)
        cur.execute("SELECT cv_geom from pois where selecionado=True and (userid=0 or userid=%s)", (id,))
        reslt2 = cur.fetchall()
        print(reslt2)
        if len(reslt2) is 0:
            resultadosolopoint = {}
            resultadosolopoint["TypeRoute"] = "SoloPoint"
            resultadosolopoint["geojson"] = ""
            cur.close()
            conn.close()
            return resultadosolopoint
        else:
            for x in reslt2:
                cur.execute("SELECT id from rede_viaria_bv_vertex where geom_vertex='"+x[0]+"'")
                reslt3 = cur.fetchone()
                sequence.append(reslt3[0])
            tsp = self.tsp(sequence,reslt1[0]) #lista e ponto inicial
            path = self.AtoB(cur,tsp,id)
            cur.close()
            conn.close()
            return path

    def AtoB(self,cur,tsp,userid): #solução para o trabalho em si (é preciso criar a função durante a inicialização)
        """

        :param cur:
        :param tsp:
        :param userid:
        :return:
        """
        teste = []
        resultadofinal = {}
        for x in tsp:
            teste.append(x[1])
        tabela = 'tablep_'+userid
        print(tabela)
        cur.execute("SELECT st_asgeojson(geom) AS geojson FROM pgr_deaparabkmtsp(%s,%s)", (str(tabela),teste,))
        rows = cur.fetchall()
        for x in rows:
            print(x)
        geojson = self.createGeoJSON(rows,1,0)
        #self.tableRestore(userid)
        resultadofinal["TypeRoute"]="MultiPoint"
        resultadofinal["geojson"]=geojson
        return resultadofinal

    def createGeoJSON(self,rows,option,id2):
        """
        Method that must receive the return from the query with GEOM (already decoded)
        :param cur: Result of the query
        :param option: Caso seja necessario selectionar a linha e que ela tenha um id
            - 0 => Para inserir o id
            - 1 => para nao inserir um id
        :param id: Caso o option seja 0 para inserir o id desejado.
        :return: geoJSON data
        """
        cont = 0
        output = ''
        rowOutput = ''
        for row in rows:
            if option is 1:
                rowOutput = (',' if len(rowOutput) > 0 else '') + '{"type": "Feature", "geometry": ' + str(
                    row[0]) + ', "properties": {'
            elif option is 0:
                rowOutput = (',' if len(rowOutput) > 0 else '') + '{"id":' + str(id2) + ', "type": "Feature", "geometry": ' + str(
                    row[0]) + ', "properties": {'
            props = ''
            id = ''
            for key, val in enumerate(row):
                if key != "geojson":
                    props = (',' if len(props) > 0 else '') + '"' + str(key) + '":"' + self.escapeJsonString(val) + '"'
                if key == "id":
                    id += ',"id":"' + self.escapeJsonString(val) + '"'
            rowOutput += props + '}'
            rowOutput += id
            rowOutput += '}'
            output += rowOutput
            cont += 1
        output = '{ "type": "FeatureCollection", "features": [ ' + output + ' ]}'
        return output

    def escapeJsonString(self,value):  # list from www.json.org: (\b backspace, \f formfeed)
        """
        Method used only in the method criarGeoJSON where the main purpose is to change the special characters pointed
        by the variable "value".
        Ddirect conversatio from the PHP correspondent.
        :param value: Special character to change.
        :return: The corresponding character.
        """
        cont = 0
        value = str(value).encode()
        find = '"\\","/","\"","\n","\r","\t","\x08","\x0c"'
        escapers = find.split(",")
        replace = '"\\\\","\\/","\\\"","\\n","\\r","\\t","\\f","\\b"'
        replacements = replace.split(",")
        while cont != len(replacements):
            a = value
            b = str(escapers[cont].encode()).replace('"', '')
            if str(a) == str(b):
                return replacements[cont].replace('"', '')
            cont += 1
        return ""

    #Done!
    def tsp(self,list,initialPoint):
        """
        Method for solving the TravelingSalesMan problem using Euclidean heuristics.
        :param list: List of points (ids) with the algorithm will iterate. Example: xxx, xxx, ... , xxxx.
        :param initialPoint: id of the point which is the initial point of the path.
        :return: Order of visit from the input list.
        TODO: Versão 2: Add the option for a cost matrix. The results test show the execution time is way bigger than the Euclidean
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        inputList = str(list).replace("[", "").replace("]", "")
        tsp_query = "SELECT * from pgr_eucledianTSP( " \
                    "$$ " \
                    "SELECT id, st_X(geom_vertex) AS x, st_Y(geom_vertex) AS y FROM rede_viaria_bv_vertex WHERE id IN ("+ inputList +") " \
                    "$$, " \
                    "start_id := " + str(initialPoint) + " , " \
                    "tries_per_temperature := 0, " \
                    "randomize := false " \
                    ");"
        cur.execute(tsp_query)
        tsp = cur.fetchall()
        cur.close()
        conn.close()
        return tsp

    def tableRestore(self,id): #É preciso
        """
        Method to restore the user personal table after every interaction.
        :param id: User indentification number.
        :return:
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
        cur = conn.cursor()
        tabela = "tablep_"+str(id)
        cur.execute("DROP TABLE " + str(tabela) + ";")
        conn.commit()
        cur.execute("SELECT * INTO %s FROM table_cost_1", (tabela,))
        conn.commit()
        cur.close()
        conn.closer()

    #Done!
    def blockRoad(self, lat, long, userid): #é preciso
        """
        Method to single block a road.
        :param lat: Lat coordenate the position that was clicked in the map
        :param long: Long coordenate the position that was clicked in the map
        :param userid: User indentification
        :return: The geojson data to show the blocked road in the map
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        pointCoord = "POINT(" + long + " " + lat + ")"
        cur.execute("SELECT id FROM rede_viaria_bv_vertex ORDER BY geom_vertex <-> ST_GeometryFromText(%s,4326) LIMIT 20;",(str(pointCoord),))
        row = cur.fetchall()
        aux = []
        pontosDosTrajectosPerto = {}
        auxRoadData=[]
        for x in row:
            aux.append(x[0])
            for i in aux:
                source = i
                for j in aux:
                    target = j
                    cur.execute("SELECT id,geom_way FROM rede_viaria_bv WHERE source=%s and target=%s", (source, target))
                    idway = str(cur.fetchone())
                    if idway != "None":
                        key_value = (idway.replace("(","").replace(")","").replace(" ","")).split(",")
                        if id not in pontosDosTrajectosPerto:
                            pontosDosTrajectosPerto[key_value[0]]=key_value[1]
        menor=100 #valor simbolico para comparação
        for caminhos in pontosDosTrajectosPerto:
            cur.execute("SELECT ST_AsText("+pontosDosTrajectosPerto.get(caminhos)+")")
            teste = cur.fetchone()
            coordLineString = str(re.search(r'\((.*?)\)', teste[0]).group(1)).split(",")
            for coord in coordLineString:
                c = coord.split(" ")
                distancia = math.sqrt((float(long)-float(c[0]))**2 + (float(lat)-float(c[1]))**2)
                if distancia<menor:
                    menor = distancia
                    estradaSelecionada = caminhos
        #verificar se a rua ja se encontra bloqueada
        cur.execute("SELECT id,ref_wayid FROM road_blocked WHERE ref_userid = %s AND ref_wayid = %s",(userid, estradaSelecionada,))
        verificarExistencia = cur.fetchall()
        if len(verificarExistencia)==0:
            cur.execute("INSERT INTO road_blocked(ref_userid,ref_wayid,ref_unwantedPoi) VALUES (%s,%s,Null)",(userid, estradaSelecionada,))
            conn.commit()
            cur.execute("SELECT id FROM road_blocked WHERE ref_userid = %s AND ref_wayid = %s", (userid,estradaSelecionada,))
            resultado_blockroadID = cur.fetchone()
            cur.execute("SELECT st_asgeojson(geom_way) AS geojson FROM rede_viaria_bv WHERE id = %s", (estradaSelecionada,))
            geojson = self.createGeoJSON(cur, 0, resultado_blockroadID[0])
            auxRoadData.append(resultado_blockroadID[0])
            auxRoadData.append(geojson)
            tabela = "tablep_"+userid
            #cur.execute("UPDATE " + tabela + " SET km=(km*5) WHERE id=" + str(estradaSelecionada))
            cur.execute(sql.SQL("UPDATE {} SET km=1000 WHERE id = %s").format(sql.Identifier(tabela)), [estradaSelecionada])
            conn.commit()
            cur.close()
            conn.close()
            return auxRoadData
        else:
            print("ja existe")

    #Done!
    def addunwantedpoi(self,userid,long,lat): #É preciso
        """
        The method will add to the database the vertice corresponding to the click and will gather all
        the information about the edges connected to that vertivem. With all this information the cost
        is increased so the algorithm can ignore that specific area.
        :param userid: Indentification of the actual user.
        :param long: unwanted-POI longitude.
        :param lat: unwanted-POI longitude.
        :return: json object with the unwanted-poi coordenates and the connected roads.
        """
        geojsonData = []
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        table = "tablep_" + userid
        #Adquirir o ponto mais proximo
        closepP = str(self.closedP(long,lat))
        closedCoord = closepP.split(" ")
        point = 'POINT('+closedCoord[0]+' '+closedCoord[1]+')'
        cur.execute("SELECT id from rede_viaria_bv_vertex where geom_vertex=ST_GeomFromText('"+point+"',4326)")
        pontoMaisProximo = cur.fetchone()
        #Adquirir o id da rua em que o ponto mais proximo é o source e o target
        listWayId = []
        cur.execute("SELECT id from rede_viaria_bv where source=" + str(pontoMaisProximo[0]))
        listaSource = cur.fetchall()
        for x in listaSource:
            listWayId.append(x[0])
        cur.execute("SELECT id from rede_viaria_bv where target=" + str(pontoMaisProximo[0]))
        listaTarget = cur.fetchall()
        for x in listaTarget:
            listWayId.append(x[0])
        #adcionar o unwanted poi
        cur.execute("INSERT INTO unwanted_poi(ref_userid,ref_pointid) VALUES (%s,%s);", (userid, pontoMaisProximo,))
        conn.commit()
        #adquirir o id do unwantedpoi adcionado
        cur.execute("SELECT id FROM unwanted_poi where ref_userid = %s and ref_pointid = %s", (userid, pontoMaisProximo,))
        resultsIdunwantedPois = cur.fetchone()
        #Utilizar o id das ruas adquiridas para as bloquear
        for x in listWayId:
            cur.execute("INSERT INTO road_blocked(ref_userid,ref_wayid,ref_unwantedPoi) VALUES (%s,%s,%s);", (userid,x,resultsIdunwantedPois[0]))
            conn.commit()
            #cur.execute("UPDATE " + table + " SET km=(km*100) WHERE id=" + str(x))
            cur.execute(sql.SQL("UPDATE {} SET km=1000 WHERE id = %s").format(sql.Identifier(table)),[str(x)])
            conn.commit()
        cur.execute("SELECT id FROM unwanted_poi where ref_pointid = %s",(pontoMaisProximo,))
        pointid = cur.fetchone()
        geojsonData.append(pointid[0])
        #geoJson o unwantedPOINT e das ruas que ligam
        listWayId = str(listWayId).replace("[","").replace("]","")
        #- Ponto
        geojsonData.append(closepP)
        #- Ruas
        cur.execute("SELECT st_asgeojson(geom_way) as geojson from rede_viaria_bv WHERE id in (" + str(listWayId) + ")")
        geojson = cur.fetchall()
        geo = self.createGeoJSON(geojson,1,0)
        geojsonData.append(geo)
        cur.close()
        conn.close()
        return geojsonData

    # Done!
    def removeblockroad(self,roadid,id):
        """
        This method will remove all blocked road.
        :param roadid: ref_way id.
        :param id: user id.
        :return: confirmation of removal.
        """
        tableuso = "tablep_" + id
        tablecusto = "table_cost_" + id
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("I am unable to connect to the database")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        cur.execute("SELECT ref_wayid FROM road_blocked where id=%s", (roadid,))
        result = cur.fetchone()
        #adquirir o custo original
        cur.execute(sql.SQL("SELECT km FROM {} WHERE id = %s").format(sql.Identifier(tablecusto)), [result[0]])
        originalCost = cur.fetchone()
        cur.execute(sql.SQL("UPDATE {} SET km=%s WHERE id = %s").format(sql.Identifier(tableuso)), [originalCost[0],result[0]])
        conn.commit()
        cur.execute("DELETE FROM road_blocked WHERE id=%s and ref_userid=%s", (roadid,id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})


    #Done!
    def removeunwantedpoi(self,poiid,userid,long,lat):
        """
        Method to remove the unwanted pois and road block aggregated to that poi
        :param userid: To identify with blocks are for who
        :param long: Coordenate Long of the unwanted poi
        :param lat: Coordenate Lat of the unwanted poi
        :return:
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        tableuso = "tablep_" + userid
        tablecusto = "table_cost_" + userid
        #adquirir a lista de pontos ligados a unwanted poi
        cur.execute("SELECT ref_wayid from road_blocked where ref_unwantedpoi=%s", (poiid,))
        results = cur.fetchall()
        for x in results:
            print(str(x[0]))
            print(tableuso)
            cur.execute(sql.SQL("SELECT km FROM {} WHERE id = %s").format(sql.Identifier(tablecusto)), [x[0]])
            originalCost = cur.fetchone()
            #sql = """UPDATE tablep_1 SET km=(km/5) WHERE id="""+str(x[0])
            cur.execute(sql.SQL("UPDATE {} SET km=%s WHERE id = %s").format(sql.Identifier(tableuso)),[originalCost[0],x[0]])
            #cur.execute("select psycorg2update(%s,%s)", (tableuso,x[0]))
            conn.commit()
        #eliminar as estradas ligadas a unwantedpoi
        cur.execute("DELETE FROM road_blocked WHERE ref_unwantedpoi=%s", (poiid,))
        conn.commit()
        #eliminiar o unwantedpoi
        cur.execute("DELETE FROM unwanted_poi WHERE id=%s", (poiid,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})

    def blockRoadWithPoint(self,id): #possivelmente para retirar
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("I am unable to connect to the database")
        cur = conn.cursor()
        print("teste: " + str(id))
        cur.execute("SELECT st_asgeojson(geom_way) as geojson from rede_viaria_bv where source=" + id)
        geojson = cur.fetchall()
        for x in geojson:
            print(x)
        geo = self.createGeoJSON(geojson)
        cur.close()
        conn.close()
        return geo

    def rreplace(self, s, old, new, occurrence):  # para o replace da direita para a esquerda #possivelmente é para retirar
        li = s.rsplit(old, occurrence)
        return new.join(li)

    def showRoads(self, lat, long): #possivelmente é para retirar
        lista = {}
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        closedPointID = str(self.closedP(long, lat))
        cur.execute("SELECT id FROM rede_viaria_bv_vertex ORDER BY geom_vertex <-> ST_GeometryFromText('POINT("+closedPointID+")',4326) LIMIT 1")
        result = cur.fetchall()
        #cur.execute("SELECT node FROM pgr_drivingDistance('SELECT id, source, target, km as cost FROM rede_viaria_bv',%s, 1);", (result[0],))
        ponto = str(result[0]).replace("(","").replace(")","").replace(",","")
        cur.execute("SELECT geom_vertex from rede_viaria_bv_vertex where id ="+ponto)
        geomPoint = cur.fetchone()
        cur.execute("SELECT id, geom_vertex FROM rede_viaria_bv_vertex where ST_DWithin('"+geomPoint[0]+"', geom_vertex, 0.004)")
        nodesDistance = cur.fetchall()
        print(nodesDistance)
        cont=0
        for x in nodesDistance:
            ponto = str(x[0]).replace("(","").replace(")","").replace(",","")
            cur.execute("SELECT id FROM rede_viaria_bv WHERE source="+ponto)
            row = cur.fetchall()
            if len(row) != 0:
                for j in row: #porque ha casos que existe 2 estradas com o mesmo id de source
                    id = str(j).replace("(", "").replace(")", "").replace(",", "")
                    lista[cont] = id
            cont+=1
            cur.execute("SELECT id FROM rede_viaria_bv WHERE target=" + ponto)
            row = cur.fetchall()
            if len(row) != 0:
                for j in row:  # porque ha casos que existe 2 estradas com o mesmo id de source
                    id = str(j).replace("(", "").replace(")", "").replace(",", "")
                    lista[cont] = id
            cont += 1
        #pontos = str(lista).replace("[", "").replace("]", "").replace("'", "")
        #cur.execute("SELECT st_asgeojson(geom_way) AS geojson FROM rede_viaria_bv WHERE id in (" + pontos + ")")
        #geojson = self.createGeoJSON(cur)
        cur.close()
        conn.close()
        json_data = json.dumps(lista, ensure_ascii=False)
        return str(json_data)

    #Done!
    def showPoints(self,long1,lat1,long2,lat2): #É para deixar
        """
        Method to show every vertex beetween the limits
        :param long1: Long coordenate from the upper left limit
        :param lat1: Lat coordenate from the upper left limit
        :param long2: Long coordenate from the bottom right limit
        :param lat2: Lat coordenate from the bottom right limit
        :return: All the vertex data in json format
        """
        #limite no mapa dos pontos escolhidos
        #long1 = -8.449817161407472
        #lat1 = 40.57785999076844
        #long2 = -8.435547809448243
        #lat2 = 40.5701996018219
        lista = {}
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        cur.execute("SELECT id, ST_AsText(geom_vertex) FROM rede_viaria_bv_vertex")
        result = cur.fetchall()
        for x in result:
            coord = (re.search(r'\((.*?)\)',x[1]).group(1)).split(" ")
            long = coord[0]
            lat = coord[1]
            if long <= str(long1) and long >= str(long2) and lat <= str(lat1) and lat >= str(lat2): #melhora isto...
                lista[x[0]] = coord
        cur.close()
        conn.close()
        json_data = json.dumps(lista, ensure_ascii=False)
        return str(json_data)

    # Done!
    def removeAllBlockedRoads(self, userid): #é preciso para remover todos os bloqueios
        """
        Method to remover every block
        :param userid:
        :return:
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        cur.execute("DELETE FROM road_blocked WHERE ref_userid=%s", (userid,))
        conn.commit()
        cur.execute("DELETE FROM unwanted_poi WHERE ref_userid=%s", (userid,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})

    #Done!
    def showBlockedRoads(self, userid): #É preciso para mostrar os unwanted pois e as estradas bloqueadas
        """
        Method returns all blocked roads and unwanted-POI related to the actual user
        :param userid: Identification of the actual user
        :return:
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("I am unable to connect to the database")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        table = "tablep_"+userid
        outputData=[]
        """Unwanted POIS"""
        listofUnwantedPoi={}
        #Adquirir a informação do unwantedpoi
        cur.execute("SELECT id,ref_pointid from unwanted_poi where ref_userid=%s", (userid,))
        getpointreferences = cur.fetchall() #(id, ref_pointid)
        contunwantedpointarray = 0
        for x in getpointreferences:
            auxArray = []
            auxArray.append(x[0])
            cur.execute("SELECT ST_AsText(geom_vertex) from rede_viaria_bv_vertex where id=" + str(x[1]))
            getpointreferences = cur.fetchone()
            coord = (re.search(r'\((.*?)\)', getpointreferences[0]).group(1))
            auxArray.append(coord) #adicionar ao sub array dentro do dicionario
            #Adquirir a informação das vias relacionadas com o anti poi
            cur.execute("SELECT ref_wayid from road_blocked where ref_userid=%s and ref_unwantedPoi=%s", (userid,x[0]))
            getreferencias = cur.fetchall()
            if len(getreferencias) is not 0:
                listaDeViasLigadasAntiPoi = []
                for x in getreferencias:
                    # para actualizar os custos das ruas bloqueadas!
                    # cur.execute("UPDATE " + table + " SET km=(km*100) WHERE id=" + str(x[0]))
                    cur.execute(sql.SQL("UPDATE {} SET km=1000 WHERE id = %s").format(sql.Identifier(table)),[x[0]])
                    conn.commit()
                    listaDeViasLigadasAntiPoi.append(x[0])
                cur.execute("SELECT st_asgeojson(geom_way) AS geojson FROM rede_viaria_bv WHERE id in (" + str(listaDeViasLigadasAntiPoi).replace("[", "").replace("]", "") + ")")
                listageoms = cur.fetchall()
                geojson = self.createGeoJSON(listageoms,1,0)
                auxArray.append(geojson)
            listofUnwantedPoi[contunwantedpointarray] = auxArray
            contunwantedpointarray = contunwantedpointarray + 1
        outputData.append(listofUnwantedPoi)
        """Estradas"""
        cur.execute("SELECT id,ref_wayid from road_blocked where ref_userid=%s and ref_unwantedPoi is Null", (userid,))
        getreferencias = cur.fetchall()
        if len(getreferencias) is not 0:
            auxroadblock=[]
            for x in getreferencias:
                auxdic = []
                auxdic.append(x[0])
                #para actualizar os custos das ruas bloqueadas!
                cur.execute(sql.SQL("UPDATE {} SET km=1000 WHERE id = %s").format(sql.Identifier(table)),[x[1]])
                #cur.execute("UPDATE "+table+" SET km=1000 WHERE id="+str(x[1]))
                conn.commit()
                #listaDeEstradasBloqueadas.append(x[1])
                cur.execute("SELECT st_asgeojson(geom_way) AS geojson FROM rede_viaria_bv WHERE id=%s", (x[1],))
                listageoms = cur.fetchall()
                geosjon = self.createGeoJSON(listageoms, 0, x[0])
                auxdic.append(geosjon)
                auxroadblock.append(auxdic)
            outputData.append(auxroadblock)
        else:
            print("entrou0")
        cur.close()
        conn.close()
        return outputData

    # ---------------------------------------------------
    # Função de Custo!
    def loadtomemory(self,field):
        """
        Para adicionar em memoria os dados retirados do ficheiro configuracao.ini
        :param field: o nome do campo
        :return: um dicionario com a key e o valor correspondente
        """
        dicAux = {}
        Config = configparser.ConfigParser()
        Config.read("configuracao.ini")
        values = Config.options(field)
        for val in values:
            dicAux[val] = Config.get(field, val)
        return dicAux

    #done!
    def checkDatabase(self,id):
        """
        This method will gather the preferences of the user for the cost function.
        :param id: Identification number of the user
        :return: JSON object with the data gather from the database
        """
        userID = id
        data = {}
        roadMultiplier = {}
        cover = {}
        incli = {}
        security = {}
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return make_response(jsonify({"Error": "Não é possivel conectar a base de dados."}), 500)
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM utilizador WHERE id=%s", (userID,))
        for row in cur:
            roadMultiplier['tarmac'] = row['tarmac']
            roadMultiplier['dirt'] = row['dirt']
            roadMultiplier['cicleway'] = row['cicleway']
            roadMultiplier['woodenway_metalway'] = row['woodenway_metalway']
            roadMultiplier['portugueswalkway_concrete'] = row['portugueswalkway_concrete']
            incli['stairs'] = row['stairs']
            incli['helpmovement'] = row['helpmovement']
            cover['coverage_rainprotected'] = row['coverage_rainprotected']
            cover['coverage_shape'] = row['coverage_shape']
            security['allowcars'] = row['allowcars']
            security['allowbikes'] = row['allowbikes']
        cur.close()
        conn.close()
        data["roadMultiplier"]=roadMultiplier
        data["cover"]=cover
        data["incli"]=incli
        data["security"]=security
        return make_response(jsonify(data), 200)
    #done!
    def addDataDatabese(self, id, Calcadaportuguesa_Cimento, Alcatrao, Pistabicicleta, Terra, Passadicomadeira_metal, escadas, ajudamovimento, coverageshape_cover, coveragerainprotected_cover,allowcars_security,allowbikes_security):
        """
        Update the information in the database with the new values.
        :param id: Identification number of the user
        :param Calcadaportuguesa_Cimento: Value of preference.
        :param Alcatrao: Value of preference.
        :param Pistabicicleta: Value of preference.
        :param Terra: Value of preference.
        :param Passadicomadeira_metal: Value of preference.
        :param escadas: If the stairs are relevant.
        :param ajudamovimento: If the helpers are relevant.
        :param coverageshape_cover:  If the cover from the sun is relevant.
        :param coveragerainprotected_cover:  If the from the rain is relevant.
        :param allowcars_security: If it allow cars in the road
        :param allowbikes_security: If it allow bicycles in the road
        :return:
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(
                self.host) + " password=" + str(self.password) + "")
            cur = conn.cursor()
        except:
            print("I am unable to connect to the database")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
            sys.exit(0)
        cur.execute("UPDATE utilizador SET portugueswalkway_concrete = %s, tarmac = %s, cicleway = %s, dirt = %s, woodenway_metalway = %s, coverage_shape = %s, coverage_rainprotected = %s, allowcars = %s, allowbikes = %s, helpmovement = %s, stairs = %s WHERE id=%s", (Calcadaportuguesa_Cimento, Alcatrao, Pistabicicleta, Terra, Passadicomadeira_metal, coverageshape_cover, coveragerainprotected_cover, allowcars_security, allowbikes_security, ajudamovimento, escadas, id))
        conn.commit()
        cur.close()
        conn.close()
        tabela = 'table_cost_'+str(id)
        self.runCostfuncton(id,tabela)
        return jsonify({'success': True})

    def runCostfuncton(self,id,tabela):
        """
        Update the
        :param id:
        :param tabela:
        :return:
        """
        userid = id
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
            cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        except:
            print("I am unable to connect to the database")
            sys.exit(0)
        # reniciar a table table_cost_"id" sempre que se submeter novas preferencias.
        cur.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(tabela)))
        cur.execute(sql.SQL("SELECT * INTO {} FROM rede_viaria_bv").format(sql.Identifier(tabela)))
        conn.commit()
        # ---- AUTOMATICO ----
        self.sidewalkWidthCost(conn, cur, tabela) #Done
        self.roadStatusCost(conn, cur, tabela) #Done
        self.wifiCost(conn, cur, tabela) #Done
        # --------------------
        # ---- INPUT DO UTILIZADOR ----
        self.typeOfRoadCost(conn, cur, userid, tabela) #Done
        self.coverCost(conn,cur, userid, tabela) #Done
        self.pathInclinationCost(conn, cur, userid, tabela) #Done
        self.securityCost(conn, cur, userid, tabela) #Done
        # -----------------------------
        #print("----------------------------")
        cur.close()
        conn.close()

    # Funciona
    def typeOfRoadCost(self, conn, cur, userid, tabela):
        """
        Method that updates de cost using the information in roadMultiplier
        :param input: order of preference.
        :return:
        """
        cur.execute("SELECT tarmac, dirt, cicleway, woodenway_metalway, portugueswalkway_concrete FROM utilizador where id=%s", (userid,))
        for row in cur:
            teste = dict(row)
        sorted_by_value = sorted(teste.items(), key=lambda kv: kv[1])
        for key, value in sorted_by_value:
            print("key:  " + str(key) + " - Value: " + str(value))
            multiplicador = self.roadMultiplier[str(value)]
            print(multiplicador)
            listaDeCodigoEstrada = str(self.roadValues[key]).replace("[","").replace("]","")
            print(listaDeCodigoEstrada)
            query = """UPDATE """+tabela+""" SET km=(km*"""+str(multiplicador)+""") WHERE clazz in ("""+listaDeCodigoEstrada+""")"""
            cur.execute(query)
            conn.commit()

    # Funciona
    def coverCost(self, conn, cur, userid, tabela):
        #TODO: Acrescentar nas tabelas as colunas "protecRain (bool) e shade (bool)
        cur.execute("SELECT coverage_shape, coverage_rainprotected FROM utilizador where id=%s", (userid,))
        for result in cur:
            dictAux = dict(result)
        if dictAux['coverage_rainprotected']:
            query = """UPDATE """ + tabela + """ SET km=(km/""" + str(self.cover['coverage_rainprotected']) + """) WHERE protecrain = TRUE"""
            cur.execute(query)
            conn.commit()
        if dictAux['coverage_shape']:
            query = """UPDATE """ + tabela + """ SET km=(km/""" + str(self.cover['coverage_shape']) + """) WHERE shade = TRUE"""
            cur.execute(query)
            conn.commit()

    # Funciona
    def pathInclinationCost(self, conn, cur, userid, tabela):
        cur.execute("SELECT stairs, helpmovement FROM utilizador where id=" + str(userid))
        for result in cur:
            dictAux = dict(result)
        if dictAux['stairs']:
            query = """UPDATE """ + tabela + """ SET km=(km/""" + str(self.pathInclination['stairs']) + """) WHERE stairs = TRUE"""
            cur.execute(query)
            conn.commit()
        if dictAux['helpmovement']:
            query = """UPDATE """ + tabela + """ SET km=(km/""" + str(self.pathInclination['helpmovement']) + """) WHERE helpmovement = TRUE"""
            cur.execute(query)
            conn.commit()

    # Funciona
    def sidewalkWidthCost(self, conn, cur, tabela):
        cur.execute("SELECT id, largura_passeio FROM "+tabela)
        resultado = cur.fetchall()
        for x in resultado:
            id = x["id"]
            largura = x["largura_passeio"]
            if largura > float(self.sidewalkWidth['max']) or largura < float(self.sidewalkWidth['min']):
                query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.sidewalkWidth['valor']) + """) WHERE id = """+str(id)+""""""
                cur.execute(query)
                conn.commit()

    # Funciona
    def roadStatusCost(self, conn, cur, tabela):
        #Piso molhado ou seco
        chuvaStatus = ['light rain', 'moderate rain', 'heavy intensity rain', 'very heavy rain', 'extreme rain', 'freezing rain', 'light intensity shower rain','shower rain','heavy intensity shower rain','ragged shower rain']
        r = requests.get('http://api.openweathermap.org/data/2.5/forecast/daily?id=2743292&mode=json&units=metric&APPID=e844b4893b2537f18c9c61446fea2da0')
        dict = r.json()
        descrição = dict['list'][0]['weather'][0]['description']
        if descrição in chuvaStatus:
            pisoMolhado = self.roadStatus["wetfloor"]
            query = """UPDATE """ + tabela + """ SET km=(km/""" + str(pisoMolhado) + """) WHERE protecRain = True"""
            cur.execute(query)
            conn.commit()
        else:
            print("Dry weather")
        #inundation
        query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.roadStatus["inundation"]) + """) WHERE inundation = True"""
        cur.execute(query)
        conn.commit()
        # inundation
        query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.roadStatus["nomaintance"]) + """) WHERE maintenance = True"""
        cur.execute(query)
        conn.commit()
        # inundation
        query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.roadStatus["unlevelingpath"]) + """) WHERE uneven = True"""
        cur.execute(query)
        conn.commit()
        # inundation
        query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.roadStatus["roadmaintenance"]) + """) WHERE construction = True"""
        cur.execute(query)
        conn.commit()

    # Funciona
    def wifiCost(self, conn, cur, tabela):
        query = """UPDATE """ + tabela + """ SET km=(km/""" + str(self.wifi['connection']) + """) WHERE wifi = True"""
        cur.execute(query)
        conn.commit()

    # Funciona
    def securityCost(self, conn, cur, userid, tabela):
        # 1: Só carro
        # 2: (bike ∩ carro [nao pes])
        # 3: (bike ∩ pes[nao carro])
        # 4: (bike ∩ pes ∩ carro])
        onlyCars = []
        bikeCars = []
        bikeFoot = []
        bikeFootCars = []
        for i in self.roadUsers["car"]:
            if i in self.roadUsers["bike"] and i in self.roadUsers["foot"]:
                bikeFootCars.append(i)
            elif i in self.roadUsers["bike"]:
                bikeCars.append(i)
            else:
                onlyCars.append(i)
        for i in self.roadUsers["bike"]:
            if i not in bikeFootCars:
                if i in self.roadUsers["foot"]:
                    if i not in bikeFoot:
                        bikeFoot.append(i)
        cur.execute("SELECT allowcars, allowbikes FROM utilizador where id=%s", (userid,))
        for result in cur:
            dictAux = dict(result)
        if dictAux['allowcars'] and dictAux['allowbikes']:
            #Só carro
            query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.security['1']) + """) WHERE clazz in ("""+str(onlyCars).replace("[","").replace("]","")+""")"""
            cur.execute(query)
            conn.commit()
            #bike ∩ carros
            query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.security['2']) + """) WHERE clazz in (""" + str(bikeCars).replace("[","").replace("]","") + """)"""
            cur.execute(query)
            conn.commit()
            #bike ∩ a pe
            query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.security['3']) + """) WHERE clazz in (""" + str(bikeFoot).replace("[","").replace("]","") + """)"""
            cur.execute(query)
            conn.commit()
            #bike ∩ a pe ∩ carros
            query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.security['4']) + """) WHERE clazz in (""" + str(bikeFootCars).replace("[","").replace("]","") + """)"""
            cur.execute(query)
            conn.commit()
        elif dictAux['allowbikes'] and dictAux['allowcars'] == False:
            #bike ∩ carros
            query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.security['2']) + """) WHERE clazz in (""" + str(bikeCars).replace("[", "").replace("]", "") + """)"""
            cur.execute(query)
            conn.commit()
            #bike ∩ a pe
            query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.security['3']) + """) WHERE clazz in (""" + str(bikeFoot).replace("[", "").replace("]", "") + """)"""
            cur.execute(query)
            conn.commit()
            #bike ∩ a pe ∩ carros)
            query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.security['4']) + """) WHERE clazz in (""" + str(bikeFootCars).replace("[", "").replace("]", "") + """)"""
            cur.execute(query)
            conn.commit()
        elif dictAux['allowcars'] and dictAux['allowbikes'] == False:
            print("checked carros e unchecked bikes")
            print(onlyCars)
            # Só carro
            query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.security['1']) + """) WHERE clazz in (""" + str(onlyCars).replace("[", "").replace("]", "") + """)"""
            cur.execute(query)
            conn.commit()
            # bike ∩ carros
            query = """UPDATE """ + tabela + """ SET km=(km*""" + str(self.security['2']) + """) WHERE clazz in (""" + str(bikeCars).replace("[", "").replace("]",                                                                                       "") + """)"""
            cur.execute(query)
            conn.commit()