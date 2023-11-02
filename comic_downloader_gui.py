import os
import requests
from termcolor import colored
from bs4 import BeautifulSoup
import time
import argparse
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import filedialog
import re

def redirector(inputStr):
    textbox.insert(tk.INSERT, inputStr)

def run_script(slug, start, end, save_dir):
    slug = slug.replace(" ", "-").lower()  # Konversi slug ke format yang diinginkan
    # Inisialisasi URL
    base_url = f"https://komikcast.io/chapter/{slug}-chapter-"
    # Jika end adalah None, atur menjadi sama dengan start
    end = end if end is not None else start

    # Tambahkan ini untuk mengubah direktori kerja ke direktori yang dipilih
    os.chdir(save_dir)

    # Selanjutnya adalah kode skrip Anda yang tidak diubah...
    # Mendefinisikan berbagai format gambar
    img_formats = ["{num}.jpg", "{num:03}.jpg", "001_{num:03}.jpg", "002_{num:03}.jpg", "00_OPM.jpg"]
    image_count = 0

    # Loop dari chapter awal sampai akhir
    for i in range(start, end+1):
        print_and_log(f"\nProcessing chapter {colored(f'{i}', 'blue')}...")
        # Coba format URL yang berbeda
        chapter_formats = [f"{i:02}-bahasa-indonesia", f"{i:02}", f"{str(i)}," f"{i:01}-bahasa-indonesia"]
        urls = [f"{base_url}{chapter_str}/" for chapter_str in chapter_formats]
        
        # Buat folder untuk chapter ini jika belum ada
        folder_name = f"{i:03}"  # Ini akan membuat string dengan nomor chapter dengan padding zeros
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        valid_url = None

        # Proses setiap URL
        for url in urls:
            print_and_log(f"\n==============================================================================================================================\nScraping URL: {f'{url}'} \n==============================================================================================================================\n")
            response = requests.get(url)
            if response.status_code != 200:
                print_and_log(f"==============================================================================================================================\n{colored('Failed', 'red')}  to access URL: {colored(f'{url}', 'red')} \n==============================================================================================================================")
                continue
            # Buat folder untuk chapter ini jika belum ada
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            soup = BeautifulSoup(response.text, 'html.parser')
            # Dapatkan div dengan class "main-reading-area"
            main_reading_area = soup.find('div', class_='main-reading-area')

            # Cari semua elemen img di dalam main_reading_area
            if main_reading_area is not None:
                images = main_reading_area.find_all('img')
            # Download setiap gambar
            image_count = 1
            for img in images:
                img_url = img.get('src')
                # Cek apakah URL valid dan berakhir dengan ".jpg"
                print_and_log("Downloading image from: " + f"{colored(f'{img_url}', 'green')}")
                img_data = requests.get(img_url).content
                img_name = f"{image_count:03}.jpg"
                with open(f'{folder_name}/{img_name}', 'wb') as handler:
                    handler.write(img_data)
                image_count += 1

            # Hentikan loop jika gambar telah diunduh
            if image_count > 1:
                valid_url = url
                break
            
        # Sisanya adalah kode skrip Anda yang tidak diubah...
        # Sisipkan seluruh kode Anda di sini
         # Setelah mendapatkan valid_url
        if valid_url is not None:
            print_and_log(f"\n==============================================================================================================================\nValid URL is: {colored(f'{valid_url}', 'green')}\n==============================================================================================================================\nSearching if there's a sub-chapters around...\n==============================================================================================================================")
            for j in range(1, 10):  # Angka ini bisa Anda sesuaikan
                # Mengganti '/' terakhir dengan '-' dan menambahkan sub-chapter dan '-bahasa-indonesia/' jika valid_url mengandung "-bahasa-indonesia"
                # sub_chapter_suffix = "-bahasa-indonesia/" if "-bahasa-indonesia/" in valid_url else "/"
                # sub_chapter_url = f"{valid_url[:-1]}-{j}{sub_chapter_suffix}"
                # Cek apakah URL valid berakhir dengan "-bahasa-indonesia/"
                if valid_url.endswith("-bahasa-indonesia/"):
                    # Mengganti '-bahasa-indonesia/' terakhir dengan '-1-bahasa-indonesia/'
                    sub_chapter_url = valid_url.replace("-bahasa-indonesia/", f"-{j}-bahasa-indonesia/")
                else:
                    # Jika URL valid tidak berakhir dengan '-bahasa-indonesia/', cukup tambahkan '-1/' di akhir
                    sub_chapter_url = f"{valid_url[:-1]}-{j}/"
                response = requests.get(sub_chapter_url)
                if response.status_code != 200:
                    # print_and_log(f"Failed to access URL: {sub_chapter_url} \n==============================================================================================================================")
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                # Dapatkan div dengan class "main-reading-area"
                main_reading_area = soup.find('div', class_='main-reading-area')

                # Cari semua elemen img di dalam main_reading_area
                if main_reading_area is not None:
                    images = main_reading_area.find_all('img')

                # Pesan bahwa akan mendownload sub chapter
                if images is not None:
                    print_and_log(f"\n==============================================================================================================================\nScraping URL: {sub_chapter_url} \n==============================================================================================================================\n")
                # Download setiap gambar
                image_count = 1
                for img in images:
                    img_url = img.get('src')
                    # Cek apakah URL valid dan berakhir dengan ".jpg"
                    if img_url is not None and img_url.endswith(".jpg"):
                        print_and_log("Downloading image from: " + f"{colored(f'{img_url}', 'green')}")
                        img_data = requests.get(img_url).content
                        img_name = f"{image_count:03}.jpg"
                        with open(f'{folder_name}/{img_name}', 'wb') as handler:
                            handler.write(img_data)
                        image_count += 1

                # Hentikan loop jika gambar telah diunduh
                if image_count > 1:
                    print_and_log(f"\n==============================================================================================================================\nSub-chapter {j} downloaded successfully\n==============================================================================================================================\n")
        else:
            print_and_log("No valid URL found.")

        # Jika tidak ada gambar yang diunduh, coba download langsung dari server svr
        if image_count == 1:
            svr_url = f"https://svr7.imgkc4.my.id/wp-content/img/O/One-Punch-man/{i:03}/"
            for fmt in img_formats:
                image_count = 1
                for num in range(1, 999):  # Ambil angka besar seperti 999, asumsi tidak akan ada chapter dengan lebih dari 999 
                    img_url = f"{svr_url}{fmt.format(num=num)}"
                    response = requests.get(img_url)
                    if response.status_code != 200:
                        break  # Jika mendapatkan respon selain 200, berhenti mengunduh gambar untuk format ini
                    print_and_log("Downloading image from: " + f"{colored(f'{img_url}', 'green')}")
                    img_name = f"{image_count:03}.jpg"
                    with open(f'{folder_name}/{img_name}', 'wb') as handler:
                        handler.write(response.content)
                    image_count += 1
        time.sleep(1)

        if start == end:
            print_and_log(f"\n==============================================================================================================================\nAll Pages from chapter f{start} has been downloaded..\n==============================================================================================================================")
        else :
            print_and_log(f"\n==============================================================================================================================\nAll pages from these chapters: [ {start} - {end}] has been downloaded..\n==============================================================================================================================")


