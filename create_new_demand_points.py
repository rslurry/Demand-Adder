#! /usr/bin/env python

"""
This script is meant to be run like
    ./create_new_demand_points.py OrangeCounty.json

The input JSON file must have the following fields defined:
    input_demand_file : string, path to the demand file that you wish to modify
                        Example: "path/to/old_demand_data.json"
    output_demand_file : string, path to save the new, modified demand file
                         Example: "path/to/new_demand_data.json"
    
    OVERWRITE : (optional) bool, determines whether you can overwrite the input demand file (true) or not (false).
                                 Only applicable if `input_demand_file` and `output_demand_file` are the same.
                Default: false
    HUMAN_READABLE : (optional) bool, determines whether to make the output demand_data.json file have indentation 
                                      structure for readability (true) or not to minimize file size (false).
                      Default: false
    MAX_WORKERS : (optional) int, sets the number of workers to use for parallel processing.
                   Default: None (total number of CPU threads)
    
    MAXPOPSIZE : int, maximum size any pop can be.  
                      Pops larger than this value are split into multiple pops to follow this setting.
                 Example: 200
    CALCULATE_ROUTES : bool, determines whether to calculate commuting routes.  
                             Recommended to set this to false when initially testing out boundaries and clustering.
                       Example: true
    bbox : list of ints, the [min_lon, min_lat, max_lon, max_lat] boundary for the city.  Required to calculate routes.
           Example: [-77.8216, 43.0089, -77.399, 43.3117],
    
    airport : list of strings, IATA codes for the local airport 
                               Note: The first listed airport is used here to uniquely identify a city.  
              Example: ["ROC"]
    airport_daily_passengers : list of ints, number of daily passengers at the city's airports.
                               Example: [7000] 
    airport_loc : list of list of floats, coordinates in [lon, lat] of the city's airports.
                  Example: [[-77.67166, 43.12919]]
    airport_required_locs : list of list of list of floats, coordinates in [lon, lat] where you want airports' travelers 
                                                    to reside.  One pop will be placed at the demand bubble closest to 
                                                    each specified coordinate.
                                                    If you don't care to set this, then use [] for each airport (e.g., 
                                                    use [[], []] for 2 airports) and the code will decide automatically.
                            Example: [[[-77.61298,  43.15729], [-77.60688,  43.15614], [-77.58936,  43.1547 ],
                                       [-77.59342,  43.15564], [-77.6741 ,  43.21029], [-77.61647,  43.10564],
                                       [-77.61391,  43.08771], [-77.55086,  43.11299], [-77.57981,  43.19774],
                                       [-77.4567 ,  43.2146 ], [-77.44227,  43.21617], [-77.68496,  43.18599],
                                       [-77.64286,  43.0601 ], [-77.65179,  43.05802], [-77.44922,  43.01093],
                                       [-77.51514,  43.09333]]]
    air_pop_size_req : list of ints, size of airports' pops assigned by `airport_required_locs`.  
                            Note that if this exceeds `MAXPOPSIZE` then each pop will be split into multiple smaller pops.
                       Example: [200]
    air_pop_size_remain : list of ints, size of airports' pops assigned automatically by the code.
                          Note that if this exceeds `MAXPOPSIZE` then each pop will be split into multiple smaller pops.
                          Example: [150]
    
    universities : list of strings, 2-4 letter identifier for each university considered.
                                    All subsequent university-related parameters must correspond exactly to this ordering.
                   Example: ["UR", "RIT", "SJF", "NU", "RWU"],
    univ_loc : list of list of floats, coordinates for each university's demand bubble.
               Example: [[-77.62668, 43.12989], [-77.67629, 43.08389], [-77.51239, 43.11575], 
                         [-77.51873, 43.10218], [-77.79857, 43.12568]]
    univ_merge_within : list of ints, distance in meters to merge any nearby demand points into the new university demand point.
                   Example: [0, 350, 300, 0, 0]
    students : list of ints, number of students that attend each campus.
               Example: [11946, 17166, 4000, 2500, 1500]
    perc_oncampus : list of floats, percentage of students that live in on-campus housing for each university.
                    Example: [0.45, 0.4, 0.33, 0.5, 0.6]
    univ_pop_size : list of ints, size of each pop created for each university.
                    Example: [75, 75, 75, 75, 75]
    univ_perc_travel : list of list of floats, fraction of students that live [on campus, off campus] that travel on an average day.   
                                Default: [0.3, 0.5]

    entertainment : list of strings, short identifiers for each entertainment location
    ent_loc : list of list of floats, coordinates in [lon, lat] for each entertainment location 
    ent_merge_within : list of ints, distance in meters to merge any nearby demand points into the new entertainment demand point
    ent_req_residences : list of list of list of floats, like `airport_required_locs` but for entertainment locations
    ent_size : list of ints, number of daily visitors to each entertainment location
    ent_pop_size : list of ints, size of each pop created for each entertainment location
    
    bases : list of strings, short identifiers for each military base
            Example: ["JFTB"]
    base_loc : list of list of floats, coordinates in [lon, lat] for each military base
               Example: [[-118.05455, 33.79490]]
    base_merge_within : list of ints, distance in meters to merge any nearby demand points into the new military base demand point
                        Example: [0]
    personnel : list of ints, number of personnel at each military base
                Example: [7200]
    perc_onbase : list of floats, percentage of personnel that live on base
                  Example: [0]
    base_pop_size : list of ints, size of each pop created for each base
                    Example: [200]

"""

