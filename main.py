from tkinter import *
from tkinter import scrolledtext
import math
from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive

import threading
import asyncio

root = Tk()

planets = ["<None>"]

status_text = StringVar()
status_text.set("loading...")

def update_statusbar(new_text):
    status_text.set(new_text)

async def fetch_exoplanet_data():
    status_text.set("loading... ")
    global planets
    # table definitions: https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html#choose

    def query():
        return NasaExoplanetArchive.query_criteria(table="pscomppars", select="pl_name")
    
    exoplanet_data = await asyncio.to_thread(query)
    planets.extend(exoplanet_data["pl_name"].tolist())

    status_text.set("Retrieved " + str(len(planets) - 1) + " planets from PsCompPars (NASA Exoplanet Archive)")

def start_list_fetch(tk_elem):
    asyncio.run(fetch_exoplanet_data())
    update_search(tk_elem, "", planets)

def update_search(tk_elem, user_query, arr):
    if user_query != "":
        results = [item for item in arr if user_query.lower().strip() in item.lower().strip()]
        
        results.sort(key=len)
        tk_elem.delete(0, END)

        for i in range(len(results)):
            tk_elem.insert(i, " " + results[i])
    else:
        tk_elem.delete(0, END)
        for i in range(len(planets)):
            tk_elem.insert(i, " " + planets[i])

# welcome screen
def root_window():
    global root

    root.title("Exosky")
    root.geometry("600x500+100+200")

    root.rowconfigure(1, weight=1)
    root.columnconfigure(1, weight=1)
    root.columnconfigure(2, weight=1)

    ## Top info/button bar
    frame_t = Frame(root, height=40)
    frame_t.grid(row=0, column=1, sticky="EW", columnspan=2, padx=2, pady=3)

    title = Label(frame_t, text="NASA Space Apps Challenge (Exoplanet)", font=("Segoe", 14, "bold"))
    title.pack(side=LEFT, fill=Y)

    credits = Button(frame_t, text=" Show Credits ", relief="groove", width=10, font=("Segoe", 10))
    credits.pack(side=RIGHT, fill=Y)

    ## Left panel: search list + selection
    frame_l = Frame(root)
    frame_l.grid(row=1, column=1, sticky="NSEW", padx=8, pady=2)
    
    ep_list = Listbox(frame_l, font=("Segoe", 10), selectmode=SINGLE) # exoplanet list
    ep_scrollbar = Scrollbar(frame_l, orient=VERTICAL)

    tk_search_val = StringVar()
    tk_search_val.set("")
    tk_search_val.trace_add("write", lambda *args: update_search(ep_list, tk_search_val.get(), planets))

    search_label = Label(frame_l, text="Search for an exoplanet... ", font=("Segoe", 10))
    search_label.pack()
    ep_search = Entry(frame_l, textvariable=tk_search_val, relief=SUNKEN, font=("Segoe", 10))
    # ep_search.bind('<Return>', lambda:update_search(ep_list, ))
    ep_search.pack(fill=X)

    for i in range(len(planets)):
        ep_list.insert(i, " " + planets[i])
    ep_list.pack(side=LEFT, fill=BOTH, expand=True)
    ep_scrollbar.pack(side=RIGHT, fill=Y)

    ## configuring the scrollbar
    ep_list.config(yscrollcommand=ep_scrollbar.set)
    ep_scrollbar.config(command=ep_list.yview)

    ep_list.bind("<<ListBoxSelect>>", )

    threading.Thread(target=lambda *args: start_list_fetch(ep_list), daemon=True).start()

    ## Right panel: description of exoplanet? map?
    frame_r = Frame(root, background="#968ef6")
    frame_r.grid(row=1, column=2, sticky="NSEW")

    planet_name = Label(frame_r, text="[exoplanet name]", font=("Segoe", 12, "bold"), bg="#968ef6", fg="#FFFFFF")
    planet_name.pack()

    info_box = scrolledtext.ScrolledText(frame_r, wrap=WORD, width=10, font=("Segoe", 10), bg="#968ef6", relief=FLAT, state=DISABLED)
    info_box.pack(fill=BOTH, expand=True)

    statusbar = Frame(root)
    statusbar.grid(row=2, column=1, columnspan=2, sticky="NSEW", pady=2)

    status_label = Label(statusbar, textvariable=status_text, font=("Segoe", 10, "italic"))
    status_label.pack()

    root.mainloop()

root_window()