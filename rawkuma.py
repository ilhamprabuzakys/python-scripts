import argparse
import difflib
import os
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import requests_cache
from bs4 import BeautifulSoup
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_fixed
from termcolor import colored
from tqdm import tqdm

base_url = "https://rawkuma.com/"
expire_after = 24 * 60 * 60  # 24 hours
# session = requests_cache.CachedSession("rawkuma_cache", expire_after=expire_after)
session = requests.Session()  # Ganti dengan ini untuk debugging


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def download_image(img_url, img_name, chapter_folder_name, pbar):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    try:
        img_data = session.get(img_url, headers=headers).content
        with open(
            os.path.join(chapter_folder_name, f"{img_name}.jpg"), "wb"
        ) as handler:
            handler.write(img_data)
        pbar.update(1)
    except Exception as e:
        print(f"Failed to download {img_url}. Error: {str(e)}")
        raise


def valid_image(img_url):
    return img_url is not None


def convert_webp_to_png(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".webp"):
                file_path = os.path.join(root, file)
                im = Image.open(file_path)
                file_without_extension = os.path.splitext(file_path)[0]
                im.save(
                    f"{file_without_extension}.jpeg", "JPEG"
                )  # Anda bisa mengganti "PNG" dengan "JPEG" untuk format jpeg
                os.remove(file_path)  # Menghapus file .webp setelah dikonversi
    print(f"Converting webp to jpeg  {colored(f'finished', 'light_green')}..")


def clean_filename(filename):
    return "".join(i for i in filename if i not in r'\/:*?"<>|')


def rename_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".jpeg"):
            # Menggunakan split untuk memisahkan nama file berdasarkan karakter '.'
            # Kemudian mengambil bagian pertama (0) yang merupakan nomor halaman
            new_name = filename.split(".")[0] + ".jpeg"
            os.rename(
                os.path.join(directory, filename), os.path.join(directory, new_name)
            )


