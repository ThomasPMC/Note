import requests
from datetime import datetime, timedelta
import pytz

API_TOKEN = '5a0fee4f0e9bdadafabdc51c6db96c1838ee4f9f'
BASE_URL_LEADS = f'https://api.pipedrive.com/v1/leads?api_token={API_TOKEN}'
PERSON_URL = f'https://api.pipedrive.com/v1/persons/{{person_id}}?api_token={API_TOKEN}'
NOTES_URL = f'https://api.pipedrive.com/v1/notes?api_token={API_TOKEN}'
ADD_NOTE_URL = f'https://api.pipedrive.com/v1/notes?api_token={API_TOKEN}'

# Calcul de la date limite (J-1) en UTC
utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
yesterday = utc_now - timedelta(days=1)

OP_key = "fe419b79ff3c3693eea4e3a3b900543006727afd"
OP_Phone_Key = "47b3b2fb6ed09c7d044e9dee3dad5c6f542701b6"
OPs_key = "3d90ef3bfee638e574841fb70c10339b0d95a287"

start = 0
limit = 100  # Limite de 100 leads par page

def get_person_name(person_id):
    """Récupère le nom de la personne en utilisant son ID."""
    if person_id:
        response = requests.get(PERSON_URL.format(person_id=person_id))
        if response.status_code == 200:
            person_data = response.json().get('data', {})
            return person_data.get('name', 'Unknown')
        else:
            print(f"Erreur lors de la récupération du nom pour la personne ID {person_id}: {response.text}")
    return 'Unknown'

def has_pinned_note(lead_id):
    """Vérifie si le lead a déjà une note épinglée."""
    response = requests.get(f'{NOTES_URL}&lead_id={lead_id}')
    if response.status_code == 200:
        notes = response.json().get('data', [])
        if isinstance(notes, list):  # Assurez-vous que 'notes' est une liste avant d'itérer
            for note in notes:
                if note.get('pinned_to_lead_flag', 0) == 1:
                    return True
    else:
        print(f"Erreur lors de la récupération des notes pour le lead {lead_id}: {response.text}")
    return False

print("Début du traitement...")

while True:
    url = f'{BASE_URL_LEADS}&start={start}&limit={limit}'
    print(f"Requête à l'API pour récupérer les leads : {url}")
    response = requests.get(url)

    if response.status_code == 200:
        leads = response.json().get('data', [])

        if not leads:
            print("Aucun lead renvoyé, fin du traitement.")
            break  # Sortir de la boucle si aucun lead n'est renvoyé

        for lead in leads:
            lead_id = lead['id']
            lead_name = lead.get('title', 'Sans nom')  # Récupérer le nom du lead
            print(f"Traitement du lead ID: {lead_id} - Nom: {lead_name}")

            add_time_str = lead.get('add_time')
            update_time_str = lead.get('update_time')
            OPs = lead.get(OP_key, None)
            OP_Phone = lead.get(OP_Phone_Key, None)
            OP = lead.get(OPs_key, None)
            person_id = lead.get('person_id')  # Récupérer l'ID de la personne associée

            print(f"Lead trouvé avec les informations : OPs: {OPs}, OP_Phone: {OP_Phone}, OP: {OP}")

            # Conversion des chaînes de date en objets datetime (en UTC)
            add_time_dt = datetime.strptime(add_time_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc) if add_time_str else None
            update_time_dt = datetime.strptime(update_time_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc) if update_time_str else None

            if (add_time_dt and add_time_dt > yesterday) or (update_time_dt and update_time_dt > yesterday):
                print(f"Lead {lead_id} ({lead_name}) mis à jour récemment.")

                # Vérifier si le lead a déjà une note épinglée
                if has_pinned_note(lead_id):
                    print(f"Le lead {lead_id} a déjà une note épinglée, aucune nouvelle note ne sera ajoutée.")
                    continue  # Passer ce lead s'il a déjà une note épinglée

                # Vérifier si OP ou OP_Phone est non vide
                if OP or OP_Phone:
                    # Récupérer le nom de la personne associée à OP Manager
                    OP_Manager_Name = get_person_name(OP) if OP else 'None'
                    
                    # Récupérer les informations de la personne associée (nom, téléphone, email)
                    person_name = "Unknown"
                    person_phone = "None"
                    person_email = "None"
                    if person_id:
                        print(f"Récupération des informations de la personne associée avec ID: {person_id}")
                        person_response = requests.get(PERSON_URL.format(person_id=person_id))
                        print(f"Statut de la requête pour la personne: {person_response.status_code}")
                        if person_response.status_code == 200:
                            person_data = person_response.json().get('data', {})
                            person_name = person_data.get('name', 'Unknown')
                            person_phone = person_data.get('phone', [{'value': 'None'}])[0].get('value', 'None')  # Premier numéro de téléphone
                            person_email = person_data.get('email', [{'value': 'None'}])[0].get('value', 'None')  # Premier email
                            print(f"Personne trouvée : {person_name}, Téléphone: {person_phone}, Email: {person_email}")
                        else:
                            print(f"Erreur lors de la récupération des informations de la personne : {person_response.text}")

                    print(f"Lead ID: {lead_id} - OP Manager: {OP_Manager_Name} - OP Phone: {OP_Phone} - OP info: {OPs}")
                    print(f"Personne associée : {person_name}, Téléphone: {person_phone}, Email: {person_email}")

                    # Ajouter une note
                    note_content = (f"<b>OP Manager:</b> {OP_Manager_Name}<br>"
                                    f"<b>OP Phone:</b> {OP_Phone}<br>"
                                    f"<b>OP info:</b> {OPs}<br>"
                                    f"<b>Person Name:</b> {person_name}<br>"
                                    f"<b>Person Phone:</b> {person_phone}<br>"
                                    f"<b>Person Email:</b> {person_email}")
                    note_data = {
                        'content': note_content,
                        'lead_id': lead_id,  # Associer la note au lead
                        'pinned_to_lead_flag': 1  # Épingler la note
                    }

                    print(f"Ajout de la note pour le lead {lead_id} ({lead_name}) avec le contenu suivant :")
                    print(note_content)

                    note_response = requests.post(ADD_NOTE_URL, json=note_data)
                    print(f"Statut de la requête d'ajout de note : {note_response.status_code}")
                    if note_response.status_code == 201:
                        print(f"Note ajoutée avec succès pour le lead {lead_id} ({lead_name})")
                    else:
                        print(f"Erreur lors de l'ajout de la note pour le lead {lead_id} ({lead_name}): {note_response.status_code}, {note_response.text}")
                else:
                    print(f"Les champs OP et OP_Phone sont vides pour le lead {lead_id} ({lead_name}), aucune note ne sera ajoutée.")
            else:
                print(f"Lead {lead_id} ({lead_name}) n'a pas été mis à jour récemment.")

        # Mise à jour de la pagination pour la prochaine itération
        pagination_info = response.json().get('additional_data', {}).get('pagination', {})
        if pagination_info.get('more_items_in_collection'):
            start = pagination_info['next_start']  # Passage à la page suivante
            print(f"Passage à la page suivante : start = {start}")
        else:
            print("Tous les leads ont été traités.")
            break  # Sortir de la boucle si plus aucun lead à traiter
    else:
        print(f"Erreur lors de la requête des leads : {response.text}")
        break  # Sortir de la boucle en cas d'erreur de requête

print("Traitement terminé.")
