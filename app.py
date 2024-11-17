from flask import Flask, render_template, url_for, request,flash, redirect

import json
from datetime import datetime,timezone


app = Flask(__name__)
app.secret_key="adfgergwt"
# Load the JSON data
input_file= "myData.json"
with open(input_file, encoding="utf-8") as json_file:
    parsed_json = json.load(json_file)


#global variable
dbSize=len(parsed_json['events'])

def write_to_json(arg_updated_json):
    with open(input_file, "w") as new_file:
        new_array=[]
        for key, value in arg_updated_json.items():
            value.update({'id': int(key)})
            new_array.append(value)
        try:
            json.dump({'events':new_array}, new_file)
        except Exception as e:
            app.logger.info(e)

def convert_time(dateTime_str):
    format = "%Y-%m-%dT%H:%M" # The format  2023-12-10T17:10
    dateList=['','','']
    if(dateTime_str != ""):
        try:
            datetime_string = (datetime.strptime(dateTime_str, format)).strftime("%B %d %Y")
            dateList = datetime_string.split(" ")
            dateList[0] = dateList[0][:3]
        except:
            dateList=['','','']
    return dateList

# Function to extract values into a dictionary
def extract_data(json_data):
    extracted_data = {}
    data_length=len(json_data['events'])
    item_index = 0
    for event in json_data['events']:
        global dbSize
        if event['id'] > dbSize:
            dbSize = event['id']
        extracted_data[item_index] = {
            'Name': event['Name'],
            'DateTime': event['DateTime'],
            'dateTimeList':['','',''],
            'Location': event['Location'],
            'IsRegistration': event['IsRegistration'],
            'RegistrationLink': event['RegistrationLink'],
            'Event_Type': event['Event_Type'],
            'Highlights': event['Highlights']
        }
        item_index+=1
    return extracted_data

# Extract the data into a dictionary
employees_dict = extract_data(parsed_json)

def update_displayDateTime():
    for key, value in employees_dict.items():
        updated_value={}
        updated_value.update(value)   
        converted_time = convert_time(str(value['DateTime']))
        updated_value.update({'dateTimeList': converted_time})
        employees_dict.update({key: updated_value})

# home route that redirects to 
# hello page
@app.route("/", methods=['GET','POST'])
def home():
    return redirect("/ZF_events")

@app.route('/ZF_events', methods=['GET','POST'])
def index():
    app.logger.info(employees_dict)
    update_displayDateTime()
    for key, value in employees_dict.items():        
        converted_time = convert_time(str(value['DateTime']))
        #app.logger.info(value['dateTimeList'])
    return render_template('index.html', allFlashed_messages= employees_dict)

@app.route("/event/<int:id>", methods=['GET','POST'])
def event(id):
    selected_id = id
    event_found = False
    #app.logger.info(employees_dict)
    for key in employees_dict:
        if key == selected_id:
            event_found=True
    if(event_found):
        return render_template('event_details.html', event_id=id,event_details=employees_dict[selected_id])
    else:
        return render_template('index.html', allFlashed_messages= employees_dict)
    
def get_form_details(arg_id:int, isNew:bool):
    event_name = str(request.form['event_name'])
    event_dateTime = str(request.form['event_dateTime'])
    event_location= str(request.form['event_location'])
    event_isReg= str(request.form['IsRegistration'])
    event_regLink= str(request.form['event_link'])
    event_type= str(request.form['event_type'])
    event_desc= str(request.form['event_highlights'])
    """"
    #enable this for debugging
    app.logger.info(event_name)
    app.logger.info(event_dateTime)
    app.logger.info(event_location)
    app.logger.info(event_isReg)
    app.logger.info(event_regLink)
    app.logger.info(event_type)
    app.logger.info(event_desc)
    """
    new_details = {}
    isValid = False
    if(event_name != ""):
        new_details['Name'] = event_name
    elif(isNew):
        new_details['Name'] = ""
        isValid = False
    else:
        new_details['Name'] = employees_dict[arg_id]['Name']
        
    if(event_dateTime != ""):
        new_details['DateTime'] = event_dateTime
        #to display the date time on the events page we format the date time received
        converted_time = convert_time(str(event_dateTime))
        new_details['dateTimeList'] = converted_time
    elif(isNew):
        new_details['DateTime'] = ""
        new_details['dateTimeList'] = ""
    else:
        new_details['DateTime'] = str(employees_dict[arg_id]['DateTime'])
        new_details['dateTimeList'] = str(employees_dict[arg_id]['dateTimeList'])

    if(event_location != ""):
        new_details['Location'] = event_location
    elif(isNew):
        new_details['Location'] = ""
    else:
        new_details['Location'] = str(employees_dict[arg_id]['Location'])

    if(event_isReg != ""):
        new_details['IsRegistration'] = event_isReg
    elif(isNew):
        new_details['IsRegistration'] = ""
    else:
        new_details['IsRegistration'] = employees_dict[arg_id]['IsRegistration']

    if(event_regLink != "" and event_isReg == "True"):
        new_details['RegistrationLink'] = event_regLink
    elif(isNew):
        new_details['RegistrationLink'] = ""
    else:
        new_details['RegistrationLink'] = employees_dict[arg_id]['RegistrationLink']

    if(event_type != ""):
        new_details['Event_Type'] = event_type
    elif(isNew):
        new_details['Event_Type'] = ""
    else:
        new_details['Event_Type'] = employees_dict[arg_id]['Event_Type']

    if(event_desc != ""):
        new_details['Highlights'] = event_desc
    elif(isNew):
        new_details['Highlights'] = ""
    else:
        new_details['Highlights'] = employees_dict[arg_id]['Highlights']

    return new_details, isValid

@app.route("/update_event/<int:id>", methods=['GET','POST'])
def update(id):
    if request.method == "GET":
        selected_id = id
        return render_template('update_event.html', event_desc="Update event", event_id=id, event_details=employees_dict[selected_id])
    else:
        if request.method == "POST":
            if 'updated_event_details' in request.form:
                updated_details,isValid = get_form_details(id, False)
                employees_dict.update({id:updated_details}) 
                write_to_json(employees_dict)
                return redirect(url_for("event",id=id))
            else:
                return render_template('update_event.html', event_desc="Update not successful, please try again",event_id=id, event_details=employees_dict[id])

        else:
            return render_template('update_event.html', event_desc="Update not successful, please try again",event_id=id, event_details=employees_dict[id])

@app.route("/delete_event/<int:id>", methods=['GET','POST'])
def delete(id):
    #app.logger.info(request.method)
    employees_dict.pop(id)
    write_to_json(employees_dict)
    return redirect(url_for("index"))

@app.route("/new_event", methods=['GET','POST'])
def create():
    #app.logger.info(request.method)
    if request.method == "GET":
        return render_template('create_event.html')
    else:
        if request.method == "POST":
            if 'new_event_details' in request.form:
                global dbSize
                dbSize= dbSize+1
                #app.logger.info(dbSize)
                new_details, isValid = get_form_details(dbSize, True)
                if(isValid != ""):
                    employees_dict.update({dbSize:new_details})
                    write_to_json(employees_dict)               
                    return redirect(url_for("index"))
                else:
                    return redirect(url_for("index"))

            else:
                return redirect(url_for("index"))
                

        else:
                return redirect(url_for("event",id=dbSize))