def download_zip(url, chapter_folder_name):
    print(f"Downloading ZIP from {colored(f'{url}', 'light_cyan')} ")

    response = session.get(url, stream=True)

    # Ambil nama file dari header respons, jika tidak ada gunakan default "chapter.zip"
    content_disposition = response.headers.get("content-disposition")
    if content_disposition:
        filename = re.findall("filename=(.+)", content_disposition)[0]
    else:
        filename = "chapter.zip"

    filename = clean_filename(
        filename
    )  # Bersihkan nama file dari karakter yang tidak valid

    filepath = os.path.join(chapter_folder_name, filename)

    with open(filepath, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    try:
        # Meng-unzip file
        with zipfile.ZipFile(filepath, "r") as zip_ref:
            zip_ref.extractall(chapter_folder_name)
        print(f"Unziping files {colored(f'finished', 'light_green')}..")
        # Konversi semua file webp di folder ini menjadi format baru
        convert_webp_to_png(chapter_folder_name)
        rename_files(chapter_folder_name)
        # Hapus file zip setelah selesai mengunzip dan mengkonversi
        os.remove(filepath)
        print(f"Process {colored(f'finished', 'light_green')} ..")
    except zipfile.BadZipFile:
        print(
            f"File from {colored(url, 'light_green')} is {colored(f'not a valid ZIP file', 'light_red')}. Skipping..."
        )


def find_closest_match(comics, nama_comic):
    titles = [comic["title"] for comic in comics]
    close_match = difflib.get_close_matches(nama_comic, titles, n=1, cutoff=0.6)
    if close_match:
        for comic in comics:
            if comic["title"] == close_match[0]:
                return comic
    return None


def search_komik(nama_comic):
    print("Starting comic search...")
    query = nama_comic.lower().replace(" ", "+")

    url = f"https://rawkuma.com/?s={query}"
    response = session.get(url).content

    soup = BeautifulSoup(response, "html.parser")

    results = soup.find_all("div", {"class": "bsx"})

    if not results:
        print("No results found.")
        return

    comics = []
    for result in results:
        a_tag = result.find("a", {"href": True})
        if a_tag:
            title = a_tag.get("title", "")
            link = a_tag["href"]
            comics.append({"title": title, "link": link})

    return comics


parser = argparse.ArgumentParser(description="Download comic chapters.")
parser.add_argument("nama_comic", type=str, help="Name of the comic to download.")
parser.add_argument("start", type=int, help="Start from this chapter.")
parser.add_argument(
    "end",
    nargs="?",
    type=int,
    help="End at this chapter. If not provided, only the start chapter will be downloaded.",
)

args = parser.parse_args()

if args.end is None:
    args.end = args.start

print("Arguments parsed...")
print(
    f"Comic Name: {args.nama_comic}, Start Chapter: {args.start}, End Chapter: {args.end if args.end else 'Not provided'}"
)

print("Searching for comic...")
comics = search_komik(args.nama_comic)
print(comics)
comic = find_closest_match(comics, args.nama_comic)

if comic is None:
    print("No comics found.")
    exit()

print("Comic found. Starting chapter retrieval...")
comic_url = comic["link"]
response = session.get(comic_url)
soup = BeautifulSoup(response.text, "html.parser")

chapter_list_ul = soup.find("ul", {"class": "clstyle"})
li_items = chapter_list_ul.find_all("li")

chapters = []  # Initialize chapters list

for li in li_items:
    a_tag = li.find("div", {"class": "eph-num"}).find("a")
    title = a_tag.find(
        "span", {"class": "chapternum"}
    ).text.strip()  # text from span within a tag
    link = a_tag["href"]  # get href attribute from a tag
    chapters.append({"title": title, "link": link})

print(f"Found {len(chapters)} chapters...")
chapters.reverse()
print("First 10 chapter titles:")
for c in chapters[:10]:
    print(c["title"])


# filtered_chapters = [c for c in chapters if args.start <= int(c['title'].split()[-1]) <= (args.end if args.end else args.start)]
filtered_chapters = [
    c
    for c in chapters
    if re.search(r"\d+", c["title"])
    and args.start <= int(re.search(r"\d+", c["title"]).group()) <= args.end
]


print(
    f"Filtered Chapters: {len(filtered_chapters)}"
)  # Add this line to know the number of chapters to be downloaded
print(
    f"Content Filtered Chapters: {filtered_chapters}"
)  # Add this line to know the number of chapters to be downloaded

if not filtered_chapters:
    print("No chapters to download. Exiting...")
    exit()

start_time = time.time()

print("Starting comic download...")
if args.start == args.end:
    print(
        f"\n==============================================================================================================================\nDownloading Chapter {colored(f'{args.start}', 'light_cyan')} \n=============================================================================================================================="
    )
else:
    print(
        f"\n==============================================================================================================================\nDownloading Chapter {colored(f'{args.start}', 'light_cyan')} to {colored(f'{args.end}', 'light_cyan')} \n=============================================================================================================================="
    )

# img_dir = os.path.join(os.getcwd(), 'IMG', args.nama_comic.replace(' ', '_'))
comic_folder_name = args.nama_comic.replace("-", " ").title()
img_dir = os.path.join(os.getcwd(), comic_folder_name, "IMG")

print(img_dir)
if not os.path.exists(img_dir):
    os.makedirs(img_dir)


for chapter in filtered_chapters:
    chapter_start_time = time.time()

    chapter_url = chapter["link"]
    url = chapter_url
    response = session.get(chapter_url)
    chapter_name = chapter["title"].split()[1].replace(":", "")
    print(f"Processing URL: {url}")

    if "." in chapter_name:
        integer_part, decimal_part = chapter_name.split(".")
        integer_part = integer_part.zfill(3)
        chapter_folder_name = os.path.join(img_dir, f"{integer_part}.{decimal_part}")
    else:
        chapter_folder_name = os.path.join(img_dir, chapter_name.zfill(3))

    if not os.path.exists(chapter_folder_name):
        os.makedirs(chapter_folder_name)

    print(f"\nProcessing chapter {colored(chapter_folder_name, 'light_cyan')}...")
    print(
        f"\n==============================================================================================================================\nScraping URL: {colored(f'{url}', 'light_yellow')} \n==============================================================================================================================\n"
    )
    response = session.get(url)
    # print(response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    download_link = soup.find("span", {"class": "dlx r"}).find("a")["href"]
    download_zip(download_link, chapter_folder_name)
    # soup = BeautifulSoup(response.text, "html.parser")
    # images = soup.select("img.ts-main-image")
    # # print(images)
    # valid_images = [
    #     img for img in images if valid_image(img.get("data-src") or img.get("src"))
    # ]
    # print(f"Found {len(images)} images, {len(valid_images)} are valid.")
    # if len(images) != len(valid_images):
    #     print("Some images are not valid. URLs:")
    #     for img in images:
    #         if img not in valid_images:
    #             print(img.get("src") or img.get("data-src"))
    # pbar = tqdm(
    #     total=len(valid_images),
    #     ncols=70,
    #     bar_format="[{l_bar}{bar} {n_fmt}/{total_fmt}]",
    # )  # use valid_images
    # image_count = 1
    # with ThreadPoolExecutor(max_workers=4) as executor:
    #     futures = []
    #     for img in valid_images:  # use valid_images
    #         img_url = img.get("data-src") or img.get("src")
    #         print(img_url)
    #         img_name = f"{image_count:03}"
    #         futures.append(
    #             executor.submit(
    #                 download_image, img_url, img_name, chapter_folder_name, pbar
    #             )
    #         )
    #         image_count += 1
    #     for future in as_completed(futures):
    #         future.result()
    # pbar.close()

    chapter_end_time = time.time()
    print(
        f"\n[{colored('Time taken to download chapter:', 'white')} {colored(f'{chapter_end_time - chapter_start_time:.2f} seconds', 'light_yellow')}]"
    )

end_time = time.time()

if args.start == args.end:
    print(
        f"\n==============================================================================================================================\nAll Pages from chapter {colored(f'{args.start}', 'light_cyan')} has been downloaded..\n=============================================================================================================================="
    )
else:
    print(
        f"\n==============================================================================================================================\nAll pages from these chapters: [ {colored(f'{args.start} - {args.end}', 'light_cyan')}] has been downloaded..\n=============================================================================================================================="
    )

print(
    f"\n[{colored('Total time taken to download chapters:', 'white')} {colored(f'{end_time - start_time:.2f}', 'light_yellow')} seconds]"
)
