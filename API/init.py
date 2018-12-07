import os
import sys
import psycopg2
import re
import math
from gdal_interfaces import GDALTileInterface

class init():
    conn = ''
    cur = ''
    host = ''
    user = ''
    dbname = ''
    password = ''
    openElevation = ''

    def __init__(self, host, user, dbname, password):
        #Open-Elevation
        self.openElevation = GDALTileInterface('data/', 'data/summary.json') #por agora os parametros vai ser os mesmos
        self.openElevation.create_summary_json()
        #resto do processo de inicialização
        self.host = host
        self.user = user
        self.dbname = dbname
        self.password = password
        try:
            self.conn = psycopg2.connect("dbname=" + self.dbname + " user=" + self.user + " host=" + self.host + " password=" + self.password + "")
            self.cur = self.conn.cursor()
        except Exception as e:
            print(e)
            print("I am unable to connect to the database")
            sys.exit(0)

    def init(self):
        """
        Function that checks if there is all the conditions to initialize the API.
        Includes:
            - Verification of the required database extensions.
            - The raster check with portugal heights.
            - The verification of the existence of the tables of pois, vertices and edges.
        :return:
        """
        # Verificar se a base de dados tem as extensões postgis e pgrounting
        self.cur.execute("SELECT * FROM pg_extension where extname='postgis';")
        checkPostgis = self.cur.fetchall()
        if len(checkPostgis) is 0:
            print("The database need the extention Postgis, https://postgis.net/install/")
            sys.exit(0)
        self.cur.execute("SELECT * FROM pg_extension where extname='pgrouting';")
        checkPgRouting = self.cur.fetchall()
        if len(checkPgRouting) is 0:
            print("The database need the extention pgRouting, https://pgrouting.org")
            sys.exit(0)
        #Open-elevation
        numberRasterFiles = [fn for fn in os.listdir('./data/') if fn.endswith('.tif')]
        if len(numberRasterFiles) == 0:
            print("Raster was not found.")
            sys.exit(0)
        elif len(numberRasterFiles) == 1:
            print("Processing raster file.")
            os.system("./scripts/create-tiles.sh ./data/mdt_aster_pt_D73_GeoTIFF.tif 10 10") #dividir o ficheiro em 5 por 5
        else:
            print("Raster file was found and processed")
        #Verificar se as tabelas rede_viaria_bv e rede_viaria_bv_vertex existem
        self.checkTable('rede_viaria_bv_vertex', 1, 4)
        self.checkTable('rede_viaria_bv', 2, 4)
        #Criar tabela dos Pois
        self.checkTable('pois', 2, 0)
        #Criar a função atob
        if os.name == 'posix':  # para linux
            os.system("PGPASSWORD=" + str(self.password) + " psql -f ./sql/atob_km_tsp.sql -h " + str(self.host) + " -U " + str(self.user) + " " + str(self.dbname) + " > /dev/null")
            os.system("PGPASSWORD=" + str(self.password) + " psql -f ./sql/solo_km_tsp.sql -h " + str(self.host) + " -U " + str(self.user) + " " + str(self.dbname) + " > /dev/null")
            #os.system("PGPASSWORD=" + str(self.password) + " psql -f ./sql/solo_km_tsp_nopenalty.sql -h " + str(self.host) + " -U " + str(self.user) + " " + str(self.dbname) + " > /dev/null")
        self.checkTable('utilizador', 2, 1)
        self.checkTable('unwanted_poi', 2, 3)
        self.checkTable('road_blocked', 2, 2)

    def checkTable(self, tablename, option, pois):
        """
        To check if the necessary tables exist, if they do not exist this method will create them.
        :param tablename: Table name.
        :param option: To be used as a parameter for the executeCMG function that is invoked
        :param pois: To separate the check between the POIS table and the graph tables.
        :return:
        """
        #TODO: verificar se o ficheiro existe
        #self.cur.execute("SELECT 1 FROM pg_class where relname='" + tablename + "';")
        # rede_viaria_bv_vertex
        self.cur.execute("SELECT 1 FROM pg_class where relname=%s", (tablename,))
        rows = self.cur.fetchall()
        if len(rows) is 0:
            print("A criar a tabela " + tablename)
            if pois is 0:
                query = """
                                   CREATE TABLE pois (
                                       id SERIAL PRIMARY KEY,
                                       userid INTEGER,
                                       nome varchar(80),
                                       tipo varchar(80),
                                       latitude varchar(80) NOT NULL,
                                       longitude varchar(80)NOT NULL,
                                       cv_lat varchar(80) NOT NULL,
                                       cv_long varchar(80) NOT NULL,
                                       selecionado boolean
                                   );
                                """
                self.cur.execute(query)
                self.conn.commit()
                self.cur.execute("SELECT AddGeometryColumn('pois','cv_geom',4326,'POINT',2);")
                self.conn.commit()
            elif pois is 1:
                query1 = """CREATE TABLE utilizador (
                                id SERIAL PRIMARY KEY,
                                username character varying(80),
                                portuguesWalkway_Concrete INTEGER,
                                tarmac INTEGER,
                                cicleway INTEGER,
                                dirt INTEGER,
                                woodenWay_metalWay INTEGER,
                                sidewalk_width INTEGER,
                                allowcars BOOLEAN,
                                allowbikes BOOLEAN,
                                helpMovement BOOLEAN,
                                stairs BOOLEAN,
                                declivity_up integer,
                                declivity_down integer,
                                coverage_shape BOOLEAN,
                                coverage_rainProtected BOOLEAN,
                                password_hash character varying(128)
                            );"""
                self.cur.execute(query1)
                self.conn.commit()
                #self.cur.execute("INSERT INTO utilizador(nome) VALUES ('nome teste')")
                #self.conn.commit()
            elif pois is 2:
                query2 = """
                                   CREATE TABLE road_blocked (
                                       id SERIAL PRIMARY KEY,
                                       ref_userID integer ,
                                       ref_wayID integer ,
                                       ref_unwantedPoi integer,
                                       FOREIGN KEY (ref_userID) REFERENCES utilizador(id),
                                       FOREIGN KEY (ref_wayID) REFERENCES rede_viaria_bv(id),
                                       FOREIGN KEY (ref_unwantedPoi) REFERENCES unwanted_poi(id)
                                   );
                                """
                self.cur.execute(query2)
                self.conn.commit()
            elif pois is 3:
                query3 = """
                                   CREATE TABLE unwanted_poi (
                                       id SERIAL PRIMARY KEY,
                                       ref_userID integer ,
                                       ref_pointID integer ,
                                       FOREIGN KEY (ref_userID) REFERENCES utilizador(id),
                                       FOREIGN KEY (ref_pointID) REFERENCES rede_viaria_bv_vertex(id)
                                   );
                                """
                self.cur.execute(query3)
                self.conn.commit()
            else:
                self.executeCMD('' + tablename + '.sql', option)
        else:
            print("A tabela " + tablename + " ja existe.")

    def executeCMD(self, sqlFile, option):
        """
        Function to execute the sql files that are in the sql folder of the API.
        :param sqlFile: The name of the sql file to execute.
        :param option: To separate whether the file is for the edges and vertices.
        :return:
        """
        fo = open('./sql/' + sqlFile, 'r')
        sqlFile = fo.read()
        sqlCommands = sqlFile.split(';')
        fn = open('./sql/tmp.sql', 'w')
        for lines in sqlCommands:
            fn.write(lines + ";")
        if option == 1:
            print("Campos extra para a rede_viaria_bv_vertex")
            fn.write('ALTER TABLE rede_viaria_bv_vertex ADD COLUMN altura INTEGER;')
            fn.write('ALTER TABLE rede_viaria_bv_vertex ADD COLUMN geom_distMeters geometry(Point,3857);')
            fn.write('UPDATE rede_viaria_bv_vertex SET geom_distmeters = ST_Transform(geom_vertex,3857);')
        else:
            print("Campos extra para a rede_viaria_bv")
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN largura_passeio INTEGER;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN inclinacao INTEGER;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN protecrain BOOLEAN;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN shade BOOLEAN;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN stairs BOOLEAN;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN helpmovement BOOLEAN;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN inundation BOOLEAN;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN maintenance BOOLEAN;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN uneven BOOLEAN;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN construction BOOLEAN;')
            fn.write('ALTER TABLE rede_viaria_bv ADD COLUMN wifi BOOLEAN;')
        fo.close()
        fn.close()
        if os.name == 'posix':  # para linux
            os.system("PGPASSWORD=" + str(self.password) + " psql -f ./sql/tmp.sql -h " + str(self.host) + " -U " + str(self.user) + " " + str(self.dbname) + " > /dev/null")
        os.remove('./sql/tmp.sql')

    def dataPopulation(self):
        """
        This method has the functionality of entering the necessary data in the database.
        :return:
        """
        print("Filling the data:")
        # veririficar se existe alguma linha cuja altura nao é nula
        self.cur.execute("SELECT id, geom_vertex, altura FROM rede_viaria_bv_vertex where altura is null")
        rowsSemAltura = self.cur.fetchall()
        if len(rowsSemAltura) is not 0:
            print("+ Entering height data (may take a few minutes)")
            self.cur.execute("SELECT id, geom_vertex, altura FROM rede_viaria_bv_vertex order by id asc")
            rows = self.cur.fetchall()
            for pontos in rows:
                if pontos[2] != 'None':
                    #self.cur.execute("SELECT ST_AsText('" + pontos[1] + "');")
                    self.cur.execute("SELECT ST_AsText(%s);", (str(pontos[1]),))
                    row1 = str(self.cur.fetchone())
                    result1 = re.search('\(\'POINT\((.*)\)\',\)', row1)
                    aux = str(result1.groups(1)).replace("(", "").replace(")", "").replace(",", "").replace("'", "")
                    coordenadas = aux.split(" ")
                    r = self.get_elevation(float(coordenadas[1]),float(coordenadas[0]))
                    #r = self.get_elevation(40.321867,-7.612967) #serra da estrela radar - altura a espera 1993
                    altura = r['elevation']
                    #self.cur.execute("UPDATE rede_viaria_bv_vertex SET altura=" + str(altura) + " WHERE id=" + str(pontos[0]) + ";")
                    self.cur.execute("UPDATE rede_viaria_bv_vertex SET altura=%s WHERE id=%s;", (str(altura),str(pontos[0])))
                    self.conn.commit()
                    if pontos[0] % 1000 == 0:
                        print("Number of points inserted :" + str(pontos[0]))
        else:
            print("+ There is height data.")
        self.cur.execute("SELECT id,source,target,km FROM rede_viaria_bv where inclinacao is null")
        rowsInclinação = self.cur.fetchall()
        if len(rowsInclinação) is not 0:
            print("+ Entering slope (may take more few minutes)")
            for pontos in rowsInclinação:
                #self.cur.execute("SELECT altura FROM rede_viaria_bv_vertex WHERE id=" + str(pontos[1]))
                self.cur.execute("SELECT altura FROM rede_viaria_bv_vertex WHERE id=%s;", (str(pontos[1]),))
                source = self.cur.fetchone()
                #self.cur.execute("SELECT altura FROM rede_viaria_bv_vertex WHERE id=" + str(pontos[2]))
                self.cur.execute("SELECT altura FROM rede_viaria_bv_vertex WHERE id=%s", (str(pontos[2]),))
                target = self.cur.fetchone()
                if target[0] is not source[0]:
                    cO = target[0] - source[0]  # cateto oposto
                    cA = float(pontos[3] * 100)  # cateto adjacente, converter os km para metros pq as alturas encontram-se me metros
                    grau = math.degrees(math.atan(cO / cA))
                    #self.cur.execute("UPDATE rede_viaria_bv SET inclinacao=" + str(grau) + " WHERE id=" + str(pontos[0]) + ";")
                    self.cur.execute("UPDATE rede_viaria_bv SET inclinacao=%s WHERE id=%s;", (grau,str(pontos[0])))
                    self.conn.commit()
                else:
                    #self.cur.execute("UPDATE rede_viaria_bv SET inclinacao=0 WHERE id=" + str(pontos[0]) + ";")
                    self.cur.execute("UPDATE rede_viaria_bv SET inclinacao=0 WHERE id=%s;", (str(pontos[0]),))
                    self.conn.commit()
        else:
            print("+ There is slope.")
        #vou deixar esta parte ate ter algum dataset para preencher a largura do passeio.
        self.cur.execute("SELECT id,source,target,km FROM rede_viaria_bv where largura_passeio is null")
        rowsLargura = self.cur.fetchall()
        if len(rowsLargura) is not 0:
            print("+ Entering side walk width data (almost there)")
            #for pontos in rowsLargura:
            #largura do passeio
            #self.cur.execute("UPDATE rede_viaria_bv SET largura_passeio=%s WHERE id=%s;", (2, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET largura_passeio=2;")
            self.conn.commit()
            #proteger da chuva
            #self.cur.execute("UPDATE rede_viaria_bv SET protecrain=%s WHERE id=%s;", (False, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET protecrain=%s;", (False,))
            self.conn.commit()
            #proteger do sol
            #self.cur.execute("UPDATE rede_viaria_bv SET shade=%s WHERE id=%s;", (False, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET shade=%s;", (False,))
            self.conn.commit()
            #escadas
            #self.cur.execute("UPDATE rede_viaria_bv SET stairs=%s WHERE id=%s;", (False, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET stairs=%s;", (False,))
            self.conn.commit()
            #ajudas
            #self.cur.execute("UPDATE rede_viaria_bv SET helpmovement=%s WHERE id=%s;", (False, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET helpmovement=%s;", (False,))
            self.conn.commit()
            #inundação
            #self.cur.execute("UPDATE rede_viaria_bv SET inundation=%s WHERE id=%s;", (False, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET inundation=%s;", (False,))
            self.conn.commit()
            #manutenção
            #self.cur.execute("UPDATE rede_viaria_bv SET maintenance=%s WHERE id=%s;", (False, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET maintenance=%s;", (False,))
            self.conn.commit()
            #desnivelados
            #self.cur.execute("UPDATE rede_viaria_bv SET uneven=%s WHERE id=%s;", (False, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET uneven=%s;", (False,))
            self.conn.commit()
            #construção
            #self.cur.execute("UPDATE rede_viaria_bv SET construction=%s WHERE id=%s;", (False, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET construction=%s;", (False,))
            self.conn.commit()
            #wifi
            #self.cur.execute("UPDATE rede_viaria_bv SET wifi=%s WHERE id=%s;", (False, str(pontos[0])))
            self.cur.execute("UPDATE rede_viaria_bv SET wifi=%s;", (False,))
            self.conn.commit()
        else:
            print("+ There is walking width data.")
        #ultimo acesso ao objecto
        self.cur.close()
        self.conn.close()

    def get_elevation(self, lat, lng):
            """
            Method taken from the initial Open-Elevations method
            Get the elevation at point (lat,lng) using the currently opened interface
            :param lat:
            :param lng:
            :return: the information in json format
            """
            try:
                elevation = self.openElevation.lookup(lat, lng)
            except:
                return {
                    'latitude': lat,
                    'longitude': lng,
                    'error': 'No such coordinate (%s, %s)' % (lat, lng)
                }

            return {
                'latitude': lat,
                'longitude': lng,
                'elevation': elevation
            }