#!/usr/bin/env python

import yaml
import os
import re
from pprint import pprint
from collections import OrderedDict

class ntc_check():

    # def __init__(self,correct_path,output_path,host_file,correct_filename,output_filename,sanitise_parameters):
    #     self.correct_path = correct_path
    #     self.output_path = output_path
    #     self.host_file = host_file
    #     self.correct_filename = correct_filename
    #     self.output_filename = output_filename
    #     self.sanitise_parameters = sanitise_parameters

    def generate_host_list(self, correct_path, host_file):
        # Generate list of hosts to check
        host_list = yaml.load(open(correct_path + '/' + host_file, "r"))
        return sorted(host_list)

    def generate_show_list(self, path, filename, sanitise_parameters=[]):
        # Build Dictionary with show outputs
        # List all files in show_outputs subdirectory

        file_list_raw = os.listdir(path)

        # Instantiate dictionary containing show values
        host_show_dict = {}

        # Iterate through show_outputs subdirectory
        # Match correct input - all files ending with "show.ip.interface.brief.output.txt"
        # Convert yaml to json
        # Create master show values dictionary in format { hostname:[ {interface dictionary} ] }

        for file in file_list_raw:
            if file.endswith(filename):
                file_name = re.match(r'(.*).'+ filename, file)
                file_json = yaml.load(open(path + '/' + file, "r"))
                # Sanitise unwanted parameters - ONLY CALL ON OUTPUTS NOT ON CORRECT
                length = len(file_json)
                for j in range(length):
                    for s in sanitise_parameters:
                        del file_json[j][s]

                file_var = file_name.group(1)
                host_show_dict[file_var] = file_json

        # print ("dictionary with SHOW values:")
        # print(host_show_dict)
        return host_show_dict

    def generate_routes_list(self, path, filename, sanitise_parameters=[]):
        # Custom generation module as to compare routes need to combine subnet/mask keypairs into single keypair
        # Build Dictionary with show outputs
        # List all files in show_outputs subdirectory

        file_list_raw = os.listdir(path)

        # Instantiate raw dictionary containing show values
        host_show_dict = {}

        # Iterate through show_outputs subdirectory
        # Match correct input - all files ending with "show.ip.interface.brief.output.txt"
        # Convert yaml to json
        # Create master show values dictionary in format { hostname:[ {interface dictionary} ] }
        # Sanitise JSON to combine network and mask

        for file in file_list_raw:
            if file.endswith(filename):
                file_name = re.match(r'(.*).' + filename, file)
                file_json = yaml.load(open(path + '/' + file, "r"))
                # Sanitise JSON to combine network and mask
                # Sanitise dictionary to remove metric and uptime and nexthopif
                length = len(file_json)
                for j in range(length):
                    x = file_json[j]["network"]
                    y = file_json[j]["mask"]
                    del file_json[j]["network"]
                    del file_json[j]["mask"]
                    file_json[j]["network"] = x + y
                    for s in sanitise_parameters:
                        del file_json[j][s]
                file_var = file_name.group(1)
                host_show_dict[file_var] = file_json

        # print ("dictionary with SHOW values:")
        # print(host_show_dict)
        return host_show_dict

    def compare_generic(self, hosts, correct, show, compare):

        # Iterate through devices and pick out the dictionary for the device in both the list of correct values and list of show values
        pprint("=========================================================")
        pprint("CHECKING " + compare)
        for device in hosts:

            correct_device = correct.get(device)
            show_device = show.get(device)

            pprint ("=================")
            pprint ("DEVICE: "+ device)

            # Iterate through correct list and find key/value
            for icorrect in correct_device:
                a = icorrect.get(compare)
                occur = 0
                # Iterate through show list and find matching key/value
                for ishow in show_device:
                    if ishow[compare] == a:
                        # Compare dictionaries and return results
                        pprint ("Comparing " + a + " - first line is desired, second line is actual output for comparison")
                        pprint(icorrect,width=300)
                        pprint(ishow,width=300)
                        if icorrect == ishow:
                            pprint("OK for " + device + " interface "+ a)
                            pprint ("---")
                            occur = occur + 1
                        else:
                            pprint("MISMATCH on " + device + " " + compare + " " + a)
                            pprint ("---")
                            occur = occur + 1
                if occur == 0:
                    print ("MISMATCH - " + compare + " not found - " + a)
                    pprint("---")

    def compare_routes(self, hosts, correct_routes, show_routes):
        # Custom comparison module for routes as logic is different due to need to compare ECMP vs unique routes
        # Iterate through devices and pick out the dictionary for the device in both the list of correct values and list of show values
        pprint("=========================================================")
        print ("CHECKING ROUTES")
        for device in hosts:
            correct_device = correct_routes.get(device)
            show_device = show_routes.get(device)

            # Generate separate list of correct ECMP routes
            correct_device_ECMP = []

            for icorrect_ECMP in correct_device:

                network = icorrect_ECMP.get("network")
                occur = 0

                for x in correct_device:
                    netdupe = x.get("network")
                    if netdupe == network:
                        occur = occur + 1
                        if occur >= 2 and x is not icorrect_ECMP:
                            correct_device_ECMP.append(x)
                            correct_device_ECMP.append(icorrect_ECMP)

            # Generate separate list of correct unique routes
            correct_device_unique = []
            for icorrect_unique in correct_device:
                network2 = icorrect_unique.get("network")
                if any(d['network'] == network2 for d in correct_device_ECMP):
                    pass
                else:
                    correct_device_unique.append(icorrect_unique)

            # Generate separate list of show ECMP routes
            show_device_ECMP = []
            for ishow_ECMP in show_device:
                network3 = ishow_ECMP.get("network")
                occur2 = 0

                for y in show_device:
                    netdupe2 = y.get("network")
                    if netdupe2 == network3:
                        occur2 = occur2 + 1
                        if occur2 >= 2 and y is not ishow_ECMP:
                            show_device_ECMP.append(y)
                            show_device_ECMP.append(ishow_ECMP)

            # Generate separate list of show unique routes
            show_device_unique = []
            for ishow_unique in show_device:
                network4 = ishow_unique.get("network")
                if any(d['network'] == network4 for d in show_device_ECMP):
                    pass
                else:
                    show_device_unique.append(ishow_unique)

            # Iterate through sanitised dictionaries and find matching routes
            print ("=================")
            print ("DEVICE: " + device + " ECMP routes")

            # Iterate through and find matching ECMP routes
            for a in correct_device_ECMP:
                route = a.get("network")
                occur3 = 0
                # Compare dictionaries and return results
                for b in show_device_ECMP:
                    if b["network"] == route:
                        if a == b:
                            print("Found matching ECMP route - " + str(a))
                            occur3 = occur3 + 1
                ### If EXACT ECMP entry not found iterate again and report all mismatching attributes
                if occur3 == 0:
                    print ("MISMATCH - ECMP entry with correct attributes not found - " + str(a))

                # Iterate through and find matching unique routes
            print ("DEVICE: " + device + " unique routes")
            for c in correct_device_unique:
                route2 = c.get("network")
                occur4 = 0
                # Compare dictionaries and return results
                for d in show_device_unique:
                    if d["network"] == route2:
                        if c == d:
                            print("Found matching unique route - " + str(c))
                            occur4 = occur4 + 1
                        else:
                            print("MISMATCH - found unique route with incorrect attributes - " + str(d))
                            print("COMPARISON correct route has following attributes       - " + str(c))
                            occur4 = occur4 + 1

                if occur4 == 0:
                    print ("MISMATCH - unique entry not found - " + str(c))


