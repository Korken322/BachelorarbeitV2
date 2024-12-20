from flask import Blueprint, render_template, request, redirect, url_for
from utils.db import connect_to_db
from utils.openai_client import get_openai_client
import asyncio

index_bp = Blueprint("index", __name__)
client = get_openai_client()

assistant_id = "asst_In04gvbq0rplQkgoPYZ2kieL"


async def fetch_merkmal(client, assistant_id, edv, relevant_attributes):
    """
    Sendet eine Anfrage, um Merkmale basierend auf relevanten Attributen zu generieren.
    """
    # Prompt für die Anfrage
    attribute_prompt = "Gebe mir zu jedem Wert eines Attributes ein Merkmal oder eine Eigenschaft, die das Produkt beschreiben:\n"
    for attr in relevant_attributes:
        attribute_prompt += f"- {attr['AttributeName']}: {attr['AttributeWert']}\n"

    formatted_message = f"EDV-Nummer: {edv}\n{attribute_prompt}\n Bitte beschreibe die Attribute mit jeweils einem Wort und gebe es in folgendem Format aus: Attribute Name - AttributeWert - Eigenschaft oder Merkmal."

    print(formatted_message)

    # Thread erstellen und Nachricht senden
    thread = client.beta.threads.create()
    thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=formatted_message,
    )

    # Run starten
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Generate concise product attributes."
    )

    # Auf Antwort warten
    merkmale = await wait_for_run_completion(client, thread_id, run.id)
    print(merkmale)
    return merkmale

    

async def fetch_ad_text(client, assistant_id, edv, merkmale, artikelbeschreibung, style, beispieltext):
    
    #Sendet eine Anfrage, um einen Werbetext basierend auf den Merkmalen, Artikelbeschreibung und Stilart zu erstellen.
    
    formatted_message = (
        f"Erstelle Werbetext im Stil von '{style}' für den folgenden Artikel.\n"
        f"EDV-Nummer: {edv}\n"
        f"Artikelbeschreibung: {artikelbeschreibung}\n"
        f"Verwende dafür die folgenden Merkmale des Artikels:\n{merkmale}\n"
        f"Der Text vom Design wie der folgende Text aufgebaut sein\n{beispieltext}"
    )
    print(formatted_message)

    # Thread erstellen und Nachricht senden
    thread = client.beta.threads.create()
    thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=formatted_message,
    )

    # Run starten
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Erstelle einen ansprechenden Werbetext"
    )

    # Auf Antwort warten
    werbetext = await wait_for_run_completion(client, thread_id, run.id)
    print(werbetext)
    return werbetext


async def wait_for_run_completion(client, thread_id, run_id, sleep_interval=2):
    """
    Warten auf den Abschluss eines OpenAI-Runs.
    """
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status == "failed":
            raise Exception(f"Run failed: {run}")

        if run.completed_at:
            # Hole die Antworten
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            for message in reversed(messages.data):
                if message.role == "assistant":
                    return message.content[0].text.value

        await asyncio.sleep(sleep_interval)


