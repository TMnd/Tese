from psycopg2 import sql
import psycopg2
import sys
import numpy as np
import math

try:
    conn = psycopg2.connect("dbname=apiTesteAveiro user=amaral host=aal.ieeta.pt password=Pokemon123")
except:
    print("I am unable to connect to the database")
    sys.exit(0)
cur = conn.cursor()

def dijkstra(pontoA,pontoB,tabela):
    #TODO: Alterar a query para que só entre como padrão os pontos A e B.
    lista = []
    lista.append(pontoA)
    lista.append(pontoB)
    cur.execute("SELECT sum(cost) FROM pgr_deaparabkmsolo_nopenalty(%s,%s)", (tabela, lista,))
    rows = cur.fetchone()
    return rows[0]

def nuvemPontos(raio, ponto, tabela):
    aux=[]
    cur.execute("SELECT geom_distmeters from rede_viaria_bv_vertex where id = %s", (ponto,))
    geom3857 = cur.fetchone()
    cur.execute("SELECT id FROM rede_viaria_bv_vertex as t where ST_DWithin(%s,t.geom_distmeters,%s)",
                (geom3857[0], float(raio)))
    nuvem = cur.fetchall()
    for x in nuvem:
        # vertices especiais com 2 ou mais vias de acesso
    #    cur.execute(sql.SQL("SELECT id,km FROM {} where source=%s or target=%s").format(sql.Identifier(tabela)),(x[0], x[0],))
    #    resultAuditWayId = cur.fetchall()
    #    if len(resultAuditWayId) >= 2:
    #        contatudorDeEstradasValidas = len(resultAuditWayId)
    #        for w in resultAuditWayId:
    #            if w[1] == 1000:
    #                contatudorDeEstradasValidas -= 1
    #        if contatudorDeEstradasValidas >= 3:
    #            aux.append(x[0])
        aux.append(x[0])
    return aux

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def AtoB(tsp,option):
    teste = []
    #resultadofinal = {}
    for x in tsp:
        teste.append(x)
    tabela = 'tablep_15'
    if option is 1:
        cur.execute("SELECT st_asgeojson(geom) AS geojson FROM pgr_deaparabkmsolo_nopenalty(%s,%s)", (str(tabela),teste,))
        rows = cur.fetchall()
    else:
        cur.execute("SELECT st_asgeojson(geom) AS geojson FROM pgr_deaparabkm2_5(%s,%s)",
                    (str(tabela), teste,))
        rows = cur.fetchall()
        conn.commit()
        cur.execute("DROP table tablep_15")
        conn.commit()
        cur.execute("SELECT * INTO tablep_15 FROM rede_viaria_bv")
        cur.execute("ALTER TABLE tablep_15 ADD PRIMARY KEY(id);")
        conn.commit()
    #for x in rows:
    #    print(x)
    geojson = createGeoJSON(rows,1,0)
    #self.tableRestore(userid)
    #resultadofinal["TypeRoute"]="MultiPoint"
    #resultadofinal["geojson"]=geojson
    return geojson

def createGeoJSON(rows,option,id2):
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
                props = (',' if len(props) > 0 else '') + '"' + str(key) + '":"' + escapeJsonString(val) + '"'
            if key == "id":
                id += ',"id":"' + escapeJsonString(val) + '"'
        rowOutput += props + '}'
        rowOutput += id
        rowOutput += '}'
        output += rowOutput
        cont += 1
    output = '{ "type": "FeatureCollection", "features": [ ' + output + ' ]}'
    return output

def escapeJsonString(value):  # list from www.json.org: (\b backspace, \f formfeed)
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

#com a distancia que falta cortada a metade
#Teste 1: Pi: 3543 - 36984 | com 4 pois | distancia percorrida = 1.8490527 -
#Teste 2: Pi: 3464 - 37731 | com 5 pois | distancia percorrida = 1.7832112 -
#Teste 3: Pi: 3505 - 3505 | com 4 pois | distancia percorrida = 1.4415375 -
#com a distancia que falta no total
##Teste 4: Pi: 58298 - 58298 | com 3 pois | distancia percorrida = 1.8412024
#-------- quando o tamanho da lista de pois é 0
#Teste 5: Pi: 3464 - 37731 | SEM pois | distancia percorrida = 1.5060772 -
##Teste 7: Pi: 3486 - 3486 | SEM pois | distancia percorrida = 2.4962384  -

lpois = []
pontoPartida = 3464
pontoFinal = 37731

