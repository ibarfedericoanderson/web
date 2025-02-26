from flask import Flask, render_template, request, jsonify
import qrcode
from PIL import Image
import io
import cv2

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qrgb', methods=['POST'])
def generate_qrgb():
    red_data = request.form['red_data']
    green_data = request.form['green_data']
    blue_data = request.form['blue_data']
    logo = request.files['logo']

    # Save the logo temporarily
    logo_path = 'static/images/logo.png'
    logo.save(logo_path)

    # Generate QR codes with logos
    img_red = create_qr_with_logo(red_data, "red", logo_path)
    img_green = create_qr_with_logo(green_data, "green", logo_path)
    img_blue = create_qr_with_logo(blue_data, "blue", logo_path)

    # Combine QR codes
    combined_img = combine_qr_images(img_red, img_green, img_blue, logo_path)

    # Save combined image to a bytes buffer
    img_byte_arr = io.BytesIO()
    combined_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return send_file(img_byte_arr, mimetype='image/png', as_attachment=True, download_name='superposed_qr.png')

@app.route('/decode_qr', methods=['POST'])
def decode_qr():
    try:
        file = request.files['qr_file']
        file_path = f"static/images/{file.filename}"
        file.save(file_path)

        data_red, data_green, data_blue = manual_decode_superposed_qr(file_path)

        return jsonify({
            "red": data_red,
            "green": data_green,
            "blue": data_blue
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_qr_with_logo(data, color, logo_path, qr_version=10, box_size=10):
    qr = qrcode.QRCode(
        version=qr_version,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color="white").convert('RGBA')

    logo = Image.open(logo_path).convert("RGBA")
    basewidth = img.size[0] // 4
    wpercent = (basewidth / float(logo.size[0]))
    hsize = int((float(logo.size[1]) * float(wpercent)))
    logo = logo.resize((basewidth, hsize), Image.LANCZOS)

    pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
    img.paste(logo, pos, logo)

    return img

def combine_qr_images(img1, img2, img3, logo_path):
    size = img1.size
    final_image = Image.new("RGBA", size, "black")

    data_red = img1.getdata()
    data_green = img2.getdata()
    data_blue = img3.getdata()

    new_data = []
    for i in range(len(data_red)):
        r1, g1, b1, a1 = data_red[i]
        red_pixel = (r1, g1, b1) != (255, 255, 255)
        r2, g2, b2, a2 = data_green[i]
        green_pixel = (r2, g2, b2) != (255, 255, 255)
        r3, g3, b3, a3 = data_blue[i]
        blue_pixel = (r3, g3, b3) != (255, 255, 255)

        if red_pixel and green_pixel and blue_pixel:
            new_data.append((255, 255, 255, 255))
        elif red_pixel and green_pixel:
            new_data.append((255, 255, 0, 255))
        elif red_pixel and blue_pixel:
            new_data.append((255, 0, 255, 255))
        elif green_pixel and blue_pixel:
            new_data.append((0, 255, 255, 255))
        elif red_pixel:
            new_data.append((255, 0, 0, 255))
        elif green_pixel:
            new_data.append((0, 255, 0, 255))
        elif blue_pixel:
            new_data.append((0, 0, 255, 255))
        else:
            new_data.append((0, 0, 0, 255))

    final_image.putdata(new_data)

    logo = Image.open(logo_path).convert("RGBA")
    basewidth = final_image.size[0] // 4
    wpercent = (basewidth / float(logo.size[0]))
    hsize = int((float(logo.size[1]) * float(wpercent)))
    logo = logo.resize((basewidth, hsize), Image.LANCZOS)

    pos = ((final_image.size[0] - logo.size[0]) // 2, (final_image.size[1] - logo.size[1]) // 2)
    final_image.paste(logo, pos, logo)

    return final_image

def manual_decode_superposed_qr(filename):
    superposed_img = Image.open(filename).convert("RGBA")
    superposed_data = superposed_img.getdata()

    size = superposed_img.size
    red_data = [(255, 255, 255, 255)] * len(superposed_data)
    green_data = [(255, 255, 255, 255)] * len(superposed_data)
    blue_data = [(255, 255, 255, 255)] * len(superposed_data)

    for i, pixel in enumerate(superposed_data):
        r, g, b, a = pixel
        if r != 0:  # Red
            red_data[i] = (0, 0, 0, 255)
        if g != 0:  # Green
            green_data[i] = (0, 0, 0, 255)
        if b != 0:  # Blue
            blue_data[i] = (0, 0, 0, 255)

    red_img = Image.new("RGBA", size)
    green_img = Image.new("RGBA", size)
    blue_img = Image.new("RGBA", size)

    red_img.putdata(red_data)
    green_img.putdata(green_data)
    blue_img.putdata(blue_data)

    red_img.save("static/images/decoded_red.png")
    green_img.save("static/images/decoded_green.png")
    blue_img.save("static/images/decoded_blue.png")

    data_red = read_qr("static/images/decoded_red.png")
    data_green = read_qr("static/images/decoded_green.png")
    data_blue = read_qr("static/images/decoded_blue.png")

    return data_red, data_green, data_blue

def read_qr(filename):
    img = cv2.imread(filename)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return data

if __name__ == '__main__':
    app.run(debug=True)
