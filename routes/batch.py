from flask import Blueprint, render_template, request, Response, stream_with_context
from utils.db import connect_to_db
from utils.openai_client import get_openai_client
import asyncio

batch_bp = Blueprint("batch", __name__)
client = get_openai_client()
assistant_id = "asst_In04gvbq0rplQkgoPYZ2kieL"


async def fetch_merkmal(client, assistant_id, edv, relevant_attributes):
    attribute_prompt = "Gebe mir zu jedem Wert eines Attributes ein Merkmal oder eine Eigenschaft, die das Produkt beschreiben:\n"
    for attr in relevant_attributes:
        attribute_prompt += f"- {attr['AttributeName']}: {attr['AttributeWert']}\n"

    formatted_message = f"EDV-Nummer: {edv}\n{attribute_prompt}\n Bitte beschreibe die Attribute mit jeweils einem Wort und gebe es in folgendem Format aus: Attribute Name - AttributeWert - Eigenschaft oder Merkmal."

    thread = client.beta.threads.create()
    thread_id = thread.id
    client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=formatted_message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Generate concise product attributes.",
    )

    merkmale = await wait_for_run_completion(client, thread_id, run.id)
    return merkmale


async def fetch_ad_text(client, assistant_id, edv, merkmale, artikelbeschreibung, style, beispieltext):
    formatted_message = (
        f"Erstelle Werbetext im Stil von '{style}' für den folgenden Artikel.\n"
        f"EDV-Nummer: {edv}\n"
        f"Artikelbeschreibung: {artikelbeschreibung}\n"
        f"Verwende dafür die folgenden Merkmale des Artikels:\n{merkmale}\n"
        f"Der Text soll wie folgt aufgebaut sein:\n{beispieltext}"
    )

    thread = client.beta.threads.create()
    thread_id = thread.id
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=formatted_message,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Erstelle einen ansprechenden Werbetext."
    )

    werbetext = await wait_for_run_completion(client, thread_id, run.id)
    return werbetext


async def wait_for_run_completion(client, thread_id, run_id, sleep_interval=2):
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status == "failed":
            raise Exception(f"Run failed: {run}")

        if run.completed_at:
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            for message in reversed(messages.data):
                if message.role == "assistant":
                    return message.content[0].text.value

        await asyncio.sleep(sleep_interval)


