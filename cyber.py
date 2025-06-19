# Secure Steganography with Streamlit (LSB + Encryption & Image-in-Image) - Final Version

import streamlit as st
import cv2
import numpy as np
from cryptography.fernet import Fernet
from PIL import Image

st.set_page_config(page_title="Secure Steganography", layout="centered")
st.title("🔐 Secure Steganography - Hide Text or Image in Image")

# Key generator and handler
if "fernet_key" not in st.session_state:
    st.session_state.fernet_key = Fernet.generate_key()
cipher = Fernet(st.session_state.fernet_key)

# Choose mode
mode = st.radio("Select Steganography Mode", ["Hide Text in Image", "Hide Image in Image"])
st.markdown("---")

# Common: Upload cover image
st.subheader("🖼️ Upload Cover Image")
cover_file = st.file_uploader("Choose a PNG or JPG image", type=["png", "jpg", "jpeg"], key="cover")

if mode == "Hide Text in Image":
    message = st.text_area("✍️ Enter Secret Message to Hide")
    if cover_file and message and st.button("🔒 Encrypt & Embed Text"):
        encrypted_message = cipher.encrypt(message.encode())
        binary_data = ''.join(format(byte, '08b') for byte in encrypted_message)

        cover_file.seek(0)
        file_bytes = np.asarray(bytearray(cover_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if image is None:
            st.error("❌ Failed to load image. Please upload a valid image.")
        else:
            img_copy = image.copy()
            height, width, _ = img_copy.shape
            idx = 0
            for row in range(height):
                for col in range(width):
                    for channel in range(3):
                        if idx < len(binary_data):
                            bit_val = int(binary_data[idx])
                            pixel_val = img_copy[row, col, channel]
                            img_copy[row, col, channel] = (int(pixel_val) & 0xFE) | bit_val
                            idx += 1

            if idx < len(binary_data):
                st.error("❌ Image too small to hold the message!")
            else:
                cv2.imwrite("stego_image.png", img_copy)
                st.image("stego_image.png", caption="🔍 Stego Image")
                with open("stego_image.png", "rb") as f:
                    st.download_button("📥 Download Stego Image", f, file_name="stego_image.png")
                st.code(st.session_state.fernet_key.decode(), language='text')
                st.success("✅ Message hidden successfully!")

    st.markdown("---")
    st.subheader("🔓 Extract & Decrypt Text")
    stego_file = st.file_uploader("📂 Upload Stego Image to Decode", type=["png", "jpg"], key="stego_text")
    decryption_key = st.text_input("🔑 Enter Decryption Key")
    msg_length = st.number_input("📏 Approximate Message Length (in characters)", min_value=1, max_value=500, value=50)

    if stego_file and decryption_key and st.button("🧪 Extract Message"):
        stego_file.seek(0)
        file_bytes = np.asarray(bytearray(stego_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img is None:
            st.error("❌ Failed to load stego image.")
        else:
            bit_len = msg_length * 8
            bits = []
            idx = 0
            height, width, _ = img.shape
            for row in range(height):
                for col in range(width):
                    for channel in range(3):
                        if idx < bit_len:
                            bits.append(str(img[row, col, channel] & 1))
                            idx += 1
            binary_str = ''.join(bits)
            bytes_data = bytes([int(binary_str[i:i+8], 2) for i in range(0, len(binary_str), 8)])

            try:
                decrypted = Fernet(decryption_key.encode()).decrypt(bytes_data).decode()
                st.success("🔓 Message Extracted Successfully!")
                st.code(decrypted, language='text')
            except Exception as e:
                st.error("❌ Failed to decrypt. Please check the key or message length.")

elif mode == "Hide Image in Image":
    st.subheader("🖼️ Upload Image to Hide")
    secret_file = st.file_uploader("Upload Image to Hide (secret image)", type=["png", "jpg"], key="secret")

    if cover_file and secret_file and st.button("🖼️ Embed Image"):
        cover_file.seek(0)
        secret_file.seek(0)
        cover = Image.open(cover_file).convert("RGB")
        secret = Image.open(secret_file).convert("RGB")

        if secret.size[0] > cover.size[0] or secret.size[1] > cover.size[1]:
            st.error("❌ Secret image must be smaller than the cover image!")
        else:
            cover_np = np.array(cover)
            secret_np = np.array(secret)
            secret_resized = np.zeros_like(cover_np)
            secret_resized[:secret_np.shape[0], :secret_np.shape[1]] = secret_np

            stego_np = (cover_np & 0xF0) | ((secret_resized >> 4) & 0x0F)
            stego_img = Image.fromarray(np.uint8(stego_np))
            stego_img.save("stego_image_imginimg.png")
            st.image("stego_image_imginimg.png", caption="🖼️ Image-in-Image Output")
            with open("stego_image_imginimg.png", "rb") as f:
                st.download_button("📥 Download Stego Image", f, file_name="stego_image_imginimg.png")
            st.success("✅ Image hidden successfully!")

    st.markdown("---")
    st.subheader("🔓 Extract Hidden Image")
    decode_stego_file = st.file_uploader("📂 Upload Stego Image to Reveal Hidden Image", type=["png", "jpg"], key="decode_img")
    if decode_stego_file and st.button("🔍 Reveal Hidden Image"):
        decode_stego_file.seek(0)
        stego = Image.open(decode_stego_file).convert("RGB")
        stego_np = np.array(stego)
        revealed_np = (stego_np & 0x0F) << 4
        revealed_img = Image.fromarray(np.uint8(revealed_np))
        revealed_img.save("revealed_image.png")
        st.image("revealed_image.png", caption="🔓 Revealed Secret Image")
        with open("revealed_image.png", "rb") as f:
            st.download_button("📥 Download Revealed Image", f, file_name="revealed_image.png")
        st.success("✅ Image revealed successfully!")
