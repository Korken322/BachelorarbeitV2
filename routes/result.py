from flask import Blueprint, render_template, request, jsonify
from utils.db import connect_to_db
from utils.openai_client import get_openai_client
import asyncio

result_bp = Blueprint("result", __name__)

# OpenAI-Client und Assistant-ID initialisieren
client = get_openai_client()
assistant_id = "asst_In04gvbq0rplQkgoPYZ2kieL"

async def fetch_feedback_text(client, assistant_id, thread_id, edv, feedback, original_text):
    """
    Sendet eine Anfrage an OpenAI, um basierend auf Feedback den Werbetext zu verbessern.
    """
    formatted_message = (
        f"Bitte verbessere den folgenden Werbetext basierend auf dem Feedback:\n"
        f"EDV-Nummer: {edv}\n\n"
        f"Feedback:\n{feedback}\n\n"
        f"Originaltext:\n{original_text}"
    )

    # Feedback-Nachricht an OpenAI senden
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=formatted_message,
    )

    # OpenAI-Run starten
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Verbessere den Werbetext basierend auf dem Feedback."
    )

    # Auf die Antwort warten
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.completed_at:
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            for message in reversed(messages.data):
                if message.role == "assistant" and message.content:
                    return message.content[0].text.value
        await asyncio.sleep(2)

@result_bp.route('/result/<edv>', methods=['GET'])
def result(edv):
    try:
        # Verbindung zur Datenbank herstellen
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)
        
        # Den generierten Werbetext basierend auf der EDV-Nummer abrufen
        cursor.execute("""
            SELECT Werbetext
            FROM Werbetexte
            WHERE EDVNr = %s
            ORDER BY id DESC
            LIMIT 1;
        """, (edv,))
        result = cursor.fetchone()
        werbetext = result['Werbetext'] if result else 'Kein Werbetext gefunden.'
        
        # Datenbankverbindung schließen
        cursor.close()
        connection.close()

    except Exception as e:
        werbetext = f"Fehler beim Abrufen des Werbetextes: {e}"
    
    # Ergebnisvorlage rendern
    return render_template('result.html', werbetext=werbetext, edv=edv)

@result_bp.route('/submit_feedback/<edv>', methods=['POST'])
def submit_feedback(edv):
    feedback = request.form.get("feedback")  # Feedback aus dem Formular
    if not feedback:
        return render_template('result.html', werbetext="Kein Feedback übermittelt.", edv=edv)

    try:
        # Verbindung zur Datenbank herstellen, um den ursprünglichen Werbetext abzurufen
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT Werbetext
            FROM Werbetexte
            WHERE EDVNr = %s
            ORDER BY id DESC
            LIMIT 1;
        """, (edv,))
        result = cursor.fetchone()
        original_text = result['Werbetext'] if result else 'Kein Werbetext gefunden.'
        cursor.close()
        connection.close()

        # OpenAI-Thread erstellen
        thread = client.beta.threads.create()
        thread_id = thread.id

        # Feedback an OpenAI senden und verbesserten Text abrufen
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        improved_text = loop.run_until_complete(
            fetch_feedback_text(client, assistant_id, thread_id, edv, feedback, original_text)
        )

        # Verbesserte Version in der Datenbank speichern
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO Feedback (EDVNr, FeedbackText, ImprovedText)
            VALUES (%s, %s, %s)
        """, (edv, feedback, improved_text))
        connection.commit()
        cursor.close()
        connection.close()

        return render_template('result.html', werbetext=improved_text, edv=edv)

    except Exception as e:
        return render_template('result.html', werbetext=f"Fehler beim Verarbeiten des Feedbacks: {e}", edv=edv)
