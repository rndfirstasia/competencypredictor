import streamlit as st
import pandas as pd
import boto3
import datetime
import mysql.connector

#page config
st.set_page_config(
    page_icon="img/icon.png",
    page_title="Prediksi Kompetensi",
)

import requests
from flask import Flask, request, jsonify

ngrok_url = None

app = Flask(__name__)

@app.route('/receive_ngrok_url', methods=['POST'])
def receivve_ngrok_url():
	global ngrok_url
	data = request.json
	ngrok_url = data.get('ngrok_url')
	if ngrok_url:
		return jsonify({'status': 'Ngrok url diterima', 'ngrok_url': ngrok_url})
	else:
		return jsonify({'status': 'Ngrok url tidak valid'}), 400
def run_flask():
	app.run()

import threading
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

st.title('Test streamlit dengan colab')

if ngrok_url:
	st.success(f'Ngrok url diterima: {ngrok_url}')
else:
	st.warning("Belum menerima url dari colab")

data_input = st.text_input("Masukkan data:")
if st.button("Simpan", key="simpan_1"):
	if data_input and ngrok_url:
		response = requests.post(f"{ngrok_url}/task", json={'data': data_input})
		if response.status_code ==200:
			st.success("Data berhasil disimpan di flask")
		else:
			st.error("gagal mengirim data ke flask")
	else:
		st.warning("ngrok kosong")
	

#env
#taruh semua credential ke st.connection
# conn = st.connection('mysql', type='sql')

aws_access_key_id = st.secrets["aws"]["aws_access_key_id"]
aws_secret_access_key = st.secrets["aws"]["aws_secret_access_key"]
endpoint_url = st.secrets["aws"]["endpoint_url"]
mysql_user = st.secrets["mysql"]["username"]
mysql_password = st.secrets["mysql"]["password"]
mysql_host = st.secrets["mysql"]["host"]
mysql_port = st.secrets["mysql"]["port"]
mysql_database = st.secrets["mysql"]["database"]

conn = mysql.connector.connect(
    user=mysql_user,
    password=mysql_password,
    host=mysql_host,
    port=mysql_port,
    database=mysql_database
)

connx = conn.cursor() 

connx.execute('SELECT * FROM txtan_assessor;')
df_txtan_assessor = connx.fetchall()
column_name_txtan_assessor = [i[0] for i in connx.description]
df_txtan_assessor = pd.DataFrame(df_txtan_assessor, columns=column_name_txtan_assessor)

connx.execute("""
SELECT
    pdc.id_product,                          
	pdc.name_product AS 'PRODUCT',
	comp.competency AS 'COMPETENCY',
	comp.description AS 'COMPETENCY DESCRIPTION'
FROM `pito_product` AS pdc
JOIN pito_competency AS comp ON comp.id_product = pdc.id_product
""")
df_pito_product = connx.fetchall()
column_names_pito_product = [i[0] for i in connx.description]
df_pito_product = pd.DataFrame(df_pito_product, columns=column_names_pito_product)
options_product_set = df_pito_product['PRODUCT'].drop_duplicates().tolist() #list produk dari database

connx.execute("""
SELECT
    lvl.name_level AS 'NAMA LEVEL',
    lvl.value_level,
    lvl.id_level_set
FROM pito_level AS lvl;
""")
df_pito_level = connx.fetchall()
column_names_pito_level = [i[0] for i in connx.description]
df_pito_level = pd.DataFrame(df_pito_level, columns=column_names_pito_level)
options_level_set = df_pito_level['id_level_set'].drop_duplicates().tolist() #list level dari database

st.header("Aplikasi Prediksi Kompetensi")

# Sidebar for navigation
st.sidebar.title("Parameter")
options_num_speaker = [ '2', '1', '3', '4', '5', '6']

#Sidebar
id_input_kode_assessor = st.sidebar.text_input("Kode Assessor Anda")
id_input_id_kandidat = st.sidebar.text_input("ID Kandidat")
selected_option_num_speaker = st.sidebar.selectbox("Jumlah Speaker", options_num_speaker)
selected_option_product_set = st.sidebar.selectbox("Produk", options_product_set)
selected_option_level_set = st.sidebar.selectbox("Set Level", options_level_set)
        