distanciaFaltaPercorrer = 1
treshold = 0.5 #valor de margem de manobra
listaViagemFinal = []
listaVisita = [] #guardar o resultado da sequencia do tsp

distanciaFaltaPercorrer_treshold = distanciaFaltaPercorrer + treshold

listaViagemFinal.append(pontoPartida)

# LISTA DE POIS selecionados
cur.execute("SELECT cv_geom from pois where selecionado=true")
pois = cur.fetchall()
print(pois)
for poisInfo in pois:
    cur.execute("SELECT id from rede_viaria_bv_vertex where geom_vertex = %s", (poisInfo[0],))
    lpois_id = cur.fetchone()
    lpois.append(lpois_id[0])

print(len(lpois))

if len(lpois)>1:
    # TSP dos pois
    inputList = str(lpois).replace("[", "").replace("]", "")
    tsp_query = "SELECT * from pgr_eucledianTSP( " \
                "$$ " \
                "SELECT id, st_X(geom_vertex) AS x, st_Y(geom_vertex) AS y FROM rede_viaria_bv_vertex " \
                "WHERE id IN (" + inputList + ") " \
                "$$, " \
                "start_id := " + str(pontoPartida) + " , " \
                "tries_per_temperature := 0, " \
                "randomize := false " \
                ");"

    cur.execute(tsp_query)
    tsp_query_result = cur.fetchall()
    cont1 = 0
    print(tsp_query_result)
    for i in tsp_query_result:
        if cont1 < len(tsp_query_result) - 1:
            listaVisita.append(i[1])
        cont1 += 1

    print(listaVisita)

    #Dijkstra
    for i in range(0,len(listaVisita)):
        valor_dijkstra_entrepontos = dijkstra(listaVisita[i],listaVisita[i-1],'tablep_15')
        valor_dijkstra_ultimoPonto_pontofinal = dijkstra(listaVisita[i],pontoFinal,'tablep_15')
        if distanciaFaltaPercorrer_treshold > valor_dijkstra_entrepontos + valor_dijkstra_ultimoPonto_pontofinal:
            listaViagemFinal.append(listaVisita[i])
            distanciaFaltaPercorrer_treshold -= valor_dijkstra_entrepontos

    ultimoVertice = listaViagemFinal[len(listaViagemFinal)-1]
else:
    print("ultimo ponto antes do pongoFinal é o ponto final")
    ultimoVertice = pontoPartida

print("Lista de visita:")
print(listaViagemFinal)

raioDePesquisa = (distanciaFaltaPercorrer_treshold * 1000)/2
#raioDePesquisa = distanciaFaltaPercorrer_treshold * 1000
print(raioDePesquisa)
print("Ultimo vertice antes do pontoFinal")
print(ultimoVertice)
lA = nuvemPontos(raioDePesquisa,ultimoVertice,'tablep_15')
print(lA)
lB = nuvemPontos(raioDePesquisa,pontoFinal,'tablep_15')
print(lB)
lFinal = intersection(lA,lB)

print("Lista intersecção:")
print(lFinal)

dicionario = {}
for l in lFinal:
    PontoFinalPerpectiva = dijkstra(listaViagemFinal[len(listaViagemFinal)-1], l, 'tablep_15')
    UltimoPontoPerpectiva = dijkstra(pontoFinal, l, 'tablep_15')
    if str(PontoFinalPerpectiva) != 'None' and str(UltimoPontoPerpectiva) != 'None':
        aux = float(PontoFinalPerpectiva) + float(UltimoPontoPerpectiva)
        dicionario[l]=aux

print("Dicionario para o pontos intermedios:")
print(dicionario)

print("distancia que falta percorrer: ")
print(distanciaFaltaPercorrer_treshold)
print("------------------")

dist=[]
k = list(dicionario.keys())
v = np.array(list(dicionario.values()))
dist = abs(v - distanciaFaltaPercorrer_treshold)
arg = np.argmin(dist)
answer = k[arg]

print(answer)
listaViagemFinal.append(answer)

listaViagemFinal.append(pontoFinal)

cur.execute("SELECT sum(cost) FROM pgr_deaparabkmsolo_nopenalty(%s,%s)", ('tablep_15', listaViagemFinal,))
rows2_5 = cur.fetchone()
print(rows2_5[0])

file = open("Testes_V2\\teste1.geojson", "w")
file.write(str(AtoB(listaViagemFinal,1)))
file.close()