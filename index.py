from flask import Flask, render_template_string, request, redirect
from icrawler.builtin import GoogleImageCrawler
from PIL import Image, UnidentifiedImageError
from supabase import create_client, Client
import os
import io
import shutil
import datetime

# Supabase Configuration
SUPABASE_URL = "https://mudecnmfofdtjszomrfw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im51ZGVjbm1mb2ZkdGpzem9tcmZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM1ODMwMTgsImV4cCI6MjA1OTE1OTAxOH0.3DVq_QJACt-7wBK1TZE69o8ycbPAT8xVxWj5KMLrAXk"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


app = Flask(__name__)

# Storage Configuration
STORAGE_BUCKET = '4word'

# HTML Form Template
HTML_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>4Word Puzzle Creator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body class="bg-gray-50 min-h-screen" x-data="{ showSuccess: false }"
      x-init="
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('success') === 'true') {
            showSuccess = true;
            setTimeout(() => showSuccess = false, 3000);
            history.replaceState(null, null, window.location.pathname);
        }
      ">
    <!-- Success Notification -->
    <div x-show="showSuccess" x-transition:enter="transition ease-out duration-300"
         x-transition:enter-start="opacity-0 translate-y-2" 
         x-transition:enter-end="opacity-100 translate-y-0"
         x-transition:leave="transition ease-in duration-200"
         x-transition:leave-start="opacity-100 translate-y-0"
         x-transition:leave-end="opacity-0 translate-y-2"
         class="fixed top-4 right-4 z-50">
        <div class="bg-green-50 border border-green-200 rounded-lg p-4 shadow-lg flex items-center gap-3 w-80">
            <div class="flex-shrink-0">
                <svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
            </div>
            <div>
                <h3 class="text-sm font-medium text-green-800">Berhasil!</h3>
                <p class="mt-1 text-sm text-green-700">Puzzle berhasil dibuat dan tersimpan di database</p>
            </div>
            <button @click="showSuccess = false" class="ml-auto text-green-800 hover:text-green-900">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
        </div>
    </div>

    <!-- Konten Utama -->
    <div class="container mx-auto px-4 py-8">
        <div class="max-w-md mx-auto bg-white rounded-xl shadow-md overflow-hidden p-6">
            <div class="mb-8">
                <h1 class="text-2xl font-bold text-gray-800 mb-2">🎮 4Word Puzzle Creator</h1>
                <p class="text-gray-600">Create image puzzles for your game!</p>
            </div>
            
            <form method="post" class="space-y-6">
                <!-- Keywords Input -->
                <div class="relative">
                    <textarea 
                        name="keywords" 
                        id="keywords"
                        rows="3"
                        class="peer h-24 w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none transition-all"
                        placeholder=" "
                        required
                    ></textarea>
                    <label 
                        for="keywords"
                        class="absolute left-4 -top-2.5 bg-white px-1 text-gray-600 text-sm transition-all
                               peer-placeholder-shown:text-base peer-placeholder-shown:text-gray-400 
                               peer-placeholder-shown:top-2 peer-focus:-top-2.5 peer-focus:text-blue-600 peer-focus:text-sm"
                    >
                        Keywords (comma separated)
                    </label>
                </div>

                <!-- Show Karakter Input -->
                <div class="relative">
                    <input 
                        type="number" 
                        name="show_karakter" 
                        id="show_karakter"
                        class="peer w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none transition-all"
                        placeholder=" "
                        required
                    >
                    <label 
                        for="show_karakter"
                        class="absolute left-4 -top-2.5 bg-white px-1 text-gray-600 text-sm transition-all
                               peer-placeholder-shown:text-base peer-placeholder-shown:text-gray-400 
                               peer-placeholder-shown:top-2 peer-focus:-top-2.5 peer-focus:text-blue-600 peer-focus:text-sm"
                    >
                        Show Karakter
                    </label>
                </div>

                <!-- Submit Button -->
                <div class="flex justify-end">
                    <button 
                        type="submit"
                        class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg
                               transition-colors duration-200 flex items-center gap-2"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clip-rule="evenodd" />
                        </svg>
                        Process Puzzle
                    </button>
                </div>
            </form>
        </div>
        
        <!-- Footer -->
        <div class="mt-8 text-center text-gray-500 text-sm">
            <p>Powered by Flask & Tailwind CSS | © 2025 4Word Puzzle | akuiiki</p>
        </div>
    </div>
