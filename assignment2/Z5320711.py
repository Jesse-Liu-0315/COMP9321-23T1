import calendar
from io import BytesIO
from matplotlib import pyplot as plt
import pandas as pd
from flask import Flask, send_file
from flask import request, make_response
from flask_restx import Resource, Api, fields, reqparse
import sqlite3
import requests
import json
from datetime import datetime, date, timedelta
#import matplotlib.pyplot as plt
from io import BytesIO

app = Flask(__name__)
api = Api(app,
          default="Events",
          title="MyCalendar REST API",
          description="A simple REST API for managing events in a calendar")

# define the data model for an event
location_model = api.model('Location', {
    'street': fields.String(required=True, description='The street of the event location', example='215B Night Ave'),
    'suburb': fields.String(required=True, description='The suburb of the event location', example='Kensington'),
    'state': fields.String(required=True, description='The state of the event location', example='NSW'),
    'post-code': fields.String(required=True, description='The post code of the event location', example='2033')
})

event_model = api.model('Event', {
    'name': fields.String(required=True, description='The name of the event', example='my birthday party'),
    'date': fields.String(required=True, description='The date of the event in format dd-mm-yyyy', example='01-01-2024'),
    'from': fields.String(required=True, description='The start time of the event in format hh:mm:ss', example='16:00:00'),
    'to': fields.String(required=True, description='The end time of the event in format hh:mm:ss', example='20:00:00'),
    'location': fields.Nested(location_model, required=True, description='The location of the event'),
    'description': fields.String(required=False, description='Some notes on the event', example='some notes on the event')
})

# create a connection to the SQLite database
conn = sqlite3.connect('Z5320711.db')
c = conn.cursor()

