from flask import Flask, render_template, url_for, request,flash, redirect

import json
from datetime import datetime,timezone
import calendar
import os


app = Flask(__name__)
#enable for debugging #app.secret_key="adfgergwt"
# Load the JSON data
file_path = str(os.path.dirname(os.path.abspath(__file__)))
input_file= os.path.join(file_path, "myData.json")
user_file = os.path.join(file_path, "users.json")
new_registrations_file= os.path.join(file_path, "newRegistrations.json")

isAdmin="False"
try:
    with open(input_file, encoding="utf-8") as json_file:
        parsed_json = json.load(json_file)
except FileNotFoundError as e:
    parsed_json = {'events':0}
    app.logger.info(f"file not found {file_path}")
except Exception as e:
    parsed_json = {'events':0}
    app.logger.info(e)

try:   
    with open(user_file, 'r') as file:
        user_data = json.load(file)
except FileNotFoundError as e:
    user_data=[]
    app.logger.info(f"file not found {file_path}")
except Exception as e:
    user_data=[]
    app.logger.info(e)

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

def write_regEvents_json(arg_updated_json):
    with open(new_registrations_file, "w") as new_file:
        new_array=[]
        try:
            json.dump({'registrations':arg_updated_json}, new_file)
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

#funciton to get calendar days
def get_calendar_days(year, month):
    # Create a text calendar
    cal = calendar.Calendar()

    # Get the days for the given month
    month_days = cal.itermonthdays(year, month)

    # Format days into a list, including placeholders for blank days
    calendar_days = []
    for day in month_days:
        if day == 0:  # Placeholder for blank days
            calendar_days.append("")
        else:
            calendar_days.append(day)

    return calendar_days

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
            'Event_Name': event['Event_Name'],
            'DateTime': event['DateTime'],
            'dateTimeList':['','',''],
            'Location': event['Location'],
            'IsRegistration': event['IsRegistration'],
            'isGroupRegistration': event['isGroupRegistration'],
            'min_team': int(event['min_team']),
            'max_team': int(event['max_team']),
            'Category': event['Category'],
            'Event_Status':event['Event_Status'],
            'Total_slots_avl':event['Total_slots_avl'],
            'Registered_slots':event['Registered_slots'],
            'Highlights': event['Highlights']
        }
        item_index+=1
    return extracted_data

# Extract the data into a dictionary
events_dict = extract_data(parsed_json)
#####################GET THE DB SIZE###########################
def get_db_size():
    # If events_dict is not empty, return the highest id + 1 for the next event
    if events_dict:         
        return max(events_dict.keys()) + 1  # Assuming ids are sequential
    else:
        return 0

def update_displayDateTime():
    for key, value in events_dict.items():
        updated_value={}
        updated_value.update(value)   
        converted_time = convert_time(str(value['DateTime']))
        updated_value.update({'dateTimeList': converted_time})
        events_dict.update({key: updated_value})
#######################################################
# Function to search for user ID and handle login
def search_user(user_id_input):
    global isAdmin, user_data
    user = next((user for user in user_data if user['user_id'] == user_id_input.lower()), None)
    is_valid = False
    user_name = user
    user_password=""
    if user:
        if user['is_admin'] == True:
            user_password = user['password']
            isAdmin = "True"
            is_valid= True
        else:
            is_valid = True
    else:
        is_valid = False
    return is_valid, user_password

#FUNCTION TO VERIFY PASSWORD
def password_check(actual_password, input_password):
    loc_return=False
    if actual_password == input_password:
        loc_return = True

    return loc_return
#######################################################
#######################################################
##FUNCTION TO FILTER EVENTS ##########################
def filter_events(Category=None, event_status=None):
    filtered_events = {}
    filtered_events_status = {}
    #app.logger.info(Category)
    #app.logger.info(event_status)
    if (Category != "All"):
        for key, event in events_dict.items(): 
            if(event["Category"].lower() == Category.lower()):
                filtered_events.update({key:event})
    else:
        filtered_events = events_dict
    if (event_status != "All"):
        #filtered_events = [event for event in filtered_events if event_status.lower() in event["Event_Status"].lower()]
        for key, event in filtered_events.items():
            if(event["Event_Status"].lower() == event_status.lower()):
                filtered_events_status.update({key:event})
    else:
        filtered_events_status = filtered_events
    return filtered_events_status

