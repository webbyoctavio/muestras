#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
cd /tmp
curl -sS -A "$UA" -c jar.txt -o page.html -w "page %{http_code}\n" "https://stocksnap.io/photo/vacation-summer-ILFQRPDLB3"
grep -oE 'href="[^"]*download[^"]*"' page.html | head -5
grep -oE 'https://cdn\.stocksnap\.io/[^"]+' page.html | sort -u | head -8
curl -sS -A "$UA" -b jar.txt -e "https://stocksnap.io/photo/vacation-summer-ILFQRPDLB3" -o dl.bin -D hdr.txt -w "download %{http_code} %{size_download} %{content_type} %{redirect_url}\n" "https://stocksnap.io/download-photo/ILFQRPDLB3"
head -20 hdr.txt
file dl.bin; head -c 300 dl.bin | tr -d '\000' | head -5; echo
curl -sS -A "$UA" -o /dev/null -w "cdn-1920 %{http_code} %{size_download}\n" "https://cdn.stocksnap.io/img-thumbs/1920w/vacation-summer_ILFQRPDLB3.jpg"
curl -sS -A "$UA" -o /dev/null -w "cdn-1280 %{http_code} %{size_download}\n" "https://cdn.stocksnap.io/img-thumbs/1280w/vacation-summer_ILFQRPDLB3.jpg"
curl -sS -A "$UA" -o /dev/null -w "cdn-w1920 %{http_code} %{size_download}\n" "https://cdn.stocksnap.io/img-thumbs/w1920/vacation-summer_ILFQRPDLB3.jpg"
