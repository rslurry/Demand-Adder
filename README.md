# Demand Adder

Demand Adder is a tool to add demand to Subway Builder maps.  At present, it consists of two scripts:
- `demand_adder.py`: the original tool. Adds demand to existing demand points.  Note: Only requires base Python.
- `create_new_demand_points.py`: creates new demand points for airports, universities, entertainment attractions, and/or military bases.  Follows the methodology of slurry's US demand generator (https://github.com/rslurry/subwaybuilder-US-demand-data).  Note: Requires a specific set of Python packages to run (see Installation below).

## Installation

1. Download Python.  You can get it from https://www.python.org/downloads/ if not already installed, or you can use a Python environment manager (recommended).  For details on setting up a compatible Python environment to run the `create_new_demand_points.py` script, follow the instructions at https://github.com/rslurry/subwaybuilder-US-demand-data and use that repo's environment file (https://github.com/rslurry/subwaybuilder-US-demand-data/blob/main/environment.yml).

2. Then, download the .py files from here into some folder.

## demand_adder.py Usage

Run the script.  It will prompt you for the demand file you wish to edit; on Windows it should be something like C:\Users\Sam\AppData\Local\Programs\Subway Builder\resources\data\[CITY CODE]\demand_data.

The script asks for a residence id and a work id. You can find these by opening the demand_data.json and finding which ids correspond to in game demand bubbles. I often ctrl + f and look for demand bubbles that have the same amount of residents/jobs.

Once you find where you want residents and where you want workers, the script asks how much demand you wish to add. Any number should work.

### Limitations

This script was made very quick and dirty to demonstrate what is possible, so at the moment there are two main drawbacks.

The script must be in the same folder as the demand_data.json and additional demand is point to point, not spread across an area. 

This means that if I wanted to model for example the significant cross-border traffic in San Diego with a border demand bubble, I would have to manually assign every single commute.

## create_new_demand_points.py Usage

Create a JSON configuration file.  The available parameters are provided below, followed by a full example.

This script is meant to be run like

    ./create_new_demand_points.py OrangeCounty.json

If you're downloading a pre-compiled release, then it might look something like

    ./create_new_demand_points.bin OrangeCounty.json

### Core Parameters
<table>
  <tr>
    <th style="width:150px;">Parameter</th>
    <th style="width:100px;">Type</th>
    <th style="width:250px;">Description</th>
    <th>Example</th>
  </tr>

  <tr>
    <td>input_demand_file</td>
    <td>string</td>
    <td>Path to the input demand file that you wish to modify.</td>
    <td><code>path/to/old_demand_data.json</code></td>
  </tr>

  <tr>
    <td>output_demand_file</td>
    <td>string</td>
    <td>Path to save the new, modified demand file</td>
    <td><code>path/to/new_demand_data.json</code></td>
  </tr>

  <tr>
    <td>OVERWRITE</td>
    <td>(optional)<br>bool</td>
    <td>Determines whether you can overwrite the input demand file (true) or not (false).<br>Only applicable if `input_demand_file` and `output_demand_file` are the same.<br>Default: false.</td>
    <td><code>true</code></td>
  </tr>

  <tr>
    <td>HUMAN_READABLE</td>
    <td>(optional)<br>bool</td>
    <td>Indent JSON output for readability.<br>Default: false.</td>
    <td><code>true</code></td>
  </tr>

  <tr>
    <td>MAX_WORKERS</td>
    <td>(optional)<br>int</td>
    <td>Number of workers for parallel processing.<br>Default: None (as many threads as you have).</td>
    <td><code>4</code></td>
  </tr>

  <tr>
    <td>MAXPOPSIZE</td>
    <td>int</td>
    <td>Maximum size of any pop; larger pops are split.<br><b>Note:</b> &le;200 is recommended due to the capacity of trains. If a pop is larger than a train can hold, it cannot use the metro.</td>
    <td><code>200</code></td>
  </tr>

  <tr>
    <td>CALCULATE_ROUTES</td>
    <td>bool</td>
    <td>Whether to calculate commuting routes<br><b>Note:</b> This can take a long time. Set to false while testing to save time until you're ready to make the final version.</td>
    <td><code>true</code></td>
  </tr>
</table>

