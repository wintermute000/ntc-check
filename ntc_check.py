#!/usr/bin/env python

import yaml
import os
import re
from pprint import pprint
from collections import OrderedDict


class ntc_check(object):

    def __init__(self, report_path, correct_path, output_path, host_file, correct_filename, output_filename, compare, sanitise_parameters=[], debug = ""):
        self.report_path = report_path
        self.correct_path = correct_path
        self.output_path = output_path
        self.host_file = host_file
        self.correct_filename = correct_filename
        self.output_filename = output_filename
        self.compare = compare
        self.sanitise_parameters = sanitise_parameters
        self.debug = ""
        
        # Report variables
        self.compare_correct_dict = {}
        self.compare_mismatch_dict = {}
        self.compare_notfound_dict = {}
        
        self.compare_correct_ECMP_dict = {}
        self.compare_mismatch_ECMP_dict = {}
        self.compare_notfound_ECMP_dict = {}
        
        self.compare_correct_unique_dict = {}
        self.compare_mismatch_unique_dict = {}
        self.compare_notfound_unique_dict = {}

    def generate_host_list(self):
        # Generate list of hosts to check
        hosts = yaml.load(open(self.correct_path + '/' + host_file, "r"))
        self.host_list = sorted(hosts)
        return sorted(hosts)

    def generate_show_list(self, category):
        # Build Dictionary with show outputs
        # Determine if method is being called for the correct attributes or output attributes
        # List all files in correct path and set method variables
        # Only use sanitise_parameters on output (exception handling)
        if category == 'correct':
            file_list_raw = os.listdir(correct_path)
            filename = self.correct_filename
            path = self.correct_path
            local_sanitise_parameters = None
        elif category == 'output':
            file_list_raw = os.listdir(output_path)
            filename = self.output_filename
            path = self.output_path
            local_sanitise_parameters = self.sanitise_parameters
        else:
            print('category argument must be "correct" or "output"')
            return None

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
                # Sanitise unwanted parameters with exception handling
                length = len(file_json)
                if local_sanitise_parameters is not None:
                    for j in range(length):
                        for s in local_sanitise_parameters:
                            del file_json[j][s]

                file_var = file_name.group(1)
                host_show_dict[file_var] = file_json

        if category == 'correct':
            self.correct_dict = host_show_dict
            return host_show_dict
        elif category == 'output':
            self.output_dict = host_show_dict
            return host_show_dict


    def generate_routes_list(self, category):
        # Custom generation module as to compare routes need to combine subnet/mask keypairs into single keypair
        # Build Dictionary with show outputs
        # Determine if method is being called for the correct attributes or output attributes
        # List all files in correct path and set method variables
        # Only use sanitise_parameters on output (exception handling)
        if category == 'correct':
            file_list_raw = os.listdir(correct_path)
            filename = self.correct_filename
            path = self.correct_path
            local_sanitise_parameters = None
        elif category == 'output':
            file_list_raw = os.listdir(output_path)
            filename = self.output_filename
            path = self.output_path
            local_sanitise_parameters = self.sanitise_parameters
        else:
            print('category argument must be "correct" or "output"')
            return None

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
                    if local_sanitise_parameters is not None:
                        for s in local_sanitise_parameters:
                            del file_json[j][s]
                file_var = file_name.group(1)
                host_show_dict[file_var] = file_json

        if category == 'correct':
            self.correct_dict = host_show_dict
            return host_show_dict
        elif category == 'output':
            self.output_dict = host_show_dict
            return host_show_dict

    def compare_generic(self):
        path = self.report_path
        # Iterate through devices and pick out the dictionary for the device in both the list of correct values and list of show values
        pprint("=========================================================")
        pprint("CHECKING " + self.compare)
        for device in self.host_list:
            host_compare_correct_list = []
            host_compare_mismatch_list = []
            host_compare_notfound_list = []
            correct_device = self.correct_dict.get(device)
            output_device = self.output_dict.get(device)

            pprint ("=================")
            pprint ("DEVICE: "+ device)

            # Iterate through correct list and find key/value
            for icorrect in correct_device:
                a = icorrect.get(self.compare)
                # marker
                occur = 0
                # Iterate through show list and find matching key/value
                for ishow in output_device:


                    if ishow[self.compare] == a:
                        # Compare dictionaries and return results
                        pprint ("Comparing " + a + " - first line is desired, second line is actual output for comparison")
                        pprint(icorrect,width=300)
                        pprint(ishow,width=300)
                        if icorrect == ishow:
                            pprint("OK for " + device + " interface "+ a)
                            pprint ("---")
                            occur = occur + 1
                            host_compare_correct_list.append(icorrect.copy())
                        else:
                            pprint("MISMATCH on " + device + " " + self.compare + " " + a)
                            pprint ("---")
                            occur = occur + 1
                            host_compare_mismatch_list.append(ishow.copy())
                # marker not found - correct line not found in all output lines
                if occur == 0:
                    print ("NOT FOUND - " + self.compare + " not found - " + a)
                    pprint("---")
                    host_compare_notfound_list.append(icorrect.copy())

            # After every device, create new key:pair in output dictionary
            self.compare_correct_dict[device] = host_compare_correct_list
            self.compare_mismatch_dict[device] = host_compare_mismatch_list
            self.compare_notfound_dict[device] = host_compare_notfound_list

        # At end, write reports
        correct_report_name = os.path.join(self.report_path, self.compare + "." + "correct.txt")
        mismatch_report_name = os.path.join(self.report_path, self.compare + "." + "mismatch.txt")
        notfound_report_name = os.path.join(self.report_path, self.compare + "." + "notfound.txt")
        with open(correct_report_name, "w") as correct_report:
            correct_report.write(str(self.compare_correct_dict))
        with open(mismatch_report_name, "w") as mismatch_report:
            mismatch_report.write(str(self.compare_mismatch_dict))
        with open(notfound_report_name, "w") as notfound_report:
            notfound_report.write(str(self.compare_notfound_dict))
        print("Results written to " + report_path + " for comparison on " + self.compare)
        pprint("=========================================================")

    def compare_routes(self):
        # Custom comparison module for routes as logic is different due to need to compare ECMP vs unique routes
        # Iterate through devices and pick out the dictionary for the device in both the list of correct values and list of show values
        path = self.report_path
        pprint("=========================================================")
        print ("CHECKING ROUTES")
        for device in self.host_list:
            host_compare_correct_ECMP_list = []
            host_compare_mismatch_ECMP_list = []
            host_compare_notfound_ECMP_list = []
            host_compare_correct_unique_list = []
            host_compare_mismatch_unique_list = []
            host_compare_notfound_unique_list = []
            correct_device = self.correct_dict.get(device)
            output_device = self.output_dict.get(device)

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
            for ishow_ECMP in output_device:
                network3 = ishow_ECMP.get("network")
                occur2 = 0

                for y in output_device:
                    netdupe2 = y.get("network")
                    if netdupe2 == network3:
                        occur2 = occur2 + 1
                        if occur2 >= 2 and y is not ishow_ECMP:
                            show_device_ECMP.append(y)
                            show_device_ECMP.append(ishow_ECMP)

            # Generate separate list of show unique routes
            show_device_unique = []
            for ishow_unique in output_device:
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
                            host_compare_correct_ECMP_list.append(a.copy())
                            occur3 = occur3 + 1
                ### If EXACT ECMP entry not found iterate again and report all mismatching attributes
                # current logic does not manage to differ between ECMP mismatch or ECMP not found
                if occur3 == 0:
                    print ("MISMATCH - ECMP entry with correct attributes not found - " + str(a))
                    host_compare_mismatch_ECMP_list.append(a.copy())

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
                            host_compare_correct_unique_list.append(d.copy())
                            occur4 = occur4 + 1
                        else:
                            print("MISMATCH - found unique route with incorrect attributes - " + str(d))
                            print("COMPARISON correct route has following attributes       - " + str(c))
                            host_compare_mismatch_unique_list.append(d.copy())
                            occur4 = occur4 + 1

                if occur4 == 0:
                    print ("NOT FOUND - unique entry not found - " + str(c))
                    host_compare_notfound_unique_list.append(c.copy())
                    
            # After every device, create new key:pair in output dictionary
            self.compare_correct_ECMP_dict[device] = host_compare_correct_ECMP_list
            self.compare_mismatch_ECMP_dict[device] = host_compare_mismatch_ECMP_list
    
            self.compare_correct_unique_dict[device] = host_compare_correct_unique_list
            self.compare_mismatch_unique_dict[device] = host_compare_mismatch_unique_list
            self.compare_notfound_unique_dict[device] = host_compare_notfound_unique_list

        # At end, write reports
        correct_ECMP_report_name = os.path.join(self.report_path, "routes.ECMP.correct.txt")
        mismatch_ECMP_report_name = os.path.join(self.report_path, "routes.ECMP.mismatch.txt")

        correct_unique_report_name = os.path.join(self.report_path, "routes.unique.correct.txt")
        mismatch_unique_report_name = os.path.join(self.report_path, "routes.unique.mismatch.txt")
        notfound_unique_report_name = os.path.join(self.report_path, "routes.unique.notfound.txt")


        with open(correct_ECMP_report_name, "w") as correct_ECMP_report:
            correct_ECMP_report.write(str(self.compare_correct_ECMP_dict))
        with open(mismatch_ECMP_report_name, "w") as mismatch_ECMP_report:
            mismatch_ECMP_report.write(str(self.compare_mismatch_ECMP_dict))
        with open(correct_unique_report_name, "w") as correct_unique_report:
            correct_unique_report.write(str(self.compare_correct_unique_dict))
        with open(mismatch_unique_report_name, "w") as mismatch_unique_report:
            mismatch_unique_report.write(str(self.compare_mismatch_unique_dict))
        with open(notfound_unique_report_name, "w") as notfound_unique_report:
            notfound_unique_report.write(str(self.compare_notfound_unique_dict))
        print ("=================")
        print("Results written to " + report_path + " for comparison on " + self.compare)
        print("WARNING: ECMP routes that mismatch and not found are listed together in '.mismatch' file")
        pprint("=========================================================")

