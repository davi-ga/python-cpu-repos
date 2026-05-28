import requests
import importlib
import logging
from flask import Flask, json, request
from collections import OrderedDict
import sqlite3


# 1) Adapter is thread-safe - use queues. when msg comes in put it in job queue for the Adapter
# when want to send a msg - put it in a queue. no need to use locks.
# 2) Insert msg upon receiveRequestLabel
# 3) file paths should be passed to adapter from agent. enable_adapter(c, config_path etc etc)
# 4) take protocol from bspl paper - like seller/buyer.

# 5)

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level="DEBUG")
logger = logging.getLogger('pos')


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""

# Class to represent a BSPL message that allows storing information about it
# Used to store a protocol structure as a list of BSPL messages


class Message:
    def __init__(self, from_, to_, message, out_param, in_param, nil_param, key_param, list_param):
        self.from_ = from_
        self.to_ = to_
        self.message = message
        self.out_param = out_param
        self.in_param = in_param
        self.nil_param = nil_param
        self.key_param = key_param
        self.list_param = list_param


class Message_:
    def __init__(self, from_, to_, message_name, parameters):
        self.from_ = from_
        self.to_ = to_
        self.message_name = message_name
        self.parameters = parameters


class Adapter:
    def __init__(self, from_, protocol_path, configuration_path, db_path):
        self.from_ = from_
        self.message_name = []
        self.parameters = []
        self.handlers = {}
        self.protocol = []
        self.protocol_ = []
        self.configuration = {}
        self.c = []
        self.conn = []
        self.schema = {}
        # self variables :
        #global module_name
        #global db
        #global conn
        self.app = Flask(__name__)
        self.db = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.c = self.conn.cursor()

        # PARSING PROTOCOL
        self.protocol = open(protocol_path, "r")
        configuration = open(configuration_path, "r")
        # Skipping unnecessary lines of the protocol
        next(self.protocol)
        next(self.protocol)
        next(self.protocol)

        # Reading messages
        messages = self.protocol.readlines()
        messages = messages[:-1]
        self.protocol = []

        # Parsing information about messages line by line
        for message in messages:

            parameters = find_between(message, "[", "]")
            words = message.split()
            from_ = words[0]
            to_ = words[2].replace(':', '')
            message_name = words[3]
            message_name = message_name[:message_name.index("[")]
            parameter_set = parameters.split(", ")

            outs = []
            ins = []
            nils = []
            keys = []
            list = []

            for sets in parameter_set:

                sets = sets.split(" ")
                parameter_name = sets[1]
                if sets[0] == "in":
                    ins.append(sets[1])
                    list.append(sets[1])
                elif sets[0] == "out":
                    outs.append(sets[1])
                    list.append(sets[1])
                elif sets[0] == "nil":
                    nils.append(sets[1])
                    list.append(sets[1])
                else:
                    print("Error: No such type of parameter:" + sets[0])

                if len(sets) == 3:

                    if sets[2] == "key":
                        keys.append(sets[1])

            # Recoding information about a message retrieved from a protocol in a Message object
            # so that the protocol structure is stored on a list of Messages called "protocol"
            message = Message(from_, to_, message_name,
                              outs, ins, nils, keys, list)
            self.protocol.append(message)

        # DEBUGGING: printing protocol struture
        for message in self.protocol:
            print("From: " + message.from_)
            print("To: " + message.to_)
            print("Message: " + message.message)
            print("Out parameters: " + str(message.out_param))
            print("In parameters: " + str(message.in_param))
            print("Nil parameters: " + str(message.nil_param))
            print("Key parameters: " + str(message.key_param))
            print("Listed parameters: " + str(message.list_param))
            print("***")

            if message.from_ == self.from_ or message.to_ == self.from_:
                #print("OOOOOOOOOOOOOOOOOOOOOOOOOO" + "message.from is " + message.from_ + ", message.to is " + message.to_ + ", this agent is " + self.from_)
                self.protocol_.append(message)
                # CREATING A TABLE TO STORE MESSAGES THAT HAVE BEEN SEEN
                query = "create table " + message.message + " ( "
                counter = 0
                for param in message.list_param:
                    counter = counter + 1
                    query = query + str(param) + " text "
                    if not counter == len(message.list_param):
                        query = query + ", "

                if message.key_param is not []:
                    query = query + ", primary key ("
                counter2 = 0

                for param in message.key_param:
                    counter2 = counter2 + 1
                    query = query + param
                    if not counter2 == len(message.key_param):
                        query = query + ", "

                if message.key_param is not []:
                    query = query + ")"
                query = query + ")"
                print("QUERY FOR CREATING A DATABASE TABLE: " + query)

                try:
                    self.c.execute("delete from RequestLabel;")
                except:
                    print("Table RequestLabel is empty")

                try:
                    self.c.execute("delete from RequestWrapping;")
                except:
                    print("Table RequestWrapping is empty")

                try:
                    self.c.execute("delete from Labeled;")
                except:
                    print("Table Labeled is empty")

                try:
                    self.c.execute(query)
                except:
                    print("Table already exists")

                self.conn.commit()

        messages = configuration.readlines()
        configuration = {}
        # Parsing information from configuration file to store uri's of agents
        for message in messages:
            # print(message)
            words = message.split()
            role = words[0]
            uri = words[1]
            self.configuration[role] = uri

        # print(str(self.configuration))

        self.c.execute("SELECT name FROM sqlite_master WHERE type = \"table\"")
        tables = self.c.fetchall()

        print(str(tables))
        self.conn.commit()
        # self.conn.close()

        @self.app.route('/messaging/<message_name>', methods=['POST'])
        def receive(message_name):
            sender = request.args.get("sender")
            record = json.loads(request.json)  # <--dictionary
            # print("RECEIVED RECORD IS " + str(record)) #<-- dictionary

            message = self.create_Message_(
                sender, self.from_, message_name, record)
            #print("Message to be inserted is: " + str(message))
            received = self.insert(message)

            if received:
                return '', 204
            else:
                return 'error inserting received message: ' + message_name, 500

    def run(self, **kwargs):
        self.app.run(**kwargs)

    def nop(self, message):
        pass

    def handle_message(self, message):
        handler = self.handlers.get(message.message_name, self.nop)
        handler(message)

    def register_handler(self, message_name):
        def store_handler(handler):  # handleRequestLabel is here <---
            self.handlers[message_name] = handler
        return store_handler

    def forward(self, message, message_name):
        self.c = self.conn.cursor()
        # print(message_name)
        # print(str(self.configuration))
        uri = "http://" + self.configuration[message.to_] + \
            "/messaging/" + message_name + "?from=" + self.from_
        print("URI is " + uri)
        item = json.dumps(message.parameters)
        requests.post(uri, json=item)

    def insert(self, message):
        # Check if message matches schema and
        # Throw error if message does NOT match schema
        # OR has an undefined key parameter,
        # OR is a duplicate,
        # OR its contents are inconsistent with a previously stored message of the same or a different name.
        self.conn = sqlite3.connect(self.db)
        #print("INSERTION STARTED")
        # Check against the protocol schema ot the db one.
        # Write an email before implemeting something to get opinion.
        self.c = self.conn.cursor()

        query = "SELECT orderID, address from RequestLabel;"
        self.c.execute(query)
        print(str(self.c.fetchall()))

        self.schema = []
        for key in message.parameters:
            self.schema.append(key)

        match = None

        #print("Schema is: " + str(self.schema))
        for message_type in self.protocol_:
            # print(message_type.list_param)
            if set(self.schema) == set(message_type.list_param):
                match = message_type.message
                matched_message = message_type

        if match is None:
            result = {"message": "Undefined message.",
                      "status": str(message.parameters)}
            logger.info(result["message"])
            return result

            #print("Match found: " + match)

            # Check if any key or non-nilable parameter of m has nil binding in tself.
        parameters = message.parameters
        #print("Parameters: " + str(parameters))

        schema_exception = False

        for keys in matched_message.key_param:
            if str(parameters[keys]) is None or str(parameters[keys]) == '':
                schema_exception = True
        for keys in matched_message.in_param:
            if str(parameters[keys]) is None or str(parameters[keys]) == '':
                schema_exception = True
        for keys in matched_message.out_param:
            if str(parameters[keys]) is None or str(parameters[keys]) == '':
                schema_exception = True

        if schema_exception:
            result = {"message": "Schema violation.",
                      "status": str(matched_message)}
            logger.info(result["message"])
            return result
        else:
            query = "SELECT EXISTS" + \
                "(" + "SELECT 1 FROM " + match + " WHERE "
            counter6 = 0
            for params in message.parameters:
                counter6 = counter6 + 1
                query = query + params + "=" + "\"" + \
                    str(message.parameters[params]) + "\""
                if counter6 is not len(self.schema):
                    query = query + " AND "
                else:
                    query = query + ");"
            # print(query)

            self.c.execute(query)
            result = self.c.fetchone()
            # print(result[0])

            # DOesnt work?
            if result[0] == 1:
                print("Such entry already exists.")
                return False
            else:
                # Check for every table if despite key values being there, non-key values are DIFFERET from intersections.
                for message_type in self.protocol_:
                    # print(str(message_type.message))
                    intersection = []
                    keys = []
                    for params in message.parameters:
                        if params in message_type.list_param:
                            intersection.append(params)
                    #print("Intersection with " + message_type.message + " is " + str(intersection))
                    # Finding subset of KEYS in the Intersection
                    for params in intersection:
                        if params in message_type.key_param:
                            keys.append(params)
                    #print("Keys in the intersection are: " + str(keys))

                    # Check if these keys exist in the relation AND the any of other params differ:
                    query = "SELECT EXISTS" + \
                        "(" + "SELECT 1 FROM " + \
                        message_type.message + " WHERE "

                    counter6 = 0
                    for key in keys:
                        counter6 = counter6 + 1
                        query = query + str(key) + "='" + \
                            str(message.parameters[key]) + "'"
                        if counter6 is not len(keys):
                            query = query + " AND "
                        else:
                            query = query + ");"
                    # print(query)

                    self.c.execute(query)
                    result = self.c.fetchone()
                    belongs = True
                    # print(result)
                    if result[0] == 1:
                        #print("Entry with such keys already exists.")
                        for param in intersection:
                            query = "SELECT " + \
                                str(param) + " FROM " + \
                                str(message_type.message) + " WHERE "

                            counter7 = 0
                            for key in keys:
                                counter7 = counter7 + 1
                                query = query + \
                                    str(key) + "=" + \
                                    str(message.parameters[key])

                                if counter7 is not len(keys):
                                    query = query + " AND "
                                else:
                                    query = query + ";"

                            print(query)
                            self.c.execute(query)
                            value = self.c.fetchone()

                            print("Value is " + value[0])

                            # Compare that the value matches the one in the message

                            if str(value[0]) != str(message.parameters[param]):
                                belongs = False

                        if belongs == False:
                            result = {"message": "Inconsistent message.",
                                      "status": str(message_type)}
                            logger.info(result["message"])
                            return result

                # Inserting a message into local store
                insert_query = "INSERT INTO " + match + " ("

                counter7 = 0
                for columns in self.schema:
                    counter7 = counter7 + 1
                    insert_query = insert_query + columns

                    if counter7 is not len(self.schema):
                        insert_query = insert_query + ", "
                    else:
                        insert_query = insert_query + ")"

                insert_query = insert_query + " VALUES ("

                counter8 = 0
                for columns in self.schema:
                    counter8 = counter8 + 1
                    insert_query = insert_query + "'" + \
                        str(message.parameters[columns]) + "'"

                    if counter8 is not len(self.schema):
                        insert_query = insert_query + ", "
                    else:
                        insert_query = insert_query + ")"
                insert_query = insert_query + ";"

                #print("QUERY: " + insert_query)

                self.c.execute(insert_query)
                inserted = self.c.fetchone()
                self.conn.commit()
                # print(inserted)

                #print("Notifying agent that message is available: " + str(message))

                # this message stays request label for some reason
                self.handle_message(message)
                return True

    def send(self, message_name, parameters):

        # Pass name of message and parameters to send and build message_ object here
        # for all parameters p in schema m do:   known ← false
        # p = [o1, brunswick], m = [orderID, address]
        # for each p in m
        # known = False
        # 1) for orderID: for each table - if orderID is in it then U=[orderID,address]/\[orderID, address, blabla] = [orderID, address]
        known = {}
        intersection = OrderedDict()
        self.c = self.conn.cursor()

        to_ = None

        for prot_lines in self.protocol:
            if prot_lines.message == message_name:
                to_ = prot_lines.to_

        if not to_:
            result = {"message": "Unknown message name.",
                      "status": message_name}
            logger.info(result["message"])
            return result

        message = self.create_Message_(
            self.from_, to_, message_name, parameters)

        # print("TABLES ON THIS AGENT ARE ##########################" + str(self.protocol_))
        for msg in self.protocol_:
            #print("COMPARISONSSSSSSSSSSSSSSSSSSSSSS" + msg.message + " AND " + message.message_name)
            if msg.message == message.message_name:
                self.schema = msg

        #print("SENDING ALGORITHM STARTED")
        for parameters in message.parameters:
            # print("************")
            #print("Parameter " + parameters)
            # print("************")
            known[parameters] = False

            # For every message type that mentions this parameter need to find intersection in schemas
            for message_type in self.protocol_:
                if parameters in message_type.list_param:
                    # take this particular db table and check if this message instance is alrerady there
                    #print(parameters + " parameter is in " + message_type.message)
                    # Find intersection between schemas
                    #keys = set(message_type.list_param).intersection(message.parameters)

                    print("Checking " + str(message_type.message) +
                          " for parameter " + parameters)

                    #intersection = set(enumerate(message_type.list_param)) & set(enumerate(message.parameters.keys()))

                    intersection = [
                        p for p in message_type.list_param if p in message.parameters.keys()]

                    # SELECT NOT THE WHOLE LINE BUT PROJECTION TO MESSAGE
                    query = "SELECT {columns} from {message_name} WHERE {condition};".format(
                        columns=",".join(intersection),
                        message_name=message_type.message,
                        condition=" and ".join(
                            ["{}='{}'".format(p, message.parameters[p]) for p in intersection])
                    )

                    print("QUERY: " + query)
                    self.c.execute(query)
                    result = self.c.fetchone()
                    print("result is " + str(result))

                    if result:
                        prior = {p: result[i]
                                 for i, p in enumerate(intersection)}
                        print("prior is " + str(prior))

                        if all(prior[p] == str(message.parameters[p]) for p in intersection):
                            #print("The values are known!")
                            print("SETTING KNOWN TO TRUE.")
                            known[parameters] = True

            print("Known: " + str(known[parameters]
                                  ) + " for parameter " + parameters)
            if not known[parameters] and parameters in self.schema.in_param:
                print("Known: " + str(known[parameters]) + "; parameters: " +
                      parameters + "; in-param of protocol: " + str(self.schema.in_param))
                result = {"message": "In-adornment violation exception.",
                          "status": str(parameters)}
                logger.info(result["message"])
                return result
            if known[parameters] and parameters in self.schema.out_param:
                result = {"message": "Out-adornment violation exception.",
                          "status": str(parameters)}
                logger.info(result["message"])
                return result
            if known[parameters] and parameters in self.schema.nil_param:
                result = {"message": "Nil-adornment violation exception.",
                          "status": str(parameters)}
                logger.info(result["message"])
                return result

        if self.insert(message):
            self.forward(message, message.message_name)
        else:
            result = {"message": "Duplicate message.",
                      "status": str(message.parameters)}
            logger.info(result["message"])
            return result

    def create_Message_(self, from_, to_, message_name, parameters):
        message = Message_(from_, to_, message_name, parameters)
        return message
