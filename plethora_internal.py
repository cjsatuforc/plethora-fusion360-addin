#Author-Gravitate Designs, LLC
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback, requests, os, json, threading, copy, webbrowser

from pathlib import Path
from .pub_sub_client import PubSubClient

# Global list to keep all event handlers in scope.
# This is only needed with Python.
_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)
_session = requests.Session()
_session.headers['Accept'] = 'application/json'
handlers = []

_part = None
_analysis = None
_active_quote_id = None
_order = None

def run_internal(context):
    try:
        global _ui, _app
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface        
        
        workspace = _ui.workspaces.itemById('FusionSolidEnvironment')
        toolbarPanels = workspace.toolbarPanels

        panel = toolbarPanels.itemById('PlethoraPanel')
        if not panel:
            panel = toolbarPanels.add('PlethoraPanel', 'Plethora')        
        
        # Add a command that displays the panel.
        command = _ui.commandDefinitions.itemById('ShowPaletteCommand')
        if not command:
            command = _ui.commandDefinitions.addButtonDefinition('ShowPaletteCommand', 'Plethora', 'Show the Plethora palette', './/resources//plethora')

            # Connect to Command Created event.
            onCommandCreated = ShowPaletteCommandCreatedHandler()
            command.commandCreated.add(onCommandCreated)
            handlers.append(onCommandCreated)
            
        control = panel.controls.itemById('ShowPaletteControl')
        if not control:
            control = panel.controls.addCommand(command)
            
        control.isPromotedByDefault = True
        control.isPromoted = True
        
        # Register events and handlers for requests.
        customEvent = _app.registerCustomEvent('ThreadCompletedEvent')
        onThreadEvent = ThreadCompletedEventHandler()
        customEvent.add(onThreadEvent)
        handlers.append(onThreadEvent)
        
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop_internal(context):
    try:
        workspace = _ui.workspaces.itemById('FusionSolidEnvironment')
        toolbarPanels = workspace.toolbarPanels
        panel = toolbarPanels.itemById('PlethoraPanel')
        if panel:
            panel.deleteMe()
        command = _ui.commandDefinitions.itemById('ShowPaletteCommand')
        if command:
            command.deleteMe()
        palette = _ui.palettes.itemById('PlethoraPalette')
        if palette:
            palette.deleteMe()
            
        _app.unregisterCustomEvent('ThreadCompletedEvent')

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
             
def logInRequest(email, password):
    return requests.Request('POST', 'https://www.plethora.com/api/login', data={'email': email,'password': password})

def materialsRequest():
    return requests.Request('GET', 'https://www.plethora.com/api/materials?enabled=true')
        
def create_part(data):
    request = _session.post('https://www.plethora.com/api/parts', json=data)
    if request.status_code == 200:
        return request.json(), None
    else:
        json = request.json()
        if json:
            return None, json['error']['message']
        return None, 'failed to create part: ' + request.status_code

def update_part(part_id, data):
    request = _session.put('https://www.plethora.com/api/parts/' + str(part_id), json=data)
    if request.status_code == 200:
        return request.json(), None
    else:
        json = request.json()
        if json:
            return None, json['error']['message']
        return None, 'failed to create part: ' + request.status_code
        
def getUploadURL(partId):
    request = _session.get('https://www.plethora.com/api/parts/' + str(partId) + '/upload_url?mimeType=application/octet-stream')          
    if request.status_code == 200:
        uploadURL = request.json()['part']
        return uploadURL, None
    else:
        json = request.json()
        if json:
            return None, json['error']['message']
        return None, 'failed to get upload url: ' + request.status_code
        
def upload(uploadURL, filename):
    request = _session.put(uploadURL, data=open(filename).read(), headers={'Content-Type': 'application/octet-stream'})
    if request.status_code == 200:
        return True, None
    else:
        json = request.json()
        if json:
            return False, json['error']['message']
        return False, 'failed to upload file: ' + request.status_code
        
def acknowledgeUpload(partId):
    global _active_quote_id
    request = _session.post('https://www.plethora.com/api/parts/' + str(partId) + '/upload_ack')
    if request.status_code == 200:
        _active_quote_id = request.json()['active_quote_id']
        return True, None
    else:
        json = request.json()
        if json:
            return False, json['error']['message']
        return False, 'failed to acknowledge upload: ' + request.status_code  
        
def getQuoting():
    request = _session.get('https://www.plethora.com/api/quoting?process=milling3Axis&material=alu6061')          
    if request.status_code == 200:
        return request.json(), None
    else:
        json = request.json()
        if json:
            return None, json['error']['message']
        return None, 'failed to get quoting: ' + request.status_code 
    
def getTurnarounds():
    request = _session.get('https://www.plethora.com/api/turnarounds?process=milling3Axis&material=alu6061')
    if request.status_code == 200:
        return request.json(), None
    else:
        json = request.json()
        if json:
            return None, json['error']['message']
        return None, 'failed to get turnarounds: ' + request.status_code          
         
