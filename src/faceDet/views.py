from django.shortcuts import render

import cv2
import numpy
import os
from PIL import Image
import numpy as np

import smtplib
from django.core.mail import EmailMessage
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from posts.models import Post
from django.contrib.auth.models import User

from blog.settings import DETECT_FILE_URL, DATASET_URL, MODEL_URL

# Create your views here.

def faceDetAdmin(request):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
        
    context = {}
    return render(request, "faceDetAdmin.html", context)
    


def createDataSet(request):
    if not request.user.is_staff or not request.user.is_superuser:
		raise Http404
    
    posts = Post.objects.filter(processed=False, draft=False)

    # create dataSet from these post images.
    # save these posts as processed=True

    faceDetect = cv2.CascadeClassifier(DETECT_FILE_URL)

    for post in posts:
        img = cv2.imread(post.image.path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # dont know why its getting empty
        if not faceDetect.empty():
            faces = faceDetect.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                user_file_path = 'User-{}-{}.jpg'.format(post.user.id, post.slug)
                file_pth = os.path.join(DATASET_URL, user_file_path)
                cv2.imwrite(file_pth, gray[y:y+h, x:x+w])

        else: print('xml not found')

        post.processed = True
        post.save()

    context = {}
    return render(request, "faceDetAdmin.html", context)

def trainModel(request):
    if not request.user.is_staff or not request.user.is_superuser:
		raise Http404

    # train model
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    imagePaths = [os.path.join(DATASET_URL, f) for f in os.listdir(DATASET_URL)]
    faces = []
    user_ids = []

    for imagePath in imagePaths:
        if imagePath.endswith('.DS_Store'):
            if os.remove(imagePath)  : print "Unable to delete!"
            else                     : print "Deleted..."
        else:
            faceImage = Image.open(imagePath).convert('L')
            faceNp = np.array(faceImage, 'uint8')
            user_id = int(os.path.split(imagePath)[1].split('-')[1])
            faces.append(faceNp)
            user_ids.append(user_id)

    recognizer.train(faces, np.array(user_ids))
    recognizer.save(os.path.join(MODEL_URL, 'trainingData.yml'))

    context = {}
    return render(request, "faceDetAdmin.html", context)

def checkAndMail(request):
    if not request.user.is_staff or not request.user.is_superuser:
		raise Http404

    posts = Post.objects.filter(processed=False, draft=True)

    # run detector on posts, detect users other than post.user
    # mail the other users the verification link
    # save posts with processed=True
    # now verification link will set my_photo=True

    faceDetect = cv2.CascadeClassifier(DETECT_FILE_URL)
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(os.path.join(MODEL_URL, 'trainingData.yml'))

    for post in posts:

        author = post.user

        img = cv2.imread(post.image.path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = faceDetect.detectMultiScale(gray, 1.3, 5)

        for (x,y,w,h) in faces:
            cv2.rectangle(img ,(x,y), (x+w, y+h), (0,255,0), 2)
            user_id, conf = recognizer.predict(gray[y:y+h, x:x+w])
            print(user_id, conf)
            pic_user = User.objects.get(id=user_id)
            if not (user_id == author.id):
                blur = cv2.blur(img[y:y+h, x:x+w],(25,25))
                img[y:y+h, x:x+w] = blur

                mail_user(user_id=user_id, author=author, post=post)

        # post.my_photo = True
        # post.save()

    context = {}
    return render(request, "faceDetAdmin.html", context)

def mail_user(user_id, author, post):
    try:
        user = User.objects.get(id=user_id)
        name = user.username
        email = user.email
        fromaddr = 'djangoprojects2@gmail.com'
        toaddr  = email
        gmail_username = 'djangoprojects2@gmail.com'
        password = 'djangoproject123'

        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(gmail_username,password)

        msg = MIMEMultipart('alternative')
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "Photo Verification Link"
        body = u'<html><head></head><body>Hey {}, <br><br>{} has tagged you in a photo.<br><br>Please go on this link to give {} the permission to post this photo online.<br><br>Verification URL - <a href="127.0.0.1:8000/verify/{}">127.0.0.1:8000/verify/{}</a><br><br><br>Ignore this mail if you dont want to give permissions to post the image</body></html>'.format(name, author.username, author.username, post.slug, post.slug)
        msg.attach(MIMEText(body, 'html'))

        mail_link_html = u"".format(post.slug, post.slug)
        verify_url = MIMEText(mail_link_html,'html')
        msg.as_string(verify_url)

        img_data = open(post.image.path, 'rb').read()
        try:
            image = MIMEImage(img_data, name=os.path.basename(post.image.path))
        except:
            print('attchment failed.')
        msg.attach(image)

        server.sendmail(fromaddr, [toaddr], msg.as_string())
        server.quit()
    except:
        print('Mail Function Failed!')