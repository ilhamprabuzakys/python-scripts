import os
import requests
from termcolor import colored
from bs4 import BeautifulSoup
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_fixed
import requests_cache
import time
import difflib

# Set up cache
expire_after = 24 * 60 * 60  # 24 hours
session = requests_cache.CachedSession('manganato_cache', expire_after=expire_after)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def download_image(img_url, img_name, chapter_folder_name, pbar):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    try:
        img_data = session.get(img_url, headers=headers).content
        with open(f'{chapter_folder_name}/{img_name}', 'wb') as handler:
            handler.write(img_data)
        pbar.update(1)
    except Exception as e:
        print(f"Failed to download {img_url}. Error: {str(e)}")
        raise


def valid_image(img_url):
    return img_url is not None and \
           (img_url.endswith(".jpg") or img_url.endswith(".png")) and \
           not img_url.endswith(".gif") and \
           "logo" not in img_url and \
           not img_url.startswith("//static")

def find_closest_match(comics, nama_comic):
    titles = [comic['title'] for comic in comics]
    close_match = difflib.get_close_matches(nama_comic, titles, n=1, cutoff=0.6)
    if close_match:
        for comic in comics:
            if comic['title'] == close_match[0]:
                return comic
    return None

def search_komik(nama_comic):
    print("Starting comic search...")
    # Ubah nama_comic menjadi lowercase dan replace spasi dengan "_"
    query = nama_comic.lower().replace(' ', '_')

    # Buat URL untuk pencarian
    url = f"https://manganato.com/search/story/{query}"

    # Membuat instance scraper
    response = session.get(url).content  

    # Parse HTML page source dengan BeautifulSoup
    soup = BeautifulSoup(response, 'html.parser')

    # Cari semua elemen div dengan class "search-story-item"
    results = soup.find_all('div', {'class': 'search-story-item'})

    # Jika tidak ada hasil, cetak pesan dan return
    if not results:
        print("No results found.")
        return

    # Iterasi hasil dan cetak judul dan URL komik
    comics = []
    for result in results:
        a_tag = result.find('a', {'class': 'item-img bookmark_check'})
        title = a_tag['title']
        link = a_tag['href']
        comics.append({"title": title, "link": link})

    return comics

parser = argparse.ArgumentParser(description='Download chapter komik.')
parser.add_argument('nama_comic', type=str, help='Nama komik untuk diunduh.')
parser.add_argument('start', type=int, help='Mulai dari chapter.')
parser.add_argument('end', nargs='?', type=int, help='Ending chapter. Jika tidak ditentukan, hanya chapter awal yang diunduh.')

args = parser.parse_args()

print("Arguments parsed...")
print(f"Comic Name: {args.nama_comic}, Start Chapter: {args.start}, End Chapter: {args.end if args.end else 'Not provided'}")

print("Searching for comic...")
comics = search_komik(args.nama_comic)

comic = find_closest_match(comics, args.nama_comic)

if comic is None:
    print("No comics found.")
    exit()

print("Comic found. Starting chapter retrieval...")
base_url = comic['link']
response = session.get(base_url)
soup = BeautifulSoup(response.text, 'html.parser')

# Cari semua elemen li dengan class 'a-h'
lis = soup.find_all('li', {'class': 'a-h'})

chapters = []  # Inisialisasi list chapters

# Untuk setiap li, cari semua elemen a dan tambahkan href ke chapters
for li in lis:
    a_tag = li.find('a', {'class': 'chapter-name text-nowrap'})
    chapters.append(a_tag)

print(f"Found {len(chapters)} chapters...")
chapters.reverse()
print("First 10 chapter titles:")
for c in chapters[:10]:
    print(c.text)

filtered_chapters = []
for c in chapters:
    chapter_title_parts = c.text.split(':')
    try:
        chapter_num = int(chapter_title_parts[0].split()[-1])
        if args.start <= chapter_num <= args.end:
            filtered_chapters.append(c)
    except ValueError:
        pass


print(f"Filtered Chapters: {len(filtered_chapters)}")  # Tambahkan baris ini untuk mengetahui jumlah chapter yang akan diunduh

if not filtered_chapters:
    print("No chapters to download. Exiting...")
    exit()

start_time = time.time()

print("Starting comic download...")
if args.start == args.end:
   print(f"\n==============================================================================================================================\nMendownload Chapter {colored(f'{args.start}', 'light_cyan')} \n==============================================================================================================================")
else:
   print(f"\n==============================================================================================================================\nMendownload Chapter {colored(f'{args.start}', 'light_cyan')} sampai {colored(f'{args.end}', 'light_cyan')} \n==============================================================================================================================")

img_dir = os.path.join(os.getcwd(), 'IMG')
os.makedirs(img_dir, exist_ok=True)  # Membuat direktori IMG jika belum ada

for chapter in filtered_chapters:
    chapter_start_time = time.time()
    
    chapter_url = chapter['href']
    url = chapter_url
    response = session.get(chapter_url)
    chapter_name = chapter.text.split()[1]
    print(f"Processing URL: {url}")
    if '.' in chapter_name:
        integer_part, decimal_part = chapter_name.split('.')
        integer_part = integer_part.zfill(3)
        chapter_folder_name = os.path.join(img_dir, f"{integer_part}.{decimal_part}")
    else:
        chapter_folder_name = os.path.join(img_dir, chapter_name.zfill(3))

    if not os.path.exists(chapter_folder_name):
        os.makedirs(chapter_folder_name)

    print(f"\nProcessing chapter {colored(chapter_folder_name, 'light_cyan')}...")
    print(f"\n==============================================================================================================================\nScraping URL: {colored(f'{url}', 'light_yellow')} \n==============================================================================================================================\n")
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Menjadi:
    images = soup.select('div.container-chapter-reader img')

    valid_images = [img for img in images if valid_image(img.get('src'))]
    print(f"Found {len(images)} images, {len(valid_images)} are valid.")
    if len(images) != len(valid_images):
        print("Some images are not valid. URLs:")
        for img in images:
            if img not in valid_images:
                print(img.get('src'))
    pbar = tqdm(total=len(valid_images), ncols=70, bar_format='[{l_bar}{bar} {n_fmt}/{total_fmt}]')  # menggunakan valid_images
    image_count = 1
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for img in valid_images:  # menggunakan valid_images
            img_url = img.get('src')
            print(img_url)
            img_name = f"{image_count:03}.jpg"
            futures.append(executor.submit(download_image, img_url, img_name, chapter_folder_name, pbar))
            image_count += 1
        for future in as_completed(futures):
            future.result()
    pbar.close()


    chapter_end_time = time.time()
    print(f"\n[{colored('Time taken to download chapter:', 'white')} {colored(f'{chapter_end_time - chapter_start_time:.2f} seconds', 'light_yellow')}]")

end_time = time.time()

if args.start == args.end:
    print(f"\n==============================================================================================================================\nAll Pages from chapter {colored(f'{args.start}', 'light_cyan')} has been downloaded..\n==============================================================================================================================")
else:
    print(f"\n==============================================================================================================================\nAll pages from these chapters: [ {colored(f'{args.start} - {args.end}', 'light_cyan')}] has been downloaded..\n==============================================================================================================================")

print(f"\n[{colored('Total time taken to download chapters:', 'white')} {colored(f'{end_time - start_time:.2f}', 'light_yellow')} seconds]")
