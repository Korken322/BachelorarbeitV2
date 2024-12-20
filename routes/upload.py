from flask import Blueprint, render_template, request, redirect, url_for
import pandas as pd
from utils.db import connect_to_db

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/file', methods=['GET', 'POST'])
def upload_attribute_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            file_path = f"/tmp/{file.filename}"
            file.save(file_path)

            try:
                # Excel-Datei lesen
                data = pd.read_excel(file_path)
                connection = connect_to_db()
                cursor = connection.cursor()

                for _, row in data.iterrows():
                    cursor.execute("""
                        INSERT INTO ArtikelAttribute (EDVNr, AttrName, AttrWert, Relevant)
                        VALUES (%s, %s, %s, %s);
                    """, (row['EDV Nr'], row['Attr Name'], row['Attr Wert'], row['Relevant']))
                connection.commit()
                cursor.close()
                connection.close()
                return redirect(url_for('index.index'))
            except Exception as e:
                return f"Fehler beim Verarbeiten der Datei: {e}"

    return render_template('upload.html')