def update_quote(quote_id, data):
    request = _session.put('https://www.plethora.com/api/quotes/' + str(quote_id), json=data)
    if request.status_code == 200:
        return request.json(), None
    else:
        json = request.json()
        if json:
            return None, json['error']['message']
        return None, 'failed to update quote: ' + request.status_code

def get_estimates():
    request = _session.get('https://www.plethora.com/api/default_estimates')
    if request.status_code == 200:
        return request.json(), None
    else:
        json = request.json()
        if json:
            return None, json['error']['message']
        return None, 'failed to get estimates: ' + request.status_code

def create_order(data):
    request = _session.post('https://www.plethora.com/api/orders', json=data)
    if request.status_code == 200:
        return request.json(), None
    else:
        json = request.json()
        if json:
            return False, json['error']['message']
        return False, 'failed to create order: ' + request.status_code
    
def analyze(material):

    # get design
    design = adsk.fusion.Design.cast(_app.activeDocument.design)
    
    # check for bodies
    if design.activeComponent.bRepBodies.count == 0:
        return None, 'Failed to analyze. There are no bodies for the active component.'
    
    # get document name
    # TODO: Use a UUID for the file name?
    document_name = design.parentDocument.name
    file_name = document_name + '.step'

    # get current directory
    root_dir = Path(__file__).parent
    
    # create tmp directory if it doesn't exist
    tmp_dir = root_dir.joinpath('tmp')
    tmp_dir.mkdir(exist_ok=True)

    file_path = os.path.join(str(tmp_dir.resolve()),file_name)
    
    # Export the current model as step.
    # TODO: Platform independent location using python file system utils. Some kind of temp folder?
    # TODO: Delete file?
    exportManager = design.exportManager
    options = exportManager.createSTEPExportOptions(file_path)
    if not exportManager.execute(options):
        return None, 'Failed to export file to {0}'.format(file_path)
        
    # Get the file size.
    fileSize = os.path.getsize(options.filename)
        
    # Create a new part.
    # TODO: different origin?
    part_data = {
        'name': document_name,
        'file_meta': {
            'name': file_name,
            'size': fileSize
        },
        'detail': {
            'manual_quote': False,
            'quote_notes': None,
            'issues': [],
            'origin': 'Web - Checkout',
            'version': None
        },
        'specs': {
            'dimensions': [],
            'material': material['name'],
            'stock_suggestion': {},
            'proposed_process': 'milling'
        },
        'quote_files': None
    }
    
    # create part
    part, error = create_part(part_data)
    if not error == None:
        return None, error
    else:
        global _part
        _part = part
        
    # get upload url
    uploadURL, error = getUploadURL(_part['id'])
    if not error == None:
        return None, error
    
    # upload file
    success, error = upload(uploadURL, options.filename)
    if not error == None:
        return None, error
        
    # acknowledge upload
    success, error = acknowledgeUpload(_part['id'])
    if not error == None:
        return None, error           

    data = {}

    # get quoting
    quoting, error = getQuoting()
    if not error == None:
        return None, error

    data['quoting'] = quoting
    
    # get turnarounds
    turnarounds, error = getTurnarounds()
    if not error == None:
        return None, error     

    data['turnarounds'] = turnarounds

    pub_sub_client = PubSubClient(_session)    

    # handshake
    pub_sub_client.handshake()
    
    # connect
    pub_sub_client.connect()            
    
    # subscribe
    pub_sub_client.subscribe('/parts/' + str(_part['id']) + '/analyses/created')
    pub_sub_client.subscribe('/parts/' + str(_part['id']) + '/analysis-failed')
    
    # poll for response
    json_response = pub_sub_client.poll()
    
    # disconnect
    pub_sub_client.disconnect()        
    
    if json_response['channel'] == '/parts/' + str(_part['id']) + '/analyses/created':
        data['analysis'] = json_response['data']['analysis']
        global _analysis          
        _analysis = data['analysis']
        return data, None
        
    elif json_response['channel'] == '/parts/' + str(_part['id']) + '/analysis-failed':
        return None, 'Analysis failed'

def check_out(setup_cost, part_cost, turnaround_time, quantity):
    global _part
    global _analysis
    global _active_quote_id

    # Get estimates
    estimates, error = get_estimates()
    if error != None:
        return None, error    
    
    # TODO: Check if part was already quoted
    
    part_data = {}
    part_data['detail'] = copy.copy(_part['detail'])
    part_data['specs'] = copy.copy(_part['specs'])
    part_data['status'] = 'quoted'
    part_data['quote_files'] = None
    part_data['specs']['dimensions'] = _analysis['dimensions']
    part_data['specs']['stock_suggestion'] = _analysis['stock_suggestion']

    part, error = update_part(_part['id'], part_data)
    if error != None:
        return None, error
    else:
        _part = part    

    quote_data = {
        "material": _part['specs']['material'],
        "unit_cost": part_cost,
        "setup_cost": setup_cost,
        "detail":
            {
                "estimates": estimates
            }
    }
    _, error = update_quote(_active_quote_id, quote_data)
    if error != None:
        return None, error
    
    order_data = {
        "turnaround_time": turnaround_time,
        "parts": 
            [
                {
                    "part_id": _part['id'],
                    "quantity": quantity
                }
            ]
        }
    return create_order(order_data)

