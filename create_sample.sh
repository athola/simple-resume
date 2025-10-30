"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe" \
 --javascript-delay 2000 \
 --dpi 300 \
 -T 0 \
 -B 0 \
 -L 0 \
 -R 0 \
 --disable-smart-shrinking \
 --print-media-type \
 localhost:5000/print.html \
 assets/sample.pdf
