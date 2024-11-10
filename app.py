from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
import datetime
import pytz
import json, re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
api = Api(app)
IST = pytz.timezone('Asia/Kolkata')

# User Model
class UserModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(IST))

    def __repr__(self):
        return f"User(username={self.username}, created_at={self.created_at})"

# Data Capture Model
class DataCaptureModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    isp = db.Column(db.String(80))
    os = db.Column(db.String(80))
    keystroke_dynamics = db.Column(db.String(255))
    mouse_movement_patterns = db.Column(db.String(255))
    touch_interaction_patterns = db.Column(db.JSON) 
    sensor_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<DataCaptureModel(user_id={self.user_id}, latitude={self.latitude}, longitude={self.longitude})>"

# Request Parsers
user_args = reqparse.RequestParser()
user_args.add_argument('username', type=str, required=True, help="Username is required")
user_args.add_argument('password', type=str, required=True, help="Password is required")

data_capture_args = reqparse.RequestParser()
data_capture_args.add_argument('latitude', type=float, required=True, help="Latitude is required")
data_capture_args.add_argument('longitude', type=float, required=True, help="Longitude is required")
data_capture_args.add_argument('isp', type=str, required=True)
data_capture_args.add_argument('os', type=str, required=True)
data_capture_args.add_argument('keystroke_dynamics', type=str)
data_capture_args.add_argument('mouse_movement_patterns', type=str)
data_capture_args.add_argument('touch_interaction_patterns', type=str)
data_capture_args.add_argument('sensor_data', type=str)

# Response Fields
user_fields = {
    'id': fields.Integer,
    'username': fields.String,
    'password': fields.String,
    'created_at': fields.DateTime
}

data_capture_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'latitude': fields.Float,
    'longitude': fields.Float,
    'isp': fields.String,
    'os': fields.String,
    'keystroke_dynamics': fields.String,
    'mouse_movement_patterns': fields.String,
    'touch_interaction_patterns': fields.String,
    'sensor_data': fields.String,
    'created_at': fields.DateTime
}

def is_valid_password(password):
    # Minimum 8 characters, at least one letter, one number, and one special character
    pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(pattern, password)


class RegisterUser(Resource):
    @marshal_with(user_fields)
    def post(self):
        args = user_args.parse_args()

        # Check if username already exists
        if UserModel.query.filter_by(username=args['username']).first():
            abort(409, message="Username already exists")

        # Validate password
        if not is_valid_password(args['password']):
            abort(400, message="Password must be at least 8 characters long, including at least one letter, one number, and one special character.")

        # Create user if password is valid
        user = UserModel(username=args['username'], password=args['password'])
        db.session.add(user)
        db.session.commit()
        return user, 201

class LoginUser(Resource):
    def post(self):
        args = user_args.parse_args()
        user = UserModel.query.filter_by(username=args['username'], password=args['password']).first()
        if user:
            user_response = {
                "id": user.id,
                "username": user.username,
                "createdAt": user.created_at.isoformat()  # Convert datetime to ISO 8601 format for JSON
            }
            return user_response, 200
        else:
            abort(401, message="Invalid credentials")

class DataCapture(Resource):
    @marshal_with(data_capture_fields)
    def post(self, user_id):
        args = data_capture_args.parse_args()
        user = UserModel.query.get(user_id)
        if not user:
            abort(404, message="User not found")

        # Parse touch_interaction_patterns and sensor_data as JSON if provided
        touch_interaction_patterns = None
        if args.get('touch_interaction_patterns'):
            touch_interaction_patterns = json.loads(args['touch_interaction_patterns'])

        sensor_data = None
        if args.get('sensor_data'):
            sensor_data = json.loads(args['sensor_data'])

        # Create a DataCaptureModel entry with parsed JSON data
        data_capture = DataCaptureModel(
            user_id=user.id,
            latitude=args['latitude'],
            longitude=args['longitude'],
            isp=args['isp'],
            os=args['os'],
            keystroke_dynamics=args.get('keystroke_dynamics', ''),
            mouse_movement_patterns=args.get('mouse_movement_patterns', ''),
            touch_interaction_patterns=touch_interaction_patterns,
            sensor_data=sensor_data
        )
        db.session.add(data_capture)
        db.session.commit()
        return data_capture, 201

class StopDataCapture(Resource):
    def post(self, user_id):
        user = UserModel.query.get(user_id)
        if not user:
            abort(404, message="User not found")
        
        # Placeholder logic to stop data capture (e.g., update a status if required)
        return {'message': 'Data capture stopped for user {}'.format(user.username)}, 200

class GetUserData(Resource):
    @marshal_with(data_capture_fields)
    def get(self, user_id):
        user = UserModel.query.get(user_id)
        if not user:
            abort(404, message="User not found")
        
        data_entries = DataCaptureModel.query.filter_by(user_id=user.id).all()
        return data_entries, 200

# Add API Resources
api.add_resource(RegisterUser, '/api/register')
api.add_resource(LoginUser, '/api/login')
api.add_resource(DataCapture, '/api/users/<int:user_id>/data_capture')
api.add_resource(StopDataCapture, '/api/users/<int:user_id>/stop_data_capture')
api.add_resource(GetUserData, '/api/users/<int:user_id>/data')

@app.route('/')
def home():
    return '<h1>Assignment API</h1>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
