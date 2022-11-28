import sys, os
from werkzeug.utils import secure_filename

import pandas as pd
from PIL import Image
import threading


from flask import Flask, render_template, Response,jsonify,request,session, redirect, url_for
import cv2
from hubconfCustom import video_detection

from send_email import prepare_and_send_email


#Email headers and body 
RECIPIENT= 'anubhavpatrick@gmail.com'
SUBJECT= 'This mail is sent after one or several person were detected without safety gears.'
MESSAGE_BODY_TEXT= 'Hello Sir, I have extended the task and integrated flask web app and gmail api in a way that it is sending emails only when person class is detected without helmet or jacket.\n\n Regards,\n Akshat Kushwaha'
FILES = []


app = Flask(__name__)
#The secret key helps to maintain a user session
app.config['SECRET_KEY'] = 'thisismysessionandnotyours'

#Specfying the upload directory for file upload
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



#Creating a function for sending email
def send_email():
    image_files= []
    img_obj_list= []
    #Sending email with frame image attached where helmet or jacket not detected
    for file in os.listdir('./PPE_missing'):
        image_files.append(os.path.abspath('./PPE_missing')+fr'\{file}')             #Getting absolute file path for all images
    
    for img_file in image_files:
        img_obj = Image.open(img_file)                        #Creating image object from file path
        img_obj_list.append(img_obj.convert(mode='RGB'))        #converting image to RGB mode before converting to pdf.

    img_obj_list[0].save(os.getcwd()+r'\PPE_missing.pdf', save_all= True, append_images= img_obj_list[1:])    #save all images in a PDF

    FILES.append(os.path.abspath('PPE_missing.pdf'))          #Adding df to FILE to be passed as argumetn in below function.

    #sends the email using function imported through send_email module.
    prepare_and_send_email(recipient= RECIPIENT, subject= SUBJECT, message_text= MESSAGE_BODY_TEXT, file_attachments= FILES)

#Creating a thread for above function
send_mail_thread = threading.Thread(target= send_email)


def generate_frames(path_x = '',conf_= 0.25):
    #Delete all the files in PPE_missing/ diectory before generating frames
    for file in os.listdir('./PPE_missing'):
        os.remove(os.path.abspath('./PPE_missing')+fr'\{file}')            #Combine f-string and raw string


    #Returns a tuple
    yolo_output = video_detection(path_x,conf_)

    #We have used enumerate() function to get the count of each iteration in a tuple
    for count, (detection_,FPS_,xl,yl,labels) in enumerate(yolo_output):       #labels here is a list of all labels in a frame.

        #The function imencode compresses the image and stores it in the memory buffer that is resized to fit the result.
        ref, buffer =cv2.imencode('.jpg',detection_)
        frame=buffer.tobytes()                         #Converts the compressed image to bytes.
        print('total detection:', yl, '\nlabel name:', labels)


        
        #Checking if all persons are wearing helmet and safety jacket
        labels_series = pd.Series(labels)
        label_count_dict = dict(labels_series.value_counts())    #Getting dictionary of all label counts in each frame by converting seres object to dict

        #Checking if count of jacketand helmet is equal to count of person if not, then send that frame as email to concerned.
        if label_count_dict.get('person') != label_count_dict.get('jacket') or \
        label_count_dict.get('person') != label_count_dict.get('helmet'):

            with open(f'./PPE_missing/{count}.jpg', 'wb') as frame_image:
                frame_image.write(frame)


        #Creating a generator object with boundary set to 'frame' to separate different frames in video.
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame +b'\r\n')


    #Calls the thread to start the mail send function. 
    send_mail_thread.start()




@app.route('/')
@app.route('/home')
def home():
    session.clear()

    return render_template("home.html")


@app.route('/result')
def video():

    #Gets the uploaded file path from upload directory and saves its path
    vdo_path = './uploads/'+os.listdir('./uploads')[0]        


    #Below we return a response object, where we define the MIMEtype to be multipart/x-mixed-replace in generate_frame func.
    #The  server can use it to push dynamically updated content to the web browser. 
    #It works by telling the browser to keep the connection open and replace the web page or 
    #piece of media it is displaying with another when it receives a special token. 

    return Response(generate_frames(path_x =vdo_path, conf_=0.55),
                        mimetype='multipart/x-mixed-replace; boundary=frame')  



@app.route('/video', methods= ['POST', 'GET'])
def upload():   

    #Deletes the previously uploaded video
    if os.listdir('./uploads'):
        for i in os.listdir('./uploads'):
            os.remove(f'./uploads/{i}')
    


    #Saving file
    if request.method == 'POST':

        #checks if user has selected a file for uplaoding
        if request.files['file1']:

            f = request.files['file1']

            #set absolute path to upload_path variable for the default Upload directory
            upload_path = os.path.abspath(app.config['UPLOAD_FOLDER'])

            #splitting the uploaded filename to get its file extension.
            f_ext = f.filename.split('.')[1]

            #saving filename to be the video plus its original file extesnion.
            f.filename = 'video.'+f_ext
            f.save(os.path.join(upload_path, f.filename))

            return render_template('stream_vdo.html')
        
        return redirect('/video')

        
    return render_template("upload.html")




    