### example variables
correct_path = "./correct_outputs"
output_path = "./show_outputs"
host_file = "hosts.yml"
correct_interfaces_filename = "interfaces.yml"
output__interfaces_filename = "show.ip.interface.brief.output.txt"
comparison_interfaces = "intf"

correct_ospf_nei_filename = "ospf.neighbors.yml"
output_ospf_nei_filename = "show.ip.ospf.neighbor.output.txt"
sanitise_ospf_nei_parameters = ["dead_time"]
comparison_ospf_nei = "neighbor_id"

correct_routes_filename = "routes.yml"
output_routes_filename = "show.ip.route.output.txt"
sanitise_routes_parameters = ["metric", "uptime", "nexthopif"]

### example run
job = ntc_check()
hosts = job.generate_host_list(correct_path,host_file)

### example check interfaces
correct_interfaces = job.generate_show_list(correct_path, correct_interfaces_filename )
show_interfaces = job.generate_show_list(output_path, output__interfaces_filename )
check_interfaces = job.compare_generic(hosts, correct_interfaces, show_interfaces, comparison_interfaces)

### example check OSPF neighbors - exclude ["dead_time"]
correct_ospf_nei = job.generate_show_list(correct_path, correct_ospf_nei_filename, )
show_ospf_nei = job.generate_show_list(output_path, output_ospf_nei_filename, sanitise_ospf_nei_parameters )
check_ospf_nei = job.compare_generic(hosts, correct_ospf_nei, show_ospf_nei, comparison_ospf_nei)

### example check routes - ["metric", "uptime", "nexthopif"], call specific route parsing show
correct_routes = job.generate_routes_list(correct_path, correct_routes_filename, )
show_routes = job.generate_routes_list (output_path, output_routes_filename, sanitise_routes_parameters )
check_routes = job.compare_routes(hosts, correct_routes, show_routes)