error_messages_login=[0,0]
user_name=""
# login page
@app.route("/login", methods=['GET','POST'])
def login_check():
    #app.logger.info("***************************************************")
    #app.logger.info(file_path)

    global isAdmin, error_messages_login, user_password, user_name
    
    if request.method == "GET":
        isAdmin = "False"
        error_messages_login = [0,0]
        return render_template("login_page.html", login_details = isAdmin, error_messages=error_messages_login, username=user_name)
    else:
        if request.method == "POST":
            if 'login_form' in request.form:
                if(isAdmin == "True"):
                    #validate both user name, password
                    is_valid, user_password = search_user(user_name)
                    if password_check(user_password, request.form['password']):
                        return redirect(url_for("index"))
                    else:
                        error_messages_login=[0,1]
                        return render_template("login_page.html", login_details = isAdmin, error_messages=error_messages_login, username=user_name)
                else:
                    user_name=request.form['username']
                    is_valid, user_password = search_user(user_name)
                    if(isAdmin == "True"):
                        error_messages_login[0]=0
                        error_messages_login[1]=0
                        return render_template("login_page.html", login_details = isAdmin, error_messages=error_messages_login, username=user_name)
                    elif(is_valid):
                        error_messages_login[0]=0
                        error_messages_login[1]=0
                        return redirect(url_for("index"))
                    else:
                        error_messages_login[0]=1#no user found
                        error_messages_login[1]=0
                        return render_template("login_page.html", login_details = isAdmin, error_messages=error_messages_login, username=user_name)

@app.route('/logout', methods=['GET','POST'])
def logout():
    user_name=""
    return redirect("/login")

def add_user(json_file, user_id, password, is_admin):
    new_user = {
        "user_id": user_id,
        "password": password,
        "is_admin": is_admin
    }
    try:
        with open(json_file, 'r+') as file:
            data = json.load(file)
            data.append(new_user)
            file.seek(0)
            json.dump(data, file, indent=4)
        print(f"User {user_id} added successfully.")
    except FileNotFoundError:
        with open(json_file, 'w') as file:
            json.dump([new_user], file, indent=4)
        print(f"User {user_id} added successfully.")
    except json.JSONDecodeError:
        print("Error reading JSON file. Please check the file format.")

@app.route('/addUser', methods=['GET',"POST"])
def addUser():
    app.logger.info("*********************************************")
    app.logger.info(request.method)
    if(request.method == 'POST'):
        if(isAdmin):
            new_user_data = request.form.to_dict()
            app.logger.info(new_user_data)
            if(new_user_data['category'] == "Admin"):
                user_isAdmin = "True"
            else:
                user_isAdmin= "False"
            add_user(user_file, new_user_data['username'],new_user_data['password'],user_isAdmin)
            return redirect('/ZF_events')
        else:
            return redirect('/ZF_events')
    if(request.method == "GET"):
        return render_template('add_user.html')
    
@app.route("/", methods=['GET','POST'])
def home():
    user_name = ""
    return redirect("/login")
                     
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    calendar_days = get_calendar_days(datetime.now().year, datetime.now().month)
    #get event count in each day # get one event name for each day
    
    total_items = {}
    for key,each_date in enumerate(calendar_days):
        calendar_dashboard={}
        calendar_dashboard.update({'date':each_date})
        #event_count, event_name = get_events(each_date)
        event_count=1
        event_name = "skdfnakjdsfhnkajsfi"
        calendar_dashboard.update({'event_count':event_count})
        calendar_dashboard.update({'event_name':event_name})
        total_items.update({key : calendar_dashboard})
    
    return render_template("dashboard.html", autoScrollMessages=events_dict, calendar_items=total_items)

@app.route('/filter', methods=['GET', 'POST'])
def filter():
    #app.logger.info("**************************************************")
    #app.logger.info(request.method)
    ##app.logger.info(events_dict)
    if(user_name != ""):
        if(request.method == "POST"):
            all_data = request.form.to_dict()
            #app.logger.info(all_data['category'])
            #app.logger.info(all_data['event_status'])
            filtered_events= filter_events(all_data['category'], all_data['event_status'])
            return render_template('index.html', allFlashed_messages= filtered_events, 
                                   isAdmin = isAdmin, 
                                   user_name=user_name, 
                                   available_categories=available_categories, 
                                   available_status=available_status,
                                   selected_category=all_data['category'],
                                   selected_status=all_data['event_status'])
    else:
        return(redirect("/login"))

