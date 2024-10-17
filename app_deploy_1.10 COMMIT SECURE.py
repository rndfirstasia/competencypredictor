import streamlit as st
import pandas as pd
import boto3
import datetime
import mysql.connector
from mysql.connector import Error

from openai import OpenAI
import requests
import io
from io import StringIO
from collections import defaultdict

#page config
st.set_page_config(
    page_icon="img/icon.png",
    page_title="Prediksi Kompetensi",
)

#env
#taruh semua credential ke secrets

#untuk deploy
aws_access_key_id = st.secrets["aws"]["aws_access_key_id"]
aws_secret_access_key = st.secrets["aws"]["aws_secret_access_key"]
endpoint_url = st.secrets["aws"]["endpoint_url"]
mysql_user = st.secrets["mysql"]["username"]
mysql_password = st.secrets["mysql"]["password"]
mysql_host = st.secrets["mysql"]["host"]
mysql_port = st.secrets["mysql"]["port"]
mysql_database = st.secrets["mysql"]["database"]
client = OpenAI(api_key=st.secrets["openai"]["api"])
hf_token = st.secrets["hf"]["token"]
flask_url = st.secrets["flask"]["url"]

conn = mysql.connector.connect(
    user=mysql_user,
    password=mysql_password,
    host=mysql_host,
    port=mysql_port,
    database=mysql_database
)

connx = conn.cursor() 