def reset():
    global _order
    global _part
    global _active_quote_id
    _order = None
    _part = None
    _active_quote_id = None
            
# Event handler for the commandCreated event.
class ShowPaletteCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()              
    def notify(self, args):
        try:
            command = args.command
            onExecute = ShowPaletteCommandExecuteHandler()
            command.execute.add(onExecute)
            handlers.append(onExecute)                                     
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))   
            
# Event handler for the commandExecuted event.
class ShowPaletteCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Create and display the palette.
            palette = _ui.palettes.itemById('PlethoraPalette')
            if not palette:
                palette = _ui.palettes.add('PlethoraPalette', 'Plethora', 'palette/index.html', True, True, True, 300, 200)

                # Dock the palette to the right side of Fusion window.
                palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
    
                # Add handler to HTMLEvent of the palette.
                onHTMLEvent = MyHTMLEventHandler()
                palette.incomingFromHTML.add(onHTMLEvent)   
                handlers.append(onHTMLEvent)
    
                # Add handler to CloseEvent of the palette.
                #onClosed = MyCloseEventHandler()
                #palette.closed.add(onClosed)
                #handlers.append(onClosed)   
            else:
                palette.isVisible = True                               
        except:
            _ui.messageBox('Command executed failed: {}'.format(traceback.format_exc()))
            
# Event handler for the palette HTML event.                
class MyHTMLEventHandler(adsk.core.HTMLEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            htmlArgs = adsk.core.HTMLEventArgs.cast(args)            
            data = json.loads(htmlArgs.data)
            if htmlArgs.action == 'login':
                request = logInRequest(data['email'], data['password'])
                requestThread = RequestThread(htmlArgs.action, request)
                requestThread.start()       

            elif htmlArgs.action == 'materials':
                request = materialsRequest()
                requestThread = RequestThread(htmlArgs.action, request, True)
                requestThread.start()                
                    
            elif htmlArgs.action == 'analyze':
                reset()

                analyzeThread = AnalyzeThread(htmlArgs.action, data)
                analyzeThread.start()

            elif htmlArgs.action == 'checkout':
                global _order
                if _order == None:
                    order, error = check_out(data['setup_cost'], data['part_cost'], data['turnaround_time'], data['quantity'])
                    if error != None:
                        _ui.messageBox('Failed:\n{}'.format(error))
                        return
                    else:
                        _order = order

                webbrowser.open('https://www.plethora.com/orders/' + str(_order['id']))
                # checkout_thread = CheckOutThread()
                # checkout_thread.start()
            
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))           

class RequestThread(threading.Thread):
    def __init__(self, action, request, parse_data=False):
        threading.Thread.__init__(self)
        self.action = action
        self.request = request
        self.parse_data = parse_data

    def run(self):
        prepped = _session.prepare_request(self.request)
        response = _session.send(prepped)
        if response.status_code == 200:
            if self.parse_data:
                self.fire_event({'data': response.json(), 'error': None})
            else:
                self.fire_event({'success': True, 'error': None})
        else:
            json = response.json()
            error = ''

            if json:
                error = json['error']['message']
            else:
                error = 'request failed: ' + response.status_code

            if self.parse_data:
                self.fire_event({'data': None, 'error': error})
            else:
                self.fire_event({'success': False, 'error': error})
            
    def fire_event(self, data):
        data['action'] = self.action
        _app.fireCustomEvent('ThreadCompletedEvent', json.dumps(data))

class AnalyzeThread(threading.Thread):
    def __init__(self, action, material):
        threading.Thread.__init__(self)
        self.action = action
        self.material = material

    def run(self):
        analysis, error = analyze(self.material)
        self.fire_event({'data': analysis, 'error': error})
            
    def fire_event(self, data):
        data['action'] = self.action
        _app.fireCustomEvent('ThreadCompletedEvent', json.dumps(data))

# class CheckoutThread(threading.Thread):
#     def __init__(self, action):
#         threading.Thread.__init__(self)
#         self.action = action

    # def run(self):
        # analysis, error = analyze(self.material)
        # self.fire_event({'data': analysis, 'error': error})
            
    # def fire_event(self, data):
        # data['action'] = self.action
        # _app.fireCustomEvent('ThreadCompletedEvent', json.dumps(data))
        
# The event handler that responds to the custom event being fired.
class ThreadCompletedEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            palette = _ui.palettes.itemById('PlethoraPalette')
            if palette:
                data = json.loads(args.additionalInfo)
                action = data['action']
                del data['action']
                palette.sendInfoToHTML(action, json.dumps(data))
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))