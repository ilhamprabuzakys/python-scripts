import os
import requests
from termcolor import colored
from bs4 import BeautifulSoup
import time
import argparse

parser = argparse.ArgumentParser(description='Download chapter komik.')
parser.add_argument('base_url', type=str, help='URL dasar dari chapter komik.')
parser.add_argument('start', type=int, help='Mulai dari chapter.')
parser.add_argument('end', nargs='?', type=int, help='Ending chapter. Jika tidak ditentukan, hanya chapter awal yang diunduh.')

args = parser.parse_args()

base_url = args.base_url

# Ending chapter akan sama dengan start chapter jika tidak ditentukan
if args.end is None:
    args.end = args.start

# Mendefinisikan berbagai format gambar
img_formats = ["{num}.jpg", "{num:03}.jpg", "001_{num:03}.jpg", "002_{num:03}.jpg", "00_OPM.jpg"]
image_count = 0

# Loop dari chapter awal sampai akhir
for i in range(args.start, args.end+1):
    print(f"\nProcessing chapter {colored(f'{i}', 'light_cyan')}...")
    # Coba format URL yang berbeda
    # chapter_formats = [str(i), f"{i:02}", f"{i:02}-bahasa-indonesia"]
    chapter_formats = [f"{i:02}-bahasa-indonesia", f"{i:02}", str(i), f"{i:01}-bahasa-indonesia"]
    urls = [f"{base_url}{chapter_str}/" for chapter_str in chapter_formats]
    
    # Buat folder untuk chapter ini jika belum ada
    folder_name = f"{i:03}"  # Ini akan membuat string dengan nomor chapter dengan padding zeros
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    valid_url = None

    # Proses setiap URL
    for url in urls:
        print(f"\n==============================================================================================================================\nScraping URL: {colored(f'{url}', 'light_yellow')} \n==============================================================================================================================\n")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"==============================================================================================================================\n{colored('Failed', 'red')}  to access URL: {colored(f'{url}', 'red')} \n==============================================================================================================================")
            # os.rmdir(folder_name)
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
            print("Downloading image from: " + colored(f"{img_url}", 'white', attrs=["underline"]))
            img_data = requests.get(img_url).content
            img_name = f"{image_count:03}.jpg"
            with open(f'{folder_name}/{img_name}', 'wb') as handler:
                handler.write(img_data)
            image_count += 1

        # Hentikan loop jika gambar telah diunduh
        if image_count > 1:
            valid_url = url
            break
        
    # Setelah mendapatkan valid_url
    if valid_url is not None:
        print(f"\n==============================================================================================================================\nValid URL is: {colored(f'{valid_url}', 'light_yellow')}\n==============================================================================================================================\nSearching if there's a sub-chapters around...\n==============================================================================================================================")
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
                # print(f"Failed to access URL: {sub_chapter_url} \n==============================================================================================================================")
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            # Dapatkan div dengan class "main-reading-area"
            main_reading_area = soup.find('div', class_='main-reading-area')

            # Cari semua elemen img di dalam main_reading_area
            if main_reading_area is not None:
                images = main_reading_area.find_all('img')

            # Pesan bahwa akan mendownload sub chapter
            if images is not None:
                print(f"\n==============================================================================================================================\nScraping URL: {colored(f'{sub_chapter_url}', 'white')} \n==============================================================================================================================\n")
            # Download setiap gambar
            image_count = 1
            for img in images:
                img_url = img.get('src')
                # Cek apakah URL valid dan berakhir dengan ".jpg"
                if img_url is not None and img_url.endswith(".jpg"):
                    print("Downloading image from: " + colored(f"{img_url}", 'white', attrs=["underline"]))
                    img_data = requests.get(img_url).content
                    img_name = f"{image_count:03}.jpg"
                    with open(f'{folder_name}/{img_name}', 'wb') as handler:
                        handler.write(img_data)
                    image_count += 1

            # Hentikan loop jika gambar telah diunduh
            if image_count > 1:
                print(f"\n==============================================================================================================================\nSub-chapter {colored(f'{j}', 'light_cyan')} downloaded successfully\n==============================================================================================================================\n")
    else:
        print("No valid URL found.")

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
                print("Downloading image from: " + colored(f"{img_url}", 'white', attrs=["underline"]))
                img_name = f"{image_count:03}.jpg"
                with open(f'{folder_name}/{img_name}', 'wb') as handler:
                    handler.write(response.content)
                image_count += 1


    # Cek adanya sub-chapter pada URL server jika ada gambar yang diunduh
    # for j in range(1, 10):  # Angka ini bisa Anda sesuaikan
    #     sub_chapter = f"{i:03}-{j}"  # Mengganti titik dengan tanda strip '-'
    #     sub_chapter_dot = f"{i:02}.{j}"  # Dua digit dan tand titik'.'
    #     sub_folder_name = f"{sub_chapter}"  # Buat folder baru untuk sub-chapter
    #     if not os.path.exists(sub_folder_name):
    #         os.makedirs(sub_folder_name)
    #     svr_url = f"https://svr7.imgkc4.my.id/wp-content/img/O/One-Punch-man/{i:03}.{j}/"  # URL asli sub-chapter masih menggunakan titik
    #     for fmt in img_formats:
    #         image_count = 1
    #         while True:
    #             img_url = f"{svr_url}{fmt.format(num=image_count)}"
    #             response = requests.get(img_url)
    #             if response.status_code != 200:
    #                 break
    #             print("Downloading image from: " + colored(f"{img_url}", 'white', attrs=["underline"]))
    #             img_name = f"{image_count:03}.jpg"
    #             with open(f'{sub_folder_name}/{img_name}', 'wb') as handler:
    #                 handler.write(response.content)
    #             image_count += 1
    #         if image_count > 1:
    #             print('==============================================================================================================================')
    #             print(f"Sub chapter: {sub_chapter_dot} successfully downloaded..")
    #             print('==============================================================================================================================')
    #             break
    #     # Hapus folder sub-chapter jika tidak ada gambar yang diunduh
    #     if image_count == 1:
    #         # print(f"Deleting empty folder: {sub_folder_name}")
    #         os.rmdir(sub_folder_name)

    # Tunda sedikit antara setiap permintaan untuk menghindari pembatasan rate
    time.sleep(1)

if args.start == args.end :
    print(f"\n==============================================================================================================================\nAll Pages from chapter {colored(f'{args.start}', 'light_cyan')} has been downloaded..\n==============================================================================================================================")
else :
    print(f"\n==============================================================================================================================\nAll pages from these chapters: [ {colored(f'{args.start} - {args.end}', 'light_cyan')}] has been downloaded..\n==============================================================================================================================")
