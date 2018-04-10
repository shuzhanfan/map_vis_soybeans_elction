#!/usr/bin/env python

#This is the class to manipulate/preprocess the data.

import os
import numpy as np
import pandas as pd
import json

class DataPreprocess():
    def __init__(self, file_path):
        self.file_path = file_path
        self.soybeans     = pd.read_csv(file_path + "soybeans_production_2016.csv", thousands=",")
        self.election     = pd.read_csv(file_path + "presidential_election_2016.csv")
        self.senate       = pd.read_csv(file_path + "us_senate_2017.csv")
        self.house        = pd.read_csv(file_path + "us_house_2017.csv")
        self.state_fips   = pd.read_csv(file_path + "state_fips.csv")
        self.cd113_json   = json.load(open(file_path + "cd113.json"))
        self.county_geo   = os.path.join(file_path, "us_counties.json")
        self.county_geo_1 = os.path.join(file_path, "us_counties.json")
        self.state_geo    = os.path.join(file_path, "us_states.json")

    def geo_files(self):
        return self.county_geo, self.county_geo_1, self.state_geo

    def preprocess_soybeans(self):
        soybeans = self.soybeans
        soybeans = soybeans.dropna(subset=["County ANSI"])
        soybeans["State ANSI"]  = soybeans["State ANSI"].astype(str)
        soybeans["Value"]       = soybeans["Value"].astype(np.int64)
        soybeans["County ANSI"] = soybeans["County ANSI"].astype(np.int64).astype(str)

        def state_ansi(row):
            state = row["State ANSI"]
            if len(state) == 1:
                return "0"+state
            else:
                return state

        def county_ansi(row):
            county = row["County ANSI"]
            if len(county) == 1:
                return "00"+county
            elif len(county) == 2:
                return "0"+county
            else:
                return county

        soybeans["State ANSI"]  = soybeans.apply(state_ansi, axis=1)
        soybeans["County ANSI"] = soybeans.apply(county_ansi, axis=1)
        soybeans["FIPS"]        = soybeans["State ANSI"] + soybeans["County ANSI"]

        return soybeans

    def preprocess_pres_elec(self):
        election = self.election
        election["combined_fips"] = election["combined_fips"].astype(str)

        def fips(row):
            one_fips = row["combined_fips"]
            if len(one_fips) == 4:
                return "0"+one_fips
            else:
                return one_fips

        election["combined_fips"] = election.apply(fips, axis=1)

        return election

    def preprocess_senate(self):
        senate = self.senate
        senate_df = senate[["state_code", "party"]]

        def party_coder(row):
            party = row["party"]
            if party == "democrat":
                return 2
            elif party == "independent":
                return 1
            else:
                return -2

        senate_df["party"] = senate_df.apply(party_coder, axis=1)
        senate_df_df       = senate_df.groupby("state_code")["party"].sum()
        senate_parties     = pd.DataFrame({'state_code':senate_df_df.index, 'party':senate_df_df.values})

        return senate_parties

    def preprocess_house(self):
        house = self.house
        state_fips = self.state_fips
        cd113_json = self.cd113_json

        house              = house[["state_code", "district", "party"]]
        state_fips         = state_fips[["state_abbr", "fips"]]
        state_fips.columns = ["state_code", "state_fips"]
        house_fips         = pd.merge(house, state_fips, on="state_code", how="outer")

        def district_coder(row):
            district = row["district"]
            if np.isnan(district):
                return 0
            else:
                return district

        def district_fips(row):
            district = row["district"]
            if len(district) == 1:
                return "0"+district
            else:
                return district

        def state_fips(row):
            state_fp = row["state_fips"]
            if len(state_fp) == 1:
                return "0"+state_fp
            else:
                return state_fp

        house_fips["district"]            = house_fips.apply(district_coder, axis=1)
        house_fips["district"]            = house_fips["district"].astype(np.int64).astype(str)
        house_fips["state_fips"]          = house_fips["state_fips"].astype(str)
        house_fips["district"]            = house_fips.apply(district_fips, axis=1)
        house_fips["state_fips"]          = house_fips.apply(state_fips, axis=1)
        house_fips["state_district_fips"] = house_fips["state_fips"] + house_fips["district"]
        cd113_geometries                  = cd113_json["objects"]["cd113"]["geometries"]

        for item in cd113_geometries:
            item["properties"]["CD113FP"] = item["properties"]["STATEFP"]+item["properties"]["CD113FP"]

        cd113_json["objects"]["cd113"]["geometries"] = cd113_geometries

        return (house_fips, cd113_json)
