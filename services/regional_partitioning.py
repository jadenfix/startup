# startup/services/regional_partitioning.py

def assign_region(lat, lng):
    if 37.0 <= lat <= 38.0 and -123.0 <= lng <= -122.0:
        return "Region_A"
    elif 36.0 <= lat <= 37.0 and -122.0 <= lng <= -121.0:
        return "Region_B"
    return "Region_Other"

def partition_data(data):
    partitioned_data = {}
    for item in data:
        region = assign_region(item["lat"], item["lng"])
        if region not in partitioned_data:
            partitioned_data[region] = []
        partitioned_data[region].append(item)
    return partitioned_data