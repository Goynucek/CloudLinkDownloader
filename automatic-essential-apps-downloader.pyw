import tkinter as tk
from tkinter import ttk, messagebox
import requests
import os
import json
from urllib.parse import urlparse, parse_qs

class DownloadManager:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("İndirme Yöneticisi")
        self.window.geometry("600x500")

        # Link listesi
        self.links = []
        self.load_links()

        # Arayüz elemanları
        self.create_widgets()

    def create_widgets(self):
        # Link ekleme kısmı
        link_frame = ttk.LabelFrame(self.window, text="Link Ekle", padding=10)
        link_frame.pack(fill="x", padx=10, pady=5)

        self.link_entry = ttk.Entry(link_frame, width=50)
        self.link_entry.pack(side="left", padx=5)

        ttk.Button(link_frame, text="Ekle", command=self.add_link).pack(side="left", padx=5)
        ttk.Button(link_frame, text="Drive Linki Dönüştür", command=self.convert_drive_link).pack(side="left", padx=5)

        # Link listesi
        list_frame = ttk.LabelFrame(self.window, text="Linkler", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview oluşturma
        self.tree = ttk.Treeview(list_frame, columns=("Link", "Durum"), show="headings")
        self.tree.heading("Link", text="Link")
        self.tree.heading("Durum", text="Durum")
        self.tree.pack(fill="both", expand=True)

        # Butonlar
        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(button_frame, text="Seçili Linki Sil", command=self.remove_link).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Durum Değiştir", command=self.toggle_status).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Tümünü İndir", command=self.download_all).pack(side="right", padx=5)

        # İndirme durumu için frame
        self.progress_frame = ttk.LabelFrame(self.window, text="İndirme Durumu", padding=10)
        self.progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(fill="x")

        self.progress_bar = ttk.Progressbar(self.progress_frame, length=300, mode='determinate')
        self.progress_bar.pack(fill="x", pady=5)

    def add_link(self):
        link = self.link_entry.get().strip()
        if link:
            self.links.append({"url": link, "active": True})
            self.tree.insert("", "end", values=(link, "Aktif"))
            self.link_entry.delete(0, "end")
            self.save_links()

    def remove_link(self):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            link = self.tree.item(item)["values"][0]
            self.links = [l for l in self.links if l["url"] != link]
            self.tree.delete(item)
            self.save_links()

    def toggle_status(self):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            link = self.tree.item(item)["values"][0]
            for l in self.links:
                if l["url"] == link:
                    l["active"] = not l["active"]
                    status = "Aktif" if l["active"] else "Pasif"
                    self.tree.item(item, values=(link, status))
            self.save_links()

    def convert_drive_link(self):
        drive_link = self.link_entry.get().strip()
        
        # Google Drive linki kontrolü
        if "drive.google.com" in drive_link:
            try:
                file_id = self.get_file_id(drive_link)
                # Büyük dosyalar için confirm parametresi eklendi
                direct_link = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
                self.link_entry.delete(0, "end")
                self.link_entry.insert(0, direct_link)
                messagebox.showinfo("Başarılı", "Link dönüştürüldü!")
            except:
                messagebox.showerror("Hata", "Geçersiz Google Drive linki!")
        
        # Mediafire linki kontrolü
        elif "mediafire.com" in drive_link:
            try:
                # Mediafire linkini direkt indirme linkine çevir
                if "/file/" in drive_link:
                    direct_link = drive_link.replace("/file/", "/download/")
                    self.link_entry.delete(0, "end")
                    self.link_entry.insert(0, direct_link)
                    messagebox.showinfo("Başarılı", "Link dönüştürüldü!")
                else:
                    messagebox.showerror("Hata", "Geçersiz Mediafire linki!")
            except:
                messagebox.showerror("Hata", "Link dönüştürme hatası!")
        
        # MEGA linki kontrolü
        elif "mega.nz" in drive_link:
            try:
                # MEGA linkini direkt formata çevir
                if "#!" in drive_link:
                    file_id = drive_link.split("#!")[1].split("!")[0]
                    direct_link = f"https://mega.nz/file/{file_id}"
                    self.link_entry.delete(0, "end")
                    self.link_entry.insert(0, direct_link)
                    messagebox.showinfo("Başarılı", "Link dönüştürüldü!")
                else:
                    messagebox.showwarning("Uyarı", "Bu link zaten direkt format!")
            except:
                messagebox.showerror("Hata", "Link dönüştürme hatası!")
        
        else:
            messagebox.showwarning("Uyarı", "Desteklenmeyen link formatı!")

    def get_file_id(self, url):
        if "/file/d/" in url:
            return url.split("/file/d/")[1].split("/")[0]
        elif "id=" in url:
            return parse_qs(urlparse(url).query)['id'][0]
        raise ValueError("Geçersiz Drive linki")

    def download_all(self):
        download_path = os.path.join(os.path.expanduser("~"), "Downloads", "AutoDownloads")
        os.makedirs(download_path, exist_ok=True)

        total_files = len([link for link in self.links if link["active"]])
        current_file = 0

        for link in self.links:
            if link["active"]:
                current_file += 1
                try:
                    self.progress_label.config(text=f"İndiriliyor: {link['url']}")
                    self.progress_bar["value"] = 0
                    self.window.update()

                    response = requests.get(link["url"], stream=True)
                    if response.status_code == 200:
                        original_filename = self.get_filename_from_response(response, link["url"])
                        safe_filename = self.sanitize_filename(original_filename)
                        filepath = os.path.join(download_path, safe_filename)

                        # Dosya boyutunu al
                        total_size = int(response.headers.get('content-length', 0))
                        block_size = 8192
                        downloaded = 0

                        with open(filepath, "wb") as f:
                            for chunk in response.iter_content(chunk_size=block_size):
                                if chunk:
                                    downloaded += len(chunk)
                                    f.write(chunk)
                                    
                                    # İlerleme çubuğunu güncelle
                                    if total_size:
                                        progress = (downloaded / total_size) * 100
                                        self.progress_bar["value"] = progress
                                        self.progress_label.config(
                                            text=f"İndiriliyor ({current_file}/{total_files}): {safe_filename}\n"
                                                 f"İndirilen: {self.format_size(downloaded)} / {self.format_size(total_size)}"
                                        )
                                        self.window.update()

                        # İndirme tamamlandığında
                        self.progress_bar["value"] = 100
                        self.progress_label.config(text=f"Tamamlandı: {safe_filename}")
                        self.window.update()

                except Exception as e:
                    messagebox.showerror("Hata", f"İndirme hatası: {str(e)}")
                    self.progress_label.config(text=f"Hata: {link['url']}")
                    continue

        self.progress_label.config(text="Tüm indirmeler tamamlandı!")
        self.progress_bar["value"] = 0
        messagebox.showinfo("Başarılı", "Aktif linkler indirildi!")

    def format_size(self, size):
        """Dosya boyutunu okunaklı formata çevirir"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def get_filename_from_response(self, response, url):
        # Content-Disposition header'dan dosya adını almaya çalış
        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            import re
            fname = re.findall("filename=(.+)", content_disposition)
            if fname:
                return fname[0].strip('"')
        
        # URL'den dosya adını al
        url_path = urlparse(url).path
        filename = os.path.basename(url_path)
        
        # Eğer dosya adı boşsa veya geçersizse
        if not filename or filename == '':
            # Content-Type'dan uzantıyı belirle
            content_type = response.headers.get('content-type', '').lower()
            ext = self.get_extension_from_content_type(content_type)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"download_{timestamp}{ext}"
        
        return filename

    def get_extension_from_content_type(self, content_type):
        # MIME türüne göre dosya uzantısını belirle
        mime_types = {
            # Dokümanlar
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-powerpoint': '.ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            
            # Arşiv dosyaları
            'application/zip': '.zip',
            'application/x-rar-compressed': '.rar',
            'application/x-7z-compressed': '.7z',
            'application/gzip': '.gz',
            'application/x-tar': '.tar',
            
            # Çalıştırılabilir dosyalar
            'application/x-msdownload': '.exe',
            'application/x-msi': '.msi',
            'application/vnd.microsoft.portable-executable': '.exe',
            'application/x-deb': '.deb',
            'application/x-rpm': '.rpm',
            'application/x-apple-diskimage': '.dmg',
            
            # Resim dosyaları
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'image/tiff': '.tiff',
            'image/svg+xml': '.svg',
            
            # Video dosyaları
            'video/mp4': '.mp4',
            'video/x-msvideo': '.avi',
            'video/quicktime': '.mov',
            'video/x-matroska': '.mkv',
            'video/webm': '.webm',
            'video/x-ms-wmv': '.wmv',
            'video/3gpp': '.3gp',
            
            # Ses dosyaları
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav',
            'audio/aac': '.aac',
            'audio/ogg': '.ogg',
            'audio/midi': '.midi',
            'audio/x-ms-wma': '.wma',
            'audio/webm': '.weba',
            
            # Metin dosyaları
            'text/plain': '.txt',
            'text/html': '.html',
            'text/css': '.css',
            'text/javascript': '.js',
            'text/xml': '.xml',
            'text/csv': '.csv',
            
            # Programlama dilleri
            'text/x-python': '.py',
            'text/x-java': '.java',
            'text/x-c': '.c',
            'text/x-cpp': '.cpp',
            
            # Veri formatları
            'application/json': '.json',
            'application/xml': '.xml',
            'application/yaml': '.yaml',
            'application/sql': '.sql'
        }
        
        # Content-type'ı kontrol et
        for mime, ext in mime_types.items():
            if mime in content_type:
                return ext
            
        # Dosya içeriğini kontrol et (magic numbers)
        def check_file_signature(data):
            signatures = {
                b'%PDF': '.pdf',
                b'PK\x03\x04': '.zip',
                b'Rar!': '.rar',
                b'7z\xBC\xAF': '.7z',
                b'\x89PNG': '.png',
                b'\xFF\xD8\xFF': '.jpg',
                b'GIF8': '.gif',
                b'MZ': '.exe',
                b'\x1F\x8B\x08': '.gz',
                b'ID3': '.mp3',
                b'\x00\x00\x00 ftyp': '.mp4'
            }
            
            for signature, ext in signatures.items():
                if data.startswith(signature):
                    return ext
                
        return '.bin'  # Bilinmeyen türler için

    def sanitize_filename(self, filename):
        # Türkçe karakterleri değiştir
        tr_chars = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        filename = filename.translate(tr_chars)
        
        # Geçersiz karakterleri temizle
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Boşlukları alt çizgi ile değiştir
        filename = filename.replace(' ', '_')
        
        # Çoklu alt çizgileri tekli alt çizgiye dönüştür
        filename = re.sub('_+', '_', filename)
        
        # Uzantıyı küçük harfe çevir
        name, ext = os.path.splitext(filename)
        if ext:
            filename = name + ext.lower()
        
        return filename

    def save_links(self):
        with open("links.json", "w", encoding="utf-8") as f:
            json.dump(self.links, f)

    def load_links(self):
        try:
            with open("links.json", "r", encoding="utf-8") as f:
                self.links = json.load(f)
        except:
            self.links = []

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = DownloadManager()
    app.run()