tab1, tab2, tab3 = st.tabs(["📈 Input Informasi", "📄 Hasil Transkrip", "🖨️ Hasil Prediksi"])

########################TAB 1
with tab1:

    if not id_input_kode_assessor: #setting default kalau tidak ada kode assessor
        st.subheader("Mohon masukkan kode Assessor Anda.")
    else:
        assessor_row = df_txtan_assessor[df_txtan_assessor['kode_assessor'].str.lower() == id_input_kode_assessor.lower()] #kode assessor bisa besar atau kecil

        if not assessor_row.empty:
            nama_assessor = assessor_row['name_assessor'].values[0]
            st.subheader(f"Selamat Datang, {nama_assessor}")
        else:
            st.subheader("Kode Assessor tidak terdaftar.") #setting kalau kode assessor salah

    #nanti dikasih juga cara dan deskripsi tiap bagian

    #ini nanti pakai API PITO
    with st.container(border=True):
        st.markdown('<h2 style="font-size: 24px; font-weight: bold;">Info Kandidat Sesuai ID</h2>', unsafe_allow_html=True)
        st.markdown('ID Kandidat: 123124')
        st.markdown('Name: Ahjussi Ahjussi')
        st.markdown('Jenis Kelamin: Pria')
        st.markdown('Produk: PITO Staff')

    selected_product = df_pito_product[df_pito_product["PRODUCT"] == selected_option_product_set]
    with st.container(border=True):
        #Produk yang dipilih
        st.markdown('<h2 style="font-size: 24px; font-weight: bold;">Produk Dipakai</h2>', unsafe_allow_html=True)
        st.write(f'**Nama Produk:** {selected_option_product_set}')
        if not selected_product.empty:
            for index, row in selected_product.iterrows():
                st.write(f"**Kompetensi:** {row['COMPETENCY']}")
                st.write(f"**Deskripsi:** {row['COMPETENCY DESCRIPTION']}")
        else:
            st.write(f"**Kompetensi tidak ditemukan.**")

    selected_level = df_pito_level[df_pito_level['id_level_set'] == selected_option_level_set]
    with st.container(border=True):
        #Level yang dipilih
        st.markdown('<h2 style="font-size: 24px; font-weight: bold;">Level Set Dipakai</h2>', unsafe_allow_html=True)
        st.write(f"**Level Set:** {selected_option_level_set}")
        st.write("Terdiri dari:")
        if not selected_level.empty:
            for index, row in selected_level.iterrows():
                st.write(f"**{row['value_level']}**. {row['NAMA LEVEL']}")
        else:
            st.write(f"**Level set tidak ditemukan.**")

    #Tempat upload audio
    st.markdown("Upload File Audio Anda")
    audio_file = st.file_uploader("Pilih File Audio", type=["mp3", "m4a", "wav",])

    #Tombol Simpan
    if st.button("Simpan", key="Simpan Tab 1"):
        if audio_file is not None:
            s3_client = boto3.client('s3',
                         aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key,
                         endpoint_url=endpoint_url)
            
            bucket_name ='rpi-ta'
            file_name = audio_file.name

            #upload file ke S3
            s3_client.upload_fileobj(audio_file, bucket_name, file_name)
            st.success(f"File {file_name} berhasil diupload.")

            #Simpan informasi ke table txtan_audio
            try:
                cursor_config = conn.cursor()
                selected_id_product = selected_product['id_product'].iloc[0]
                insert_query = """
                INSERT INTO txtan_audio (registration_id, date, num_speakers, id_product, id_level_set, kode_assessor, audio_file_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                data = (
                    id_input_id_kandidat,
                    datetime.datetime.now(),
                    selected_option_num_speaker,
                    selected_id_product,
                    selected_option_level_set,
                    id_input_kode_assessor,
                    file_name
                )
                cursor_config.execute(insert_query, data)
                conn.commit()
                st.success("Informasi berhasil tersimpan")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                cursor_config.close()
        else:
            st.warning("Silahkan cek inputan Anda")
    else:
        st.write()

########################TAB 2
with tab2:
    with st.container(border=True):
        st.markdown('<h2 style="font-size: 24px; font-weight: bold;">Info Kandidat Sesuai ID</h2>', unsafe_allow_html=True)
        st.markdown('ID Kandidat: 123124')
        st.markdown('Name: Ahjussi Ahjussi')
        st.markdown('Jenis Kelamin: Pria')
        st.markdown('Produk: PITO Staff')
    with st.container():
        def get_transkrip_data(registration_id):
            query = """
            SELECT revisi_start_section AS 'Start', revisi_end_section AS 'End', revisi_transkrip AS 'Transkrip', revisi_speaker AS 'Speaker'
            FROM txtan_separator
            WHERE registration_id = %s
            """
            cursor = conn.cursor()
            cursor.execute(query, (registration_id,))
            result = cursor.fetchall()

            cursor.close()
        
            if result:
                #Ini start sama endnya masih dalam sec
                df = pd.DataFrame(result, columns=["Start", "End", "Transkrip", "Speaker"])
                return df
            else:
                return pd.DataFrame(columns=["Start", "End", "Transkrip", "Speaker"])
        
        if id_input_id_kandidat:
            df_transkrip = get_transkrip_data(id_input_id_kandidat)
            st.dataframe(df_transkrip, hide_index=True)
        else:
            st.write("ID Kandidat Tidak Ditemukan")

########################TAB 3
with tab3:
    with st.container(border=True):
        st.markdown('<h2 style="font-size: 24px; font-weight: bold;">Info Kandidat Sesuai ID</h2>', unsafe_allow_html=True)
        st.markdown('ID Kandidat: 123124')
        st.markdown('Name: Ahjussi Ahjussi')
        st.markdown('Jenis Kelamin: Pria')
        st.markdown('Produk: PITO Staff')

    with st.container():
        def get_result_data(registration_id):
            query = """
            SELECT competency, level, reason
            FROM txtan_competency_result
            WHERE registration_id = %s
            """
            cursor = conn.cursor()
            cursor.execute(query, (registration_id,))
            result = cursor.fetchall()

            cursor.close()
        
            if result:
                df = pd.DataFrame(result, columns=["competency", "level", "reason"])
                return df
            else:
                return pd.DataFrame(columns=["competency", "level", "reason"])

        def save_so_to_db(data_to_save):
            query = """
            INSERT INTO txtan_competency_result_so (registration_id, competency, level, reason, so_level, so_reason)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor = conn.cursor()
            cursor.executemany(query, data_to_save)
            conn.commit()
            cursor.close()
        
        if id_input_id_kandidat:
            df_result_prediction = get_result_data(id_input_id_kandidat)

            if not df_result_prediction.empty:
                # Buat list untuk menyimpan data yang akan disimpan
                data_to_save = []

                # Loop untuk menampilkan data
                for i, row in enumerate(df_result_prediction.itertuples()):
                    filtered_levels = df_pito_level[df_pito_level['id_level_set'] == selected_option_level_set]
                    dropdown_options = filtered_levels['NAMA LEVEL'].tolist()

                    # Tampilkan kompetensi dan level
                    st.markdown(f"##### {row.competency}")
                    st.markdown(f"###### Level: {row.level}")

                    # Menggunakan expander untuk Reason
                    st.write(f"###### Alasan muncul:")
                    st.write(row.reason)

                    # Input SO Level dan SO Reason
                    so_level = st.selectbox(f"SO Level{row.competency}", 
                                    [f" ", *dropdown_options], key=f"dropdown_{i}",
                                    index=0)
                    level_to_save = None if so_level == f" " else so_level
                    so_reason = st.text_area(f"Keterangan (opsional)", key=f'text_input_{i}')
                    reason_to_save = None if not so_reason.strip() else so_reason

                    # Simpan data untuk disimpan nanti
                    data_to_save.append((id_input_id_kandidat, row.competency, row.level, row.reason, level_to_save, reason_to_save))

                # Simpan data ke database jika tombol diklik
                if st.button("Simpan", key="Simpan Tab 2"):
                    save_so_to_db(data_to_save)
                    st.success("Data berhasil disimpan ke database!")
            else:
                st.write("ID Kandidat tidak ditemukan.")

