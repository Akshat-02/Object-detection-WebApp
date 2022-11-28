import os
import base64
import mimetypes

#Importing google api libraries
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.message import EmailMessage

import socket                         #Added to fix "socket.timeout: The write operation timed out" error which was caused
socket.setdefaulttimeout(150)         #due to connection time out


#OAuth 2.0 SCOPES basically defines the resources that are accessible with the current access token, upating SCOPES will 
#need you to update access token as well in token.json file (which means the saved token.json file will not work with
#updated SCOPES).
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def authenticate():
    """The authentication function checks if the required credential file (token.json) which contains
    the user's access and refresh tokens exists or not.

    If it doesnt exists then user will be asked to manually login into there google account,
    after which the cred file (token.json) will be created."""

    creds = None

    #If the token.json file already exists then authenticate it with the currrent api SCOPES.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    #If the credentials doesn't exists then ask user to login again or if it's invalid and expired
    #refresh the access token.
    if not creds or not creds.valid:                                   

        #Checks if creds has expired and there is a refresh token available
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        #Asks user to login to get credentials.
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)    #InstallAppFlow class is used for installed applications.
            
            #Run the flow for authentication on any port. 
            # (Port 0 is a wildcard port that tells the system to find a suitable port number)
            creds = flow.run_local_server(port=0)       

        # Save the credentials in 'token.json' file for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds




def create_message_with_attachment(sender, to, subject, message_text, file_attachments):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.
    file_attachments: The files to attach in email in iterable.

    Returns:
    An object containing a base64url encoded email object.
    """

    message = EmailMessage()
    
    #Set email headers
    message['To'] = to
    message['From'] = sender
    message['Subject'] = subject

    #create a msg body
    message.set_content(message_text)

    #Checking if there are files to be sen as attachment
    if file_attachments != None:

        #Supports multiple file attachments
        for f in file_attachments:
            with open(f, 'rb') as file:
                file_attachment_data = file.read()

            try:
                #using mimetypes module to get a tuple containing info of mimetype and encoding used
                mimetype, encoding = mimetypes.guess_type(f)

                #spliting the mimetype string which is in format like this: text/plain (where text is main type & plain is subtype)
                main_type, subtype = mimetype.split('/')

                #adding attachment to message
                message.add_attachment(file_attachment_data, main_type, subtype)
            
            except:
                #If mimetype module fails to guess mime type then add attachmetn as octet-stream (aka bytestream).
                #application/octet-stream MIME type is used for unknown binary files, it lets the reciever application
                #to determine the file type, for example, from the filename extension. 
                message.add_attachment(file_attachment_data, maintype='application', subtype='octet-stream')

    
    #encoding message to base64 url safe to transfer it in email
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    return {'raw': encoded_message}



def send_message(service, user_id, message):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me" can be used to indicate the authenticated user.
    message: Message to be sent.

    Returns:
    Sent Message.
    """

    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())

        print(f'Message Id: {message["id"]}', message)

        return message

    except HttpError as error:
        print(f'An error occurred: {error}')




def prepare_and_send_email(recipient, subject, message_text, file_attachments= None):
    """Prepares and send email with attachment to the participants"""
    
    #Getting the credentials
    creds = authenticate()

    #same email as used for API authentication (actually I tested with different mail and it still sends the email with 
    # the mail used for authentication a only user_id is used to identify and athentcate the email id)
    MY_EMAIL = 'caml20003@glbitm.ac.in'


    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        #calling user defined function for creating message
        msg = create_message_with_attachment(MY_EMAIL, recipient, subject, message_text, file_attachments)

        #calling user defined function for sending email
        send_message(service, user_id= 'me', message= msg)        #'me' can be used to indicate the authenticated user


    except HttpError as error:
        print(f'An error occured: {error}')


if __name__ == '__main__':

    RECIPIENT= 'thesuspectindia@gmail.com'
    SUBJECT= 'This is for testing please ignore.'
    MESSAGE_BODY_TEXT= 'YOu are the chosen few, few the fearless you gonna be'
    
    FILES= [r'C:\Users\aksha\OneDrive\Desktop\Wallpapers\19609.jpg', r'C:\Users\aksha\OneDrive\Desktop\Wallpapers\21635.jpg']

    prepare_and_send_email(recipient= RECIPIENT, subject= SUBJECT, 
                        message_text= MESSAGE_BODY_TEXT, file_attachments= FILES)