if __name__ == "__main__":
    ### example variables
    correct_path = "./correct_outputs"
    output_path = "./show_outputs"
    host_file = "hosts.yml"
    report_path = "./reports"

    ### REFERENCE: class variables - correct_path,output_path,host_file,correct_filename,output_filename,compare, sanitise_parameters)
    ### EXAMPLE check show ip interface brief

    correct_interfaces_filename = "interfaces.yml"
    output__interfaces_filename = "show.ip.interface.brief.output.txt"
    comparison_interfaces = "intf"

    job_interfaces = ntc_check(report_path, correct_path,output_path,host_file,correct_interfaces_filename, output__interfaces_filename, comparison_interfaces)
    job_interfaces.generate_host_list()
    job_interfaces.generate_show_list("correct")
    job_interfaces.generate_show_list("output")
    job_interfaces.compare_generic()

    ### EXAMPLE check OSPF neighbors - exclude ["dead_time"]
    correct_ospf_nei_filename = "ospf.neighbors.yml"
    output_ospf_nei_filename = "show.ip.ospf.neighbor.output.txt"
    comparison_ospf_nei = "neighbor_id"
    sanitise_ospf_nei_parameters = ["dead_time"]


    job_ospf_nei = ntc_check(report_path, correct_path,output_path,host_file,correct_ospf_nei_filename, output_ospf_nei_filename, comparison_ospf_nei, sanitise_ospf_nei_parameters)
    job_ospf_nei.generate_host_list()
    job_ospf_nei.generate_show_list("correct")
    job_ospf_nei.generate_show_list("output")
    job_ospf_nei.compare_generic()

    ### example check routes - ["metric", "uptime", "nexthopif"], call specific route parsing show
    correct_routes_filename = "routes.yml"
    output_routes_filename = "show.ip.route.output.txt"
    comparison_routes = 'network'
    sanitise_routes_parameters = ["metric", "uptime", "nexthopif"]

    ###
    job_routes = ntc_check(report_path, correct_path,output_path,host_file,correct_routes_filename, output_routes_filename, comparison_routes, sanitise_routes_parameters)
    job_routes.generate_host_list()
    job_routes.generate_routes_list("correct")
    job_routes.generate_routes_list("output")
    job_routes.compare_routes()

