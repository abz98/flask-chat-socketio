#imports
from flask import Flask , request ,session,render_template, abort, url_for,flash, redirect
import pyrebase
from flask_socketio import SocketIO,join_room, leave_room
import requests
import os
import json
import firebase_admin
import math
from werkzeug.utils import secure_filename
from datetime import datetime

import random
from firebase_admin import credentials ,auth,firestore
# from flask_session import Session

app = Flask(__name__,template_folder= '/home/knox/Desktop/Flask and react/pyrebase/src/template')
SECRET_KEY = os.urandom(32)
socketio = SocketIO(app)
app.config['UPLOAD_FOLDER'] = "/home/knox/Desktop/Flask and react/pyrebase/src/static/images"
app.config['SECRET_KEY'] = SECRET_KEY
users = [{'uid': 1, 'name': 'Abhit patil'}]

#Connect to firebase
cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('firebaseConfig.json')))
auth = pb.auth()
db = firestore.client()

#Initialze person as dictionary
person = {"is_logged_in": False, "name": "", "email": "", "uid": ""}

#Sign up/ Register
@app.route("/signup")
def signup():
    return render_template("signup.html")

#Login
@app.route("/")
def login():
    return render_template("login.html")   

@app.route('/chat/<room_id>/ok')
def chats(room_id):
    if  session.get("name"):
     print("room_id royute=====000099"+room_id)
     friendName = request.args.get("name")
     friendsEmail = request.args.get("email")
     friendsUid =request.args.get("id")
     roomid = request.args.get("roomid")
     session['room'] = roomid
     docid = request.args.get("docid")
     return render_template('onetoone.html',email = session["email"], name = session["name"],uid = session['uid'],session=roomid,friendName=friendName,items= session['items'],docid=docid,friendsEmail=friendsEmail,friendsUid=friendsUid)
    else:
       return redirect(url_for('login'))    


@app.route('/chat/room')
def chat():
    return render_template('body.html',email = session["email"], name = session["name"],uid = session['uid'],session=session['room'],items= session['items'])




#Welcome page
@app.route("/welcome")
def welcome():
    if  session.get("name"):
        items = fetchFriends()
        session['items'] = items
        session['randomColor'] = str(math.floor(random.random()*16777215))    
        return render_template("chat.html", email = session["email"], name = session["name"],uid = session['uid'],session=session['room'],items=items)
    else:
        return redirect(url_for('login'))    

#If someone clicks on register, they are redirected to /register
@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":        #Only listen to POST
        result = request.form           #Get the data submitted
        email = result["email"]
        password = result["pass"]
        name = result["name"]
        file = request.files['file']
        try:
            #Try creating the user account using the provided data
            print("entered")
            signup = auth.create_user_with_email_and_password(email, password)
            #Login the user
            print("sign in")
            user = auth.sign_in_with_email_and_password(email, password)
            #Add data to global person
            global person
            print("entered here====")
            try:
              if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
              if file != None:
                filename = f'{user.localId}.jpeg'
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except:

              
                unique = user['localId']
                filename = unique+'.jpeg'
                print(filename+"fdlfksd")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print("image saved succesfully")
               
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            person["name"] = name
            #Append data to the firebase realtime database
            data = {"name": name, "email": email,"uid":  user["localId"]}
            print("addin firebase")
            doc_ref = db.collection('users').document(user['localId'])
            doc_ref.set(data)
            print(doc_ref)
            message = "sucessfully created account!"

            
             #Go to welcome page
          
            return redirect(url_for('/'))
        except:
            #If there is any error, redirect to register
            return redirect(url_for('register'))

    else:
            return redirect(url_for('login'))

#If someone clicks on login, they are redirected to /result
@app.route("/result", methods = ["POST", "GET"])
def result():
    if request.method == "POST":        #Only if data has been posted
        result = request.form           #Get the data
        email = result["email"]
        print(email)
        # print(session.sid)
        password = result["pass"]
        uids = ""
        try:
            #Try signing in the user with the given information
            user = auth.sign_in_with_email_and_password(email, password)
            #Insert the user data in the global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] =  user['localId']
            if user['localId'] is None:
                uids  = "none is "
            else:    
               uids = user["localId"]
            # print(session.sid)
            dt = db.collection('users').document(user['localId']).get().to_dict()
            
            print(dt)   
            person["name"] = dt["name"]
            session["name"]  = dt['name']
            session['uid'] = user['localId']
            session['email'] = dt['email']

            session['room'] = ""
            print(session)

            # ui = f"{user.uid}"

            #Get the name of the user
            # data = db.child("users").get()
            
            # person["name"] = data.val()[person["uid"]]["name"]
            #Redirect to welcome page
            return redirect(url_for('welcome',uid=uids))
        except:
            #If there is any error, redirect back to login
            return redirect(url_for('login'))
    else:
        if person["is_logged_in"] == True:
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('login'))






