import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from pathlib import Path
import json
import ipaddress
import os, sys
import subprocess
from subprocess import CREATE_NO_WINDOW

# App configurations
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"
ctk.set_appearance_mode("system")  # default "system", "light", "dark"

def resource_path(relative_path):
    """Retourne le chemin correct, même après compilation avec --onefile"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

window = ctk.CTk()
window.title("DNS Setting App")
window.iconbitmap(resource_path("icon.ico"))
window.resizable(False,False)


# App var

filter_g_var = ctk.IntVar(value=1)
filter_f_var = ctk.IntVar(value=1)
filter_a_var = ctk.IntVar(value=1)
filter_p_var = ctk.IntVar(value=1)
selectedDNS = ctk.StringVar(value = "Automatic (DHCP)")
files_dir = Path.home() / "AppData" / "Roaming" / "DNS Setting App"
files_dir.mkdir(parents=True, exist_ok=True)
file_path = files_dir / "config.ps1"
file_path.write_text("Configuration DNS par défaut 2", encoding="utf-8")

# App logic 
dns_dir = Path(__file__).resolve().parent
dns_dir = dns_dir / "public_dns.json"

with open(dns_dir, "r", encoding="utf-8") as f:
    dns_data = json.load(f)

current_mode = ctk.get_appearance_mode()
offvalue = current_mode
switch_mode = ctk.StringVar(value=offvalue)
if current_mode == "Dark" : 
    onvalue = "light" 
else : 
    onvalue = "Dark"

def changeAppearance(value):
    ctk.set_appearance_mode(value.get())

# parse DNS in json file
def transform_category(category_dict):
    result = {}
    for provider, addrs in category_dict.items():
        # IPv4 : split et tuple
        if addrs[0][0]:
            ipv4 = tuple(addrs[0][0].split(","))
        else:
            ipv4 = ("", "")
        # IPv6 : split et tuple
        if addrs[1][0]:
            ipv6 = tuple(addrs[1][0].split(","))
        else:
            ipv6 = ("", "")
        # Assigner à la clé fournisseur
        result[provider] = [ipv4, ipv6]
    return result

# get DNS by cagetogy
General = transform_category(dns_data["General"])
Family_Safe = transform_category(dns_data["Family_Safe"])
Ad_Blocking = transform_category(dns_data["Ad_Blocking"])
Privacy_Focused = transform_category(dns_data["Privacy_Focused"])
All_DNS = {}
All_DNS.update(General)
All_DNS.update(Family_Safe)
All_DNS.update(Ad_Blocking)
All_DNS.update(Privacy_Focused)
general_dns = list(General.keys())
family_dns = list(Family_Safe.keys())
ad_blocking_dns = list(Ad_Blocking.keys())
privacy_dns = list(Privacy_Focused.keys())
all_dns_provides = []
all_dns_provides = all_dns_provides + general_dns + family_dns + ad_blocking_dns + privacy_dns
all_dns_provides.sort()
all_dns_provides[0] = 'Automatic (DHCP)'
all_dns_provides[1] = 'Manual'
# print(All_DNS["Google Public DNS"][0][0]) 
# global dns_option_menu 
dns_option_menu = all_dns_provides
# get connected interfaces 
def connectedIterfaces():
    # command = 'Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -ExpandProperty Name'
    command = 'Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -ExpandProperty Name | Out-String -Stream'
    resultat = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, encoding='utf-8', errors='ignore', creationflags=CREATE_NO_WINDOW)

    interfaces = [ligne.strip() for ligne in resultat.stdout.splitlines() if ligne.strip()]

    return interfaces
def entriesStates(state):
    primary_dns4_entry.configure(state=state)
    secondary_dns4_entry.configure(state=state)
    primary_dns6_entry.configure(state=state)
    secondary_dns6_entry.configure(state=state)

def verify_dns(d1, d2, d3, d4):
    if all(d == "" for d in [d1, d2, d3, d4]):
        return "empty"
    try:
        for dns in [d1, d2, d3, d4]:
            if dns:
                ipaddress.ip_address(dns)
    except ValueError:
        return "invalid"
    return "OK"
def updateDNSEntries(_):
    select = selectedDNS.get()
    entriesStates("normal")
    if select == "Automatic (DHCP)":
        pass
    elif select =="Manual": 
        primary_dns4_entry.delete(0,ctk.END)
        secondary_dns4_entry.delete(0,ctk.END)
        primary_dns6_entry.delete(0,ctk.END)
        secondary_dns6_entry.delete(0,ctk.END)
        return
    else: 
        try:
            d4a = All_DNS[select][0][0]
            d4b = All_DNS[select][0][1]
            d6a = All_DNS[select][1][0]
            d6b = All_DNS[select][1][1]
        except : pass
    try:
        # delete entries, then insert DNS
        primary_dns4_entry.delete(0,ctk.END)
        secondary_dns4_entry.delete(0,ctk.END)
        primary_dns6_entry.delete(0,ctk.END)
        secondary_dns6_entry.delete(0,ctk.END)
        primary_dns4_entry.insert(0,d4a)
        secondary_dns4_entry.insert(0,d4b)
        primary_dns6_entry.insert(0,d6a)
        secondary_dns6_entry.insert(0,d6b)
    except: pass
    entriesStates("disabled")
    # w = selec_dns_frame.winfo_width()
    # h = selec_dns_frame.winfo_height()
    # print(f"w = {w}; h = {h}")

def filterUpdateOptionMenu():
    # Récupère les états (booléens) des filtres
    g = filter_g_var.get()
    f = filter_f_var.get()
    a = filter_a_var.get()
    p = filter_p_var.get()

    dns_option_menu = []

    # Ajoute les DNS selon les filtres activés
    if g:
        dns_option_menu += general_dns
    if f:
        dns_option_menu += family_dns
    if a:
        dns_option_menu += ad_blocking_dns
    if p:
        dns_option_menu += privacy_dns

    # Si aucun filtre n’est activé, on reste sur auto
    if not any([g, f, a, p]):
        dns_option_menu = []
    # Trie et ajoute "Automatic (DHCP)" au début
    dns_option_menu.sort()
    # update dns list
    dns_option_menu.insert(0, "Automatic (DHCP)")
    dns_option_menu.insert(1, "Manual")
    dns_list_option.configure(values=dns_option_menu)
    updateDNSEntries
def applyDNS():
    d4a = primary_dns4_entry.get()
    d4b = secondary_dns4_entry.get()
    d6a = primary_dns6_entry.get()
    d6b = secondary_dns6_entry.get()
    interface_option = apply_option.get()
    reset_val = dns_list_option.get()
    if interface_option == "All" : interface = interfaces
    else : interface = [interface_option]
    n_inter = len(interface)
    for i in range(n_inter): 
        val = verify_dns(d4a, d4b, d6a, d6b)
        if val =="OK":
            command_dns4 = f'Set-DnsClientServerAddress -InterfaceAlias "{interface[i]}" -ServerAddresses ("{d4a}","{d4b}")'
            command_dns6 = f'Set-DnsClientServerAddress -InterfaceAlias "{interface[i]}" -ServerAddresses ("{d6a}","{d6b}")'
            subprocess.run(["powershell", "-Command", command_dns4], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
            subprocess.run(["powershell", "-Command", command_dns6], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
            if i==n_inter-1: CTkMessagebox(title = "Success",message="DNS settings successfully applied.",icon="check", option_1="OK",font=("",18))
        elif val=="invalid" and reset_val !="Automatic (DHCP)":
            if i==n_inter-1: CTkMessagebox(title="Error", message="Some of the entries are invalid.", icon="cancel",font=("",18))
        elif val == "empty" and reset_val !="Automatic (DHCP)": 
            if i==n_inter-1: CTkMessagebox(title="Error", message="You must provide at least one DNS entry", icon="cancel",font=("",18))
        elif reset_val=="Automatic (DHCP)":
            reset_command = f'Set-DnsClientServerAddress -InterfaceAlias "{interface[i]}" -ResetServerAddresses'
            subprocess.run(["powershell", "-Command", reset_command], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
            if i==n_inter-1: CTkMessagebox(title = "Success",message="DNS settings successfully set to Automatic",icon="check", option_1="OK", font=("",18))

#############################################################
# Main frame & select dns frame & filter frame
interfaces = [i for i in connectedIterfaces()]
interfaces_all = ["All"]+interfaces

main_frame = ctk.CTkFrame(window)
selec_dns_frame = ctk.CTkFrame(main_frame, width=300, height=80)
selec_dns_frame.grid_propagate(False)
# add change appearance 
appearance_but = ctk.CTkSwitch(main_frame,text ="Light/Dark",onvalue=onvalue, offvalue=offvalue, variable=switch_mode, command = lambda: changeAppearance(switch_mode))
appearance_but.grid(row =0, column=0, padx=5, pady=10)
#
main_frame.pack(padx=10, pady=10)
selec_dns_frame.grid(row=0, column=1, padx=10, pady=10)
filter_frame = ctk.CTkFrame(main_frame)
filter_frame.grid(row= 0, column =2, padx=10, pady=10)
# select DNS label
selectDNS_label = ctk.CTkLabel(selec_dns_frame, text="Select a DNS Provider")
selectDNS_label.grid(row=0, column=1, padx = 10, pady = 5, columnspan=2)
# List of DNS in dropdown menu
dns_list_option = ctk.CTkOptionMenu(selec_dns_frame,values = dns_option_menu, variable=selectedDNS, command=updateDNSEntries, width=250, height=30,anchor="c")
dns_list_option.grid_propagate(False)
dns_list_option.grid(row=1, column=1, padx = 10, pady = 5, columnspan=2)
# filter list 
filter_general = ctk.CTkCheckBox(filter_frame, text = "General", variable=filter_g_var, command=filterUpdateOptionMenu)
filter_general.grid(row=0, column = 0, padx=5, pady=5)
filter_family = ctk.CTkCheckBox(filter_frame, text = "Family-Safe", variable=filter_f_var, command=filterUpdateOptionMenu)
filter_family.grid(row=0, column = 1, padx=5, pady=5)
filter_ad = ctk.CTkCheckBox(filter_frame, text = "Ad-Blocking", variable=filter_a_var, command=filterUpdateOptionMenu)
filter_ad.grid(row=1, column = 0, padx=5, pady=5)
filter_privacy = ctk.CTkCheckBox(filter_frame, text = "Privacy-Focused", variable=filter_p_var, command=filterUpdateOptionMenu)
filter_privacy.grid(row=1, column = 1, padx=5, pady=5, columnspan=5)
# DNS 4 and 6 text label
dns4_label = ctk.CTkLabel(main_frame,text="DNS IP v4")
dns6_label = ctk.CTkLabel(main_frame,text="DNS IP v6")
dns4_label.grid(row=2, column=1, padx = 10, pady = 5)
dns6_label.grid(row=2, column=2, padx = 10, pady = 5)
# DNS entries and placement
primary_dns4_entry = ctk.CTkEntry(main_frame)
secondary_dns4_entry = ctk.CTkEntry(main_frame)
primary_dns6_entry = ctk.CTkEntry(main_frame)
secondary_dns6_entry = ctk.CTkEntry(main_frame)
primary_dns4_entry.grid(row=3, column=1, padx = 10, pady = 5)
primary_dns6_entry.grid(row=3, column=2, padx = 10, pady = 5)
secondary_dns4_entry.grid(row=4, column=1, padx = 10, pady = 5)
primary_dns6_entry.grid(row=3, column=2, padx = 10, pady = 5)
secondary_dns6_entry.grid(row=4, column=2, padx = 10, pady = 5)
# DNS entry label
primary_dns_label = ctk.CTkLabel(main_frame, text= "Primary DNS")
secondary_dns_label = ctk.CTkLabel(main_frame, text= "Scondary DNS")
primary_dns_label.grid(row=3, column = 0, padx = 10, pady = 5)
secondary_dns_label.grid(row=4, column = 0, padx = 10, pady = 5)
# Apply button
apply_frame = ctk.CTkFrame(main_frame)
apply_frame.grid(row =5, column=1, padx = 10, pady = 5, columnspan=3)
# interface option and apply
apply_button = ctk.CTkButton(main_frame, text = "Apply DNS", command=applyDNS)
apply_button.grid(row=6, column=1, padx = 10, pady = 5, columnspan=3)
apply_label = ctk.CTkLabel(apply_frame, text="Select an interface")
apply_label.grid(row=0, column=0, padx = 5, pady = 5)
apply_option = ctk.CTkOptionMenu(apply_frame,values=interfaces_all)
apply_option.grid(row=0, column=1, padx = 5, pady = 5)

# default
entriesStates("disabled")
window.mainloop()