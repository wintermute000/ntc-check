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


#CORRECT DEFINITIONS
YAML files (sample is located in ./correct_outputs) will define the desired outputs to be matched against. The YAML format MUST be consistent with the JSON output produced by the ntc-ansible modules.

Caveat: all numbers have to be defined as a string with quotes as per the example.

Caveat: comparison is EXACT - e.g. will even pick up OSPF DR/BDR mismatches unless you specifically exclude - see below

Caveat: show ip route has different methods owing to need to parse ECMP - see below

#HOW TO USE
Before using:
- need YAML of hosts - YML list
- need LIST of parameters to exclude from comparison - must use exact ntc-ansible returned JSON key e.g. comparing OSPF neighbors you probably don't want 'dead_time'
- for multiple parameters use a python list ['exclude-A','exclude-B']

- use ntc-ansible in an ansible play to grab details and place in per-host text files somewhere. MUST use naming schema '<host>.<template_name>'
- instantiate the Class
- generate the list of hosts - requires YML list of hosts
- generate the list of correct JSON - call method generate_show_list(<path of correct YAML files> , <template_name>)
- generate the list of ntc-ansible obtained JSON - call method generate_show_list(<path of show output YAML files> , <template_name>, <paramters_to_exclude>)
- run the comparison - call method compare_generic(<hosts>, <correct list>, <show list>, <exact key to compare e.g. 'neighbor_id'>)

#FOR SHOW IP ROUTE:
Use different methods
- generate the list of correct JSON - call method generate_routes_list(<path of correct YAML files> , <template_name>)
- generate the list of ntc-ansible obtained JSON - call method generate_routes_list(<path of show output YAML files> , <template_name>, <paramters_to_exclude>)
- run the comparison - call method compare_routes(<hosts>, <correct list>, <show list>, <exact key to compare e.g. 'neighbor_id'>)


#EXAMPLE: HOW TO USE
```
### example variables
correct_path = './correct_outputs'
output_path = './show_outputs'
host_file = 'hosts.yml'
correct_interfaces_filename = 'interfaces.yml'
output__interfaces_filename = 'show.ip.interface.brief.output.txt'
comparison_interfaces = 'intf'

correct_ospf_nei_filename = 'ospf.neighbors.yml'
output_ospf_nei_filename = 'show.ip.ospf.neighbor.output.txt'
sanitise_ospf_nei_parameters = ['dead_time']
comparison_ospf_nei = 'neighbor_id'

correct_routes_filename = 'routes.yml'
output_routes_filename = 'show.ip.route.output.txt'
sanitise_routes_parameters = ['metric', 'uptime', 'nexthopif']

### example run
job = ntc_check()
hosts = job.generate_host_list(correct_path,host_file)

### example check interfaces
correct_interfaces = job.generate_show_list(correct_path, correct_interfaces_filename )
show_interfaces = job.generate_show_list(output_path, output__interfaces_filename )
check_interfaces = job.compare_generic(hosts, correct_interfaces, show_interfaces, comparison_interfaces)

### example check OSPF neighbors - exclude ['dead_time']
correct_ospf_nei = job.generate_show_list(correct_path, correct_ospf_nei_filename, )
show_ospf_nei = job.generate_show_list(output_path, output_ospf_nei_filename, sanitise_ospf_nei_parameters )
check_ospf_nei = job.compare_generic(hosts, correct_ospf_nei, show_ospf_nei, comparison_ospf_nei)

### example check routes - ['metric', 'uptime', 'nexthopif'], call specific route parsing show
correct_routes = job.generate_routes_list(correct_path, correct_routes_filename, )
show_routes = job.generate_routes_list (output_path, output_routes_filename, sanitise_routes_parameters )
check_routes = job.compare_routes(hosts, correct_routes, show_routes)
th the lack of the correct ECMP routes and an attribute mismatch will return the same MISMATCH error (so to find an attribute mismatch you will have to manually look into the output).
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