@index_bp.route("/", methods=["GET", "POST"])
def index():
    response = None
    edv_numbers = []
    relevant_attributes = []
    stilarten = []

    try:
        # Datenbankabfragen
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)

        # EDV-Nummern und Beschreibungen abrufen
        cursor.execute("""
            SELECT DISTINCT 
                item_attribute_mapping.HGNummer, 
                artikelattribute.Artikelbeschreibung 
            FROM item_attribute_mapping 
            INNER JOIN artikelattribute 
            ON item_attribute_mapping.HGNummer = artikelattribute.HGNummer;
        """)
        edv_data = cursor.fetchall()
        edv_numbers = [(row["HGNummer"], row["Artikelbeschreibung"]) for row in edv_data]

        # Stilarten aus der Datenbank abrufen
        cursor.execute("SELECT id, stilname FROM Stilarten;")
        stilarten = cursor.fetchall()

        cursor.close()
        connection.close()

        if request.method == "POST":
            selected_edv = request.form.get("edv")
            selected_style_id = request.form.get("style")  # Stil-ID aus dem Formular abrufen

            connection = connect_to_db()
            cursor = connection.cursor(dictionary=True)

            # Stilname und Beispiel basierend auf der Stil-ID abrufen
            cursor.execute("SELECT stilname FROM Stilarten WHERE id = %s;", (selected_style_id,))
            style_result = cursor.fetchone()
            selected_style = style_result["stilname"] if style_result else ""

            cursor.execute("SELECT beispieltext FROM StilBeispiele WHERE stilart_id = %s;", (selected_style_id,))
            beispiel_result = cursor.fetchone()
            beispieltext = beispiel_result["beispieltext"] if beispiel_result else ""

            # Artikelbeschreibung abrufen
            cursor.execute("""
                SELECT Artikelbeschreibung
                FROM ArtikelAttribute
                WHERE HGNummer = %s
                LIMIT 1;
            """, (selected_edv,))
            artikelbeschreibung_result = cursor.fetchone()
            artikelbeschreibung = artikelbeschreibung_result["Artikelbeschreibung"] if artikelbeschreibung_result else ""

            # Attributgruppe des Artikels abrufen
            cursor.execute(
                """
                SELECT AttributgroupId
                FROM item_attribute_mapping
                WHERE HGNummer = %s;
                """,
                (selected_edv,)
            )
            attribute_group = cursor.fetchone()["AttributgroupId"]

            # Relevante Attribut-IDs für die Gruppe abrufen
            cursor.execute(
                """
                SELECT MaterialattributID
                FROM relevanteattribute
                WHERE Relevant = 1 AND ID = %s;
                """,
                (attribute_group,)
            )
            relevant_attribute_ids = [row["MaterialattributID"] for row in cursor.fetchall()]

            # Abrufen der relevanten Attribute aus der Artikelattribute-Tabelle
            cursor.execute(
                f"""
                SELECT AttributeName, AttributeWert
                FROM ArtikelAttribute
                WHERE AttributId IN {tuple(relevant_attribute_ids)}
                AND HGNummer = %s;
                """,
                (selected_edv,)
            )
            relevant_attributes = cursor.fetchall()

            cursor.execute(
                    """
                    SELECT Artikelbeschreibung
                    FROM ArtikelAttribute
                    WHERE HGNummer = %s
                    LIMIT 1;
                    """,
                    (selected_edv,)
                )
            artikelbeschreibung_result = cursor.fetchone()
            artikelbeschreibung = artikelbeschreibung_result["Artikelbeschreibung"] if artikelbeschreibung_result else ""


            # Asynchrone Verarbeitung starten
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Merkmale abrufen
            merkmale = loop.run_until_complete(
                fetch_merkmal(client, assistant_id, selected_edv, relevant_attributes)
            )

            # Werbetext basierend auf Merkmalen, Artikelbeschreibung und Stilart abrufen
            werbetext = loop.run_until_complete(
                fetch_ad_text(client, assistant_id, selected_edv, merkmale, artikelbeschreibung, selected_style, beispieltext)
            )

            # Ergebnisse in der Datenbank speichern
            cursor.execute(
                """
                INSERT INTO Merkmale (EDVNr, Merkmale)
                VALUES (%s, %s);
                """,
                (selected_edv, merkmale),
            )

            cursor.execute(
                """
                INSERT INTO Werbetexte (EDVNr, Werbetext)
                VALUES (%s, %s);
                """,
                (selected_edv, werbetext),
            )

            connection.commit()
            return redirect(url_for('result.result', edv=selected_edv))
        
                # Indexseite rendern
        return render_template("index.html", edv_numbers=edv_numbers, stilarten=stilarten)
            
    except Exception as e:
        response = f"Fehler bei der Verarbeitung Ihrer Anfrage: {e}"

    return render_template("index.html", response=response, edv_numbers=edv_numbers, stilarten=stilarten)

