import requests
import cfscrape
from bs4 import BeautifulSoup
import argparse
import difflib

def search_komik(nama_comic):
    # Ubah nama_comic menjadi lowercase dan replace spasi dengan "_"
    query = nama_comic.lower().replace(' ', '_')

    # Buat URL untuk pencarian
    url = f"https://manganato.com/search/story/{query}"

    # Membuat instance scraper
    scraper = cfscrape.create_scraper()

    try:
        # Menggunakan scraper untuk mendapatkan konten halaman
        response = scraper.get(url).content  
    except Exception as e:
        print(f"Error: {e}")
        return

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

def find_closest_match(comics, nama_comic):
    titles = [comic['title'] for comic in comics]
    close_match = difflib.get_close_matches(nama_comic, titles, n=1, cutoff=0.6)
    if close_match:
        for comic in comics:
            if comic['title'] == close_match[0]:
                return comic
    return None

def main():
    # Membuat parser argumen
    parser = argparse.ArgumentParser(description="Search comic script")
    parser.add_argument("nama_comic", help="The name of the comic to search")

    # Parsing argumen
    args = parser.parse_args()

    # Jalankan fungsi search_komik dengan nama_comic sebagai argumen
    results = search_komik(args.nama_comic)

    # Cari komik yang paling mendekati nama_comic
    closest_comic = find_closest_match(results, args.nama_comic)

    # Print hasil
    if closest_comic:
        print(f"Title: {closest_comic['title']}")
        print(f"Link: {closest_comic['link']}\n")

if __name__ == "__main__":
    main()
