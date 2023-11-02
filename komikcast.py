import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import requests_cache
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed
from termcolor import colored
from tqdm import tqdm

# Set up cache
expire_after = 24 * 60 * 60  # 24 hours
session = requests_cache.CachedSession("komik_cache", expire_after=expire_after)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def download_image(img_url, img_name, chapter_folder_name, pbar):
    img_data = session.get(img_url).content
    with open(f"{chapter_folder_name}/{img_name}", "wb") as handler:
        handler.write(img_data)
    pbar.update(1)


def valid_image(img_url):
    return (
        img_url is not None
        and (img_url.endswith(".jpg") or img_url.endswith(".png"))
        and not img_url.endswith(".gif")
        and "kclogo.png" not in img_url
        and not img_url.startswith("//sstatic")
    )


parser = argparse.ArgumentParser(description="Download chapter komik.")
parser.add_argument("slug", type=str, help="URL dasar dari chapter komik.")
parser.add_argument("start", type=int, help="Mulai dari chapter.")
parser.add_argument(
    "end",
    nargs="?",
    type=int,
    help="Ending chapter. Jika tidak ditentukan, hanya chapter awal yang diunduh.",
)

args = parser.parse_args()

slug = args.slug
slug = slug.replace(" ", "-").lower()

nama_comic = args.slug.replace("-", " ").title()

if args.end is None:
    args.end = args.start

base_url = f"https://komikcast.ch/komik/{slug}/"
response = session.get(base_url)
soup = BeautifulSoup(response.text, "html.parser")

chapters = soup.find_all("a", class_="chapter-link-item")
chapters.reverse()

filtered_chapters = []
for c in chapters:
    chapter_title_parts = c.text.split()
    try:
        chapter_num = float(chapter_title_parts[1].split("-")[0])
        if int(args.start) <= int(chapter_num) <= int(args.end):
            filtered_chapters.append(c)
    except ValueError:
        try:
            chapter_num = float(chapter_title_parts[2].split("-")[0])
            if int(args.start) <= int(chapter_num) <= int(args.end):
                filtered_chapters.append(c)
        except (ValueError, IndexError):
            pass

start_time = time.time()

if args.start == args.end:
    print(
        f"\n==============================================================================================================================\nMendownload Chapter {colored(f'{args.start}', 'white')} \n=============================================================================================================================="
    )
else:
    print(
        f"\n==============================================================================================================================\nMendownload Chapter {colored(f'{args.start}', 'grene')} sampai {colored(f'{args.end}', 'grene')} \n=============================================================================================================================="
    )

# Direktori berdasarkan current directory saat skrip dijalankan
# current_dir = os.getcwd()

# # Direktori untuk komik spesifik berdasarkan slug yang diberikan
# comic_dir = os.path.join(current_dir, slug)

# # Direktori untuk menyimpan gambar
# img_dir = os.path.join(comic_dir, "IMG")

# # Buat direktori jika belum ada
# os.makedirs(img_dir, exist_ok=True)

comic_folder_name = nama_comic
img_dir = os.path.join(os.getcwd(), comic_folder_name, "IMG")

print(img_dir)
if not os.path.exists(img_dir):
    os.makedirs(img_dir)

for chapter in filtered_chapters:
    chapter_start_time = time.time()

    chapter_url = chapter["href"]
    url = chapter_url
    chapter_name = chapter.text.split()[1]

    if "." in chapter_name:
        integer_part, decimal_part = chapter_name.split(".")
        integer_part = integer_part.zfill(3)
        chapter_folder_name = os.path.join(img_dir, f"{integer_part}.{decimal_part}")
    else:
        chapter_folder_name = os.path.join(img_dir, chapter_name.zfill(3))

    if not os.path.exists(chapter_folder_name):
        os.makedirs(chapter_folder_name)

    print(f"\nProcessing chapter {colored(chapter_folder_name, 'white')}...")
    print(
        f"\n==============================================================================================================================\nScraping URL: {colored(f'{url}', 'green')} \n==============================================================================================================================\n"
    )
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    images = [img for img in soup.find_all("img") if valid_image(img.get("src"))]
    pbar = tqdm(
        total=len(images), ncols=70, bar_format="[{l_bar}{bar} {n_fmt}/{total_fmt}]"
    )
    image_count = 1
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for img in images:
            img_url = img.get("src")
            img_name = f"{image_count:03}.jpg"
            futures.append(
                executor.submit(
                    download_image, img_url, img_name, chapter_folder_name, pbar
                )
            )
            image_count += 1
        for future in as_completed(futures):
            future.result()
    pbar.close()

    chapter_end_time = time.time()
    print(
        f"\n[{colored('Time taken to download chapter:', 'white')} {colored(f'{chapter_end_time - chapter_start_time:.2f} seconds', 'green')}]"
    )

end_time = time.time()

if args.start == args.end:
    print(
        f"\n==============================================================================================================================\nAll Pages from chapter {colored(f'{args.start}', 'white')} has been downloaded..\n=============================================================================================================================="
    )
else:
    print(
        f"\n==============================================================================================================================\nAll pages from these chapters: [ {colored(f'{args.start} - {args.end}', 'yellow')}] has been downloaded..\n=============================================================================================================================="
    )

print(
    f"\n[{colored('Total time taken to download chapters:', 'white')} {colored(f'{end_time - start_time:.2f}', 'green')} seconds]"
)