import sys, os
import copy
import csv
import functools
import glob
import gzip
import json
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
import requests
import time
import numpy as np
import geopandas as gpd
from shapely.ops import unary_union, polygonize
from shapely.geometry import Point
from tqdm import tqdm
import osmnx as ox
import networkx as nx

from collections import defaultdict

np.random.seed(42)

###############################################################################

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    From https://stackoverflow.com/a/4913653 w/ slight modifications
    """
    # convert decimal degrees to radians 
    lon1, lat1 = np.radians([lon1, lat1])
    lon2 = np.radians(lon2)
    lat2 = np.radians(lat2)

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.asin(np.sqrt(a)) 
    r = 6371000 # Radius of earth in meters. Use 3956 for miles. Determines return value units.
    return c * r


def process_home_node(i, demand, G, points_by_id):
    home_point = demand['points'][i]
    home_id = home_point['id']
    home_node = ox.nearest_nodes(G, Y=home_point['location'][1], X=home_point['location'][0])
    pops = [p for p in demand['pops'] if p['residenceId'] == home_id]
    for p in pops:
        job_id = p['jobId']
        job_point = points_by_id[job_id]
        try:
            job_node = ox.nearest_nodes(G, Y=job_point['location'][1], X=job_point['location'][0])
            path_nodes = nx.shortest_path(G, home_node, job_node, weight='travel_time')
            distance_in_meters = nx.path_weight(G, path_nodes, weight='length')
            travel_time_in_seconds = nx.path_weight(G, path_nodes, weight='travel_time')
        except:
            try:
                # Find closest road segment and project a point onto it
                x, y = job_point['location']
                u, v, key = ox.nearest_edges(G, Y=y, X=x)
                edge_data = G[u][v][key]
                line = edge_data['geometry']
                point = Point(x, y)
                nearest_point = line.interpolate(line.project(point))
                new_node = max(G.nodes) + 1
                G.add_node(new_node, x=nearest_point.x, y=nearest_point.y)
                dist_to_u = Point(G.nodes[u]['x'], G.nodes[u]['y']).distance(nearest_point)
                dist_to_v = Point(G.nodes[v]['x'], G.nodes[v]['y']).distance(nearest_point)
                G.add_edge(new_node, u, length=dist_to_u)
                G.add_edge(new_node, v, length=dist_to_v)
                job_node = ox.nearest_nodes(G, X=x, Y=y)
                path_nodes = nx.shortest_path(G, home_node, job_node, weight='travel_time')
                distance_in_meters = nx.path_weight(G, path_nodes, weight='length')
                travel_time_in_seconds = nx.path_weight(G, path_nodes, weight='travel_time')
            except:
                path_nodes = []
                distance_in_meters = 0
                travel_time_in_seconds = 0
        # Add time penalties for intersections + traffic: 5 seconds per intersection
        travel_time_in_seconds += len(path_nodes) * 5
        
        p['drivingSeconds']  = int(travel_time_in_seconds)
        p['drivingDistance'] = int(np.ceil(distance_in_meters))
    return pops


###############################################################################

def main():
    start = time.time()
    # Load the configuration file
    with open(sys.argv[1], 'r') as fcfg:
        cfg = json.load(fcfg)

    # Defines for preparing the demand file
    MAXPOPSIZE = cfg['MAXPOPSIZE']
    CALCULATE_ROUTES = cfg['CALCULATE_ROUTES']
    if CALCULATE_ROUTES:
        bbox = cfg['bbox']
    
    try:
        HUMAN_READABLE = cfg['HUMAN_READABLE']
    except:
        HUMAN_READABLE = False
    
    try:
        MAX_WORKERS = cfg['MAX_WORKERS']
    except:
        MAX_WORKERS = None
    
    try:
        OVERWRITE = cfg['OVERWRITE']
    except:
        OVERWRITE = False

    input_demand_file = cfg['input_demand_file']
    output_demand_file = cfg['output_demand_file']
    if input_demand_file == output_demand_file and not OVERWRITE:
        raise ValueError("Same input_demand_file and output_demand_file specified, but OVERWRITE is not set to true.")

    

    # Airport data
    try:
        airport = cfg['airport']
        if not isinstance(airport, list):
            airport = [airport]
        airport = [iata.upper() for iata in airport]
        
        airport_daily_passengers = cfg['airport_daily_passengers']
        if not isinstance(airport_daily_passengers, list):
            airport_daily_passengers = [airport_daily_passengers]
        assert len(airport) == len(airport_daily_passengers), str(len(airport))+" airports provided, but "+str(len(airport_daily_passengers))+" daily passenger values provided.  There must be one daily passenger value provided per airport specified."
    
        airport_loc = cfg['airport_loc']
        if not isinstance(airport_loc[0], list):
            airport_loc = [airport_loc]
        assert len(airport) == len(airport_loc), str(len(airport))+" airports provided, but "+str(len(airport_loc))+" airport locations provided.  There must be one [lon, lat] coordinate value provided per airport specified."
    
        try:
            airport_required_locs = cfg['airport_required_locs']
        except:
            print("airport_required_locs not specified/understood.  All airport pops will be placed according to the code's simple model.")
            airport_required_locs = [[] for i in range(len(airport))]
        else:
            if not len(airport_required_locs):
                airport_required_locs = [[] for i in range(len(airport))]
    
        try:
            air_pop_size_req = cfg['air_pop_size_req']
            if not isinstance(air_pop_size_req, list):
                air_pop_size_req = [air_pop_size_req for i in range(len(airport))]
        except:
            print("air_pop_size_req not specified/understood.  Any required locations for airport pops will have MAXPOPSIZE people.")
            air_pop_size_req = [MAXPOPSIZE for i in range(len(airport))]
        try:
            air_pop_size_remain = cfg['air_pop_size_remain']
            if not isinstance(air_pop_size_remain, list):
                air_pop_size_remain = [air_pop_size_remain for i in range(len(airport))]
        except:
            print("air_pop_size_remain not specified/understood.  Using MAXPOPSIZE ("+str(MAXPOPSIZE)+") for airport pops assigned by the code.")
            air_pop_size_remain = [MAXPOPSIZE for i in range(len(airport))]
    except Exception as e:
        print("Airport data either not provided or missing required parameters.  No demand added for airports.\n"+str(e))
        airport = False

    # University data
    try:
        universities = cfg['universities']
        if not isinstance(universities, list):
            universities = [universities]
    
        univ_loc = cfg['univ_loc']
        if not isinstance(univ_loc[0], list):
            univ_loc = [univ_loc]
        assert len(universities) == len(univ_loc), str(len(universities))+" universities provided, but "+str(len(univ_loc))+" university locations provided.  There must be one [lon, lat] coordinate value provided per university specified."
    
        try:
            univ_merge_within = cfg['univ_merge_within']
        except:
            print("univ_merge_within not specified/understood.  No bubbles will be merged around the universities.")
            univ_merge_within = [0 for i in range(len(universities))]
        assert len(universities) == len(univ_merge_within), str(len(universities))+" universities provided, but "+str(len(univ_merge_within))+" merge distances provided.  There must be one merge distance value provided per university specified."
    
        students = cfg['students']
        if not isinstance(students, list):
            students = [students]
        assert len(universities) == len(students), str(len(universities))+" universities provided, but "+str(len(students))+" student counts provided.  There must be one student count value provided per university specified."
    
        perc_oncampus = cfg['perc_oncampus']
        if not isinstance(perc_oncampus, list):
            perc_oncampus = [perc_oncampus]
        assert len(universities) == len(perc_oncampus), str(len(universities))+" universities provided, but "+str(len(perc_oncampus))+" % on campus values provided.  There must be one % on campus value provided per university specified."
    
    
        try:
            univ_pop_size = cfg['univ_pop_size']
        except:
            print("univ_pop_size not specified/understood.  Using MAXPOPSIZE ("+str(MAXPOPSIZE)+") for university pops.")
            univ_pop_size = [MAXPOPSIZE for i in range(len(universities))]
        assert len(universities) == len(univ_pop_size), str(len(universities))+" universities provided, but "+str(len(univ_pop_size))+" pop sizes provided.  There must be one pop size per university specified."
    
        try:
            univ_perc_travel = cfg['univ_perc_travel']
        except:
            print("Assuming that 30% of on-campus students and 50% of off-campus students travel daily.")
            univ_perc_travel = [0.3, 0.5]
        assert len(univ_perc_travel) == 2, "univ_pop_size must be a list of 2 values.\nFormat: [% on-campus students that travel daily, % off-campus students that travel daily]"
    except Exception as e:
        print("University data either not provided or missing required parameters.  No demand added for universities.\n"+str(e))
        universities = False

    # Entertainment data
    try:
        entertainment = cfg['entertainment']
        if not isinstance(entertainment, list):
            entertainment = [entertainment]
        ent_loc = cfg['ent_loc']
        if not isinstance(ent_loc[0], list):
            ent_loc = [ent_loc]
        assert len(ent_loc) == len(entertainment), str(len(entertainment))+" entertainment locations specified, but "+str(len(ent_loc))+" entertainment locations were provided."
        try:
            ent_req_residences = cfg['ent_req_residences']
        except:
            print("ent_req_residences not specified/understood.  All entertainment pops will be placed according to the code's simple model.")
            ent_req_residences = [[] for i in range(len(entertainment))]
        else:
            if not len(ent_req_residences):
                ent_req_residences = [[] for i in range(len(entertainment))]
            assert len(ent_req_residences) == len(entertainment), str(len(entertainment))+" entertainment locations specified, but "+str(len(ent_req_residences))+" groups of required entertainment residences were provided."

        try:
            ent_merge_within = cfg['ent_merge_within']
        except:
            print("ent_merge_within not specified/understood.  No bubbles will be merged around the entertainment points.")
            ent_merge_within = [0 for i in range(len(entertainment))]
        assert len(entertainment) == len(ent_merge_within), str(len(entertainment))+" entertainment points provided, but "+str(len(ent_merge_within))+" merge distances provided.  There must be one merge distance value provided per entertainment points specified."
        
        ent_size = cfg['ent_size']
        assert len(ent_size) == len(entertainment), str(len(entertainment))+" entertainment locations specified, but "+str(len(ent_size))+"entertainment demand sizes were provided."
        
        try:
            ent_pop_size = cfg['ent_pop_size']
        except:
            print("ent_pop_size not specified/understood.  Using MAXPOPSIZE ("+str(MAXPOPSIZE)+") for entertainment pops.")
            ent_pop_size = [MAXPOPSIZE for i in range(len(entertainment))]
        else:
            assert len(ent_pop_size) == len(entertainment), str(len(entertainment))+" entertainment locations specified, but "+str(len(ent_pop_size))+" entertainment pop sizes were provided."
    except Exception as e:
        print("Entertainment data either not provided or missing required parameters.  No demand added for entertainment.\n"+str(e))
        entertainment = False

    # Military data
    try:
        bases = cfg['bases']
        if not isinstance(bases, list):
            bases = [bases]

        base_loc = cfg['base_loc']
        if not isinstance(base_loc[0], list):
            base_loc = [base_loc]
        assert len(bases) == len(base_loc), str(len(bases))+" bases provided, but "+str(len(base_loc))+" base locations provided.  There must be one [lon, lat] coordinate value provided per base specified."

        try:
            base_merge_within = cfg['base_merge_within']
        except:
            print("base_merge_within not specified/understood.  No bubbles will be merged around the bases.")
            base_merge_within = [0 for i in range(len(bases))]
        assert len(bases) == len(base_merge_within), str(len(bases))+" bases provided, but "+str(len(base_merge_within))+" base distances provided.  There must be one merge distance value provided per base specified."

        personnel = cfg['personnel']
        if not isinstance(personnel, list):
            personnel = [personnel]
        assert len(personnel) == len(bases), str(len(bases))+" bases provided, but "+str(len(personnel))+" personnel counts provided.  There must be one personnel count value provided per base specified."

        perc_onbase = cfg['perc_onbase']
        if not isinstance(perc_onbase, list):
            perc_onbase = [perc_onbase]
        assert len(bases) == len(perc_onbase), str(len(bases))+" bases provided, but "+str(len(perc_onbase))+" % on base values provided.  There must be one % on base value provided per base specified."


        try:
            base_pop_size = cfg['base_pop_size']
        except:
            print("base_pop_size not specified/understood.  Using MAXPOPSIZE ("+str(MAXPOPSIZE)+") for base pops.")
            base_pop_size = [MAXPOPSIZE for i in range(len(bases))]
        assert len(bases) == len(base_pop_size), str(len(bases))+" bases provided, but "+str(len(base_pop_size))+" pop sizes provided.  There must be one pop size per base specified."

        try:
            base_perc_travel = cfg['base_perc_travel']
        except:
            print("Assuming that 30% of on-site employees and 50% of off-site employees travel daily.")
            base_perc_travel = [0.3, 0.5]
        assert len(base_perc_travel) == 2, "univ_pop_size must be a list of 2 values.\nFormat: [% on-campus students that travel daily, % off-campus students that travel daily]"
    except:
        bases = False

    ###############################################################################

    print("Modifying demand file", input_demand_file)

    print("Loading file")
    with open(input_demand_file, 'r') as foo:
        demand = json.load(foo)
    
    points_by_id = {p["id"]: p for p in demand["points"]}

    print("Initial points:", len(demand['points']))
    print("Initial pops:", len(demand['pops']))
    print("Initial total pop size:", np.sum([p['size'] for p in demand['pops']]))
    print("Initial workers:", np.sum([p['jobs'] for p in demand["points"]]))
    print("Initial residents:", np.sum([p['residents'] for p in demand["points"]]))

    ###############################################################################

    if airport:
        print("Adding airport demand to simulate travelers")
        air_points = []
        counter = 0
        for iair in range(len(airport)):
            print(" ", airport[iair])
    
            point = {
                "id": "AIR_"+airport[iair],
                "location": airport_loc[iair],
                "jobs": 0,
                "residents": 0,
                "popIds": []
            }
    
            point_locs = np.array([p['location'] for p in demand['points']])
    
            # Calculate where the pops will "live"
            # Required points - Find nearest points to these coords
            ilocs_air_req = np.zeros(len(airport_required_locs[iair]), dtype=int)
            for i in range(len(airport_required_locs[iair])):
                ilocs_air_req[i] = haversine(airport_required_locs[iair][i][0], airport_required_locs[iair][i][1], 
                                               point_locs[:,0], point_locs[:,1]).argmin()
    
            # And determine remaining number of points that will get pops
            ntarget_locs_air_remain = int((airport_daily_passengers[iair] - \
                                           (air_pop_size_req[iair] * len(airport_required_locs[iair]))) / \
                                          air_pop_size_remain[iair])
            size_of_points = np.array([p['residents'] for p in demand['points']])
            size_of_points[ilocs_air_req] = 0 # Don't consider these points
            ilocs_air_remain = np.random.choice(size_of_points.size, size=ntarget_locs_air_remain, replace=False, p=size_of_points/size_of_points.sum())
    
            # Make them
            for it in range(2):
                if not it:
                    psize = air_pop_size_req[iair]
                    locs_arr = ilocs_air_req
                else:
                    psize = air_pop_size_remain[iair]
                    locs_arr = ilocs_air_remain
                for i, iloc in enumerate(locs_arr):
                    counter += 1
                    pop = {
                            "id" : "AIR_"+airport[iair]+'_'+str(counter),
                            "residenceId" : demand['points'][iloc]["id"],
                            "jobId" : point["id"],
                            "size" : psize,
                            "drivingSeconds"  : -1,
                            "drivingDistance" : -1
                    }
                    demand['pops'].append(pop)
                    demand['points'][iloc]['residents'] += pop['size']
                    point["jobs"] += pop['size']
                    demand['points'][iloc]['popIds'].append(pop['id'])
                    point['popIds'].append(pop['id'])
            air_points.append(point)
    
        demand['points'] += air_points

    ###############################################################################

    if universities:
        print("Adding university demand")
        univ_points = []
        for iuniv in range(len(universities)):
            print(" ", universities[iuniv], students[iuniv], perc_oncampus[iuniv])
            oncampus = int(perc_oncampus[iuniv] * students[iuniv]) # live on campus, "work" elsewhere
            offcampus = students[iuniv] - oncampus # "work" on campus, live elsewhere
            
            point = {
                "id": "UNI_" + universities[iuniv],
                "location": univ_loc[iuniv],
                "jobs": 0,
                "residents": 0,
                "popIds": []
            }
            
            if univ_merge_within[iuniv]:
                # Merge nearby points into this one
                point_locs = np.array([p['location'] for p in demand['points']])
                dists = haversine(point['location'][0], point['location'][1], 
                                    point_locs[:,0], point_locs[:,1])
                iloc_merge = np.arange(len(demand['points']), dtype=int)[dists <= univ_merge_within[iuniv]][::-1] # largest to smallest
                pops_by_id = {p["id"]: p for p in demand["pops"]}
                for iloc in iloc_merge:
                    point['jobs'] += demand['points'][iloc]['jobs']
                    point['residents'] += demand['points'][iloc]['residents']
                    point['popIds'] += demand['points'][iloc]['popIds']
                    for popid in demand['points'][iloc]['popIds']:
                        if pops_by_id[popid]['residenceId'] == demand['points'][iloc]['id']:
                            pops_by_id[popid]['residenceId'] = point['id']
                        if pops_by_id[popid]['jobId'] == demand['points'][iloc]['id']:
                            pops_by_id[popid]['jobId'] = point['id']
                    del demand['points'][iloc]
            
            # On-campus students
            point_locs = np.array([p['location'] for p in demand['points']])
            iloc_airport = [p['id'][:4] == "AIR_" for p in demand['points']]
            size_of_points = np.array([p['jobs'] for p in demand['points']])
            size_of_points[iloc_airport] = 0 # Don't consider the airport
            dist_of_points = haversine(point['location'][0], point['location'][1], 
                                         point_locs[:,0], point_locs[:,1])
            weight_of_points = size_of_points / dist_of_points**2 # Prefer places near campus
            ilocs = np.random.choice(weight_of_points.size, 
                                     size=int((oncampus * univ_perc_travel[0])//univ_pop_size[iuniv]), 
                                     p=weight_of_points/weight_of_points.sum())
            i = 0
            for i, iloc in enumerate(ilocs):
                pop = {
                        "id" : "UNI_" + universities[iuniv] + "_" + str(i+1),
                        "residenceId" : point["id"],
                        "jobId" : demand['points'][iloc]["id"],
                        "size" : int(univ_pop_size[iuniv]),
                        "drivingSeconds"  : 1,
                        "drivingDistance" : 1
                }
                demand['pops'].append(pop)
                demand['points'][iloc]['jobs'] += pop['size']
                point["residents"] += pop['size']
                demand['points'][iloc]['popIds'].append(pop['id'])
                point['popIds'].append(pop['id'])
    
            # Off-campus students
            size_of_points = np.array([p['residents'] for p in demand['points']])
            size_of_points[iloc_airport] = 0 # Don't consider the airport
            dist_of_points = haversine(point['location'][0], point['location'][1], 
                                         point_locs[:,0], point_locs[:,1])
            weight_of_points = size_of_points / dist_of_points
            ilocs = np.random.choice(weight_of_points.size, 
                                     size=int((offcampus * univ_perc_travel[1])//univ_pop_size[iuniv]), 
                                     p=weight_of_points/weight_of_points.sum())
            for j, iloc in enumerate(ilocs):
                pop = {
                        "id" : "UNI_" + universities[iuniv] + "_" + str(i+j+2),
                        "residenceId" : demand['points'][iloc]["id"],
                        "jobId" : point["id"],
                        "size" : int(univ_pop_size[iuniv]),
                        "drivingSeconds"  : -1,
                        "drivingDistance" : -1
                }
                demand['pops'].append(pop)
                demand['points'][iloc]['residents'] += pop['size']
                point["jobs"] += pop['size']
                demand['points'][iloc]['popIds'].append(pop['id'])
                point['popIds'].append(pop['id'])
            univ_points.append(point)
    
        demand['points'] += univ_points

    ###############################################################################

    if entertainment:
        print("Adding entertainment demand")
        ent_points = []
        counter = 0
        for ient in range(len(entertainment)):
            print(" ", entertainment[ient], ent_size[ient])
            point = {
                "id": "ENT_" + entertainment[ient],
                "location": ent_loc[ient],
                "jobs": 0,
                "residents": 0,
                "popIds": []
            }

            if ent_merge_within[iuniv]:
                # Merge nearby points into this one
                point_locs = np.array([p['location'] for p in demand['points']])
                dists = haversine(point['location'][0], point['location'][1], 
                                    point_locs[:,0], point_locs[:,1])
                iloc_merge = np.arange(len(demand['points']), dtype=int)[dists <= ent_merge_within[iuniv]][::-1] # largest to smallest
                pops_by_id = {p["id"]: p for p in demand["pops"]}
                for iloc in iloc_merge:
                    point['jobs'] += demand['points'][iloc]['jobs']
                    point['residents'] += demand['points'][iloc]['residents']
                    point['popIds'] += demand['points'][iloc]['popIds']
                    for popid in demand['points'][iloc]['popIds']:
                        if pops_by_id[popid]['residenceId'] == demand['points'][iloc]['id']:
                            pops_by_id[popid]['residenceId'] = point['id']
                        if pops_by_id[popid]['jobId'] == demand['points'][iloc]['id']:
                            pops_by_id[popid]['jobId'] = point['id']
                    del demand['points'][iloc]
            
            point_locs = np.array([p['location'] for p in demand['points']])

            # Calculate where the pops will "live"
            # Required points - Find nearest points to these coords
            ilocs_ent_req = np.zeros(len(ent_req_residences[ient]), dtype=int)
            for i in range(len(ent_req_residences[ient])):
                ilocs_ent_req[i] = haversine(ent_req_residences[ient][i][0], ent_req_residences[ient][i][1], 
                                               point_locs[:,0], point_locs[:,1]).argmin()

            # And determine remaining number of points that will get pops
            psize = ent_pop_size[ient]
            ntarget_locs_ent_remain = int((ent_size[ient] - (psize * len(ent_req_residences[ient]))) / \
                                          psize)
            size_of_points = np.array([p['residents'] for p in demand['points']])
            iloc_airport = [p['id'][:4] == "AIR_" for p in demand['points']]
            size_of_points[iloc_airport ] = 0 # Don't consider these points
            size_of_points[ilocs_ent_req] = 0 
            dist_of_points = haversine(point['location'][0], point['location'][1], 
                                         point_locs[:,0], point_locs[:,1])
            weight_of_points = size_of_points / dist_of_points
            
            ilocs_ent_remain = np.random.choice(size_of_points.size, size=ntarget_locs_ent_remain, 
                                                replace=False, 
                                                p=weight_of_points/weight_of_points.sum())
                                                #p=(size_of_points + weight_of_points) / \
                                                #  (size_of_points.sum() + weight_of_points.sum()))

            # Make them
            for it in range(2):
                if not it:
                    locs_arr = ilocs_ent_req
                else:
                    locs_arr = ilocs_ent_remain
                for i, iloc in enumerate(locs_arr):
                    counter += 1
                    pop = {
                            "id" : "ENT_"+entertainment[ient]+'_'+str(counter),
                            "residenceId" : demand['points'][iloc]["id"],
                            "jobId" : point["id"],
                            "size" : psize,
                            "drivingSeconds"  : -1,
                            "drivingDistance" : -1
                    }
                    demand['pops'].append(pop)
                    demand['points'][iloc]['residents'] += pop['size']
                    point["jobs"] += pop['size']
                    demand['points'][iloc]['popIds'].append(pop['id'])
                    point['popIds'].append(pop['id'])
            ent_points.append(point)

        demand['points'] += ent_points


    ###############################################################################
    
    if bases:
        print("Adding base demand")
        base_points = []
        for ibase in range(len(bases)):
            print(" ", bases[ibase], personnel[ibase], perc_onbase[ibase])
            onbase = int(perc_onbase[ibase] * personnel[ibase]) # live on campus, "work" elsewhere
            offbase = personnel[ibase] - onbase # "work" on campus, live elsewhere
            #print(bases[ibase])
            point = {
                "id": bases[ibase],
                "location": base_loc[ibase],
                "jobs": 0,
                "residents": 0,
                "popIds": []
            }
            
            if base_merge_within[ibase]:
                # Merge nearby points into this one
                point_locs = np.array([p['location'] for p in demand['points']])
                dists = haversine(point['location'][0], point['location'][1], 
                                    point_locs[:,0], point_locs[:,1])
                iloc_merge = np.arange(len(demand['points']), dtype=int)[dists <= base_merge_within[ibase]][::-1] # largest to smallest
                pops_by_id = {p["id"]: p for p in demand["pops"]}
                for iloc in iloc_merge:
                    point['jobs'] += demand['points'][iloc]['jobs']
                    point['residents'] += demand['points'][iloc]['residents']
                    point['popIds'] += demand['points'][iloc]['popIds']
                    for popid in demand['points'][iloc]['popIds']:
                        if pops_by_id[popid]['residenceId'] == demand['points'][iloc]['id']:
                            pops_by_id[popid]['residenceId'] = point['id']
                        if pops_by_id[popid]['jobId'] == demand['points'][iloc]['id']:
                            pops_by_id[popid]['jobId'] = point['id']
                    del demand['points'][iloc]
            
            # On-base pops
            point_locs = np.array([p['location'] for p in demand['points']])
            iloc_airport = [p['id'][:4] == "AIR_" for p in demand['points']]
            size_of_points = np.array([p['jobs'] for p in demand['points']])
            size_of_points[iloc_airport] = 0 # Don't consider the airport
            dist_of_points = haversine(point['location'][0], point['location'][1], 
                                         point_locs[:,0], point_locs[:,1])
            weight_of_points = size_of_points / dist_of_points**2 # Prefer places near base
            ilocs = np.random.choice(weight_of_points.size, 
                                     size=int((onbase * base_perc_travel[0])//base_pop_size[ibase]), 
                                     p=weight_of_points/weight_of_points.sum())
            i = 0
            for i, iloc in enumerate(ilocs):
                pop = {
                        "id" :bases[ibase] + "_" + str(i+1),
                        "residenceId" : point["id"],
                        "jobId" : demand['points'][iloc]["id"],
                        "size" : int(base_pop_size[ibase]),
                        "drivingSeconds"  : -1,
                        "drivingDistance" : -1
                }
                demand['pops'].append(pop)
                demand['points'][iloc]['jobs'] += pop['size']
                point["residents"] += pop['size']
                demand['points'][iloc]['popIds'].append(pop['id'])
                point['popIds'].append(pop['id'])

            # Off-base pops
            size_of_points = np.array([p['residents'] for p in demand['points']])
            size_of_points[iloc_airport] = 0 # Don't consider the airport
            dist_of_points = haversine(point['location'][0], point['location'][1], 
                                         point_locs[:,0], point_locs[:,1])
            weight_of_points = size_of_points / dist_of_points
            ilocs = np.random.choice(weight_of_points.size, 
                                     size=int((offbase * base_perc_travel[1])//base_pop_size[ibase]), 
                                     p=weight_of_points/weight_of_points.sum())
            for j, iloc in enumerate(ilocs):
                pop = {
                        "id" :  bases[ibase] + "_" + str(i+j+2),
                        "residenceId" : demand['points'][iloc]["id"],
                        "jobId" : point["id"],
                        "size" : int(base_pop_size[ibase]),
                        "drivingSeconds"  : -1,
                        "drivingDistance" : -1
                }
                demand['pops'].append(pop)
                demand['points'][iloc]['residents'] += pop['size']
                point["jobs"] += pop['size']
                demand['points'][iloc]['popIds'].append(pop['id'])
                point['popIds'].append(pop['id'])
            base_points.append(point)

        demand['points'] += base_points


    ###############################################################################

    # Parallelize the route calculations over home nodes
    if CALCULATE_ROUTES:
        points_by_id = {p["id"]: p for p in demand["points"]}
        pops_by_id   = {p["id"]: p for p in demand["pops"  ]}
        
        # Set up OSM graph
        print("Initializing OSM drive network graph")
        G = ox.graph_from_bbox(bbox, network_type='drive')#, simplify=False)
        G = ox.truncate.largest_component(G, strongly=True)
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        
        # Prepare arguments for parallel jobs
        print("Calculating driving paths for each home node.  This may take a while.")
        process_home_node_worker = functools.partial(process_home_node, 
                                                     demand=demand, G=G, 
                                                     points_by_id=points_by_id)
        with Pool() as pool:
            results = []
            for r in tqdm(pool.imap(process_home_node_worker, range(len(demand['points']))), total=len(demand['points'])):
                results.append(r)
        
        # Flatten results and update demand
        for ret in results:
            for pop in ret:
                pops_by_id[pop['id']]['drivingSeconds']  = pop['drivingSeconds']
                pops_by_id[pop['id']]['drivingDistance'] = pop['drivingDistance']

    ###############################################################################

    # Make sure that pops are <=200 in size
    print("Pops before enforcing size <="+str(MAXPOPSIZE)+":", len(demand['pops']))
    for p in demand['pops']:
        if p['size'] > MAXPOPSIZE:
            niter = int(np.ceil(p['size'] / MAXPOPSIZE))
            for n in range(1, niter):
                pop = copy.deepcopy(p)
                pop['id'] += "_"+str(n)
                if n < niter - 1:
                    # More than MAXPOPSIZE pops remain - cap at MAXPOPSIZE
                    pop["size"] = MAXPOPSIZE
                else:
                    # Less than MAXPOPSIZE remains - put all into this pop
                    pop["size"] = int(p['size']) % MAXPOPSIZE
                demand["pops"].append(pop)
            # Update the original pop
            p['size'] = MAXPOPSIZE

    print("Final points:", len(demand['points']))
    print("Final pops:", len(demand['pops']))
    print("Final total pop size:", np.sum([p['size'] for p in demand['pops']]))
    print("Final workers:", np.sum([p['jobs'] for p in demand['points']]))
    print("Final residents:", np.sum([p['residents'] for p in demand['points']]))

    ###############################################################################

    # Save out demand file
    with open(output_demand_file, "w") as json_file:
        if HUMAN_READABLE:
            json.dump(demand, json_file, indent=4)
        else:
            json.dump(demand, json_file, indent=None, separators=(',', ':'))
    end = time.time()
    print("Time elapsed:", end-start, "s")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
