import psycopg2
import re
from flask import jsonify, make_response

class PontosInterese():
    host = ''
    user = ''
    dbname = ''
    password = ''

    def __init__(self, host, user, dbname, password):
        self.host = host
        self.user = user
        self.dbname = dbname
        self.password = password

    #Done!
    def add(self, input):
        """
        Method used to insert into the database multiple points of interest by reading a
        CSV file with the following fields:
            => nome: POI name,
            => tipo: Type of POI (cafe for example),
            => latitude: The POI latitude coordinate,
            => longitude: The POI longitude coordinate.
        Also generate the geographic value of the vertex closest to the specified coordinates.
        :param input: JSON file with the information of points of interest.
        :return: Success message
        """
        try:
            conn = psycopg2.connect(
                "dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        response = input
        for x in response:
            userid = x.get('userid')
            if userid is None:
                userid = 0
            nome = x.get('nome')
            tipo = x.get('tipo')
            latitude = x.get('latitude')
            longitude = x.get('longitude')
            selecionado = True
            pointCoord = "POINT(" + longitude + " " + latitude + ")"
            cur.execute("SELECT geom_vertex FROM rede_viaria_bv_vertex ORDER BY geom_vertex <-> ST_GeometryFromText(%s,4326) LIMIT 1;", (str(pointCoord),))
            row = str(cur.fetchone())
            geom = re.search('\((.*),\)', row)
            cur.execute("SELECT ST_AsText(geom_vertex) FROM rede_viaria_bv_vertex where geom_vertex="+ str(geom.group(1)))
            row2 = str(cur.fetchone())
            closestCoord = re.search('\(\'POINT\((.*)\)\',\)', row2)
            closedVertexCoord = closestCoord.group(1).split(" ")
            #cur.execute("INSERT INTO pois (nome, tipo, latitude, longitude, cv_lat, cv_long, selecionado, cv_geom) VALUES ('" + nome + "','" + tipo + "'," + latitude + "," + longitude + "," +closedVertexCoord[1] + "," + closedVertexCoord[0] + "," + str(selecionado) + "," + geom.group(1) + ")")
            geom = geom.group(1).replace("'","")
            cur.execute("INSERT INTO pois (userid, nome, tipo, latitude, longitude, cv_lat, cv_long, selecionado, cv_geom) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);", (str(userid),nome,tipo,latitude,longitude,closedVertexCoord[1],closedVertexCoord[0],str(selecionado),geom))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success':True})
    #Done!
    def load(self,userid):
        """
        This method will acquire all POI of a certain type.
        :param userid: User identifier
        :return: Data acquired in JSON format
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        cur.execute("SELECT * FROM pois WHERE userid = 0 or userid =%s", (userid,))  # WHERE tipo=cafe")
        columns = ('id', 'userid', 'nome', 'tipo', 'latitude', 'longitude', 'cv_lat', 'cv_long', 'selecionado', 'geom')
        results = []
        for row in cur.fetchall():
            results.append(dict(zip(columns, row)))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(results)
    #Done!
    def select(self,userid,long,lat,selec):
        """
        Method to select the points of interest when changing the selected column in the database.
        :param userid: User identification number
        :param long: POI longitude value
        :param lat: POI latitude value
        :param selec: boolean values of true or false to check id the pois is selected or not
        :return: Success message
        """
        try:
            conn = psycopg2.connect(
                "dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        if selec == "false":
            cur.execute("UPDATE pois SET selecionado=True where latitude='"+str(lat)+"' and longitude='"+str(long)+"'")
        else:
            cur.execute("UPDATE pois SET selecionado=False where latitude='"+str(lat)+"' and longitude='"+str(long)+"'")
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})

    def geomToCoord(self, geom):
        """
        Method that will convert the geom of the to the coordinates.
        :param geom: geom that contains the coded coordinates
        return: A STRING with coordinates and important point information such as geom, id, and whether it has already
        been selected
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        print(geom)
        cur.execute("SELECT ST_AsText('" + geom + "');")
        row1 = str(cur.fetchone())
        result1 = re.search('\(\'POINT\((.*)\)\',\)', row1)
        conn.commit()
        cur.close()
        conn.close()
        return result1.group(1)

    #Done!
    def removePOI(self,long,lat,option,userid):
        """
        This method will delete from the database all custom pois from the current user or only the selected poi.
        :param long: Longitude value from the selected poi.
        :param lat: Latitude value from the selected poi.
        :param option: Option to determinate if the deletion is global or singular
        :param userid: User identification
        :return: Success message
        """
        try:
            conn = psycopg2.connect("dbname=" + str(self.dbname) + " user=" + str(self.user) + " host=" + str(self.host) + " password=" + str(self.password) + "")
        except:
            print("Não é possivel conectar a base de dados.")
            return jsonify({"Error": "Não é possivel conectar a base de dados."})
        cur = conn.cursor()
        if option is '1':
            cur.execute("DELETE FROM pois WHERE tipo='custom' and userid=%s", (userid,))
            conn.commit()
        elif option is '0':
            cur.execute("DELETE FROM pois where latitude='"+str(lat)+"' and longitude='"+str(long)+"' and userid="+str(userid))
            conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})