</body>
</html>
"""

def compress_to_webp(input_path, output_path, max_size_kb=50):
    try:
        img = Image.open(input_path)
        img = img.convert("RGB")
        quality = 90
        while quality >= 10:
            buffer = io.BytesIO()
            img.save(buffer, format='WEBP', quality=quality)
            size_kb = len(buffer.getvalue()) / 1024
            if size_kb <= max_size_kb:
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return True
            quality -= 10
        return False
    except Exception as e:
        print(f"Error compressing {input_path}: {e}")
        return False

def upload_to_supabase(file_path, keyword):
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        file_name = f"{keyword}_{os.path.basename(file_path)}"
        res = supabase.storage.from_(STORAGE_BUCKET).upload(file_name, file_data)
        return supabase.storage.from_(STORAGE_BUCKET).get_public_url(file_name)
    except Exception as e:
        print(f"Upload error: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keywords = [k.strip() for k in request.form['keywords'].split(',')]
        show_karakter = int(request.form['show_karakter'])
        
        for keyword in keywords:
            temp_dir = os.path.join('temp', keyword)  # Unique folder per keyword
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # Download gambar
                crawler = GoogleImageCrawler(storage={'root_dir': temp_dir})
                crawler.crawl(keyword=keyword, max_num=4)
                
                # Proses gambar yang berhasil di-download
                image_files = os.listdir(temp_dir)
                image_urls = []
                last_valid_url = None
                
                # Process maksimal 4 gambar
                for i in range(4):
                    if i < len(image_files):
                        input_path = os.path.join(temp_dir, image_files[i])
                        output_path = os.path.join(temp_dir, f"{keyword}_{i}.webp")
                        
                        if compress_to_webp(input_path, output_path):
                            url = upload_to_supabase(output_path, keyword)
                            if url:
                                image_urls.append(url)
                                last_valid_url = url  # Simpan URL terakhir yang valid
                            else:
                                image_urls.append(last_valid_url if last_valid_url else '#')  # Fallback
                        else:
                            image_urls.append(last_valid_url if last_valid_url else '#')  # Fallback
                    else:
                        # Jika gambar kurang dari 4, duplikat URL terakhir atau isi dummy
                        image_urls.append(last_valid_url if last_valid_url else '#')
                
                # Pastikan selalu ada 4 URL
                final_urls = image_urls[:4]  # Ambil maksimal 4
                
                # Insert ke database
                response = supabase.table('puzzles').insert({
                    'answer': keyword,
                    'image_url_1': final_urls[0] if final_urls[0] else '#',
                    'image_url_2': final_urls[1] if len(final_urls) > 1 else final_urls[0],
                    'image_url_3': final_urls[2] if len(final_urls) > 2 else final_urls[0],
                    'image_url_4': final_urls[3] if len(final_urls) > 3 else final_urls[0],
                    'created_at': datetime.datetime.now().isoformat(),
                    'show_karakter': show_karakter
                }).execute()
                
                if response.error:
                    print(f"⚠️ Database Error for {keyword}: {response.error.message}")
                else:
                    print(f"✅ Success: {keyword} inserted with {len(final_urls)} images")
                
            except Exception as e:
                print(f"❌ Critical error processing {keyword}: {str(e)}")
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        return redirect('/?success=true')  # Tambahkan query parameter
    
    return render_template_string(HTML_FORM)

if __name__ == '__main__':
    app.run(debug=True)