def create_db_connection():
    # global conn
    # if conn is None or not conn.is_connected():
    #     try:
    #         conn = mysql.connector.connect(
    #             user=mysql_user,
    #             password=mysql_password,
    #             host=mysql_host,
    #             port=mysql_port,
    #             database=mysql_database
    #         )
    #         return conn
    #     except Exception as e:
    #         print(f"Error: {e}")
    #         return None
    try:
        conn = mysql.connector.connect(
            user=mysql_user,
            password=mysql_password,
            host=mysql_host,
            port=mysql_port,
            database=mysql_database
        )
        if conn.is_connected():
            return conn
        else:
            return None
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

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
connx.close()

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

    # Fungsi untuk mengambil transkrip
    def get_transcriptions(registration_id):
        conn = create_db_connection()
        if conn is None:
            st.error("Failed to connect to the database.")
            return []

        try:
            cursor = conn.cursor()
            query = """
            SELECT t.id_transkrip, t.registration_id, t.transkrip, t.speaker, t.start_section, t.end_section, a.num_speakers
            FROM txtan_transkrip t
            INNER JOIN txtan_audio a ON t.id_audio = a.id_audio
            WHERE a.is_transcribed = %s AND t.registration_id = %s
            """
            st.write(f"Executing query: {query}") #debug
            cursor.execute(query, (1, registration_id))
            result = cursor.fetchall()
            st.write(f"Transcriptions fetched: {len(result)}") #debug
            return result

        except Exception as e:
            st.error(f"Transcriptions fetched: {len(result)} for registration_id {registration_id}")
            return []

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Fungsi untuk menyimpan ke tabel separator
    def insert_into_separator(id_transkrip, registration_id, revisi_transkrip, revisi_speaker, revisi_start_section, revisi_end_section):
        conn = create_db_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO txtan_separator (id_transkrip, registration_id, revisi_transkrip, revisi_speaker, revisi_start_section, revisi_end_section)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (id_transkrip, registration_id, revisi_transkrip, revisi_speaker, revisi_start_section, revisi_end_section)
        cursor.execute(query, values)

        st.write("Inserting into txtan_separator with values:", (id_transkrip, registration_id, revisi_transkrip, revisi_speaker, revisi_start_section, revisi_end_section)) #debug

        conn.commit()
        cursor.close()
        conn.close()

    # Fungsi untuk menyimpan ke tabel result
    def insert_into_result(final_predictions_df, registration_id):
        conn = create_db_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO txtan_competency_result (registration_id, competency, level, reason)
        VALUES (%s, %s, %s, %s)
        """

        for index, row in final_predictions_df.iterrows():
            competency = row['Kompetensi']
            level = row['Level']
            reason = row['Alasan Kemunculan']

            values = (registration_id, competency, level, reason)
            cursor.execute(query, values)

        # st.write("Inserting into txtan_separator with values:", (registration_id, competency, level, reason)) #debug

        conn.commit()
        cursor.close()
        conn.close()

        st.success("Prediction Inserted!")

    # Fungsi untuk mengoreksi label pembicara
    def correct_speaker_labels(transkrip, speaker, num_speakers):
        prompt = (
            "Berikut adalah transkrip dari percakapan interview:\n"
            f"{transkrip}\n\n"
            f"Dalam transkrip ini ada {num_speakers} orang.\n"
            "Jika orang lebih dari 2 maka akan ada lebih dari satu assessor. Kandidat tetap hanya akan ada satu."
            f"Saat ini pembicara dilabel dengan {speaker}."
            "Tolong pisahkan percakapan berdasarkan peran berikut:\n"
            "1. Kandidat (yang menjawab pertanyaan)\n"
            "2. Assessor (yang mengajukan pertanyaan)\n"
            "Pisahkan dialog dengan garis baru masing-masing pembicara.\n"
            "Betulkan juga bagian yang ada salah ketik atau ejaan yang kurang benar kecuali nama orang, nama perusahaan, nama jalan, nama kota, nama provinsi, nama negara, nama produk, singkatan.\n"
        )

        messages = [
            {"role": "system", "content": "Kamu adalah pemisah transkrip interview antara assessor dan kandidat"},
            {"role": "user", "content": prompt}
        ]

        try:
            st.write("Sending request to API...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0,
                top_p=0.5,
                frequency_penalty=0,
                presence_penalty=0
            )

            st.write("API Response:", response)

            # Validasi respons dari API
            corrected_transcript = response.choices[0].message.content.strip()
            return corrected_transcript
            
        except Exception as e:
            st.error(f"Error while processing: {str(e)}")
            return None

    def process_gpt_response_to_dataframe(gpt_response):
        lines = gpt_response.split('\n')  # Memecah berdasarkan garis baru
        data = {'text': [], 'speaker': []}
        current_speaker = None
        current_dialogue = []

        for line in lines:
            line = line.strip()  # Hapus spasi kosong di awal/akhir setiap baris

            # Jika baris adalah pengenal pembicara
            if line.startswith("**Assessor:**") or line.startswith("Assessor: "):
                # Jika ada dialog yang sedang berlangsung, tambahkan ke DataFrame
                if current_speaker and current_dialogue:
                    data['text'].append(' '.join(current_dialogue).strip())
                    data['speaker'].append(current_speaker)

                current_speaker = "Assessor"
                current_dialogue = []  # Reset dialog untuk pembicara baru

            elif line.startswith("**Kandidat:**") or line.startswith("Kandidat: "):
                # Tambahkan dialog yang sedang berlangsung sebelum mengganti pembicara
                if current_speaker and current_dialogue:
                    data['text'].append(' '.join(current_dialogue).strip())
                    data['speaker'].append(current_speaker)

                current_speaker = "Kandidat"
                current_dialogue = []  # Reset dialog untuk pembicara baru

            elif line:  # Jika baris bukan pengenal pembicara (dialog sebenarnya)
                current_dialogue.append(line)

        # Tambahkan dialog terakhir jika ada
        if current_speaker and current_dialogue:
            data['text'].append(' '.join(current_dialogue).strip())
            data['speaker'].append(current_speaker)

        # Debugging untuk memeriksa hasil akhir
        df = pd.DataFrame(data)
        st.write("Processed DataFrame:", df)

        if df.empty:
            st.error("DataFrame is empty after processing GPT response.")
        return df

    # Fungsi untuk memproses transkripsi
    def process_transcriptions(registration_id):
        transcriptions = get_transcriptions(registration_id)
        
        if not transcriptions:
            st.error("No transcriptions found.")
            return
        
        transcriptions_by_registration = {}

        for transcription in transcriptions:
            reg_id = transcription[1]
            if reg_id not in transcriptions_by_registration:
                transcriptions_by_registration[reg_id] = []
            transcriptions_by_registration[reg_id].append(transcription)

        for registration_id, transcription_group in transcriptions_by_registration.items():
            combined_transcript = "\n".join([f"{t[3]}: {t[2]}" for t in transcription_group])
            num_speakers = transcription_group[0][6]

            st.write(f"Processing transcription for registration_id {registration_id}")  # Debug

            corrected_transcript = correct_speaker_labels(combined_transcript, "SPEAKER_00", num_speakers)
            if not corrected_transcript:
                st.error("Corrected Transcript is None for registration_id {registration_id}")
                continue

            df = process_gpt_response_to_dataframe(corrected_transcript)
            
            if df.empty:
                st.error(f"Empty DataFrame for registration_id {registration_id}.")
                continue
            
            st.write(f"Processed DataFrame for {registration_id}:", df)  # Debug

            # Merger text dan speaker
            merged_text = []
            merged_speakers = []
            previous_speaker = None
            temp_text = ""
            temp_speaker = ""

            for _, row in df.iterrows():
                current_speaker = row['speaker']
                current_text = row['text']

                if current_speaker == previous_speaker:
                    temp_text += ' ' + current_text
                else:
                    if previous_speaker is not None:
                        merged_text.append(temp_text)
                        merged_speakers.append(temp_speaker)
                    
                    temp_text = current_text
                    temp_speaker = current_speaker
                    previous_speaker = current_speaker

            if temp_text:
                merged_text.append(temp_text)
                merged_speakers.append(temp_speaker)

            df_merged = pd.DataFrame({
                'text': merged_text,
                'speaker': merged_speakers
            })

            df_merged['text'] = df_merged['text'].replace(r'\s+', ' ', regex=True)

            for index, row in df_merged.iterrows():
                st.write(f"Inserting into txtan_separator: {row['text']}, {row['speaker']}")
                insert_into_separator(
                    transcription_group[0][0], 
                    registration_id, 
                    row['text'], 
                    row['speaker'], 
                    transcription_group[0][4], 
                    transcription_group[0][5]
                )

            st.success("Transcriptions processed and inserted.")

    def update_transcription_status(id_audio):
        conn = create_db_connection()

        try:
                cursor = conn.cursor()

                update_query = '''
                    UPDATE txtan_audio
                    SET is_transcribed = 1
                    WHERE id_audio = %s
                '''
                cursor.execute(update_query, (id_audio,))
                conn.commit()
                print(f"Audio with id_audio {id_audio} marked as transcribed.")

        except Exception as e:
                print(f"Error: {e}")

    #Tab3
    def get_separator(registration_id):
        conn = create_db_connection()
        cursor = conn.cursor()
        query = """
        SELECT s.id_transkrip, s.registration_id, s.revisi_transkrip, s.revisi_speaker, s.revisi_start_section, s.revisi_end_section
        FROM txtan_separator s
        INNER JOIN txtan_audio a ON s.registration_id = a.registration_id
        WHERE a.is_transcribed = 1 AND s.registration_id = %s
        """

        cursor.execute(query, (registration_id,))
        result = cursor.fetchall()

        st.write(f"Separator data fetched: {len(result)} entries for registration_id {registration_id}") #debug

        cursor.close()
        conn.close()
        return result            
    
    def get_competency(registration_id):
        conn = create_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT
                a.registration_id,
                prd.name_product,
                comp.competency,
                comp.description
            FROM txtan_audio a
            JOIN pito_product prd ON prd.id_product = a.id_product
            JOIN pito_competency comp ON comp.id_product = prd.id_product
            WHERE a.registration_id = %s
        """

        cursor.execute(query, (registration_id,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result            
    
    def predict_competency(combined_text, competency_list):
        prompt = "Saya memiliki transkrip hasil dari wawancara dan daftar kompetensi yang ingin diidentifikasi. Kompetensi ini memiliki deskripsi dan level yang berbeda.\n\n"

        prompt += "Buatlah hasil analisa menjadi bentuk tabel dan prediksi juga levelnya.\n"
        prompt += f"Teks transkrip berikut {combined_text} dan berdasarkan kompetensi berikut {competency_list}\n"
        prompt += "Hasil hanya akan berupa table dan valuenya. Kolomnya adalah Kompetensi, Level, Alasan Kemunculan\n"
        prompt += "Level yang digunakan adalah likert dari Very Low sampai Very High\n"
        prompt += "Buatlah menjadi table sehingga bisa dimasukkan ke tabledatabase"

        messages = [
            {"role": "system", "content": "Kamu adalah pemisah transkrip interview antara assessor dan kandidat"},
            {"role": "user", "content": prompt}
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages = messages,
            temperature=0,
            top_p=0.5,
            frequency_penalty=0,
            presence_penalty=0
        )

        corrected_transcript_dict = response.model_dump()
        corrected_transcript = corrected_transcript_dict['choices'][0]['message']['content']
        return corrected_transcript

    def combine_text_by_registration(separator_data):
        combined_data = defaultdict(lambda: {"revisi_transkrip": "", "revisi_speaker": ""})

        for record in separator_data:
            registration_id = record[1] #ini kuraang yakin harusnya dimulai dari 0 atau 1, nanti di cek
            revisi_transkrip = record[2] or ""
            revisi_speaker = record[3] or ""

            combined_data[registration_id]["revisi_transkrip"] += f" {revisi_transkrip}"
            combined_data[registration_id]["revisi_speaker"] += f" {revisi_speaker}"

        return combined_data

    def predictor(registration_id):
        # Ambil data revisi dan kompetensi
        separator_data = get_separator(registration_id)
        competency_data = get_competency(registration_id)

        st.write(f"Fetched {len(separator_data)} separator data entries") #debug
        st.write(f"Fetched {len(competency_data)} competency data entries") #debug

        if not separator_data:
            st.error("No data found in the separator table.")
            return

        if not competency_data:
            st.error("No competency data found.")
            return

        competency_list = [{"competency": row[2], "description": row[3]} for row in competency_data]

        combined_data = combine_text_by_registration(separator_data)

        all_predictions = []

        for registration_id, text_data in combined_data.items():
            combined_text = f"{text_data['revisi_transkrip']} {text_data['revisi_speaker']}"

            st.write(f"Predicting competency for {registration_id}") #debug

            predicted_competency = predict_competency(combined_text, competency_list)

            st.write(f"Predicted competency for {registration_id}:\n{predicted_competency}") #debug

            try:
                df_competency = pd.read_csv(StringIO(predicted_competency), sep='|', skipinitialspace=True)
                df_competency.columns = df_competency.columns.str.strip()
                df_competency['registration_id'] = registration_id

                all_predictions.append(df_competency)

            except Exception as e:
                st.error(f"Error processing prediction for registration ID {registration_id}: {e}")

        if all_predictions:
            final_predictions_df = pd.concat(all_predictions, ignore_index=True)
            final_predictions_df = final_predictions_df.drop(index=0).reset_index(drop=True)
            st.write("Final Predictions:")
            st.write(final_predictions_df)
            insert_into_result(final_predictions_df, registration_id)
        else:
            st.write("No predictions to display.")

    if st.button("Simpan dan Transcribe Audio", key="SimpanTranscribe"):
        if audio_file is not None:
            s3_client = boto3.client('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        endpoint_url=endpoint_url)
            
            bucket_name = 'rpi-ta'
            file_name = audio_file.name

            audio_file_copy = io.BytesIO(audio_file.getvalue()) 

            try:
                s3_client.upload_fileobj(audio_file, bucket_name, file_name)
                st.success(f"File {file_name} berhasil diupload ke S3.")
            except Exception as e:
                st.error(f"Error saat upload ke S3: {e}")
                st.stop()

            try:
                cursor = conn.cursor()
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
                cursor.execute(insert_query, data)
                conn.commit()
                id_audio = cursor.lastrowid
                st.success("Informasi berhasil tersimpan ke database.")
                # transcriptions = get_transcriptions(id_input_id_kandidat)
                # separator_data = get_separator(id_input_id_kandidat)
                # competency_data = get_competency(id_input_id_kandidat)
            except Exception as e:
                st.error(f"Error saat menyimpan ke database: {e}")
                st.stop()
            finally:
                cursor.close()

            try:
                files = {'file': (file_name, audio_file_copy.getvalue(), 'audio/wav')}
                data = {'registration_id': id_input_id_kandidat}
                response = requests.post(f"{flask_url}/transcribe", files=files, data=data)
                
                if response.status_code == 200:
                    st.success("Transkripsi berhasil!")
                    segments = response.json()  # Assuming this is a list of segments

                    # Insert each segment into the database
                    if segments:
                        for segment in segments:
                            registration_id = segment['registration_id']
                            text = segment['transcript']
                            speaker = segment['speaker']
                            start_section = segment['start_section']
                            end_section = segment['end_section']

                            try:
                                cursor = conn.cursor()
                                insert_transcript_query = """
                                INSERT INTO txtan_transkrip (registration_id, id_audio, start_section, end_section, transkrip, speaker)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """

                                data_transcript = (
                                    registration_id,
                                    id_audio,  # Use the retrieved id_audio
                                    start_section,
                                    end_section,
                                    text,
                                    speaker
                                )
                                cursor.execute(insert_transcript_query, data_transcript)
                                conn.commit()

                                update_transcription_status(id_audio)
                            except Exception as e:
                                st.error(f"Error saat menyimpan transkrip ke database: {e}")
                            finally:
                                cursor.close()

                    else:
                        st.error("No segments found in the response.")
                else:
                    st.error(f"Error saat memanggil API transkripsi: {response.content}")

                process_transcriptions(id_input_id_kandidat)
                predictor(id_input_id_kandidat)
            
            except Exception as e:
                st.error(f"Error saat memanggil API transkripsi: {e}")

            finally:
                cursor.close()
                conn.close()

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
            conn = create_db_connection()
            if conn is None:
                st.error("Database connection not available.")
                return pd.DataFrame(columns=["Start", "End", "Transkrip", "Speaker"])

            try:
                cursor = conn.cursor()
                query = """
                SELECT revisi_start_section AS 'Start', revisi_end_section AS 'End', revisi_transkrip AS 'Transkrip', revisi_speaker AS 'Speaker'
                FROM txtan_separator
                WHERE registration_id = %s
                """
                cursor.execute(query, (registration_id,))
                result = cursor.fetchall()
                cursor.close()
                conn.close()

                if result:
                    df = pd.DataFrame(result, columns=["Start", "End", "Transkrip", "Speaker"]) #start dan end masihh dalam sec
                    return df
                else:
                    return pd.DataFrame(columns=["Start", "End", "Transkrip", "Speaker"])

            except mysql.connector.Error as e:
                st.error(f"Error fetching transcription data: {e}")
                return pd.DataFrame(columns=["Start", "End", "Transkrip", "Speaker"])
            finally:
                if conn.is_connected():
                    conn.close()
        
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
    
    with st.container(border=True):
        st.write("Pilihan tidak ada bisa dipilih jika dirasa memang tidak muncul di Assessor")

    with st.container():

        def get_result_data(registration_id):
            query = """
            SELECT competency, level, reason
            FROM txtan_competency_result
            WHERE registration_id = %s
            """
            conn = create_db_connection()
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
            INSERT INTO txtan_competency_result (registration_id, competency, level, reason, so_level, so_reason)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor = conn.cursor()
            cursor.executemany(query, data_to_save)
            conn.commit()
            cursor.close()

        
        def update_single_entry_db(conn, competency, level, reason, so_level, so_reason, registration_id):
            try:
                cursor = conn.cursor()
                
                so_level = so_level if so_level != '' else None
                so_reason = so_reason if so_reason != '' else None

                
                check_query = """
                SELECT COUNT(*) FROM txtan_competency_result
                WHERE registration_id = %s AND competency = %s AND level = %s AND reason = %s
                """
                cursor.execute(check_query, (registration_id, competency, level, reason))
                count = cursor.fetchone()[0]

                if count > 0:
                    update_query = """
                    UPDATE txtan_competency_result
                    SET so_level = %s, so_reason = %s
                    WHERE registration_id = %s AND competency = %s AND level = %s AND reason = %s
                    """
                    cursor.execute(update_query, (so_level, so_reason, registration_id, competency, level, reason))
                else:
                    
                    insert_query = """
                    INSERT INTO txtan_competency_result (registration_id, competency, level, reason, so_level, so_reason)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (registration_id, competency, level, reason, so_level, so_reason))

                conn.commit()

            except Exception as e:
                st.error(f"Error updating or inserting entry: {e}")

            finally:
                cursor.close()

        def get_all_so_values(registration_id):
            conn = create_db_connection()
            try:
                cursor = conn.cursor()
                query = """
                SELECT competency, so_level, so_reason
                FROM txtan_competency_result
                WHERE registration_id = %s
                """
                cursor.execute(query, (registration_id,))
                return cursor.fetchall() 
            except mysql.connector.Error as e:
                print(f"Database error: {e}")
                return []  
            finally:
                cursor.close()
                conn.close()

        if id_input_id_kandidat:
            df_result_prediction = get_result_data(id_input_id_kandidat)

            if not df_result_prediction.empty:
                filtered_levels = df_pito_level[df_pito_level['id_level_set'] == selected_option_level_set]
                dropdown_options = filtered_levels['NAMA LEVEL'].tolist()
                dropdown_options.insert(0, '')

                so_values = get_all_so_values(id_input_id_kandidat)
                so_dict = {comp[0]: (comp[1], comp[2]) for comp in so_values} 

                for i, row in enumerate(df_result_prediction.itertuples()):
                    st.markdown(f"##### {row.competency}")
                    st.markdown(f"###### Level: {row.level}")
                    st.write(f"###### Alasan muncul: {row.reason}")

                    so_level_key = f"dropdown_{i}"
                    so_reason_key = f"text_input_{i}"

                    current_so_level_value, current_so_reason_value = so_dict.get(row.competency, ("", ""))

                    if f"prev_so_level_{i}" not in st.session_state:
                        st.session_state[f"prev_so_level_{i}"] = current_so_level_value
                    if f"prev_so_reason_{i}" not in st.session_state:
                        st.session_state[f"prev_so_reason_{i}"] = current_so_reason_value

                    so_level = st.selectbox(
                        f"SO Level {row.competency}", 
                        dropdown_options, 
                        key=so_level_key,
                        index=dropdown_options.index(current_so_level_value) if current_so_level_value in dropdown_options else 0
                    )

                    so_reason = st.text_area(
                        f"Keterangan (opsional)", 
                        value=current_so_reason_value if current_so_reason_value else "",
                        key=f"so_reason_{row.competency}_{i}"
                    )

                    if (so_level != st.session_state[f"prev_so_level_{i}"]) or (so_reason != st.session_state[f"prev_so_reason_{i}"]):
                        update_single_entry_db(create_db_connection(), row.competency, row.level, row.reason, so_level, so_reason, id_input_id_kandidat)

                        st.session_state[f"prev_so_level_{i}"] = so_level
                        st.session_state[f"prev_so_reason_{i}"] = so_reason

                        update_success = True

                        #st.success(f"Update berhasil untuk: {row.competency}") #ini masih salah







