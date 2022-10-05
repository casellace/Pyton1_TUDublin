from tkinter import *
from tkinter import ttk
from tkinter import messagebox #second box after quiting

def hello(txt):
    print("hello")
    messagebox.showinfo("Title Box", "message box " + txt.get())

root = Tk()
root.geometry("500x400")
frm = ttk.Frame(root, padding=200)
frm.grid()
mytext = StringVar()
ttk.Entry(frm, textvariable=mytext).grid(row=1, column=0)
ttk.Label(frm, text="Hello World!").grid(column=0, row=0)
ttk.Button(frm, text="Quit", command=lambda: hello(mytext)).grid(column=0, row=2)
root.mainloop()
