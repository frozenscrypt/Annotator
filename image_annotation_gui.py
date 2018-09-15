#Image Annotation

import PIL
from PIL import Image, ImageTk
import tkinter as tk
import argparse
import datetime
import cv2
import os
import threading
import sys
import time
import numpy as np
import json
import tensorflow as tf
import os.path as ops
from os import path
import matplotlib.pyplot as plt
import itertools
# import handlers
import requests
import ast





def init_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('config_file', type=str, help = 'config file name')

	return parser.parse_args()



class Application:
	def __init__(self, output_path = path):

		self.is_paused = False
		self.prev_x = 0 
		self.prev_y = 0
		self.x_topleft = 0
		self.y_topleft = 0
		self.prev_xtl = 0
		self.prev_ytl = 0
		self.x_bottomright = 0
		self.y_bottomright = 0
		self.prev_xbr = 0
		self.prev_ybr = 0
		self.x_live =  0
		self.y_live = 0
		self.prev_xl = 0
		self.prev_yl = 0
		self.points = []
		self.frame_no = 0
		self.global_image_frame = None
		self.log_list = []
		self.index = 0
		self.speed_ratio = 1
		self.text = []
		self.is_submit = False

		
		self.config = init_args()
		self.args = json.loads(open(self.config.config_file).read())
		print(self.args,type(self.args))
		self.filename = self.args['filename']#self.args.filename
		self.output_dir = self.args['output_dir']#self.args.output_dir
		self.image_folder = self.args['image_folder']#image_folder
		self.frame_no = self.args['frame_no']
		self.mul = self.args['mul']
		if not os.path.exists(self.output_dir):
			os.mkdir(self.output_dir)
		if not os.path.exists(self.output_dir + '/' + 'boxes'):
			os.mkdir(self.output_dir + '/' + 'boxes')
		if not os.path.exists(self.output_dir + '/' + 'detections'):
			os.mkdir(self.output_dir + '/' + 'detections')	

		self.log = open(self.output_dir + '/' + self.image_folder + '_log.txt','a')
		self.img_list =  [f for f in os.listdir(self.filename + '/' + self.image_folder + '/')]
		print(self.img_list)
		self.current_image = None  # current image from the camera

		self.root = tk.Tk()  # initialize root window
		self.root.geometry('1280x720')
		self.root.geometry("%dx%d+%d+%d" % (1280, 720, 0, 0))
		self.root.title("Test")  # set window title
		
		self.root.protocol('WM_DELETE_WINDOW', self.destructor)
	
		self.clear_button = tk.Button(self.root, text="Clear", command = self.clear)
		self.clear_button.place(x = 570, y = 50)
		self.next_button = tk.Button(self.root, text = 'Next', command = self.next_call)
		self.next_button.place(x = 700, y = 50)
		self.previous_button = tk.Button(self.root, text = 'Previous', command = self.previous_call)
		self.previous_button.place(x = 627, y = 50)
		
		self.panel = tk.Label(self.root)  # initialize image panel
		self.panel.place(x = 300, y = 100)
		self.panel2 = tk.Label(self.root)  # initialize panel for cropped image
		self.panel2.place(x = 50,y = 600)
		self.text_object = tk.Text(self.root,width = 50,height = 1)
		self.text_object.place(x = 300,y = 600)
		self.text_object.configure(font=("Times New Roman", 12, "bold"))
		self.text_object.insert(tk.END,'Comment')
		

		self.panel6 = tk.Button(self.root, text="Submit", command=self.submit)
		self.panel6.place(x = 850,y = 600)
		self.log_object = tk.Text(self.root,width = 50, height = 40)
		self.log_object.place(x = 1000,y = 100)
		self.log_object_text = tk.Label(self.root, text = 'PROCESS LOG')
		self.log_object_text.configure(font=("Times New Roman", 12, "bold"))
		self.log_object_text.place(x = 1000, y = 80)

		self.root.config(cursor="arrow")
		self.readLogFile = open(self.output_dir + '/' + self.image_folder + '_log.txt','r').readlines()
		self.start = True

		self.video_loop()


	def video_loop(self):
		
		""" Get frame from the video stream and show it in Tkinter """
		if self.frame_no != 0 and self.start == True:
			try:
				self.index = self.img_list.index(str(self.readLogFile[-1].split('\t')[0])) + 1 
				self.start = False
			except:
				pass

		if len(self.readLogFile)!=0 and self.start == True:
			self.index = self.img_list.index(str(self.readLogFile[-1].split('\t')[0])) + 1 
			self.start = False


		if  not self.is_paused:
			self.frame_no = self.img_list[self.index].split('.')[0]
			print(self.filename,'the filename is this' )
			self.frame = cv2.imread(self.filename + '/' + self.image_folder + '/' + self.img_list[self.index])
			self.global_image_frame = self.frame
			self.is_paused = True
			self.x_topleft,self.y_topleft,self.x_bottomright,self.y_bottomright,self.x_live,self.y_live = 0,0,0,0,0,0
		else:
			self.frame = self.global_image_frame

		cv2image = self.frame 
		r,col,ch = cv2image.shape
		cv2resized = cv2.resize(cv2image,fx = self.mul,fy = self.mul,dsize = (0,0))


		if True:  # frame captured without any errors
			self.panel.bind("<Button-1>",self.top_left_click)
			self.panel.bind("<ButtonRelease-1>",self.bottom_right_release)
			self.panel.bind("<B1-Motion>",self.mouse_movement)


			if (self.x_topleft, self.y_topleft)!=(self.prev_xtl, self.prev_ytl):
				self.prev_xtl,self.prev_ytl = self.x_topleft,self.y_topleft
				self.points = [(self.prev_xtl,self.prev_ytl)]
				self.is_paused = True
			print(self.x_bottomright,self.y_bottomright,self.prev_xbr, self.prev_ybr,'this is before bottoms')
			if (self.x_bottomright, self.y_bottomright)!=(self.prev_xbr, self.prev_ybr) and self.is_paused:
				print(self.x_bottomright,self.y_bottomright,self.prev_xbr, self.prev_ybr,'this is call bottoms')
				self.prev_xbr,self.prev_ybr = self.x_bottomright,self.y_bottomright
				self.points += [(self.prev_xbr,self.prev_ybr)]
				thread1 = threading.Thread(target=self.boundingbox,args=(cv2image,self.filename,self.frame_no,self.points))
				thread1.start()

			if (self.x_live, self.y_live)!=(self.prev_xl, self.prev_yl):
				self.prev_xl, self.prev_yl = self.x_live, self.y_live
				cv2.rectangle(cv2resized,(self.x_topleft,self.y_topleft),(self.x_live,self.y_live),(0,255,0),1)

			if self.is_paused:
				cv2.rectangle(cv2resized,(self.x_topleft,self.y_topleft),(self.x_live,self.y_live),(0,255,0),1)


			self.current_image = Image.fromarray(cv2resized)  # convert image for PIL
			imgtk = ImageTk.PhotoImage(image=self.current_image)  # convert image for tkinter 
			self.panel.imgtk = imgtk  # anchor imgtk so it does not be deleted by garbage-collector  
			self.panel.config(image=imgtk)  # show the image
		self.root.after(40//self.speed_ratio, self.video_loop)  # call the same function after 30 milliseconds



	def trigger(self):
		self.log_object.insert(tk.END,'The Trigger is called for frame {}\n'.format(frame_no))
		thread2 = threading.Thread(target=self.api_calls)
		thread2.start()
		

	def api_calls(self): 
		# global delay,text,mul,rotation_signal,frame_no,output_dir
		time.sleep(delay)   
		img = global_image_frame
		cv2.imwrite(output_dir + '/img.jpg',img)
		img = open("/home/vivek/IBI/output_1_hour_masked/img.jpg","rb").read()
		headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
		data = {'img':img,'frame_no':str(frame_no)}
		print('line 198-----------------')
		r = json.loads(requests.request('post',url = 'http://localhost:5000/predict',files = data).json())
		print(r)
		# bdata = json.loads(r['boxes'])#json.loads(r.decode('utf-8'))['boxes']
		try:
			boxes = r#np.array(bdata)#np.array(json.loads(bdata))
		except:
			boxes = ''
		if type(boxes)==str:
			self.text_object.insert(tk.END,'No Boxes Detected')
		else:
			self.panel_list = []
			for i in range(len(boxes)):
				panel = tk.Label(self.root)
				panel.place(x = 50,y = 100 + 100*i )
				self.panel_list.append(panel)
			print(type(boxes),'the type of box pos1',type(boxes['0']))
			boxes_tmp = {}
			for k,box in boxes.items():
				tmp_box={}
				for k1,pt in box.items():
					temp_pt = {}
					temp_pt['x'] = pt[0]
					temp_pt['y'] = pt[1]
					tmp_box[k1] = temp_pt.copy()
				boxes_tmp[k] = tmp_box.copy()
			print(boxes_tmp)
			# for item in zip(boxes.tolist(),self.panel_list):
			# 	smx = int(min([pt[0] for pt in item[0]]))
			# 	lgx = int(max([pt[0] for pt in item[0]]))
			# 	smy = int(min([pt[1] for pt in item[0]]))
			# 	lgy = int(max([pt[1] for pt in item[0]]))
			# 	im = global_image_frame[smy*mul:lgy*mul,smx*mul:lgx*mul]
			# 	im = cv2.resize(im,(100,50))
			# 	current_image = Image.fromarray(im)  # convert image for PIL
			# 	imgtk = ImageTk.PhotoImage(image=current_image)
			# 	item[1].imgtk = imgtk
			# 	item[1].config(image = imgtk)
			# self.log_object.insert(tk.END,'The box for frame {} is created\n'.format(frame_no))
			# boxes = boxes.tolist()
			'''Here is the json data sent with the request'''
			print(type(boxes),'the type of box pos2',type(img))
			print(boxes)
			data = {'img':img,'frame_no':str(frame_no),'boxes':json.dumps(boxes_tmp.copy()),'index':str(0)}
			r = requests.request('post',url = 'http://localhost:5000/recognize',files = data)
			print(r,'the output from recognizer')
			tdata = json.loads(r.decode('utf-8'))
			text = ast.literal_eval(tdata['text'])
			text_list = []
			for word in text:
				txt = [i + ' ' for i in word]
				ftxt = ''.join(txt)
				text_list.append(ftxt)
			self.panel3.delete('1.0',tk.END)
			self.text_object.delete('1.0',tk.END)
			self.panel3.insert(tk.END,text_list)
			self.text_object.insert(tk.END,text_list)
			self.log_object.insert(tk.END,'The recognition of plate for frame {} is done\n'.format(frame_no))
	   
	def boundingbox(self,image,filename,frame_no,points):
		# global log_list,text,mul,rotation_signal
		print(points,'line 258')
		smallest_x = int(np.min([pt[0] for pt in points])/self.mul)
		smallest_y = int(np.min([pt[1] for pt in points])/self.mul)
		largest_x = int(np.max([pt[0] for pt in points])/self.mul)
		largest_y = int(np.max([pt[1] for pt in points])/self.mul)
		box_img = cv2.rectangle(image,(smallest_x,smallest_y),(largest_x,largest_y),(0,255,0))
		# box_img = Image.fromarray(image)
		# box_img.save(self.output_dir + '/detections/' + '{}.jpg'.format(self.frame_no))
		cv2.imwrite(self.output_dir + '/detections/' + '{}.jpg'.format(self.frame_no),box_img)
		cv2.imwrite(self.output_dir + '/boxes/' + '{}.jpg'.format(self.frame_no),
			image[smallest_y:largest_y,smallest_x:largest_x])

		# Show cropped image on gui
		self.panel2 = tk.Label(self.root)  # initialize panel for cropped image
		self.panel2.place(x = 50,y = 600)
		# img = cv2.resize(box_img,(100,100))
		img = cv2.resize(image[smallest_y:largest_y,smallest_x:largest_x],(100,100))
		current_image = Image.fromarray(img)  # convert image for PIL
		imgtk = ImageTk.PhotoImage(image=current_image)  # convert image for tkinter 
		self.panel2.imgtk = imgtk  # anchor imgtk so it does not be deleted by garbage-collector  
		self.panel2.config(image=imgtk)  # show the image
		self.log_object.insert(tk.END,'The box for frame {} is created\n'.format(self.frame_no))
		box = [(smallest_x,smallest_y),(largest_x,largest_y)]
		self.log_list.append([self.frame_no + '.jpg',box])

	   
	def clear(self):
		print("RESUMING...")
		self.text_object.delete('1.0',tk.END)
		self.text_object.insert(tk.END,'Comment')
		try:
			for panel in self.panel_list:
				panel.destroy()
		except:
			pass
		try:
			self.panel2.destroy()
		except:
			pass
		self.is_paused = True#False
		if self.is_submit == False:
			self.log_list.remove(self.log_list[-1])
		self.x_topleft,self.y_topleft,self.x_bottomright,self.y_bottomright,self.x_live,self.y_live = 0,0,0,0,0,0



	def submit(self):
		
		commented_text = self.text_object.get('1.0',tk.END).split('\n')[0]
		self.text_object.delete('1.0',tk.END)
		self.text_object.insert(tk.END,'Comment')
		self.log_list[-1].append(commented_text)
		print(self.log_list,'lalala')
		try:
			for panel in self.panel_list:
				panel.destroy()
		except:
			pass
		try:
			self.panel2.destroy()
		except:
			pass

		self.is_paused = False
		self.is_submit = True
		print(self.x_bottomright,self.y_bottomright,self.prev_xbr, self.prev_ybr,'this is bottoms')


	#Top Left Click
	def top_left_click(self,event):
		self.x_topleft = event.x
		self.y_topleft = event.y
		self.is_submit = False

	#Bottom Right Mouse Release
	def bottom_right_release(self,event):
		self.x_bottomright = event.x
		self.y_bottomright = event.y

	#Mouse movements after click
	def mouse_movement(self,event):
		self.x_live = event.x
		self.y_live = event.y



	def set_delay(self):
		global delay
		delay = int(self.delay_text.get('1.0',tk.END).split('\n')[0])
		

	def next_call(self):

		self.is_paused = False
		self.index+=1

	def previous_call(self):

		self.is_paused = False
		self.index-=1




	def destructor(self):

		""" Destroy the root object and release all resources """
		print("Last frame:",self.frame_no)
		print("[INFO] closing...")
		try:
			for line in self.log_list:
				print(line)
				self.log.write('{}\t{}\t{}\n'.format(line[0],line[1],line[2]))
		except:
			pass
		self.root.destroy()
		# self.f.close()
		self.log.close()
	 
	  

	
# start the app
print("[INFO] starting...")
pba = Application(path)	 
pba.root.mainloop()