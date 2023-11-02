import os
import argparse
import textwrap

# Mendefinisikan argumen parser
parser = argparse.ArgumentParser(description='Check for missing chapters.')
parser.add_argument('dir_path', type=str, help='The directory path where the chapters are located.')

args = parser.parse_args()

# Mendaftar semua subdirektori dalam direktori yang diberikan
chapter_paths = [os.path.join(args.dir_path, name) for name in os.listdir(args.dir_path) if os.path.isdir(os.path.join(args.dir_path, name))]

# Mendapatkan nomor chapter dari setiap direktori
chapter_numbers = []
for path in chapter_paths:
    base_name = os.path.basename(path)
    if base_name != 'PDF' and '-' not in base_name:
        chapter_numbers.append(int(base_name))

# Mengecek setiap angka dari 1 sampai chapter terakhir
missing_chapters = []
for i in range(1, max(chapter_numbers)+1):
    # Jika angka tersebut tidak ada dalam chapter_numbers, maka itu adalah chapter yang hilang
    if i not in chapter_numbers:
        missing_chapters.append(f"Chapter {i:03}")

# Convert list of missing chapters into a string and print it with 6 columns
missing_chapters_str = '  '.join(missing_chapters)
print("\n".join(textwrap.wrap(missing_chapters_str, width=90)))  # Set the width as you need
