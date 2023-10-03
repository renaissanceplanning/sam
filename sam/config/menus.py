tod_menu = {
    'pull_lodes': {'lodes_data': ["rac", "wac", "od"],
                   'lodes_level': "bgrp"},
    'pull_acs': {},
    'pull_tiger': {},
    'pull_parcels': {'parcel_source': "replica",
                     'parcel_replica_fields': True},
    'pull_OSM': {'add_travel_time': False},
    'pull_lihtc': {},
    'pull_replica_trip_table': {'mid_week': True,
                                'link_ids': False,
                                'time': "all",  
                                'purpose': "all"},
    'pull_replica_acs': {},
    'pull_replica_population': {},
}

parcels_menu = {
    'pull_parcels': {'parcel_source': "replica",
                     'parcel_replica_fields': False}
}

frieght_menu = {
    'pull_lodes': {'lodes_data': ["rac", "wac", "od"],
                   'lodes_level': "bgrp"},
    'pull_acs': {},
    'pull_tiger': {},
    # 'pull_parcels': {'parcel_source': "replica",
    #                  'parcel_replica_fields': True},
    'pull_OSM': {'add_travel_time': True},
    # 'pull_lihtc': {},
    'pull_replica_trip_table': {'mid_week': True,
                                'link_ids': False,
                                'time': "all",  
                                'purpose': "all"},
    'pull_replica_acs': {},
    'pull_replica_population': {},
}

corridor_studies = {
    'pull_lodes': {'lodes_data': ["rac", "wac", "od"],
                   'lodes_level': "tabblk2020"},
    'pull_acs': {},
    'pull_tiger': {},
    'pull_parcels': {'parcel_source': "replica",
                     'parcel_replica_fields': True},
    'pull_OSM': {'add_travel_time': False},
    'pull_lihtc': {},
    'pull_replica_trip_table': {'mid_week': True,
                                'link_ids': False,
                                'time': "all",  
                                'purpose': "all"},
    'pull_replica_acs': {},
    'pull_replica_population': {},
}
