import json
import psycopg2
import sys
import configparser
import psycopg2.extras
from pathlib import Path

class customcost():
    host = ''
    user = ''
    dbname = ''
    password = ''
    #variaveis do ficheiro ini
    roadMultiplier = {}
    cover = {}
    roadStatus = {}
    sidewalkWidth = {}
    pathInclination = {}
    #valores pre-definidos para calculo de preferencias de caminho
    #o utilizador pode nao querer usar um certo caminho mas a um caso extremo
    #poderá ser usado. O custo vai ser aumentado mas nao ao ponto de nao ser utilizado.
    roadValues={
        "tarmac": [41,21,22,31,31,42,63],
        "dirt": [51],
        "portugueswalkway_concrete": [72,62,92], #a calçada portuguesa e o chao de betao estao dentro destas categorias.
        "cicleway": [81,71],
        "woodenway_metalway": [91] #as pontes de meta e de passadiços de metal têm o mesmo valor.
    }
    roadUsers={
        "car": [21, 22, 31, 32, 41, 42, 43, 51, 63],
        "bike": [31, 32, 41, 42, 43, 51, 62, 63, 71, 72, 81],
        "foot": [63, 62, 71, 72, 91, 92, 81]
    }
    priorities={
        "51": "P1",
        "63": "P1",
        "62": "P1",
        "71": "P1",
        "72": "P1",
        "91": "P1",
        "92": "P1",
        "81": "P2",
        "41": "P2",
        "42": "P2",
        "43": "P2",
        "21": "P3",
        "22": "P3",
        "31": "P3",
        "32": "P3"
    }
    roadMultiplier={#exemplo com o valor 100
        "1": 1,     #100
        "2": 1.1,   #110
        "3": 1.2,   #120
        "4": 1.3,   #130
        "5": 1.4    #140
    }

    def __init__(self, host, user, dbname, password):
        self.host = host
        self.user = user
        self.dbname = dbname
        self.password = password
        self.roadMultiplier = self.loadtomemory("roadMultiplier")
        self.cover = self.loadtomemory("cover")
        self.roadStatus = self.loadtomemory("roadStatus")
        self.sidewalkWidth = self.loadtomemory("sidewalkWidth")
        self.pathInclination = self.loadtomemory("pathInclination")

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

    #Utilizado
    def checkDatabase(self,id):
        userID = id
        data = {}
        roadMultiplier = {}
        cover = {}
        incli = {}
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("I am unable to connect to the database")
            sys.exit(0)
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM utilizador WHERE id="+userID)
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
        cur.close()
        conn.close()
        data["roadMultiplier"]=roadMultiplier
        data["cover"]=cover
        data["incli"]=incli
        return data

    def addDataDatabese(self,id,Calcadaportuguesa_Cimento,Alcatrao,Pistabicicleta,Terra,Passadicomadeira_metal,coverageshape_cover,coveragerainprotected_cover):
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
            cur = conn.cursor()
        except:
            print("I am unable to connect to the database")
            sys.exit(0)
        cur.execute("UPDATE utilizador SET portugueswalkway_concrete = %s, tarmac = %s, cicleway = %s, dirt = %s, woodenway_metalway = %s, coverage_shape = %s, coverage_rainprotected = %s WHERE id=%s",(Calcadaportuguesa_Cimento,Alcatrao,Pistabicicleta,Terra,Passadicomadeira_metal,coverageshape_cover,coveragerainprotected_cover,id))
        conn.commit()
        cur.close()
        conn.close()
        return "teste"

    def runCostfuncton(self,id):
        userid = id
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
            cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        except:
            print("I am unable to connect to the database")
            sys.exit(0)
        print(self.roadMultiplier)
        self.typeOfRoad(conn, cur, userid)
        print("----------------------------")
        print(self.cover)
        print(self.roadStatus)
        print(self.sidewalkWidth)
        print(self.pathInclination)
        cur.close()
        conn.close()

    #    self.loadValuesFromIni()
        #my_file = Path("./userData/user_"+str(id)+".json")
        #if my_file.is_file():
            #with open('./userData/user_'+str(id)+'.json') as f:
                #data = json.load(f)
    #
                #self.tamanhoPasseio(conn,cur,data["sidewalk_width"],id) #todo
                #self.seguranca(conn,cur,data["roadUserPreferences"],id) #todo
                #self.declive(conn,cur,data["declivity"])   #TODO: Determinar os valores maximos e minimos com a patricia e a prof anabela
                #self.ajudamovimento(conn,cur,data["helpMovement"]) #TODO: ALTERAR O INIT PARA INCLUIR ESTE CAMPO NA TABELA
                #self.estadoEstrada(conn,cur) #TODO: biblioteca da meteorologia
                #self.cobertura(conn,cur,data[]) #TODO: ALTERAR O INIT PARA INCLUIR ESTE CAMPO NA TABELA
                #self.tipoEstrada(conn,cur,data[]) #TODO: Determinar se é preciso ou não
    #    cur.close()
    #    conn.close()

    def typeOfRoad(self, conn, cur, userid):
        """
        Method that updates de cost using the information in roadMultiplier
        :param input: order of preference.
        :return:
        """
        print("tipo de estradas - ordem")
        tabela = "tablep_" + userid
        cur.execute("SELECT tarmac, dirt, cicleway, woodenway_metalway, portugueswalkway_concrete FROM utilizador where id="+userid)
        for row in cur:
            teste = dict(row)
        sorted_by_value = sorted(teste.items(), key=lambda kv: kv[1])
        for key, value in sorted_by_value:
            multiplicador = self.roadMultiplier[str(value)]
            listaDeCodigoEstrada = str(self.roadValues[key]).replace("[","").replace("]","")
            query = """UPDATE """+tabela+""" SET km=(km*"""+str(multiplicador)+""") WHERE clazz in ("""+listaDeCodigoEstrada+""")"""
            cur.execute(query)
            conn.commit()
        #"tarmac": [41, 21, 22, 31, 31, 42, 63],
        #"dirt": [51],
        #"portuguesWalkway_Concrete": [72, 62,92],
        #"cicleway": [81, 71],
        #"woodenWay_metalWay": [91]
        #for x in order:
            #print("tipo: " + x + " -- " + str(input.get(x)) + " multiplier =" + str(self.roadMultiplier.get(input.get(x))))
            # cur.execute("UPDATE %s SET km=(km*%s)", (tabela, str(self.roadMultiplier.get(input.get(x))),)) #é preciso testar
            # conn.commit()
