import os
import requests
import json

from dotenv import load_dotenv
load_dotenv()

class MayaCalendar():
    def __init__(self,token=os.getenv("SAMPLE_USER_TOKEN")):
        self.event_url = os.getenv("GET_EVENTS_URL")
        self.event_keys = ["from_date","to_date","title","attendees"]
        self.bearer = f"Bearer {token}"

    @staticmethod
    def filter_event_by_keys(list_of_dicts, keys):
        return [{key: value for key, value in d.items() if key in keys} for d in list_of_dicts]

    def get_events(self,when):
        try:
            params = {"time": when}
            headers = {
                "accept": "application/json",
                "Authorization": self.bearer
            }
            response = requests.get(self.event_url, params=params, headers=headers)
            response = response.json()
            response = self.filter_event_by_keys(response['data'],self.event_keys)
            if response == []:
                return f'There are no events for {when}'
            else:
                result = {'count': len(response), 'events' : response}
                return json.dumps(result)
        except Exception as e:
            print(e)
            return 'Something went wrong in retrieving your events from your calendar'

    def post_events(self,title,from_date,to_date,invitees=None,description=None):
        try:
            headers = {
                "accept": "text/plain",
                "Authorization": self.bearer,
                "Content-Type": "application/json-patch+json"
            }
            data = {
                "description": title,
                "title": title,
                "from_date": from_date,
                "to_date": to_date,
            }
            if description:
                data['description'] = description
            if invitees:
                data['invitees'] = invitees
            print(data)
            response = requests.post(self.event_url, headers=headers, json=data)
            return response.text
        except Exception as e:
            return 'Something went wrong when posting events to calendar'