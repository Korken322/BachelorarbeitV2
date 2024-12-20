from flask import Blueprint, render_template, request, redirect, url_for
from utils.db import connect_to_db

relevant_bp = Blueprint('relevant', __name__)

# Route: Anzeige der relevanten Attributgruppen
@relevant_bp.route('/manage', methods=['GET'])
def manage_relevant():
    try:
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)

        # Daten aus der RelevantAttrGroup-Tabelle abrufen
        cursor.execute("""
            SELECT id, Attributgruppenname, ID AS AttrGrpID, Sprache, BezeichnungInTG, Attributeart, Materialattribut, MaterialattributID, Relevant
            FROM relevanteattribute order by id asc;
        """)
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template('manage_relevant.html', data=data)
    except Exception as e:
        return f"Fehler: {e}"

# Route: Aktualisieren der relevanten Attributgruppen
@relevant_bp.route('/update', methods=['POST'])
def update_relevant():
    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        # Iteriere durch die übermittelten Formulardaten
        for key, value in request.form.items():
            if key.startswith('relevant_'):
                row_id = key.split('_')[1]  # Extrahiere die ID
                # Update der Tabelle relevanteattribute
                cursor.execute("""
                    UPDATE relevanteattribute
                    SET Relevant = %s
                    WHERE id = %s;
                """, (value, row_id))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for('relevant.manage_relevant'))
    except Exception as e:
        return f"Fehler: {e}"
