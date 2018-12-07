from flask import Flask, request, jsonify, render_template, abort, g, url_for, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from init import init
from POIS import PontosInterese
from mapInteration import mapInteration
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
import sys, os
import psycopg2

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'ola'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+sys.argv[2]+':'+sys.argv[4]+'@'+sys.argv[3]+'/'+sys.argv[1]+''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#CORS(app, resources={r"/api/*": {"origins": "*", "Access-Control-Allow-Origin": "*"}})

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

class User(db.Model):
    __tablename__ = 'utilizador'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))
    portugueswalkway_concrete = db.Column(db.Integer)
    tarmac = db.Column(db.Integer)
    cicleway = db.Column(db.Integer)
    dirt = db.Column(db.Integer)
    woodenway_metalway = db.Column(db.Integer)
    sidewalk_width = db.Column(db.Integer)
    allowcars = db.Column(db.Boolean)
    allowbikes = db.Column(db.Boolean)
    helpmovement = db.Column(db.Boolean)
    stairs = db.Column(db.Boolean)
    declivity_up = db.Column(db.Integer)
    declivity_down = db.Column(db.Integer)
    coverage_shape = db.Column(db.Boolean)
    coverage_rainprotected = db.Column(db.Boolean)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

#----------- AUTENTICACAO --------
@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