# create the table for storing events if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS events
             (id INTEGER PRIMARY KEY,
              name TEXT,
              date TEXT,
              start_time TEXT,
              end_time TEXT,
              street TEXT,
              suburb TEXT,
              state TEXT,
              post_code TEXT,
              last_update TEXT,
              description TEXT,
              reverse_date TEXT)''')

# commit the changes and close the connection
conn.commit()
conn.close()

# define a helper function to check for overlapping events
def has_overlap(start_time, end_time, date):
    conn = sqlite3.connect('Z5320711.db')
    c = conn.cursor()
    c.execute('SELECT * FROM events WHERE date=?', (date,))
    for event in c.fetchall():
        if start_time < event[4] and end_time > event[3]:
            conn.close()
            return True
    conn.close()
    return False

# define a helper function to check if a date is a weekend
def is_weekend(year, month, day):
    d = date(year, month, day)
    return d.weekday() >= 5


def stateNameConvert(state):
    if state == "NSW" or state == "nsw" or state == "Nsw" or state == "NEW SOUTH WALES" or state == "new south wales":
        state = "New South Wales"
    elif state == "VIC" or state == "vic" or state == "Vic" or state == "VICTORIA" or state == "victoria":
        state = "Victoria"
    elif state == "QLD" or state == "qld" or state == "Qld" or state == "QUEENSLAND" or state == "queensland":
        state = "Queensland"
    elif state == "SA" or state == "sa" or state == "Sa" or state == "SOUTH AUSTRALIA" or state == "south australia":
        state = "South Australia"
    elif state == "WA" or state == "wa" or state == "Wa" or state == "WESTERN AUSTRALIA" or state == "western australia":
        state = "Western Australia"
    elif state == "TAS" or state == "tas" or state == "Tas" or state == "TASMANIA" or state == "tasmania":
        state = "Tasmania"
    elif state == "NT" or state == "nt" or state == "Nt" or state == "NORTHERN TERRITORY" or state == "northern territory":
        state = "Northern Territory"
    elif state == "ACT" or state == "act" or state == "Act" or state == "AUSTRALIAN CAPITAL TERRITORY" or state == "australian capital territory":
        state = "Australian Capital Territory"
    else:
        return "Invalid State"
    return state

def diffHour(start_time_str, end_time_str):
    start_time = datetime.strptime(start_time_str, '%d-%m-%Y %H:%M:%S')
    end_time = datetime.strptime(end_time_str, '%d-%m-%Y %H:%M:%S')

    time_diff = end_time - start_time
    hours_diff = time_diff.total_seconds() / 3600
    return hours_diff


# define the endpoint for adding an event
@api.route('/events')
class Event(Resource):
    @api.doc(description = 'add_event')
    @api.response(400, 'Invalid Input')
    @api.response(409, 'Event overlaps with an existing event')
    @api.response(201, 'Event added')
    @api.expect(event_model)
    def post(self):
        event = request.json
        location = event.pop('location') # remove the location field from the event dictionary
        
        # check for overlapping events
        if has_overlap(event['from'], event['to'], event['date']):
            return {'message': 'Event overlaps with an existing event'}, 409
        # check if the state is valid
        if stateNameConvert(location['state']) == "Invalid State":
            return {'message': 'Invalid State'}, 400
        # check if the from time is before the to time
        if event['from'] >= event['to']:
            return {'message': 'Invalid Time'}, 400
        
        conn = sqlite3.connect('Z5320711.db')
        c = conn.cursor()
        last_update = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('INSERT INTO events (name, date, start_time, end_time, street, suburb, state, post_code, last_update, description, reverse_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (event['name'], event['date'], event['from'], event['to'], location['street'], location['suburb'], location['state'], location['post-code'], last_update, event['description'], event['date'][::-1]))
        # result preperties
        id = c.lastrowid
        
        href = f'/events/{id}'
        # commit the changes and close the connection
        conn.commit()
        conn.close()
        # result
        self = {'href': href}
        _links = {'self': self}
        return {'id': id, 'last_update': last_update, '_links': _links}, 201
    
    @api.expect(api.parser().add_argument('order', type=str, default='+id', help='The sort order for the events (+/-id/name/datetime)'), 
                api.parser().add_argument('page', type=int, default=1, help='The page number for the events'),
                api.parser().add_argument('size', type=int, default=10, help='The number of events per page'),
                api.parser().add_argument('filter', type=str, default='id,name', help='The fields to include in the response (comma-separated)'))
    @api.doc(description = 'get_events')
    @api.response(200, 'Events retrieved')
    @api.response(400, 'Bad request')
    @api.response(404, 'Filter not found')
    def get(self):
        conn = sqlite3.connect('Z5320711.db')
        c = conn.cursor()
        # get the query parameters
        order = str(request.args.get('order'))
        page = int(request.args.get('page'))
        size = int(request.args.get('size'))
        filter = str(request.args.get('filter'))
        # deal with the order
        orders = order.split(',')
        order_by = []
        for order in orders:
            if order[0] == '+':
                order_by.append(order[1:] + ' ASC')
            elif order[0] == '-':
                order_by.append(order[1:] + ' DESC')
        # deal with the filter
        filters = filter.split(',')
        for i in range(len(filters)):
            if filters[i] == 'location':
                filters[i] = 'street, suburb, state, post_code'
        
        if filters == ['None']:
            return {'message': 'Filter not fount'}, 404
        else:
            query = f'SELECT {", ".join(filters)} FROM events'
        if order_by:
            query += ' ORDER BY ' + ', '.join(order_by)
        query += f' LIMIT {size} OFFSET {(page - 1) * size}'
        try:
            c.execute(query)
        except:
            return {'message': 'Bad request'}, 400
        events = c.fetchall()
        # result
        self = {'href': f'/events?order={order}&page={page}&size={size}&filter={filter}'}
        _links = {'self': self}
        next = {'href': f'/events?order={order}&page={page + 1}&size={size}&filter={filter}'}
        _links['next'] = next
        if page > 1:
            prev = {'href': f'/events?order={order}&page={page - 1}&size={size}&filter={filter}'}
            _links['prev'] = prev
        result = {'page': page, 'page-size': size}
        result['events'] = []
        for event in events:
            event_dict = {}
            count = 0
            for i in range(len(filters)):
                if filters[i] == 'street, suburb, state, post_code':
                    event_dict['location'] = {'street': event[count], 'suburb': event[count + 1], 'state': event[count + 2], 'post-code': event[count + 3]}
                    count += 3
                else:
                    event_dict[filters[i]] = event[count]
                count += 1
            result['events'].append(event_dict)
        result['_links'] = _links
        return result, 200


@api.route('/events/<int:id>')
class Event(Resource):
    @api.doc(description = 'get_event')
    @api.response(404, 'Event not found')
    @api.response(200, 'Event found')
    def get(self, id):
        self = {'href': f'/events/{id}'}
        _links = {'self': self}
        _metadata = {}
        _metadata['holiday'] = False

        conn = sqlite3.connect('Z5320711.db')
        c = conn.cursor()
        c.execute('SELECT * FROM events WHERE id=?', (id,))
        event = c.fetchone()
        if event is None:
            return {'message': 'Event not found'}, 404
        
        # get date, from, and to fields for current event
        date, frm, to = event[2], event[3], event[4]

        # search for previous event
        c.execute('SELECT id FROM events WHERE reverse_date < ? OR (date = ? AND start_time < ?) ORDER BY date DESC, start_time DESC LIMIT 1', (date[::-1], date, frm,))
        prev_id = c.fetchone()
        if prev_id:
            prev_href = f'/events/{prev_id[0]}'
            _links['previous'] = {'href': prev_href}

        # search for next event
        c.execute('SELECT id FROM events WHERE reverse_date > ? OR (date = ? AND start_time > ?)  ORDER BY date ASC, start_time ASC LIMIT 1', (date[::-1], date, to,))
        next_id = c.fetchone()
        if next_id:
            next_href = f'/events/{next_id[0]}'
            _links['next'] = {'href': next_href}

        # deal with the metadate
        
        # weather
        suburb = event[6]
        stateA = event[7]
        state = stateNameConvert(stateA)
        locdf = pd.read_csv('georef-australia-state-suburb.csv', header=0, delimiter=";")
        locdf = locdf.fillna('')
        locdf['Official Name Suburb'] = locdf['Official Name Suburb'].str.replace(r'\s*\((.*?)\)', '')
        locdf = locdf[(locdf['Official Name State'] == state)]
        locdf = locdf[(locdf['Official Name Suburb'] == suburb)]
        lat = locdf['Geo Point'].values[0].split(',')[0] # 维度
        lon = locdf['Geo Point'].values[0].split(',')[1] # 经度
        time = event[2] + ' ' + event[3]
        seventimeurl = f'http://www.7timer.info/bin/api.pl?lon={lon}&lat={lat}&product=civil&tzshift=10&output=json'
        response = requests.get(seventimeurl)
        data = response.json()
        # deal with the init time and event time
        initYear = data['init'][0:4]
        initMonth = data['init'][4:6]
        initDay = data['init'][6:8]
        initHour = data['init'][8:10]
        initTime = initDay + '-' + initMonth + '-' + initYear + ' ' + initHour + ':00:00'
        diff = diffHour(initTime, time)
        for i in data['dataseries']:
            if i['timepoint'] == ((diff // 3) + 1) * 3:
                _metadata['wind-speed'] = str(i['wind10m']['speed']) + ' KM'
                _metadata['weather'] = str(i['weather'])
                _metadata['humidity'] = str(i['rh2m'])
                _metadata['temperature'] = str(i['temp2m']) + ' C'
                break
        # holiday
        year = date.split('-')[2]
        holiday_api_url = f'https://date.nager.at/api/v2/publicholidays/{year}/AU'
        response = requests.get(holiday_api_url)
        if response.status_code == 200:
            holidays = response.json()
            for holiday in holidays:
                if holiday['date'].split('-')[0] == date.split('-')[2] and holiday['date'].split('-')[1] == date.split('-')[1] and holiday['date'].split('-')[2] == date.split('-')[0]:
                    if _metadata['holiday'] == False:
                        _metadata['holiday'] = holiday['name']
                    else:
                        _metadata['holiday'] = _metadata['holiday'] + ', ' + holiday['name']
        # weekend
        if is_weekend(int(year), int(date.split('-')[1]), int(date.split('-')[0])):
            _metadata['weekend'] = True
        else:
            _metadata['weekend'] = False
        conn.close()
        # result
        return {'id': event[0], 'last-update': event[9], 'name': event[1], 'date': event[2], 'from': event[3], 'to': event[4], 'location': {'street': event[5], 'suburb': event[6], 'state': event[7], 'post-code': event[8]}, 'description': event[10], '_metadata' : _metadata, '_links': _links}, 200

    @api.doc(description = 'delete_event')
    @api.response(404, 'Event not found')
    @api.response(200, 'Event deleted')
    def delete(self, id):
        conn = sqlite3.connect('Z5320711.db')
        c = conn.cursor()
        c.execute('SELECT * FROM events WHERE id=?', (id,))
        event = c.fetchone()
        if event is None:
            return {'message': 'Event not found'}, 404
        c.execute('DELETE FROM events WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return {'message': f'The event with id {id} was removed from the database!', 'id': id}, 200

    @api.doc(description = 'update_event')
    @api.response(404, 'Event not found')
    @api.response(409, 'Time conflict')
    @api.response(200, 'Event updated')
    @api.expect(event_model)
    def patch(self, id):
        conn = sqlite3.connect('Z5320711.db')
        c = conn.cursor()
        c.execute('SELECT * FROM events WHERE id=?', (id,))
        event = c.fetchone()
        if 'from' in data and 'to' in data:
            # check if the from time is before the to time
            if data['from'] > data['to']:
                return {'message': 'The from time is after the to time!'}, 400
            # check for overlapping events
            if 'date' in data:
                if has_overlap(event['from'], event['to'], data['date']):
                    return {'message': 'Event overlaps with an existing event'}, 409
            else:
                if has_overlap(event['from'], event['to'], event[2]):
                    return {'message': 'Event overlaps with an existing event'}, 409
            c.execute('UPDATE events SET start_time=? WHERE id=?', (data['from'], id,))
            c.execute('UPDATE events SET end_time=? WHERE id=?', (data['to'], id,))
        else:
            if 'from' in data:
                # check if the from time is before the to time
                if data['from'] > event[4]:
                    return {'message': 'The from time is after the to time!'}, 400
                # check for overlapping events
                if 'date' in data:
                    if has_overlap(data['from'], event[4], data['date']):
                        return {'message': 'Event overlaps with an existing event'}, 409
                else:
                    if has_overlap(data['from'], event[4], event[2]):
                        return {'message': 'Event overlaps with an existing event'}, 409
                c.execute('UPDATE events SET start_time=? WHERE id=?', (data['from'], id,))
            if 'to' in data:
                # check if the from time is before the to time
                if event[3] > data['to']:
                    return {'message': 'The from time is after the to time!'}, 400
                # check for overlapping events
                if 'date' in data:
                    if has_overlap(event[3], data['to'], data['date']):
                        return {'message': 'Event overlaps with an existing event'}, 409
                else:
                    if has_overlap(event[3], data['to'], event[2]):
                        return {'message': 'Event overlaps with an existing event'}, 409
                c.execute('UPDATE events SET end_time=? WHERE id=?', (data['to'], id,))
        if 'location' in data:
            if 'state' in data['location']:
                # check if the state is valid
                if stateNameConvert(data['location']['state']) == "Invalid State":
                    return {'message': 'Invalid State'}, 409
                c.execute('UPDATE events SET state=? WHERE id=?', (data['location']['state'], id,))
            if 'street' in data['location']:
                c.execute('UPDATE events SET street=? WHERE id=?', (data['location']['street'], id,))
            if 'suburb' in data['location']:
                c.execute('UPDATE events SET suburb=? WHERE id=?', (data['location']['suburb'], id,))
            
            if 'post-code' in data['location']:
                c.execute('UPDATE events SET post_code=? WHERE id=?', (data['location']['post-code'], id,))
        if event is None:
            return {'message': 'Event not found'}, 404
        data = request.get_json()
        if 'name' in data:
            c.execute('UPDATE events SET name=? WHERE id=?', (data['name'], id,))
        if 'date' in data:
            c.execute('UPDATE events SET date=? WHERE id=?', (data['date'], id,))
            c.execute('UPDATE events SET reverse_date=? WHERE id=?', (data['date'][::-1], id,))
        if 'description' in data:
            c.execute('UPDATE events SET description=? WHERE id=?', (data['location']['description'], id,))
        last_update = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('UPDATE events SET last_update=? WHERE id=?', (last_update, id,))
        conn.commit()
        conn.close()
        return {'message': f'The event with id {id} was updated in the database!', 'id': id}, 200


# helper function to parse date strings
def get_statistics(format):
    conn = sqlite3.connect('Z5320711.db')
    c = conn.cursor()
    c.execute('SELECT * FROM events')
    events = c.fetchall()
    # total
    total = len(events)
    # total-current-week
    current_week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
    current_week_end = datetime.now().date() + timedelta(days=6 - datetime.now().weekday())
    sql = f'SELECT * FROM events WHERE date BETWEEN {current_week_start} AND {current_week_end}'
    c.execute(sql)
    total_current_event = len(c.fetchall())
    # total-current-month
    current_month_start = datetime.now().date().replace(day=1)
    current_month_end = datetime.now().date().replace(day=calendar.monthrange(datetime.now().year, datetime.now().month)[1])
    sql = f'SELECT * FROM events WHERE date BETWEEN {current_month_start} AND {current_month_end}'
    c.execute(sql)
    month_event = c.fetchall()
    total_current_month = len(month_event)
    # per-days
    per_days = {}
    for event in events:
        date_str = event[2]
        per_days[date_str] = per_days.get(date_str, 0) + 1
    
    # result
    if format == 'json':
        return {'total': total, "total-current-week": total_current_event, "total-current-month" : total_current_month, 'per_days' :per_days}
    else:
        fig, ax = plt.subplots()
        ax.bar(per_days.keys(), per_days.values())
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of events')
        ax.set_title('Events per day')
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        return buf


@api.route('/events/statistics')
class EventStatistics(Resource):

    @api.expect(api.parser().add_argument('format', type=str, choices=('json', 'image'), default='json'))
    def get(self):
        format = request.args.get('format')
        if format == 'json':
            return get_statistics('json'), 200
        elif format == 'image':
            return send_file(get_statistics('image'), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
