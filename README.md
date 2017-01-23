# ntc-check

A python module to check the JSON output of ntc-ansible against YAML files that define the 'correct' parameters.
The module checks outputs that are generated by ntc-ansible and placed in the specified location via the ansible copy module.
It is assumed that the outputs are the .response contents of the appropriate ntc-ansible output 

e.g. example ansible task to get 'show ip ospf neighbor' on Cisco IOS device
```
 - name: get show ip ospf neighbor
    ntc_show_command:
      connection: ssh
      command: 'show ip ospf neighbor'
      template_dir: '/usr/share/ansible/ntc-ansible/ntc-templates/templates'
      platform: '{{ platform }}'
      host: '{{ inventory_hostname }}'
      username: '{{ username }}'
      password: '{{ password }}'
    register: show_ip_ospf_neighbor_output

  - set_fact: show_ip_ospf_neighbor_output={{ show_ip_ospf_neighbor_output}}

  - debug: var=show_ip_ospf_neighbor_output.response

  - copy: content='{{ show_ip_ospf_neighbor_output.response }}' dest=./show_outputs/{{ inventory_hostname }}.show.ip.ospf.neighbor.output.txt
```
  
#DEPENDENCIES
- ansible 2.1+
- ntc-ansible (https://github.com/networktocode/ntc-ansible)
- python 2.x including ntc-ansible dependencies


#DEFINE CHECKS
YAML files (sample is located in ./correct_outputs) will define the desired outputs to be matched against. The YAML format MUST be consistent with the JSON output produced by the ntc-ansible modules.

Caveats: 
- all numbers have to be defined as a string with quotes as per the example.
- comparison is EXACT - e.g. will even pick up OSPF DR/BDR mismatches unless you specifically exclude - see below
- show ip route needs different methods owing to need to parse ECMP - see below

#PREREQUISITES
Before using:
- need YAML of hosts - YML list
- need LIST of parameters to exclude from comparison - must use exact ntc-ansible returned JSON key e.g. comparing OSPF neighbors you probably don't want 'dead_time'
- for multiple parameters use a python list ['exclude-A','exclude-B']

#HOW TO USE
- use ntc-ansible in an ansible play to grab details and place in per-host text files somewhere. MUST use naming schema 'host'.'template_name'
- instantiate the class defining common variables
- call method ntc_check.generate_host_list() to generate list of hosts
	- this will also instantiate a class attribute self.host_list
- call method ntc_check.generate_show_list("correct") to generate dictionary of correct values (gathered from YAML files).
	- this will also instantiate a class attribute self.correct_dict
- call method ntc_check.generate_show_list("output") to generate dictionary of output values (gathered from ntc-ansible outputs)
	- this will also instantiate a class attribute self.output_dict
- call method ntc_check.compare_generic to compare the two dictionaries
	- this will also instantiate the following class attributes (self explanatory):
		- compare_correct_dict
		- compare_mismatch_dict
		- compare_notfound_dict
	- dictionaries will be written to the path specific in the reports_path variable
	- comparison is LITERAL - use sanitise_parameters (see below) to exclude key-value pairs that don't make sense e.g. OSPF dead time or route age
	
#SHOW TO USE FOR SHOW IP ROUTE
Due to the need to handle ECMP and to merge the network/mask key-pairs into one key/value pair, use different methods for show ip route.
- Same first steps up to and including generating host list
- call method ntc_check.generate_routes_list("correct") to generate dictionary of correct routes (gathered from YAML files).
	- this will also instantiate a class attribute self.correct_dict
- call method ntc_check.generate_routes_list("output") to generate dictionary of output routes (gathered from ntc-ansible outputs)
	- this will also instantiate a class attribute self.output_dict
- call method ntc_check.compare_generic to compare the two dictionaries
	- this will also instantiate the following class attributes (self explanatory):
		- compare_correct_ECMP_dict
		- compare_mismatch_ECMP_dict
		- compare_correct_unique_dict
		- compare_mismatch_unique_dict
		- compare_notfound_unique_dict
	- dictionaries will be written to the path specific in the reports_path variable
	- comparison is LITERAL - use sanitise_parameters (see below) to exclude key-value pairs that don't make sense e.g. uptime
	- WARNING: ECMP route parsing treats mismatch the same as not found and cannot distinguish the difference - need to fix (not easy!)
	
#VARIABLES
- reports_path - path to place comparison reports
- correct_path - path with YAML files defining the correct output
- output_path - path where outputs of ntc_ansible are located
- host_file - YAML list of hosts
- correct_filename - naming convention for YAML files to grep, assumes device.format (e.g. ".show.ip.routes.output.txt")
- output_filename - naming convention for ntc_ansible output files to grep, assumes device.format (e.g. ".show.ip.routes.output.txt")
- compare - when calling ntc_check.compare_generic(), this is the key that is being compared e.g. to compare OSPF neighbors it would be "neighbor_id" - needs to match ntc_ansible JSON key EXACTLY
- sanitise_parameters - LIST of keys to ignore when comparing - useful for things like dead_time etc. where the show command's output cannot possibly be predicted or matched

#EXAMPLE: HOW TO USE
```
## example generic variables
correct_path = "./correct_outputs"
output_path = "./show_outputs"
host_file = "hosts.yml"
report_path = "./reports"

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

 ```

#EXAMPLE ANSIBLE COMPONENTS
- setuplab.yml - this ansible play sets up a sample lab environment which this repo was tested against.
- getdetails.yml - this ansible play obtains sample show outputs and places the outputs in ./show_outputs
	- show ip interface brief
	- show ip ospf neighbor
	- show ip route
 
#SAMPLE LAB
The sample lab is defined in hostvars via standard ansible YAML. It consists of 4 IOS routers in a ring. 
Lab topology is provided as a png file in the repo.
r4 is intentionally missing the configurations for Loopback88 (88.88.88.88/32) and the corresponding OSPF network statements.
This has the following consequences:
- THe interface Lo88 will come up as missing
- A number of OSPF adjacencies will come up as missing as they are defined as 4.4.4.4 but r4 will use 88.88.88.88
- routes to 88.88.88.88 are missing
- pings to 88.88.88.88 fails

#SAMPLE OUTPUT
Included in directory