@batch_bp.route('/batch', methods=['GET', 'POST'])
def batch():
    if request.method == 'POST':
        # Ausgewählte Artikel
        selected_edvs = request.form.getlist("selected_edvs")
        # Ausgewählte Stil-ID
        selected_style_id = request.form.get("style")

        def generate():
            yield """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Batch-Werbetexte werden generiert...</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            margin: 0;
            padding: 0;
        }
        header {
            background-color: #002e12;
            color: white;
            padding: 15px;
            text-align: center;
        }
        main {
            max-width: 1500px;
            margin: 20px auto;
            background: #eaf2ea;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #004225;
        }
        .status {
            margin-top: 20px;
            padding: 10px;
            background: #fffbe6;
            border: 1px solid #ccc;
            border-radius: 8px;
        }
        .result-container {
            margin-top: 20px;
            background-color: white;
            border: 1px solid #ccc;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .result-container h2 {
            color: #004225;
        }
        .action-buttons {
            text-align: center;
            margin-top: 20px;
        }
        button, a {
            font-size: 1em;
            padding: 10px 20px;
            margin: 10px 5px;
            background-color: #004225; 
            color: white;
            border: none;
            border-radius: 4px;
            text-decoration: none;
            text-align: center;
            cursor: pointer;
        }
        button:hover, a:hover {
            background-color: #006837;
        }
    </style>
</head>
<body>
    <header>
        <h1>Batch-Werbetext Ergebnisse</h1>
    </header>
    <main>
    <div class="status">
    """

            yield f"<p>Starte die Verarbeitung von {len(selected_edvs)} Artikel(n)...</p></div>"

            connection = connect_to_db()
            cursor = connection.cursor(dictionary=True)

            # Stilname und Beispieltext basierend auf der Stil-ID abrufen
            cursor.execute("SELECT stilname FROM Stilarten WHERE id = %s;", (selected_style_id,))
            style_result = cursor.fetchone()
            selected_style = style_result["stilname"] if style_result else ""

            cursor.execute("SELECT beispieltext FROM StilBeispiele WHERE stilart_id = %s;", (selected_style_id,))
            beispiel_result = cursor.fetchone()
            beispieltext = beispiel_result["beispieltext"] if beispiel_result else ""

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            for idx, edv in enumerate(selected_edvs, start=1):
                yield f"<div class='status'><p>Verarbeite Artikel {idx}/{len(selected_edvs)} mit EDV-Nummer: {edv}...</p></div>"

                # Artikelbeschreibung abrufen
                cursor.execute("""
                    SELECT Artikelbeschreibung
                    FROM ArtikelAttribute
                    WHERE HGNummer = %s
                    LIMIT 1;
                """, (edv,))
                artikelbeschreibung_result = cursor.fetchone()
                artikelbeschreibung = artikelbeschreibung_result["Artikelbeschreibung"] if artikelbeschreibung_result else ""

                # Attributgruppe holen
                cursor.execute(
                    """
                    SELECT AttributgroupId
                    FROM item_attribute_mapping
                    WHERE HGNummer = %s;
                    """,
                    (edv,)
                )
                attribute_group_data = cursor.fetchone()
                if not attribute_group_data:
                    continue
                attribute_group = attribute_group_data["AttributgroupId"]

                # Relevante Attribute
                cursor.execute(
                    """
                    SELECT MaterialattributID
                    FROM relevanteattribute
                    WHERE Relevant = 1 AND ID = %s;
                    """,
                    (attribute_group,)
                )
                relevant_attribute_ids = [row["MaterialattributID"] for row in cursor.fetchall()]

                if not relevant_attribute_ids:
                    relevant_attribute_ids = [0]

                format_placeholder = "(" + ",".join(["%s"] * len(relevant_attribute_ids)) + ")"
                query = f"""
                    SELECT AttributeName, AttributeWert
                    FROM ArtikelAttribute
                    WHERE AttributId IN {format_placeholder}
                    AND HGNummer = %s;
                """
                cursor.execute(query, relevant_attribute_ids + [edv])
                relevant_attributes = cursor.fetchall()

                # Merkmale holen
                merkmale = loop.run_until_complete(fetch_merkmal(client, assistant_id, edv, relevant_attributes))
                werbetext = loop.run_until_complete(fetch_ad_text(client, assistant_id, edv, merkmale, artikelbeschreibung, selected_style, beispieltext))

                yield f"""
                <div class="result-container">
                    <h2>EDV-Nummer: {edv}</h2>
                    <p><strong>Werbetext:</strong></p>
                    <p>{werbetext}</p>
                </div>
                """

            cursor.close()
            connection.close()

            yield """
            <div class="action-buttons">
                <a href='""" + str(request.url_root) + """batch'>Neue Auswahl</a>
                <a href='""" + str(request.url_root) + """'>Zurück zur Startseite</a>
            </div>
            </main></body></html>"""

        return Response(stream_with_context(generate()), mimetype='text/html')

    else:
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)

        # Artikel abrufen
        cursor.execute("""
            SELECT DISTINCT item_attribute_mapping.HGNummer, artikelattribute.Artikelbeschreibung 
            FROM item_attribute_mapping 
            INNER JOIN artikelattribute ON item_attribute_mapping.HGNummer = artikelattribute.HGNummer
        """)
        articles = cursor.fetchall()

        # Stilarten abrufen
        cursor.execute("SELECT id, stilname FROM Stilarten;")
        stilarten = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template("batch.html", articles=articles, stilarten=stilarten)
