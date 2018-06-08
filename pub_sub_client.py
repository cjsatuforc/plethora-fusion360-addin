import requests, time

class PubSubClient:
    def __init__(self, session):
        self.message_counter = 0
        self.timeout = 0.0
        self.client_id = ''
        self.session = session
            
    def handshake(self):
        self.message_counter = self.message_counter + 1
        
        payload = [
            {
                'channel': '/meta/handshake',
                'version': '1.0',
                'supportedConnectionTypes': [
                    #'websocket',
                    #'eventsource',
                    'long-polling',
                    #'cross-origin-long-polling',
                    #'callback-polling'
                ],
                'id': str(self.message_counter)
            }
        ]
        response = self.session.post('https://www.plethora.com/api/pubsub', json=payload)
        if response.status_code != 200:
            print('failed to handshake: ' + str(response))
            exit()          
                
        if response.json()[0]['successful'] == False:
            print('handshake was unsuccessful: ' + str(response.json()))
            exit() 
            
        self.client_id = response.json()[0]['clientId']
        
    def connect(self):
        self.message_counter = self.message_counter + 1
        
        payload = [
                {
                    'channel': '/meta/connect',
                    'clientId': self.client_id,
                    'connectionType': 'long-polling',
                    'id': str(self.message_counter),
                    'advice': {
                        'timeout': 0
                    }
                }
        ]
        response = self.session.post('https://www.plethora.com/api/pubsub', json=payload)
        if response.status_code != 200:
            print('failed to connect: ' + str(response))
            exit() 
        if response.json()[0]['successful'] == False:
            print('connect was unsuccessful: ' + str(response.json()))
            exit()   
        self.timeout = response.json()[0]['advice']['timeout'] / 1000.0
    
    def subscribe(self, subscription):
        self.message_counter = self.message_counter + 1
        
        payload = [
            {
                'channel': '/meta/subscribe',
                'clientId': self.client_id,
                'subscription': subscription,
                'id': str(self.message_counter)
            }
        ]
        response = self.session.post('https://www.plethora.com/api/pubsub', json=payload)
        if response.status_code != 200:
            print('failed to subscribe: ' + str(response))
            exit() 
        if response.json()[0]['successful'] == False:
            print('subscribe was unsuccessful: ' + str(response.json()))
            exit()
            
    def poll(self):
        self.message_counter = self.message_counter + 1
        payload = [
            {
                'channel': '/meta/connect',
                'clientId': self.client_id,
                'connectionType': 'long-polling',
                'id': str(self.message_counter)
            },
        ]
        while True:
            try:
                response = self.session.post('https://www.plethora.com/api/pubsub', json=payload, timeout=self.timeout)
                if response.status_code != 200:
                    print('failed to poll: ' + str(response))
                    exit() 
                if response.json()[0]['successful'] == False:
                    print('poll was unsuccessful: ' + str(response.json()))
                    exit()
                return response.json()[1]
                
            except requests.exceptions.ReadTimeout as err:
                print('request timed out')
                time.sleep(0.1)
                
    
    def disconnect(self):
        self.message_counter = self.message_counter + 1
        
        payload = [
            {
                'channel': '/meta/disconnect',
                'clientId': self.client_id,
                'id': str(self.message_counter)
            },
        ]
        response = self.session.post('https://www.plethora.com/api/pubsub', json=payload)
        if response.status_code != 200:
            print('failed to disconnect: ' + str(response))
            exit() 
        if response.json()[0]['successful'] == False:
            print('disconnect was unsuccessful: ' + str(response.json()))
            exit()