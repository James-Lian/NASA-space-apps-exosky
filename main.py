from tkinter import *
from tkinter import scrolledtext
from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
import math
import threading
import asyncio

from renderer import open_pygame_window
exoplanet_ra = None
exoplanet_dec = None
root = Tk()

planets = ["<None>"]

status_text = StringVar()
status_text.set("loading...")

## fetching ALL the planets
async def fetch_exoplanet_data():
    status_text.set("loading... ")
    global planets

    def query():
        # table definitions: https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html#choose
        
        return NasaExoplanetArchive.query_criteria(table="pscomppars", select="pl_name")
    
    exoplanet_data = await asyncio.to_thread(query)
    planets.extend(exoplanet_data["pl_name"].tolist())

    status_text.set("Retrieving " + str(len(planets) - 1) + " planets from PsCompPars (NASA Exoplanet Archive)")

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


## fetching a specific planet
async def fetch_exoplanet(pl_name):
    status_text.set("Retrieved data for " + str(pl_name) + "... ")

    def query():
        return NasaExoplanetArchive.query_object(pl_name, table="pscomppars")
    
    exoplanet_data = await asyncio.to_thread(query)
    dict_data = exoplanet_data[0].as_void() # Converts the row to a dictionary-like void object
    dict_data = dict(zip(exoplanet_data.colnames, dict_data))

    status_text.set("Fetched!")

    return dict_data

def start_exoplanet_fetch(tk_elem, pl_name):
    global exoplanet_ra, exoplanet_dec  # Access global variables
    if pl_name != "<None>":
        tk_elem.configure(state=NORMAL)
        tk_elem.delete('1.0', END)
        tk_elem.insert(INSERT, "\n Fetching... ")
        tk_elem.configure(state=DISABLED)

        info_data = asyncio.run(fetch_exoplanet(pl_name))

        formatted_data = (
            "\n Planet Orbital Period: " + str(info_data["pl_orbper"]) + " days\n"
            " Planet Radius: " + str(info_data["pl_rade"]) + " Earth radii\n"
            " Planet Mass: " + str(info_data["pl_bmasse"]) + " Earth masses\n"
            " Planet Density: " + str(info_data["pl_dens"]) + " g/cm^3\n"
            " Planet Equilibrium Temperature: " + str(info_data["pl_eqt"]) + " K\n"
            " Distance from Earth: " + str(info_data["sy_dist"]) + " parsecs\n"
            " Radius of Host Star: " + str(info_data["st_rad"]) + " solar radii\n"
            " Mass of Host Star: " + str(info_data["st_mass"]) + " solar masses\n"
            " Exoplanet RA: " + str(info_data["ra"]) + "\n"
            " Exoplanet Dec: " + str(info_data["dec"]) + "\n"
        )

        # Store RA and Dec
        exoplanet_ra = math.radians(info_data["ra"])
        exoplanet_dec = math.radians(info_data["dec"])

        tk_elem.configure(state=NORMAL)
        tk_elem.delete('1.0', END)
        tk_elem.insert(INSERT, formatted_data)
        tk_elem.configure(state=DISABLED)
    else:
        tk_elem.configure(state=NORMAL)
        tk_elem.delete('1.0', END)
        tk_elem.configure(state=DISABLED)



exoplanet_name = StringVar()
exoplanet_name.set("[exoplanet name]")

def exoplanet_select(event, tk_elem, tk_elem2):
    selected_index = tk_elem.curselection()

    if selected_index:
        selected_value = tk_elem.get(selected_index)
        exoplanet_name.set(selected_value.strip())

        threading.Thread(target=lambda *args: start_exoplanet_fetch(tk_elem2, selected_value.strip()), daemon=True).start()

# welcome screen
def root_window():
    global root

    root.title("Exosky")
    root.geometry("800x600+100+200")

    root.rowconfigure(1, weight=1)
    root.columnconfigure(1, weight=1)
    root.columnconfigure(2, weight=1)

    ## Top info/button bar
    frame_t = Frame(root, height=40)
    frame_t.grid(row=0, column=1, sticky="EW", columnspan=2, padx=2, pady=3)

    title = Label(frame_t, text="NASA Space Apps Challenge (Exoplanet)", font=("Segoe", 14, "bold"))
    title.pack(side=LEFT, fill=Y)

    credits = Label(frame_t, text=" Lucas Pop, Andrew Wu, James Lian ", relief="groove", width=28, font=("Segoe", 10))
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

    info_box = None

    ep_list.bind("<<ListboxSelect>>", lambda event: exoplanet_select(event, ep_list, info_box))

    threading.Thread(target=lambda *args: start_list_fetch(ep_list), daemon=True).start()

    ## Right panel: description of exoplanet? map?
    frame_r = Frame(root, background="#968ef6")
    frame_r.grid(row=1, column=2, sticky="NSEW")

    spacer = Label(frame_r, font=("Segoe", 6), bg="#968ef6")
    spacer.pack(side=TOP)

    planet_name = Label(frame_r, textvariable=exoplanet_name, font=("Segoe", 14, "bold"), bg="#968ef6", fg="#FFFFFF")
    planet_name.pack(side=TOP, fill=X)

    info_box = scrolledtext.ScrolledText(frame_r, wrap=WORD, width=10, font=("Segoe", 12, "bold"), bg="#968ef6", fg="#FFFFFF", relief=FLAT, state=DISABLED)
    info_box.pack(fill=BOTH, expand=True)

    go_button = Button(frame_r, text=" GO! >> ", relief="groove", width=28, font=("Segoe", 14, "bold"), 
                       command=lambda: threading.Thread(target=lambda: open_pygame_window(exoplanet_ra, exoplanet_dec, exoplanet_name.get()), daemon=True).start())
    go_button.pack(fill=X, side=BOTTOM)

    statusbar = Frame(root)
    statusbar.grid(row=2, column=1, columnspan=2, sticky="NSEW", pady=2)

    status_label = Label(statusbar, textvariable=status_text, font=("Segoe", 10, "italic"))
    status_label.pack()

    root.mainloop()

root_window()