# GUI dengan Tkinter
def validate_and_run_script():
    base_url = e1.get()
    start_chapter = e2.get()
    end_chapter = e3.get()
    save_dir = e4.get()
    
    if not base_url or not start_chapter or not save_dir:
        messagebox.showerror("Error", "Slug Komik, chapter awal, dan lokasi penyimpanan harus diisi.")
        return

    if not start_chapter.isdigit() or (end_chapter and not end_chapter.isdigit()):
        messagebox.showerror("Error", "Chapter awal dan akhir harus berupa angka.")
        return

    run_script(base_url, int(start_chapter), int(end_chapter) if end_chapter else None, save_dir)
    messagebox.showinfo("Info", "Proses download komik telah selesai.")

def select_directory():
    dir_selected = filedialog.askdirectory()
    save_dir.set(dir_selected)  # Set nilai save_dir menjadi direktori yang dipilih

master = tk.Tk()
master.geometry("900x600")  # Set window size

# Variabel tkinter untuk menyimpan direktori yang dipilih
save_dir = tk.StringVar()

tk.Label(master, text="Slug Komik:").grid(row=0)
tk.Label(master, text="Chapter Awal:").grid(row=1)
tk.Label(master, text="Chapter Akhir (Opsional):").grid(row=2)
tk.Label(master, text="Lokasi Penyimpanan:").grid(row=3)

e1 = tk.Entry(master)
e2 = tk.Entry(master)
e3 = tk.Entry(master)
e4 = tk.Entry(master, textvariable=save_dir)  # Field baru untuk lokasi penyimpanan

e1.grid(row=0, column=1)
e2.grid(row=1, column=1)
e3.grid(row=2, column=1)
e4.grid(row=3, column=1)

textbox = scrolledtext.ScrolledText(master, width=100, height=20)
textbox.grid(column=0, row=5, columnspan=2)
# Mendefinisikan warna teks untuk setiap tag
textbox.tag_config("red", foreground="red")
textbox.tag_config("green", foreground="green")
textbox.tag_config("yellow", foreground="yellow")
textbox.tag_config("blue", foreground="blue")
textbox.tag_config("magenta", foreground="magenta")
textbox.tag_config("cyan", foreground="cyan")
textbox.tag_config("white", foreground="white")
textbox.tag_config("light_cyan", foreground="#88ffff")  # RGB color code for light cyan
textbox.tag_config("light_yellow", foreground="#ffff88")  # RGB color code for light yellow


def print_and_log(message):
    print(message)  # print ke stdout
    
    # Ekstrak kode warna dari pesan
    color_code = re.search("\033\[\d+m", message)
    if color_code:
        # Konversi kode warna ANSI ke nama warna Tkinter
        color = {
            "\033[31m": "red",               # merah
            "\033[32m": "green",             # hijau
            "\033[33m": "yellow",            # kuning
            "\033[34m": "blue",              # biru
            "\033[35m": "magenta",           # magenta
            "\033[36m": "cyan",              # cyan
            "\033[37m": "white",             # putih
            "\033[96m": "light cyan",        # light_cyan
            "\033[93m": "light yellow"       # light_yellow
        }.get(color_code.group(), "black")

        
        # Hapus kode warna dari pesan
        message = re.sub("\033\[\d+m", "", message)
        
        # Tambahkan pesan ke GUI dengan warna yang sesuai
        textbox.insert(tk.END, message + '\n', color)
    else:
        # Tambahkan pesan ke GUI tanpa warna
        textbox.insert(tk.END, message + '\n')
    
    textbox.see(tk.END)  # scroll ke bawah jika diperlukan
    master.update_idletasks()  # update GUI

tk.Button(master, text='Mulai', command=validate_and_run_script).grid(row=4, column=1, pady=4)
tk.Button(master, text='Pilih Lokasi Penyimpanan', command=select_directory).grid(row=4, column=0, pady=4)  # Tombol baru untuk memilih direktori

sys.stdout.write = redirector

tk.mainloop()
