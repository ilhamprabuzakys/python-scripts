import argparse
import glob
import logging
import math
import os
from os.path import basename, isdir, join, splitext

# Inisialisasi logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Membuat parser argumen
parser = argparse.ArgumentParser(description="Convert comic directories to HTML.")
parser.add_argument(
    "target_dirs",
    nargs="*",
    default=[os.getcwd()],
    help="Target directories to be converted.",
)
args = parser.parse_args()


def str_to_float(s):
    while s:
        try:
            return float(s)
        except ValueError:
            s = s[:-1]
    return 0  # Mengembalikan 0 jika tidak ada angka dalam string


def process_directory(target_dir):
    for target_dir in args.target_dirs:
        root_dir = join(target_dir, "IMG")  # Menggunakan direktori target dari argumen

        if not os.path.isdir(
            root_dir
        ):  # Jika sub-direktori 'IMG' tidak ada, lanjutkan ke direktori target berikutnya
            continue

        # List direktori yang akan dikecualikan
        excluded_dirs = ["PDF", "HTML", "IMG"]

        dirs = [
            f
            for f in os.listdir(root_dir)
            if isdir(join(root_dir, f)) and f not in excluded_dirs
        ]  # Dapatkan semua sub-direktori kecuali yang ada di 'excluded_dirs'
        # dirs.sort(key=lambda x: math.floor(str_to_float(x.split('-')[0])))
        dirs.sort()

        html_dir = join(target_dir, "HTML")
        os.makedirs(html_dir, exist_ok=True)  # Buat direktori HTML jika belum ada

        for i, dir in enumerate(dirs):
            # Mengambil nama direktori induk dari root_dir
            parent_dir = os.path.split(target_dir.rstrip("/"))[-1]
            parent_dir_title = parent_dir.replace(
                "-", " "
            ).title()  # Ganti '-' dengan ' ' dan awali setiap kata dengan huruf kapital
            if len(dir) > 2 and dir.startswith(
                "0"
            ):  # Jika panjang string lebih dari 2 dan dimulai dengan '0'
                dir_title = dir[1:]  # Hapus karakter pertama (yaitu '0')
            else:
                dir_title = dir
            title = f"{parent_dir_title} Chapter {dir}"

            # Buat file HTML untuk setiap direktori
            with open(join(html_dir, f"{dir}.html"), "w") as file:
                # Rest of your code...
                file.write(
                    f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{title}</title>
                    <link rel="shortcut icon" href="/images/kclogo.png" type="image/x-icon">
                    <!-- Bootstrap -->
                    <link rel="stylesheet" href="/assets/bootstrap/bootstrap.min.css">
                    <!-- Jquery -->
                    <script src="/assets/jquery/jquery.min.js"></script>
                    <!-- Select2 -->
                    <link href="/assets/select2/select2.min.css" rel="stylesheet" />
                    <!-- Select2 Theme -->
                    <link href="/assets/select2/select2-bootstrap-5-theme.min.css" rel="stylesheet" />
                    <style>
                        img {{
                            width: 100%;
                            object-fit: contain;
                            margin-top: 0;
                            margin-bottom: 0;
                        }}
                        body {{ 
                            background-color: #16151D;
                        }}
                        
                        .container#wrapper {{ 
                            max-width: 950px !important;
                        }}

                        #flying-arrow {{ 
                            position: fixed;
                            top: 14%;
                            left: 63%;
                        }}
                        
                        #flying-arrow a {{ 
                            border-radius: 50%;
                            font-weight: bold;
                            font-size: 16px;
                        }}

                        #flying-select {{ 
                            position: fixed;
                            top: 6%;
                            left: 84.7%;
                        }}

                        #flying-select select#flying-select-input {{ 
                            width: 13%;
                        }}
                    </style>
                </head>
                <body>
                    <center>
                    <div class="container" id="wrapper">
                    <div class="row justify-content-center mt-5">
                        <div class="col-10 text-center">
                            <h3 class="text-white">{ title }</h3>
                        </div>
                    </div>
                """
                )

                file.write(
                    f"""
                    <div class="row">
                        <div class="col-4 d-flex justify-content-end gap-2" id="flying-arrow">
                        """
                )

                if i > 0:  # Arrow Previous
                    file.write(
                        f"""
                                <a href="{dirs[i-1]}.html" class="btn btn-primary px-3">&lt;</a>
                            """
                    )

                if i < len(dirs) - 1:  # Arrow Next
                    file.write(
                        f"""
                            <a href="{dirs[i+1]}.html" class="btn btn-primary px-3">&gt;</a>
                            """
                    )

                file.write(
                    f"""
                        </div>
                    </div>
                        """
                )

                file.write(
                    f"""
                    <div class="row">
                        <div id="flying-select">
                                <select onchange="window.location.href=this.value+'.html'" class="form-select" id="flying-select-input">
                                <option value="">Select Chapter</option>
                        """
                )
                html_files = glob.glob(
                    join(html_dir, "*.html")
                )  # Dapatkan semua file HTML di direktori HTML setelah semua file HTML telah dibuat
                for html_file in sorted(html_files):
                    file_name = splitext(basename(html_file))[0]
                    selected = " selected" if file_name == dir else ""
                    file.write(
                        f"""
                                <option value="{file_name}"{selected}>Chapter {file_name}</option>
                                """
                    )
                file.write(
                    """
                                </select>
                        </div>
                    </div>
                """
                )

                file.write(
                    f""" 
                    <div class="row justify-content-between my-5">
                        <div class="col-5">
                            <select onchange="window.location.href=this.value+'.html'" class="form-select">
                                <option value="">Select Chapter</option>
                                """
                )
                for html_file in sorted(html_files):
                    file_name = splitext(basename(html_file))[0]
                    selected = " selected" if file_name == dir else ""
                    file.write(
                        f"""
                                <option value="{file_name}"{selected}>Chapter {file_name}</option>
                                """
                    )
                file.write(
                    """
                            </select>
                        </div>
                """
                )

                file.write(
                    f"""
                        <div class="col-7 d-flex justify-content-end gap-4">
                        """
                )
                # Tambahkan tombol previous dan next
                if (
                    i > 0
                ):  # Jika ini bukan direktori pertama, tambahkan link ke direktori sebelumnya
                    file.write(
                        f"""
                                <a href="{dirs[i-1]}.html" class="btn btn-primary px-2">Previous Chapter</a>
                            """
                    )

                if (
                    i < len(dirs) - 1
                ):  # Jika ini bukan direktori terakhir, tambahkan link ke direktori berikutnya
                    file.write(
                        f"""
                            <a href="{dirs[i+1]}.html" class="btn btn-primary px-2">Next Chapter</a>
                            """
                    )

                file.write(
                    f"""
                        </div>
                    </div>
                """
                )

                file.write(
                    f"""
                    <div class="row justify-content-center">
                """
                )

                # Dapatkan semua file dalam direktori dan urutkan berdasarkan nama
                images = sorted(os.listdir(join(root_dir, dir)))
                for img in images:
                    if img.endswith(".jpg") or img.endswith(
                        ".png"
                    ):  # Hanya tambahkan file gambar
                        img_src = f"../IMG/{dir}/{img}"
                        file.write(
                            f"""
                            <img src="{img_src}" alt="{img}">
                        """
                        )

                file.write(
                    f"""
                    </div>"""
                )

                file.write(
                    f""" 
                    <div class="row justify-content-between my-5">
                        <div class="col-5">
                            <select onchange="window.location.href=this.value+'.html'" class="form-select">
                                <option value="">Select Chapter</option>
                                """
                )
                for html_file in sorted(html_files):
                    file_name = splitext(basename(html_file))[0]
                    selected = " selected" if file_name == dir else ""
                    file.write(
                        f"""
                                <option value="{file_name}"{selected}>Chapter {file_name}</option>
                                """
                    )
                file.write(
                    """
                            </select>
                        </div>
                """
                )

                file.write(
                    f"""
                        <div class="col-7 d-flex justify-content-end gap-4">
                        """
                )
                # Tambahkan tombol previous dan next
                if (
                    i > 0
                ):  # Jika ini bukan direktori pertama, tambahkan link ke direktori sebelumnya
                    file.write(
                        f"""
                                <a href="{dirs[i-1]}.html" class="btn btn-primary px-2">Previous Chapter</a>
                            """
                    )

                if (
                    i < len(dirs) - 1
                ):  # Jika ini bukan direktori terakhir, tambahkan link ke direktori berikutnya
                    file.write(
                        f"""
                            <a href="{dirs[i+1]}.html" class="btn btn-primary px-2">Next Chapter</a>
                            """
                    )

                file.write(
                    f"""
                        </div>
                    </div>
                    </center>
                """
                )

                file.write(
                    f"""
                <script>
                    $(document).ready(function() {{
                        $('.form-select').select2({{ 
                        theme: 'bootstrap-5'
                        }});
                    }});
                </script>
                """
                )

                file.write(
                    f"""
                    
                    <script src="/assets/select2/select2.min.js"></script>
                </body>
                </html>                   
                """
                )
    pass


# Berjalan melalui setiap direktori argumen
# for target in args.target_dirs:
#     logging.info(f"Memeriksa direktori: {target}")
#     img_dir = join(target, "IMG")
#     if isdir(img_dir):
#         logging.info(f"Menemukan direktori IMG di: {target}. Memproses...")
#         process_directory(target)
#     else:
#         logging.warning(f"Direktori IMG tidak ditemukan di: {target}")


def explore_and_process(directory):
    logging.info(f"Memeriksa direktori: {directory}")
    img_dir = join(directory, "IMG")

    if isdir(img_dir):
        logging.info(f"Menemukan direktori IMG di: {directory}. Memproses...")
        process_directory(directory)
        return  # Menghentikan crawling ketika menemukan direktori IMG

    if isdir(directory):  # Tambahkan pengecekan ini
        for subdir in os.listdir(directory):
            full_path = join(directory, subdir)
            if isdir(full_path):
                explore_and_process(full_path)


for target in args.target_dirs:
    if isdir(target):
        explore_and_process(target)