@app.route('/api/v1/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username,portugueswalkway_concrete=1,tarmac=1,cicleway=1,dirt=1,woodenway_metalway=1,sidewalk_width=1,allowbikes=False,allowcars=False,helpmovement=False,stairs=False,declivity_down=0,declivity_up=0,coverage_shape=False,coverage_rainprotected=False)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,{'Location': url_for('new_user', id=user.id, _external=True)})

@app.route('/api/v1/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})

@app.route('/api/v1/resource')
@auth.login_required
def get_resource():
    return jsonify({'id': g.user.id,'username': g.user.username})

@app.route("/api/")
def hello():
    """
    Home Page da API que vai ser usada como Documentação.
    :return: Varias informações
    """
    return render_template('index.html')

@app.route("/api/v1/")
def checkAPI():
    """
    Verify if the server is online
    :return: Sucess code
    """
    return make_response(jsonify({'addPois':True}), 200)

#UserData
@app.route("/api/v1/readdata/", methods=['GET'])
def readdata():
    """
    Uses the method checkDatabase from mapInteration.py
    """
    id = request.values.get('id')
    return mapa.checkDatabase(id)

@app.route("/api/v1/updateData/", methods=['POST'])
def updateData():
    """
    Uses the method addDataDatabese from mapInteration.py
    :return: JSON object with the success message.
    """
    Calcadaportuguesa_Cimento = request.values.get('Calcadaportuguesa_Cimento')
    Alcatrao = request.values.get('Alcatrao')
    Pistabicicleta = request.values.get('Pistabicicleta')
    Terra = request.values.get('Terra')
    Passadicomadeira_metal = request.values.get('Passadicomadeira_metal')
    escadas = request.values.get('escadas')
    ajudamovimento = request.values.get('ajudamovimento')
    coverageshape_cover = request.values.get('coverageshape_cover')
    coveragerainprotected_cover = request.values.get('coveragerainprotected_cover')
    allowcars_security = request.values.get('allowcars_security')
    allowbikes_security = request.values.get('allowbikes_security')
    id = request.values.get('id')
    return mapa.addDataDatabese(id,Calcadaportuguesa_Cimento,Alcatrao,Pistabicicleta,Terra,Passadicomadeira_metal,escadas,ajudamovimento,coverageshape_cover,coveragerainprotected_cover,allowcars_security,allowbikes_security)
    #return make_response(jsonify({'success':True}), 200)

#PARA RETIRAR
#@app.route("/api/v1/userdatainit/", methods=['GET'])
#def userdatainit():
#    """
#    ?? por fazer
#    :return:
#    """
#    id = request.values.get('id')
#    mapa.runCostfuncton(id)
#    return "teste"

#POIS
@app.route("/api/v1/addPois/", methods=['POST'])
def addpois():
    """
    Upload the json file to add Point of interest information.
    """
    dadosInseridos = request.get_json()
    return make_response(POIS.add(dadosInseridos), 200)

@app.route("/api/v1/loadPois/", methods=['GET'])
def loadpois():
    """
    Method to load the POIS stored in the database
    """
    userid = request.values.get('userid')
    return POIS.load(userid)

@app.route("/api/v1/selectPOI/", methods=['POST'])
def selectPOI():
    """
    Method to select the points of interest when changing the selected column in the database.
    """
    long = request.values.get('long')
    lat = request.values.get('lat')
    selecionado = request.values.get('selec')
    userid = request.values.get('userid')
    return make_response(POIS.select(userid,long,lat,selecionado), 200)

@app.route("/api/v1/removeallpoi/", methods=['POST'])
def removeallpoi():
    """
    Methos to remove all custom pois by user
    """
    long = request.values.get('long')
    lat = request.values.get('lat')
    option = request.values.get('option')
    userid = request.values.get('userid')
    return make_response(POIS.removePOI(long,lat,option,userid), 200)

#POSSIVELMENTE É PARA RETIRAR
@app.route("/api/v1/geomCoord/", methods=['GET'])
def geomCoord():
    geom = request.args.get('geom')
    return POIS.geomToCoord(geom)

#Mapa
@app.route("/api/v1/initUser/", methods=['POST'])
def initUser():
    """
    Create the user personal table in the database.
    """
    userid = request.values.get('id')
    return make_response(mapa.initU(userid), 200)

@app.route("/api/v1/closedPoints/", methods=['GET'])
def closedPoints():
    """
    Method to get the point closest to the coordinates clicked on the map.
    """
    longitude = request.args.get('long')
    latitude = request.args.get('lat')
    return mapa.closedP(longitude,latitude)

@app.route("/api/v1/teseSolucao/", methods=['GET'])
def teseSolucao():
    """
    Method that solves the problem at hand
    :return: The path generated
    """
    longitude = request.args.get('long')
    latitude = request.args.get('lat')
    userid = request.args.get('userid')
    return jsonify(mapa.travelingSalemanSolução(longitude,latitude,userid))

@app.route("/api/v1/soloteseSolucao/", methods=['GET'])
def soloteseSolucao():
    """
    Method that solves the problem at hand with only the clicek edge.
    :return: The path generated
    """
    longitude = request.args.get('long')
    latitude = request.args.get('lat')
    userid = request.args.get('userid')
    distanciaArea = request.args.get('distancia')
    return jsonify(mapa.SolotravelingSalemanSolução(longitude,latitude,userid,distanciaArea))

@app.route("/api/v1/tsp/", methods=['GET'])
def tsp():
    pointList = request.args.get('list')
    initialPointID = request.args.get('id')
    return mapa.tsp(pointList, initialPointID)

@app.route("/api/v1/blockRoad/", methods=['GET']) #utilizado
def blockRoad():
    """
    Method to single block a road.
    :return: The geojson data to show the blocked road in the map
    """
    userid = request.args.get('id')
    lat = request.args.get('lat')
    long = request.args.get('long')
    return jsonify(mapa.blockRoad(lat, long, userid))

@app.route("/api/v1/showPoints/", methods=['GET']) #openlayers.js
def showPoints():
    """
    Method to show every vertex beetween the limits
    :return: All the vertex data in json format
    """
    long1 = request.args.get('long1')
    lat1 = request.args.get('lat1')
    long2 = request.args.get('long2')
    lat2 = request.args.get('lat2')
    return jsonify(mapa.showPoints(long1,lat1,long2,lat2))

@app.route("/api/v1/Insertblock/", methods=['GET']) #openlayers para o unwanted poi
def Insertblock():
    """
    Method to insert a unwanted poi
    :return: information about the unwantedpoi in a json format
    """
    userid = request.args.get('userid')
    long = request.args.get('long')
    lat = request.args.get('lat')
    return jsonify(mapa.addunwantedpoi(userid,long,lat))

@app.route("/api/v1/showBlockedRoad/", methods=['GET']) #openlayers.js
def showBlockedRoad():
    """
    Method returns all blocked roads and unwanted-POI related to the actual user
    """
    id = request.args.get('id')
    return jsonify(mapa.showBlockedRoads(id))

@app.route("/api/v1/removeallBlockedRoad/", methods=['GET']) #openlayers.js todas as estradas
def removeallBlockedRoad():
    """
    Method to remover every block
    :return:
    """
    id = request.args.get('userid')
    return mapa.removeAllBlockedRoads(id)

@app.route("/api/v1/unwantedPois/", methods=['GET'])
def unwantedPois():
    """
    Method to remove the unwanted pois and road block aggregated to that poi
    """
    id = request.args.get('userid')
    poiid = request.args.get('poiid')
    long = request.args.get('long')
    lat = request.args.get('lat')
    return mapa.removeunwantedpoi(poiid,id,long,lat)

@app.route("/api/v1/removeBlockedRoads/", methods=['GET'])
def removeBlockedRoads():
    """
    Method to remove all the blocked roads
    """
    id = request.args.get('userid')
    roadid = request.args.get('roadid')
    return mapa.removeblockroad(roadid,id)

if __name__ == '__main__':
    #AUTENTICACAO
    if not os.path.exists('db.sqlite'):
        db.create_all()
    #INIT
    inicilizacao = init(sys.argv[3], sys.argv[2], sys.argv[1], sys.argv[4])
    POIS = PontosInterese(sys.argv[3], sys.argv[2], sys.argv[1], sys.argv[4])
    mapa = mapInteration(sys.argv[3], sys.argv[2], sys.argv[1], sys.argv[4])
    #cost = customcost(sys.argv[3], sys.argv[2], sys.argv[1], sys.argv[4])
    inicilizacao.init()
    inicilizacao.dataPopulation() #altura, inclinação, etc
    app.run(host='127.0.0.1',port='4000',debug=False)