### Airport‑related Parameters
<table>
  <tr>
    <th style="width:150px;">Parameter</th>
    <th style="width:100px;">Type</th>
    <th style="width:200px;">Description</th>
    <th>Example</th>
  </tr>

  <tr>
    <td>airport</td>
    <td>list of strings</td>
    <td>IATA codes for local airports; first uniquely identifies the city.</td>
    <td><code>["ROC"]</code></td>
  </tr>

  <tr>
    <td>airport_daily_passengers</td>
    <td>list of ints</td>
    <td>Daily passengers at each airport.</td>
    <td><code>[7000]</code></td>
  </tr>

  <tr>
    <td>airport_loc</td>
    <td>list of list of floats</td>
    <td>Coordinates of the city's airports.</td>
    <td><code>[[-77.67166, 43.12919]]</code></td>
  </tr>

  <tr>
    <td>airport_required_locs</td>
    <td>list of list of list</td>
    <td>Preferred residence locations for airport travelers.</td>
    <td><code>[[[-77.61298, 43.15729], ...]]</code></td>
  </tr>

  <tr>
    <td>air_pop_size_req</td>
    <td>list of ints</td>
    <td>Pop sizes assigned via airport_required_locs.</td>
    <td><code>[200]</code></td>
  </tr>

  <tr>
    <td>air_pop_size_remain</td>
    <td>list of ints</td>
    <td>Remaining airport pop sizes assigned automatically.</td>
    <td><code>[150]</code></td>
  </tr>
</table>


### University‑related Parameters
<table>
  <tr>
    <th style="width:150px;">Parameter</th>
    <th style="width:100px;">Type</th>
    <th style="width:200px;">Description</th>
    <th>Example</th>
  </tr>

  <tr>
    <td>universities</td>
    <td>list of strings</td>
    <td>Identifiers for each university.</td>
    <td><code>["UR","RIT","SJF","NU","RWU"]</code></td>
  </tr>

  <tr>
    <td>univ_loc</td>
    <td>list of list of floats</td>
    <td>Coordinates for each university's demand bubble.</td>
    <td><code>[[-77.62668, 43.12989], ...]</code></td>
  </tr>

  <tr>
    <td>univ_merge_within</td>
    <td>list of ints</td>
    <td>Merge distance (meters) for nearby demand points.</td>
    <td><code>[0, 350, 300, 0, 0]</code></td>
  </tr>

  <tr>
    <td>students</td>
    <td>list of ints</td>
    <td>Number of students at each campus.</td>
    <td><code>[11946, 17166, 4000, 2500, 1500]</code></td>
  </tr>

  <tr>
    <td>perc_oncampus</td>
    <td>list of floats</td>
    <td>Percent of students living on campus.</td>
    <td><code>[0.45, 0.4, 0.33, 0.5, 0.6]</code></td>
  </tr>

  <tr>
    <td>univ_pop_size</td>
    <td>list of ints</td>
    <td>Pop size created for each university.</td>
    <td><code>[75, 75, 75, 75, 75]</code></td>
  </tr>

  <tr>
    <td>univ_perc_travel</td>
    <td>list of list of floats</td>
    <td>Fraction of students [on‑campus, off‑campus] who travel daily.</td>
    <td><code>[0.3, 0.5]</code></td>
  </tr>
</table>

### Entertainment‑related Parameters
<table>
  <tr>
    <th style="width:150px;">Parameter</th>
    <th style="width:100px;">Type</th>
    <th style="width:200px;">Description</th>
    <th style="width:202px;">Example</th>
  </tr>

  <tr>
    <td>entertainment</td>
    <td>list of strings</td>
    <td>Identifiers for entertainment locations.</td>
    <td><code>["AQUA", "CY", "RAV"]</code></td>
  </tr>

  <tr>
    <td>ent_loc</td>
    <td>list of list of floats</td>
    <td>Coordinates for entertainment locations.</td>
    <td><code>[[-76.60832, 39.28540],
  [-76.62232, 39.28318],
  [-76.62269, 39.27800]]</code></td>
  </tr>

  <tr>
    <td>ent_merge_within</td>
    <td>list of ints</td>
    <td>Merge distance (meters) for entertainment demand points.</td>
    <td><code>[0, 0, 0]</code></td>
  </tr>

  <tr>
    <td>ent_req_residences</td>
    <td>list of list of list</td>
    <td>Like airport_required_locs. Required residence locations for entertainment visitors.</td>
    <td><code>[]</code></td>
  </tr>

  <tr>
    <td>ent_size</td>
    <td>list of ints</td>
    <td>Daily visitors to each entertainment location.</td>
    <td><code>[4110, 6247, 4384]</code></td>
  </tr>

  <tr>
    <td>ent_pop_size</td>
    <td>list of ints</td>
    <td>Pop size created for each entertainment location.</td>
    <td><code>[200, 200, 200]</code></td>
  </tr>