###  go
@app.route('/userinfo')
def userinfo():
    return {'data': users}, 200

# @app.route("/fetchfriends")
def fetchFriends():

    dt = db.collection('users').document(session['uid']).collection('channel').stream()
    print(dt)
    items = []
    for a in dt:
        print(f'{a.id} => {a.to_dict()}')
        items.append(a.to_dict())
    print(f'=====>items==>{items}')
    return items    

@app.route("/addfriend")
def addFriend():
    fname = request.args.get("name")
    femail = request.args.get("email")
    fid = request.args.get('id')
    print(fid+"nulll")
   
    # data = {"fuid" : fid, "docid"}
    try:    
      dt = db.collection('users').document(session['uid']).collection('channel').document()
      data = {"fuid" : fid, "docid" : dt.id, "email" : femail, "name": fname ,"roomid" : session['uid']}
      dt.set(data)
      print("sucessfull adding the data")
      print("adding in friends database")
      database = db.collection('users').document(fid).collection('channel').document(dt.id)
      fdata = {"fuid" : session['uid'], "docid" : dt.id, "email" : session['email'], "name": session['name'] ,"roomid" : session['uid']}
      database.set(fdata)
      print("sucessfull adding into friends data")
      return redirect(url_for('welcome'))

    except:
        print("adding unscuessfull")
        msg = "Error adding the friends pls try again"
        return render_template('erroradding.html',message=msg)
 
    #


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

def savemessages(msg,created_at,uid,name,sentAt):
    save = db.collection("messages").document(uid).collection('message').document(created_at)
    save.set({"username": name,"createdAt": created_at,"message":msg,"uid":session['uid'],"sentAt":sentAt})
    print(f"saved message:- '{msg}' successfully")


@app.route("/getoldermessages/<docid>")
def getoldermessages(docid):

    docid = request.args.get('docid')
    try: 
      cities_ref = db.collection('messages').document(docid).collection('message')
      query = cities_ref.order_by('createdAt', direction=firestore.Query.DESCENDING).limit(15)
      results = query.stream()
      oldMessage = []
      for a in results:
          print(f'{a.id} => {a.to_dict()}')
          oldMessage.append(a.to_dict())
      response = app.response_class(
          response=json.dumps(oldMessage),
          status=200,
          mimetype='application/json')
      return response
    except :
        print("unsucfull getting old messages")


@socketio.on('my event')
def handle_sockets(json, methods=['GET', 'POST']):
    print('==>event receiv: ' + str(json))
    # privateid()
    join_room(session['room'])
    
    # print("adsdas===>{}"+request.sid)
    json["color"] = session['randomColor']
    json["name"] = session["name"]
    json["id"] = session['uid']
    sentAt = json['sentAt']=  datetime.now().strftime("%I:%M")
    # docid = datetime.now().strftime("%Y %d %b, %I:%M :%S")
    docid = str(int(datetime.now().timestamp()* 1000))
    savemessages(json['message'],docid,json['docid'],json['name'],sentAt)



    socketio.emit('my response', json, callback=messageReceived,room=session['room'])


@socketio.on('join_room')
def handle_join_room_events(data):
    data["name"] = session["name"]
    app.logger.info("{} has joined the room {}".format(data['name'], session['room']))
    join_room(session['room'])
    socketio.emit('join_room_announcement', data, room=session['room'])




#rooms
@socketio.on('allroom ok')
def handle_socket(json, methods=['GET', 'POST']):
    print('==>event receiv: ' + str(json))
    # privateid()
    # print("adsdas===>{}"+request.sid)

    json["color"] = session['randomColor']
    json["id"] = session['uid']
    json["name"] = session["name"]
    socketio.emit('res ok', json)


@socketio.on('joined_room')
def handle_join_room_event(data):
    data["name"] = session["name"]
    app.logger.info("{} has joined the room {}".format(data['name'], session['room']))
    socketio.emit('joined_room_announcement', data)


@app.route("/fetchuser")
def fetchusers():
    dt = db.collection('users').stream()
    print(dt)
    items = []
    for a in dt:
        print(f'{a.id} => {a.to_dict()}')
        items.append(a.to_dict())
    print(f'=====>items==>{items}')
    response = app.response_class(
        response=json.dumps(items),
        status=200,
        mimetype='application/json'
    )
    return response  


 




if __name__ == '__main__':
  socketio.run(app,debug=True)  
  #app.run(debug=True)
  """ host='192.168.2.5' """