@app.route('/ZF_events', methods=['GET','POST'])
def index():
    #app.logger.info("**************************************************")
    #app.logger.info(request.method)
    ##app.logger.info(events_dict)
    if(user_name != ""):
        if(request.method == "GET"):
            update_displayDateTime()
            for key, value in events_dict.items():        
                converted_time = convert_time(str(value['DateTime']))
                ##app.logger.info(value['dateTimeList'])
            filtered_events = filter_events('All', "Upcoming")#category, status
            
            return render_template('index.html', allFlashed_messages= filtered_events, 
                                   isAdmin = isAdmin, 
                                   user_name=user_name, 
                                   available_categories=available_categories, 
                                   available_status=available_status,
                                   selected_Category="All",
                                   selected_status="Upcoming")
                
    else:
        return(redirect("/login"))

@app.route("/event/<int:id>", methods=['GET','POST'])
def event(id):
    if(user_name != ""):
        selected_id = id
        event_found = False
        ##app.logger.info(events_dict)
        for key in events_dict:
            if key == selected_id:
                event_found=True
        if(event_found):
            return render_template('event_details.html', event_id=id,event_details=events_dict[selected_id], isAdmin=isAdmin, Event_details = "Event details")
        else:
            return render_template('index.html', allFlashed_messages= events_dict)
    else:
        return(redirect("/login"))

available_categories= ["All", "Cricket", "Chess", "Badminton", "Table tennis", "Carroms", "Throw ball", "Fuse ball", "Basket ball", "Painting", "General"]
available_status=[ "Upcoming", "On-going", "Completed", "Cancelled", "All"]

def get_form_details(arg_id:int, isNew:bool):
    form_details = request.form.to_dict()
    ##app.logger.info(form_details)
    event_name = str(form_details['event_name'])
    event_dateTime = str(form_details['event_dateTime'])
    event_location= str(form_details['event_location'])
    event_isReg= str(form_details['IsRegistration'])
    event_isGroupReg= str(form_details['event_isGroup'])
    event_groupSize = str(form_details['event_groupSize'])
    event_category= str(form_details['category'])
    event_status= str(form_details['event_status'])
    event_totalSlots= str(form_details['event_totalSlots'])
    event_registeredSlots= str(form_details['event_registeredSlots'])
    event_desc= str(form_details['event_highlights'])
    
    """""
    #enable this for debugging
    #app.logger.info(event_name)
    #app.logger.info(event_dateTime)
    #app.logger.info(event_location)
    #app.logger.info(event_isReg)
    #app.logger.info(event_isGroupReg)
    #app.logger.info(event_groupSize)
    #app.logger.info(event_category)
    #app.logger.info(event_desc)
    """
    new_details = {}
    if(event_name != ""):
        new_details['Event_Name'] = event_name
    elif(isNew):
        new_details['Event_Name'] = ""
    else:
        new_details['Event_Name'] = events_dict[arg_id]['Event_Name']
        
    if(event_dateTime != ""):
        new_details['DateTime'] = event_dateTime
        #to display the date time on the events page we format the date time received
        converted_time = convert_time(str(event_dateTime))
        new_details['dateTimeList'] = converted_time
    elif(isNew):
        new_details['DateTime'] = ""
        new_details['dateTimeList'] = ""
    else:
        new_details['DateTime'] = str(events_dict[arg_id]['DateTime'])
        new_details['dateTimeList'] = str(events_dict[arg_id]['dateTimeList'])

    if(event_location != ""):
        new_details['Location'] = event_location
    elif(isNew):
        new_details['Location'] = ""
    else:
        new_details['Location'] = str(events_dict[arg_id]['Location'])

    if(event_isReg != ""):
        new_details['IsRegistration'] = event_isReg
    elif(isNew):
        new_details['IsRegistration'] = ""
    else:
        new_details['IsRegistration'] = events_dict[arg_id]['IsRegistration']

    if(event_isGroupReg != "" and event_isReg == "True"):
        new_details['isGroupRegistration'] = event_isGroupReg
    elif(isNew):
        new_details['isGroupRegistration'] = ""
    else:
        new_details['isGroupRegistration'] = events_dict[arg_id]['isGroupRegistration']

    if(event_isGroupReg == "True" and event_isReg == "True" and event_groupSize != ""):
        new_details['isGroupRegistration'] = event_isGroupReg
        new_details['min_team'] = int(event_groupSize.split(',')[0])
        new_details['max_team'] = int(event_groupSize.split(',')[1])
    elif(isNew and event_isGroupReg=="True" and event_isReg=="True"):
        new_details['min_team'] = int("1")
        new_details['max_team'] = int("2")
    elif(isNew):
        new_details['min_team'] = int("0")
        new_details['max_team'] = int("0")    
    else:
        new_details['min_team'] = int(events_dict[arg_id]['min_team'])
        new_details['max_team'] = int(events_dict[arg_id]['max_team'])

    if(event_category != ""):
        new_details['Category'] = event_category
    elif(isNew):
        new_details['Category'] = ""
    else:
        new_details['Category'] = events_dict[arg_id]['Category']

    if(event_status != ""):
        new_details['Event_Status'] = event_status
    elif(isNew):
        new_details['Event_Status'] = ""
    else:
        new_details['Event_Status'] = events_dict[arg_id]['Event_Status']
    
    if(event_totalSlots != ""):
        new_details['Total_slots_avl'] = event_totalSlots
    elif(isNew):
        new_details['Total_slots_avl'] = ""
    else:
        new_details['Total_slots_avl'] = events_dict[arg_id]['Total_slots_avl']
 
    if(event_registeredSlots != ""):
        new_details['Registered_slots'] = event_registeredSlots
    elif(isNew):
        new_details['Registered_slots'] = ""
    else:
        new_details['Registered_slots'] = events_dict[arg_id]['Registered_slots']

    if(event_desc != ""):
        new_details['Highlights'] = event_desc
    elif(isNew):
        new_details['Highlights'] = ""
    else:
        new_details['Highlights'] = events_dict[arg_id]['Highlights']
    
    return new_details