</table>


### Military base‑related Parameters
<table>
  <tr>
    <th style="width:150px;">Parameter</th>
    <th style="width:100px;">Type</th>
    <th style="width:200px;">Description</th>
    <th style="width:202px;">Example</th>
  </tr>

  <tr>
    <td>bases</td>
    <td>list of strings</td>
    <td>Identifiers for military base locations.</td>
    <td><code>["JFTB"]</code></td>
  </tr>

  <tr>
    <td>base_loc</td>
    <td>list of list of floats</td>
    <td>Coordinates for military base locations.</td>
    <td><code>[[-118.05455, 33.79490]]</code></td>
  </tr>

  <tr>
    <td>base_merge_within</td>
    <td>list of ints</td>
    <td>Merge distance (meters) for base demand points.</td>
    <td><code>[0]</code></td>
  </tr>

  <tr>
    <td>personnel</td>
    <td>list of ints</td>
    <td>Number of personnel at each base location.</td>
    <td><code>[7200]</code></td>
  </tr>

  <tr>
    <td>perc_onbase</td>
    <td>list of floats</td>
    <td>Percent of personnel living on base</td>
    <td><code>[0]</code></td>
  </tr>

  <tr>
    <td>base_pop_size</td>
    <td>list of ints</td>
    <td>Pop size created for each base location.</td>
    <td><code>[200]</code></td>
  </tr>

</table>

### Example: OrangeCounty.json
```
{
    "input_demand_file" : "path/to/old_demand_data.json",
    "output_demand_file" : "path/to/new_demand_data.json",
    
    "OVERWRITE" : false,
    "MAXPOPSIZE" : 200,
    "CALCULATE_ROUTES" : true,
    
    "airport" : ["SNA", "FUL"],
    "airport_daily_passengers" : [30000, 600], 
    "airport_loc" : [[-117.86288, 33.67888], [-117.97976, 33.87049]],
    "airport_required_locs" : [],
    "air_pop_size_req" : [200, 100],
    "air_pop_size_remain" : [200, 100],
    
    "universities" : ["UCI", "CUI", "WU", "SAC"],
    "univ_loc" : [[-117.84274, 33.64599], [-117.80905, 33.65429], [-117.84799, 33.68552], [-117.88874, 33.75853]],
    "univ_merge_within" : [0, 0, 0, 200],
    "students" : [37000, 3500, 7200, 20000],
    "perc_oncampus" : [0.48, 0.29, 0, 0],
    "univ_pop_size" : [200, 75, 100, 200],
    
    "entertainment": ["DL", "CA", "KBF", "HB", "LB", "NB", "DP", "CCHD", "CCMB", "CCRP", "CCPP", "IRP", "MSJC", "OCMA"],
    "ent_loc" : [[-117.91896, 33.81209], [-117.91918, 33.80762], [-118.00135, 33.84403],
                 [-118.00324, 33.65600], [-117.78571, 33.54229], [-117.92915, 33.60742],
                 [-117.69239, 33.46026], [-117.84012, 33.57428], [-117.82180, 33.56029],
                 [-117.83297, 33.56615], [-117.85368, 33.58010], [-117.75369, 33.79772],
                 [-117.66268, 33.50206], [-117.88128, 33.69166]],
    "ent_req_residences" : [],
    "ent_size" : [47600, 27600, 12200, 8200, 16000, 19200, 6800, 1100, 1800, 1200, 600, 4200, 850, 900],
    "ent_pop_size" : [200, 200, 200, 200, 200, 200, 200, 100, 100, 100, 50, 200, 50, 100],

    "bases" : ["JFTB"],
    "base_loc" : [[-118.05455, 33.79490]],
    "base_merge_within" : [0],
    "personnel" : [7200],
    "perc_onbase" : [0],
    "base_pop_size" : [200]
}
```


## Contributing

This script is super simplistic and more a proof of concept. I would love to see how you guys can improve it!
