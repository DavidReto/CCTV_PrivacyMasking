import cv2
import re
import sys
import datetime as dt
import logging as log
import numpy as np
import socket
from time import sleep
import PIL.Image
from datetime import datetime
from tkinter import *
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename

def imagesearch(): 
    global startdate
    global enddate
    startdatefunc = startdate.get()  # gets the startdate value from input box
    enddatefunc = enddate.get()    # gets the enddate value from input box
    pattern = r'(0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012])[- /.](19|20)\d\d'
    matchStart = re.search(pattern, startdatefunc)
    matchEnd = re.search(pattern, enddatefunc)
    if matchStart and matchEnd:
        filename: str = askopenfilename()
        client_program(filename ,startdatefunc ,enddatefunc )
        return filename ,startdatefunc ,enddatefunc
    else:
        print('Wrong format')  
def client_program(filename:str ,startdate:str ,enddate:str ):
    
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    im=PIL.Image.open(filename)
    frameResult = np.array(im)
    frameResult = cv2.cvtColor(frameResult, cv2.COLOR_BGR2RGB)
    byteimage = frameResult.tobytes()
    anexData = '/_/@/_'.encode('utf8')+ str(frameResult.shape[1]).encode('utf8') + '/_/@/_'.encode('utf8')+ str(frameResult.shape[0]).encode('utf8') +'/_/@/_'.encode('utf8') + startdate.encode('utf8')  +'/_/@/_'.encode('utf8') + enddate.encode('utf8')
    searchImage = byteimage + anexData
    client_socket.send(searchImage)  # send message
    response = client_socket.recv(2097152)  # receive response

sys.path.append('.')
root = Tk()
root.geometry("500x100")
root.title("Face Search")
l1 = Label(text = 'Insert start Search Date')
l2 = Label(text = 'Insert end Search Date')
startdate = Entry(root, justify='center')
enddate = Entry(root, justify='center')
fact = 'dd/mm/yyyy'
photo = PhotoImage(file = 'icons/folder_icon.png')  
browsebutton = Button(root,text='Browse',command=imagesearch, image = photo)    
l1.grid(column=0, row= 0, pady=(10, 10), padx=(100,0))
startdate.grid(column=0, row= 1, pady=(0, 10), padx=(100,0))
l2.grid(column=1, row= 0, pady=(10, 10), padx=(10,0))
enddate.grid(column=1, row= 1, pady=(0, 10), padx=(10,0))
browsebutton.grid(column=2, row= 1, pady=(0, 10), padx=(10,0)) 
startdate.insert(END, fact)
enddate.insert(END, fact)

mainloop()

if __name__ == '__main__':
    client_program()