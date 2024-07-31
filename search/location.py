import requests
import os
import json
from nltk import word_tokenize

class Location:

    def __init__(self):

        pass

    def add_location_index (self, location):

        pass

    def search_country (self, location):

        countries_list = json.loads(open(os.path.join('static/json/locations/countries.json'), "r", encoding="utf8").read())

        for country_index, country in enumerate(countries_list):

            if location in country.lower():

                return location

        return False

    def search_state (self, location):

        states_list = json.loads(open(os.path.join('static/json/locations/states.json'), "r", encoding="utf8").read())

        for states_index, state in enumerate(states_list):

            if location in state.lower():

                return location

        return False

    def search_location_index (self, location):

        index_file_name = location[0].lower()

        # print("Searching " + location + " location in index file")

        if os.path.exists(os.path.join('static/json/locations/index/' + index_file_name + '.json')):

            # print("index file found")

            index_file_contents = json.loads(
                open(os.path.join('static/json/locations/index/' + index_file_name + '.json'), "r",
                     encoding="utf8").read())

            for indexed_location in index_file_contents:

                if location in indexed_location:

                    # print("location found in index file----")

                    return indexed_location

            return -1 # locaiton not found in index file

        else:

            return -2 # index file doesn't exist

    def create_location_index (self, location):

        start_letter = location[0]

        if not os.path.exists(os.path.join('static/json/locations/index/' + start_letter + '.json')):

            new_index_file = open(os.path.join('static/json/locations/index/' + start_letter + '.json'), 'w',
                                        encoding='utf8')

            new_index_file.write('{}')
            new_index_file.close()

    def update_location_index (self, location_detail):

        if location_detail is not None and 'name' in location_detail:

            location_name = location_detail['name']

            index_file_data = {}

            start_letter = location_name[0]

            index_file = open(os.path.join('static/json/locations/index/' + start_letter + '.json'), 'r+',
                 encoding='utf8')
            # print("Read Index file data...........")
            index_file_data = json.loads(index_file.read())
            print(index_file_data)
            index_file.close()
            index_file_data[location_name] = location_detail
            index_file = open(os.path.join('static/json/locations/index/' + start_letter + '.json'), 'w',
                 encoding='utf8')
            # print("Updated Index file data...........")
            print(json.dumps(index_file_data))

            index_file.write(json.dumps(index_file_data))
            index_file.close()


    def search_location (self, location): # temp

        location_detail = {}

        # location parsing (exp) start
        # location = location.split(', ')

        # select outer most region (country / state; index : array length -1 )

        # location parsing (exp) end

        location = location.split(', ')[0]

        cities_states_countries = json.loads(
            open(os.path.join('static/json/locations/countries+states+cities.json'), "r", encoding="utf8").read())

        for country_index, country in enumerate(cities_states_countries):

            if location == country['name'].lower():

                print("Country " + country['name'] + " found ")
                location_detail['name'] = country['name']
                location_detail['type'] = 'country'
                location_detail['country'] = country['name']

                break

            for region_index, region in enumerate(country['states']):

                if location == region['name'].lower():

                    print("Region " + country['name'] + " found ")
                    location_detail['name'] = region['name']
                    location_detail['type'] = 'state'
                    location_detail['country'] = country['name']

                    break

                for city_index, city in enumerate(region['cities']):

                    if location == city['name'].lower():

                        print("City in " + region['name'] + ", " + country['name'] + " found ")
                        location_detail['name'] = region['name']
                        location_detail['type'] = 'city'
                        location_detail['region'] = region['name']
                        location_detail['country'] = country['name']

                        break

        return location_detail



    def search_location_ (self, location):

        # test start

        ls_res = word_tokenize(location)[0]

        # location = location.split(', ')
        #
        # if len(location) > 1:
        #
        #     location = location[len(location) - 1]
        #
        # # test end
        #
        # print("location in search_location ")
        # print(location)

        index_sr = self.search_location_index(ls_res)
        # print("Returned index .........")
        # print(index_sr)


        # print("index sr")
        # print(index_sr)
        # exit()
        if index_sr != -1 and index_sr != -2:

            return index_sr

        else:

            location_detail = {}

            cities_states_countries = json.loads(open(os.path.join('static/json/locations/countries+states+cities.json'), "r", encoding="utf8").read())

            for country_index, country in enumerate(cities_states_countries):

                if location == country['name'].lower():

                    print("Country " + country['name'] + " found ")
                    location_detail['name'] = country['name'].lower()
                    location_detail['type'] = 'country'
                    location_detail['country'] = country['name'].lower()

                    self.create_location_index(location_detail['name'])
                    self.update_location_index(location_detail)

                    break

                for region_index, region in enumerate(country['states']):

                    if location == region['name'].lower():

                        print("Region " + country['name'] + " found ")
                        location_detail['name'] = region['name'].lower()
                        location_detail['type'] = 'state'
                        location_detail['country'] = country['name'].lower()

                        self.create_location_index(location_detail['name'])
                        self.update_location_index(location_detail)

                        break

                    for city_index, city in enumerate(region['cities']):

                        if location == city['name'].lower():

                            print("City in " + region['name'] + ", " + country['name'] + " found ")
                            location_detail['name'] = region['name'].lower()
                            location_detail['type'] = 'city'
                            location_detail['region'] = region['name'].lower()
                            location_detail['country'] = country['name'].lower()

                            self.create_location_index(location_detail['name'])
                            self.update_location_index(location_detail)

                            break


            return location_detail

        # fast search start
        # locations = location.split(', ')
        #
        # no_of_locations = len(locations)
        #
        # print("locations")
        # print(locations)
        #
        # if no_of_locations > 1:
        #
        #     print("Country > 1 ")
        #     print(locations[no_of_locations - 1])
        #     search_loc = locations[no_of_locations - 1]
        #
        # else:
        #
        #     print("Country == 1 ")
        #     print(locations[0])
        #     search_loc = locations[0]
        # # fast search end
        #
        # location_info = {}
        #
        # ls_res = self.search_country(search_loc)
        #
        # if ls_res != False:
        #
        #     pass
        #
        # else: # search city
        #
        #     ls_res = word_tokenize(location)[0]
        #     location_info = self.search_city(ls_res)

