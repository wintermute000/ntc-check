# automated-testlab

A collection of ansible scripts and python scripts to automate data gathering and testing of Cisco IOS devices.

DEPENDENCIES
- ansible 2.1+
- ntc-ansible (https://github.com/networktocode/ntc-ansible)
- python 2.x including ntc-ansible dependencies

ANSIBLE COMPONENTS
- getdetails.yml - this ansible play obtains show outputs and places the outputs in ./show_outputs
- pingtest.yml - this ansible play runs multiple pings and places the outputs in ./show_outputs
- setuplab.yml - this ansible play sets up a sample lab environment which this repo was tested against.

CORRECT DEFINITIONS
YAML files located in ./correct_outputs will define the desired outputs to be matched against. The YAML format MUST be consistent with the JSON output produced by the ntc-ansible modules.
One exception is the ping testing - as the pings are called via an ansible play for easy iteration, the pings are defined in /hostvars via standard ansible YAML.
Caveat: all numbers have to be defined as a string with quotes as per the example.

PYTHON COMPONENTS
- check-interfaces.py - checks the <device>.show.ip.interface.brief.output.txt file in ./show_outputs against the YAML file defined in <device>.interfaces.yml in ./correct_outputs.
Extra interfaces (i.e. those not defined in ./correct_outputs file) will be ignored.
To pass a check, the JSON has to match exactly i.e. all interface attributes defined in the YAML.

- check-ospf-neighbors.py - checks the <device>.show.ip.ospf.neighbor.output.txt file in ./show_outputs against the YAML file defined in <device>.ospf.neighbors.yml in ./correct_outputs.
Extra neighbors (i.e. those not defined in ./correct_outputs file) will be ignored.
Note the dead time is not checked for obvious reasons and the python script will sanitise the JSON when parsing.
To pass a check, the JSON has to match exactly i.e. all neighbor attributes defined in the YAML e.g. DR/BDR.

- check-routes.py - checks the <device>.show.ip.route.output.txt file in ./show_outputs against the YAML file defined in <device>.routes.yml in ./correct_outputs.
Extra routes (i.e. those not defined in ./correct_outputs file) will be ignored.
Note the metric/interface/uptime is not checked and the python script will sanitise the JSON when parsing.

- checkping.py - checks the results of the ping tests defined in hostvars

Multipath checking appears to work, however, observe the following caveats
   - >2 ECMP paths have not been tested
   - For unique routes, if the same network/mask is present but the attributes do not match (e.g. Type), a warning is given and the mismatch explicitly shown. However, this does not happen for ECMP mismatches - both the lack of the correct ECMP routes and an attribute mismatch will return the same MISMATCH error (so to find an attribute mismatch you will have to manually look into the output).
 
SAMPLE LAB
The sample lab is defined in hostvars via standard ansible YAML. It consists of 4 IOS routers in a ring. 
Lab topology is provided as a png file in the repo.
r4 is intentionally missing the configurations for Loopback88 (88.88.88.88/32) and the corresponding OSPF network statements.
This has the following consequences:
- THe interface Lo88 will come up as missing
- A number of OSPF adjacencies will come up as missing as they are defined as 4.4.4.4 but r4 will use 88.88.88.88
- routes to 88.88.88.88 are missing
- pings to 88.88.88.88 fails

USAGE
- setup lab via ansible playbook setuplab.yml (as per standard ansible, basic SSH connectivity to hosts and correct ansible ./hosts file is required)
- call ansible playbook getdetails.yml
- call pingtest.yml
- run the appropriate python test script

EXAMPLE OUTPUTS
- example-getdetails-json.txt - this illustrates the data gathered by getdetails.yml
- example-pingtest.txt - this illustrates the data gathered by getdetails.yml
- example-check-interfaces.txt - this shows the output of check-interfaces.py
- example-check-ospf-neighbors.txt - this shows the output of check-interfaces.py
- example-check-routes.txt - this shows the output of check-interfaces.py
- example-checkping.txt - this shows the output of check-interfaces.py