@app.route("/update_event/<int:id>", methods=['GET','POST'])
def update(id):
    if request.method == "GET":
        selected_id = id
        ##app.logger.info(events_dict[id])
        return render_template('update_event.html', event_desc="Update event", event_id=id, event_details=events_dict[selected_id], available_categories=available_categories, available_status=available_status)
    else:
        if request.method == "POST":
            if 'updated_event_details' in request.form:
                updated_details = get_form_details(id, False)
                events_dict.update({id:updated_details}) 
                write_to_json(events_dict)
                return redirect(url_for("event",id=id))
            else:
                return render_template('update_event.html', event_desc="Update not successful, please try again",event_id=id, event_details=events_dict[id], available_categories=available_categories, available_status=available_status)

        else:
            return render_template('update_event.html', event_desc="Update not successful, please try again",event_id=id, event_details=events_dict[id], available_categories=available_categories, available_status=available_status)

@app.route("/delete_event/<int:id>", methods=['GET','POST'])
def delete(id):
    ##app.logger.info(request.method)
    if(user_name != "" and isAdmin == "True"):
        events_dict.pop(id)
        write_to_json(events_dict)
        return redirect(url_for("index"))
    else:
        return redirect("/login")

@app.route("/new_event", methods=['GET','POST'])
def create():
    ##app.logger.info(request.method)
    if request.method == "GET":
        return render_template('create_event.html', available_categories=available_categories, available_status=available_status)
    else:
        if request.method == "POST":
            if 'new_event_details' in request.form:
                global dbSize
                dbSize= dbSize+1
                ##app.logger.info(dbSize)
                new_details = get_form_details(dbSize, True)
                events_dict.update({dbSize:new_details})
                write_to_json(events_dict)          
                return redirect(url_for("index"))

            else:
                return redirect(url_for("index"))
                

        else:
                return redirect(url_for("event",id=dbSize))
@app.route("/register/<int:id>", methods=['GET',"POST"])
def register(id):
    app.logger.info("*********************IN register event")
    app.logger.info(request.method)
    
    if request.method == 'GET':
        return render_template('register_event.html', event_id=id, event_details=events_dict[id])
    else:
        if request.method == 'POST':
            if 'register_event_form' in request.form:                
                register_form_details = request.form.to_dict()
                app.logger.info(register_form_details)
                totalSlots = int(events_dict[id]['Total_slots_avl'])
                registeredSlots = int(events_dict[id]['Registered_slots'])
                available_slots = totalSlots-registeredSlots;

                if(available_slots > 0):
                    registeredSlots += 1
                    events_dict[id]['Registered_slots'] = registeredSlots
                    app.logger.info(events_dict)
                    write_regEvents_json(register_form_details)
                    return render_template('event_details.html', event_id=id,event_details=events_dict[id], isAdmin=isAdmin, Event_details = "Registered successfully")
                else:
                    return render_template('event_details.html', event_id=id,event_details=events_dict[id], isAdmin=isAdmin, Event_details = "Registered not successfull, ")

            else:
                return redirect(url_for("index"))
        else:
            return redirect(url_for("index"))
"""
if __name__ == "__main__":
    app.run(debug=True)
"""
