#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
mkdir -p tmp-fotos/probe
cd tmp-fotos/probe
curl -sS -A "$UA" -o stocksnap.json -w "stocksnap %{http_code}\n" "https://stocksnap.io/api/search-photos/kayak/relevance/desc/1"
curl -sS -A "$UA" -o stocksnap.html -w "stocksnap-html %{http_code}\n" "https://stocksnap.io/search/kayak"
curl -sS -A "$UA" -o openverse.json -w "openverse %{http_code}\n" "https://api.openverse.org/v1/images/?q=kayak&license=cc0,pdm&page_size=20"
curl -sS -A "$UA" -o pexels.html -w "pexels %{http_code}\n" "https://www.pexels.com/search/kayak/"
curl -sS -A "$UA" -o pixabay.html -w "pixabay %{http_code}\n" "https://pixabay.com/images/search/kayak/"
curl -sS -A "$UA" -o commons.json -w "commons %{http_code}\n" "https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrsearch=kayak%20filetype:bitmap&gsrlimit=20&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=400"
curl -sS -A "$UA" -o unsplash-dl.txt -w "unsplash-download %{http_code} %{redirect_url}\n" "https://unsplash.com/photos/QR68kC8i6C0/download?force=true"
curl -sS -A "$UA" -o unsplash-img.jpg -w "unsplash-cdn %{http_code} %{size_download}\n" "https://images.unsplash.com/photo-1737070264375-fa35f29bbb20?w=400&q=60"
curl -sS -A "$UA" -o kaboom.html -w "kaboompics %{http_code}\n" "https://kaboompics.com/gallery?search=kayak"
curl -sS -A "$UA" -o burst.html -w "burst %{http_code}\n" "https://burst.shopify.com/photos/search?utf8=%E2%9C%93&q=kayak"
ls -la
