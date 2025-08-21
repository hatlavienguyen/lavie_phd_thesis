import os
import sys
#pygplates is a specific package for plate tectonic study
sys.path.insert(1,r'C:\Users\Lavie\Desktop\Research\GPlates\pygplates_rev28_python38_win64\pygplates_rev28_python38_win64')
import pygplates
import pandas as pd
import geopandas as gpd
import numpy as np
import pyproj
from shapely.ops import transform
from shapely.geometry import Polygon, LineString, MultiPoint, MultiPolygon, LinearRing, Point
import math
#import supporting_topological_modules as tm
#import supporting_topological_modules_for_MOR as MOR_topology
import rotation_utility
import evaluate_tectonic_motion as tectonic_motion

#A function to calculate the distance between two points on the sphere - specifically the Earth 
#I could have used haversine module for python, but for the purpose of practise, I do it myself
#According to the formula from https://www.igismap.com/haversine-formula-calculate-geographic-distance-earth/, 
#a = sin^2(Difference in latitudes/2)+cos(lat1)*cos(lat2)*sin^2(Difference in longitude/2)
#c = 2*atan2(sqrt(a),sqrt(1-a))
#d = Radius of the sphere * c
def calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2):
	difference_lat = math.radians(lat1 - lat2)
	difference_lon = math.radians(lon1 - lon2)
	a = (math.pow(math.sin(difference_lat/2.00),2.00)) + (math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.pow(math.sin(difference_lon/2.00),2.00))
	c = 2.00*math.atan2(math.sqrt(a),math.sqrt(1-a))
	distance = pygplates.Earth.mean_radius_in_kms * c
	return distance

def convert_Point_in_Shapely_to_PointOnSphere_in_pygplates(point):
	'''point has coordinate as longitude and latitude'''
	longitude = point.x
	latitude = point.y
	point_on_sphere = pygplates.PointOnSphere(latitude,longitude)
	return point_on_sphere

def convert_LineString_in_Shapely_to_LineOnSphere_in_pygplates(line):
	'''each data point of the line has coordinate as longitude and latitude'''
	if (line.length > 0.00):
		try:
			list_of_lat_lon_vertices = [(lat,lon) for lon,lat in line.coords]
		except NotImplementedError as error:
			list_of_lat_lon_vertices = [(lat,lon) for lon,lat in line.exterior.coords]
		line_on_sphere = pygplates.PolylineOnSphere(list_of_lat_lon_vertices)
		if (line_on_sphere is None):
			print ("Error to convert convert_LineString_in_Shapely_to_LineOnSphere_in_pygplates")
			print ("Here is a list_of_lat_lon_vertices")
			print (list_of_lat_lon_vertices)
			print (list_of_lat_lon_vertices)
			exit()
		return line_on_sphere
	else:
		print ("Error in convert_LineString_in_Shapely_to_LineOnSphere_in_pygplates")
		print ("line.length == 0")
		print ("here are coords for line:")
		print((line.coords))
		print ("here is line")
		print (line)
		exit()

def convert_Polygon_in_Shapely_to_PolygonOnSphere_in_pygplates(each_polygon):
	'''each data point of each_polygon has a coordinate as longitude and latitude'''
	if (each_polygon.area > 0.00):
		list_of_lat_lon_vertices = [(lat,lon) for lon,lat in list(each_polygon.exterior.coords)]
		final_list_of_lat_lon_vertices = []
		for lat,lon in list_of_lat_lon_vertices:
			#print("lat,lon")
			#print(lat,lon)
			if (pygplates.LatLonPoint.is_valid_latitude(lat) == False or pygplates.LatLonPoint.is_valid_longitude(lon) == False):
				print("Warning in convert_Polygon_to_PolygonOnSphere_in_pygplates")
				print("Warning invalid value of latitude or/and longitude")
				print("value of latitude")
				print(lat)
				print("value of longitude")
				print(lon)
				if (pygplates.LatLonPoint.is_valid_latitude(lat) == False):
					if (abs(abs(lat) - 90.00) < 0.500):
						if (lat < -90.00):
							lat = -90.000
						elif (lat > 90.00):
							lat = 90.000
					else:
						print("Error in convert_Polygon_to_PolygonOnSphere_in_pygplates")
						print("Error invalid value of latitude")
						print("value of latitude")
						print(lat)					
						exit()
				if (pygplates.LatLonPoint.is_valid_longitude(lon) == False):
					if (abs(abs(lon) - 180.00) < 0.500):
						if (lon < -180.00):
							lon = -180.00
						elif (lon > 180.00):
							lon = 180.00
					else:
						print("Error in convert_Polygon_to_PolygonOnSphere_in_pygplates")
						print("Error invalid value of longitude")
						print("value of longitude")
						print(lon)					
						exit()
			final_list_of_lat_lon_vertices.append((lat,lon))	
		new_polygon = pygplates.PolygonOnSphere(final_list_of_lat_lon_vertices)
		if (new_polygon is None):
			print("Error in creating polygon in pygplates in conversion module")
			print("Here is a list of lat_lon vertices")
			print(list_of_lat_lon_vertices)
			print("Here is the first vertex and the last vertex:")
			print(list_of_lat_lon_vertices[0])
			print(list_of_lat_lon_vertices[len(list_of_lat_lon_vertices)-1])
			exit()
		return new_polygon
	else:
		print("Error in creating polygon in pygplates in conversion module")
		print("Error each_polygon.area <= 0.00")
		print("here is each_polygon")
		print(each_polygon)
		print([(lon,lat) for lon,lat in each_polygon.exterior.coords])
		exit()

def convert_PolygonOnSphere_to_Polygon_in_Shapely(polygon_on_sphere):
	list_of_lon_lat_vertices = [(lon,lat) for lat,lon in polygon_on_sphere.to_lat_lon_list()]
	new_polygon = Polygon(list_of_lon_lat_vertices)
	if (new_polygon is None):
		print("Error in creating Polygon in Shapely in conversion module")
		print("Here is a list of lon_lat vertices")
		print(list_of_lon_lat_vertices)
		print("Here is the first vertex and the last vertex:")
		print(list_of_lon_lat_vertices[0])
		print(list_of_lon_lat_vertices[len(list_of_lon_lat_vertices)-1])
		exit()
	return new_polygon

def convert_PolylineOnSphere_to_LineString_in_Shapely(polyline_on_sphere):
	list_of_lon_lat_vertices = [(lon,lat) for lat,lon in polyline_on_sphere.to_lat_lon_list()]
	new_linestring = LineString(list_of_lon_lat_vertices)
	if (new_polygon is None):
		print("Error in creating LineString in Shapely in conversion module")
		print("Here is a list of lon_lat vertices")
		print(list_of_lon_lat_vertices)
		print("Here is the first vertex and the last vertex:")
		print(list_of_lon_lat_vertices[0])
		print(list_of_lon_lat_vertices[len(list_of_lon_lat_vertices)-1])
		exit()
	return new_linestring

def convert_PointOnSphere_to_Point_in_Shapely(point_on_sphere):
	lat,lon = point_on_sphere.to_lat_lon()
	new_point = Point(lon,lat)
	if (new_point is None):
		print("Error in creating Point in Shapely in conversion module")
		print("Here is a vertices")
		print(lat,lon)
		exit()
	return new_point

def project_any_Shapely_geometry_in_wgs84_lon_lat_coordinates_to_planar_projection(wgs84_geom, choosen_epsg_projection):
	'''wgs84_geom has a geometry data type defined in Shapely and coordinates with order longitude as x and latitude as y'''
	wgs84 = pyproj.CRS('EPSG:4326')
	projection = pyproj.CRS(choosen_epsg_projection)
	project = pyproj.Transformer.from_crs(wgs84, projection, always_xy = True).transform
	projected_geom = transform(project, wgs84_geom)
	return projected_geom

def project_any_Shapely_geometry_in_planar_projection_to_spherical_projection_wgs84_lon_lat(projected_geom, choosen_epsg_projection):
	wgs84 = pyproj.CRS('EPSG:4326')
	projection = pyproj.CRS(choosen_epsg_projection)
	project = pyproj.Transformer.from_crs(projection, wgs84, always_xy = True).transform
	wgs84_geom = transform(project,projected_geom)
	return wgs84_geom

def get_first_point_of_line(polyline_on_sphere):
	if (polyline_on_sphere is None):
		print("Error input for get_first_point_of_line is None")
		exit()
	return pygplates.PointOnSphere(polyline_on_sphere[0])

def get_last_point_of_line(polyline_on_sphere):
	if (polyline_on_sphere is None):
		print("Error input for get_last_point_of_line is None")
		exit()
	last_point_index = len(polyline_on_sphere.to_lat_lon_list())-1
	return pygplates.PointOnSphere(polyline_on_sphere[last_point_index])

def get_second_last_point_of_line(polyline_on_sphere):
	if (polyline_on_sphere is None):
		print("Error input for get_last_point_of_line is None")
		exit()
	second_last_point_index = len(polyline_on_sphere.to_lat_lon_list())-2
	return pygplates.PointOnSphere(polyline_on_sphere[second_last_point_index])

def find_final_reconstructed_geometries(reconstructed_features_geometries,type):
	list_of_final_reconstructed_geometries = []
	if (type is pygplates.PointOnSphere):
		for each_ft,reconstructed_ft_geometries in reconstructed_features_geometries:
			if (len(reconstructed_ft_geometries) == 1):
				ft_geometry = reconstructed_ft_geometries[0]
				point = ft_geometry.get_reconstructed_geometry()
				list_of_final_reconstructed_geometries.append((each_ft,point))
			else:
				lat_values = []
				lon_values = []
				for ft_geometry in reconstructed_ft_geometries:
					point = ft_geometry.get_reconstructed_geometry()
					lat,lon = point.to_lat_lon()
					lat_values.append(lat)
					lon_values.append(lon)
				mean_lat = np.mean(lat_values)
				mean_lon = np.mean(lon_values)
				new_point = pygplates.PointOnSphere((mean_lat,mean_lon))
				list_of_final_reconstructed_geometries.append((each_ft,new_point))
	elif (type is pygplates.PolygonOnSphere):
		for each_ft,reconstructed_ft_geometries in reconstructed_features_geometries:
			current_area = 0
			current_polygon = None
			for reconstructed_ft_geometry in reconstructed_ft_geometries:
				polygon = reconstructed_ft_geometry.get_reconstructed_geometry()
				if (polygon.get_area() > current_area):
					current_area = polygon.get_area()
					current_polygon = polygon 
			if (current_area > 0 and current_polygon is not None):
				list_of_final_reconstructed_geometries.append((each_ft,current_polygon))
	elif (type is pygplates.PolylineOnSphere):
		for each_ft,reconstructed_ft_geometries in reconstructed_features_geometries:
			current_len = 0
			current_line = None
			for reconstructed_ft_geometry in reconstructed_ft_geometries:
				line = reconstructed_ft_geometry.get_reconstructed_geometry()
				if (line is None):
					print("Error in calculate_distance_between_end_nodes")
					print("Error reconstructed_ft_geometry.get_reconstructed_geometry() is None")
					exit()
				first_point_of_line = get_first_point_of_line(line)							
				end_point_of_line = get_last_point_of_line(line)
				# if (line.get_arc_length() > current_len and first_point_of_line!= end_point_of_line):
					# current_len = line.get_arc_length()
					# current_line = line
				if (line.get_arc_length() > current_len):
					current_len = line.get_arc_length()
					current_line = line 
			if (current_len > 0 and current_line is not None):
				list_of_final_reconstructed_geometries.append((each_ft,current_line))
	return list_of_final_reconstructed_geometries
	
def find_valid_con_ocn_line_features(line_features, common_filename_for_invalid_con_ocn_line_csv, reconstruction_time):
	#csv_filename = common_filename_for_invalid_con_ocn_line_csv.format(time = str(reconstruction_time))
	csv_filename= common_filename_for_invalid_con_ocn_line_csv
	#'reconstruction_time','LineID','OPOLYLID','POLYLID','GPLATE_FID'
	invalid_con_ocn_df = pd.read_csv(csv_filename, delimiter = ';', header = 0)
	valid_line_features = []
	for line_ft in line_features:
		polylid = line_ft.get_shapefile_attribute('POLYLID')
		opolylid = line_ft.get_shapefile_attribute('OPOLYLID')
		lineid = line_ft.get_shapefile_attribute('LineID')
		gplate_fid = line_ft.get_feature_id().get_string()
		result = invalid_con_ocn_df.loc[(invalid_con_ocn_df['POLYLID'] == polylid) & (invalid_con_ocn_df['OPOLYLID'] == opolylid) & (invalid_con_ocn_df['LineID'] == lineid) & (invalid_con_ocn_df['GPLATE_FID'] == gplate_fid)]
		if (result is not None):
			if (len(result) == 0):
				valid_line_features.append(line_ft)
		else:
			valid_line_features.append(line_ft)
	return valid_line_features

def find_gdu_features_associated_with_line_features(gdu_features, line_features):
	selected_gdu_features = {}
	for line_ft in line_features:
		polygid = line_ft.get_shapefile_attribute('POLYGID')
		if (polygid is not None):
			for gdu_ft in gdu_features:
				if (gdu_ft.get_shapefile_attribute('POLYGID') is not None and gdu_ft.get_shapefile_attribute('POLYGID') == polygid):
					if (polygid not in selected_gdu_features):
						selected_gdu_features[polygid] = [gdu_ft]
					else:
						list_of_gdu_fts = selected_gdu_features[polygid]
						found_duplicated = False
						for prev_ft in list_of_gdu_fts:
							prev_geometries = prev_ft.get_geometries()
							current_geometries = gdu_ft.get_geometries()
							for prev_geom in prev_geometries:
								for current_geom in current_geometries:
									if (prev_geom == current_geom):
										found_duplicated = True
										break
								if (found_duplicated == True):
									break
							if (found_duplicated == True):
								break
						if (found_duplicated == False):
							selected_gdu_features[polygid].append(gdu_ft)
	return selected_gdu_features

def find_gdu_members_of_each_sgdu_feat_old(gdu_features, sgdu_features,common_filename_for_temporary_sgdu_and_members_csv,reconstruction_time):
	list_of_distinct_gdu_ids = []
	dict_of_sgdu_and_members_ids = {}
	# for gdu_ft in gdu_features:
		# if (gdu_ft.get_reconstruction_plate_id() not in list_of_distinct_gdu_ids):
			# list_of_distinct_gdu_ids.append(gdu_ft.get_reconstruction_plate_id())
		# if (gdu_ft.get_reconstruction_plate_id() == 11732):
			# print('found gdu fts with gdu id')
			# print(gdu_ft.get_reconstruction_plate_id() in list_of_distinct_gdu_ids)
	# array_of_distinct_gdu_ids = np.array(list_of_distinct_gdu_ids)
	for sgdu_ft in sgdu_features:
		sgdu_id = sgdu_ft.get_name()
		rep_gdu_id = sgdu_ft.get_reconstruction_plate_id()
		list_of_associated_gdu_members = None
		if (sgdu_id not in dict_of_sgdu_and_members_ids):
			temp_sgdu_and_members_csv = common_filename_for_temporary_sgdu_and_members_csv.format(time = str(reconstruction_time))
			#;from_time;to_time;SGDUID;GDUID;buffer_distance_km;repGDUID
			temp_df = pd.read_csv(temp_sgdu_and_members_csv, delimiter = ';', header = 0)
			
			unique_sgdus = temp_df.loc[(temp_df['repGDUID'] == rep_gdu_id),'SGDUID'].unique()
			records_of_gdu_members = []
			for sgdu in unique_sgdus:
				temp_members = temp_df.loc[(temp_df['SGDUID'] == sgdu),'GDUID'].unique()
				for temp_mem in temp_members:
					if (temp_mem not in records_of_gdu_members):
						records_of_gdu_members.append(temp_mem)

			#records_of_gdu_members = temp_df.loc[(temp_df['repGDUID'] == rep_gdu_id)|(temp_df['GDUID'] == rep_gdu_id),'GDUID'].unique()
			# if (sgdu_id == '70290'):
				# print('records_of_gdu_members',records_of_gdu_members)
			#array_of_all_distinct_gdu_members = records_of_gdu_members
			#wanted_gdu_members = np.intersect1d(array_of_distinct_gdu_ids,array_of_all_distinct_gdu_members)
			
			wanted_gdu_members = records_of_gdu_members
			
			#if (sgdu_id == '70290'):
				# print('wanted_gdu_members',wanted_gdu_members)
				# print(array_of_distinct_gdu_ids)
				# print(array_of_all_distinct_gdu_members)
			if (len(wanted_gdu_members) > 0):
				list_of_wanted_gdu_fts = []
				for each_gdu_ft in gdu_features:
					if (each_gdu_ft.is_valid_at_time(reconstruction_time) and each_gdu_ft.get_reconstruction_plate_id() in wanted_gdu_members):
						list_of_wanted_gdu_fts.append(each_gdu_ft)
				
				#the thing: there is a time latency between when SuperGDU feature occurs and when CON-OCN line features occur. 
				#if (len(list_of_wanted_gdu_fts) == 0):
					#print("Error could not find any gdu features for SuperGDU feature",sgdu_id)
					#print('records_of_gdu_members')
					#print(records_of_gdu_members)
					#pygplates.FeatureCollection(sgdu_ft).write('SGDU_feature_'+str(sgdu_id)+'_could_not_find_gdus.shp')
					# for each_gdu_ft in gdu_features:
						# if (each_gdu_ft.get_reconstruction_plate_id() == 19508):
							# print('each_gdu_ft.get_reconstruction_plate_id()',each_gdu_ft.get_reconstruction_plate_id())
							# print(each_gdu_ft.get_reconstruction_plate_id() in wanted_gdu_members)
					# exit()
				dict_of_sgdu_and_members_ids[sgdu_id] = list_of_wanted_gdu_fts
	return dict_of_sgdu_and_members_ids

def find_gdu_members_of_each_sgdu_feat(gdu_features, sgdu_features,common_filename_for_temporary_sgdu_and_members_csv,reconstruction_time):
	list_of_distinct_gdu_ids = []
	dict_of_sgdu_and_members_ids = {}
	# for gdu_ft in gdu_features:
		# if (gdu_ft.get_reconstruction_plate_id() not in list_of_distinct_gdu_ids):
			# list_of_distinct_gdu_ids.append(gdu_ft.get_reconstruction_plate_id())
		# if (gdu_ft.get_reconstruction_plate_id() == 11732):
			# print('found gdu fts with gdu id')
			# print(gdu_ft.get_reconstruction_plate_id() in list_of_distinct_gdu_ids)
	# array_of_distinct_gdu_ids = np.array(list_of_distinct_gdu_ids)
	for sgdu_ft in sgdu_features:
		sgdu_id = sgdu_ft.get_name()
		rep_gdu_id = sgdu_ft.get_reconstruction_plate_id()
		sgdu_begin,sgdu_end = sgdu_ft.get_valid_time()
		list_of_associated_gdu_members = None
		if (sgdu_id not in dict_of_sgdu_and_members_ids):
			temp_sgdu_and_members_csv = common_filename_for_temporary_sgdu_and_members_csv.format(time = str(reconstruction_time))
			#;from_time;to_time;SGDUID;GDUID;buffer_distance_km;repGDUID
			temp_df = pd.read_csv(temp_sgdu_and_members_csv, delimiter = ';', header = 0)
			
			initial_sgdu_and_members_csv = common_filename_for_temporary_sgdu_and_members_csv.format(time = str(sgdu_begin))
			#;from_time;to_time;SGDUID;GDUID;buffer_distance_km;repGDUID
			initial_df = pd.read_csv(initial_sgdu_and_members_csv, delimiter = ';', header = 0)
			
			unique_sgdus = temp_df.loc[(temp_df['repGDUID'] == rep_gdu_id)|(temp_df['GDUID'] == rep_gdu_id),'SGDUID'].unique()
			records_of_gdu_members = []
			for sgdu in unique_sgdus:
				temp_members = temp_df.loc[(temp_df['SGDUID'] == sgdu),'GDUID'].unique()
				for temp_mem in temp_members:
					if (temp_mem not in records_of_gdu_members):
						records_of_gdu_members.append(temp_mem)
			
			temp_members = initial_df.loc[(initial_df['SGDUID'] == int(sgdu_id)),'GDUID'].unique()
			for temp_mem in temp_members:
				if (temp_mem not in records_of_gdu_members):
					records_of_gdu_members.append(temp_mem)

			#records_of_gdu_members = temp_df.loc[(temp_df['repGDUID'] == rep_gdu_id)|(temp_df['GDUID'] == rep_gdu_id),'GDUID'].unique()
			# if (sgdu_id == '70290'):
				# print('records_of_gdu_members',records_of_gdu_members)
			#array_of_all_distinct_gdu_members = records_of_gdu_members
			#wanted_gdu_members = np.intersect1d(array_of_distinct_gdu_ids,array_of_all_distinct_gdu_members)
			
			wanted_gdu_members = records_of_gdu_members
			
			#if (sgdu_id == '70290'):
				# print('wanted_gdu_members',wanted_gdu_members)
				# print(array_of_distinct_gdu_ids)
				# print(array_of_all_distinct_gdu_members)
			if (len(wanted_gdu_members) > 0):
				list_of_wanted_gdu_fts = []
				list_of_already_included_polygids = []
				for each_gdu_ft in gdu_features:
					if (each_gdu_ft.is_valid_at_time(reconstruction_time) and each_gdu_ft.get_reconstruction_plate_id() in wanted_gdu_members):
						if (each_gdu_ft.get_shapefile_attribute('POLYGID') not in list_of_already_included_polygids):
							list_of_already_included_polygids.append(each_gdu_ft.get_shapefile_attribute('POLYGID'))
							list_of_wanted_gdu_fts.append(each_gdu_ft)
				# if (len(list_of_wanted_gdu_fts) == 0):
					# print("Error could not find any gdu features for SuperGDU feature",sgdu_id)
					# print('records_of_gdu_members')
					# print(records_of_gdu_members)
					#pygplates.FeatureCollection(sgdu_ft).write('SGDU_feature_'+str(sgdu_id)+'_could_not_find_gdus.shp')
					# for each_gdu_ft in gdu_features:
						# if (each_gdu_ft.get_reconstruction_plate_id() == 19508):
							# print('each_gdu_ft.get_reconstruction_plate_id()',each_gdu_ft.get_reconstruction_plate_id())
							# print(each_gdu_ft.get_reconstruction_plate_id() in wanted_gdu_members)
					# exit()
				dict_of_sgdu_and_members_ids[sgdu_id] = list_of_wanted_gdu_fts
	return dict_of_sgdu_and_members_ids

def find_centroid_of_each_reconstructed_gdu_ft(final_reconstructed_gdu_features):
	dict_of_gdu_and_centroid = {}
	for recontructed_gdu_ft, polygon in final_reconstructed_gdu_features:
		gdu_id = recontructed_gdu_ft.get_reconstruction_plate_id()
		centroid = polygon.get_interior_centroid()
		polygid = recontructed_gdu_ft.get_shapefile_attribute('POLYGID')
		# if (str(gdu_id) not in dict_of_gdu_and_centroid):
			# dict_of_gdu_and_centroid[str(gdu_id)] = [(centroid,polygid)]
		# else:
			# dict_of_gdu_and_centroid[str(gdu_id)].append((centroid,polygid))
		
		if (polygid not in dict_of_gdu_and_centroid):
			dict_of_gdu_and_centroid[polygid] = [(centroid,polygid)]
		else:
			dict_of_gdu_and_centroid[polygid].append((centroid,polygid))
		
	return dict_of_gdu_and_centroid

def find_neighbours_of_each_reconstructed_gdu_ft(dict_of_gdu_and_centroid,threshold_distance_in_km_for_neighbour):
	dict_of_neighbours = {}
	# for str_gduid in dict_of_gdu_and_centroid:
		# tuples_of_centroid_and_polygid = dict_of_gdu_and_centroid[str_gduid]
		# for other_str_gduid in dict_of_gdu_and_centroid:
			# if (other_str_gduid != str_gduid):
				# tuples_of_other_centroid_and_polygid = dict_of_gdu_and_centroid[str_gduid]
				# for centroid_of_polygid, polygid in tuples_of_centroid_and_polygid:
					# lat1,lon1 = centroid_of_polygid.to_lat_lon()
					# for other_centroid, other_polygid in tuples_of_other_centroid_and_polygid:
						# lat2,lon2 = other_centroid.to_lat_lon()
						# if (calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2) <= threshold_distance_in_km_for_neighbour):
							# if (str_gduid not in dict_of_neighbours):
								# dict_of_neighbours[str_gduid] = [other_centroid]
							# else:
								# dict_of_neighbours[str_gduid].append(other_centroid)
	
	for polygid in dict_of_gdu_and_centroid:
		tuples_of_centroid_and_polygid = dict_of_gdu_and_centroid[polygid]
		for other_polygid in dict_of_gdu_and_centroid:
			if (other_polygid != polygid):
				tuples_of_other_centroid_and_polygid = dict_of_gdu_and_centroid[other_polygid]
				for centroid_of_polygid, _ in tuples_of_centroid_and_polygid:
					lat1,lon1 = centroid_of_polygid.to_lat_lon()
					for other_centroid, _ in tuples_of_other_centroid_and_polygid:
						lat2,lon2 = other_centroid.to_lat_lon()
						if (calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2) <= threshold_distance_in_km_for_neighbour):
							if (polygid not in dict_of_neighbours):
								#dict_of_neighbours[polygid] = [(other_centroid,other_polygid)]
								dict_of_neighbours[polygid] = [other_polygid]
							else:
								#dict_of_neighbours[polygid].append((other_centroid,other_polygid))
								dict_of_neighbours[polygid].append(other_polygid)
	
	return dict_of_neighbours

def find_magnitude_azimuth_inclination_from_a_ref_point_to_a_given_point(ref_point, given_point):
	'''ref_point and given_point have data type as PointOnSphere in pygplates'''
	if (ref_point == given_point):
		print('ref_point == given_point in find_azimuth_from_a_ref_point_to_a_given_point')
		return None
	elif (ref_point is None or given_point is None):
		print('ref_point is None or given_point is None')
		print('ref_point', ref_point, 'given_point', given_point)
		return None
	else:
		#local_cartesian = pygplates.LocalCartesian(ref_point)
		geocentric_vec = pygplates.Vector3D(given_point.to_xyz())
		mag,azi,inc = pygplates.LocalCartesian.convert_from_geocentric_to_magnitude_azimuth_inclination(ref_point,geocentric_vec)
		return mag,azi,inc

def find_planar_vector_direction_from_a_ref_point_to_a_given_point(ref_point, given_point):
	'''ref_point and given_point have data type as Point in Shapely with planar projection coordinates xy'''
	vec_x = given_point.x - ref_point.x
	vec_y = given_point.y - ref_point.y
	return (vec_x,vec_y)

def calculate_dot_product_between_two_planar_vectors(tuple_vec1, tuple_vec2):
	#compute dot product
	x1,y1 = tuple_vec1
	x2,y2 = tuple_vec2
	dot_prod = (x1*x2)+(y1*y2)
	return dot_prod

def calculate_magnitude_of_a_planar_vector(tuple_vec1):
	x1,y1 = tuple_vec1
	magnitude_of_vec1 = math.sqrt((x1*x1)+(y1*y1))
	return magnitude_of_vec1

def calculate_angle_between_two_planar_vectors(tuple_vec1, tuple_vec2):
	#compute dot product
	dot_prod = calculate_dot_product_between_two_planar_vectors(tuple_vec1, tuple_vec2)
	#compute magnitude of each vector
	magnitude_of_vec1 = calculate_magnitude_of_a_planar_vector(tuple_vec1)
	magnitude_of_vec2 = calculate_magnitude_of_a_planar_vector(tuple_vec2)
	#cosine angle between two vectors
	cosine_angle_rads = dot_prod/(magnitude_of_vec1*magnitude_of_vec2)
	if (cosine_angle_rads < -1.00 or cosine_angle_rads > 1.00):
		print("cosine_angle_rads is out of the range -1.00 to 1.00")
		return None
	theta = math.acos(cosine_angle_rads)
	theta_degrees = math.degrees(theta)
	return theta_degrees

def examine_position_of_unknown_pt_relative_to_from_and_to_pts_in_planar_coordinates(from_point,to_point,unknown_point,maximum_accepted_angle_in_degrees):
	'''from_point, to_point and unknown_point have data type as Point in Shapely with planar projection coordinates xy'''
	ref_vec_direction = find_planar_vector_direction_from_a_ref_point_to_a_given_point(from_point,to_point)
	vec_direction_from_pt_to_unknown_pt = find_planar_vector_direction_from_a_ref_point_to_a_given_point(from_point,unknown_point)
	angle_between_two_planar_vectors = calculate_angle_between_two_planar_vectors(ref_vec_direction, vec_direction_from_pt_to_unknown_pt)
	if (angle_between_two_planar_vectors is None):
		return 'invalid'
	if (angle_between_two_planar_vectors <= maximum_accepted_angle_in_degrees):
		magnitude_of_ref_vec = calculate_magnitude_of_a_planar_vector(ref_vec_direction)
		magnitude_of_other_vec = calculate_magnitude_of_a_planar_vector(vec_direction_from_pt_to_unknown_pt)
		if (magnitude_of_other_vec <= magnitude_of_ref_vec):
			return 'between'
		else:
			return 'possibly_between'
	else:
		return 'outside'

def is_line_crossing_polygon(point_1, point_2, polygon, threshold_distance_in_km):
	"""point_1, point_2 and polygon have planar projected coordinates
	point_1 and point_2 have data type as Point and polygon has data type as Polygon in Shapely"""
	linestring = LineString([point_1,point_2])
	if (linestring.crosses(polygon) == True or linestring.within(polygon) == True):
		#find the portion of linestring intersecting Polygon and obtain its length
		portion = linestring.intersection(polygon)
		portion_in_meters = portion.length #length of the intersecting segment is in meters because often the planar map projection has unit in meters
		portion_in_km = portion_in_meters/1000.00
		if (portion_in_km >= threshold_distance_in_km):
			return True
		else:
			return False
	else:
		return False

def find_and_record_valid_sgdus_and_outer_gdu_members_at_each_reconstruction_time(rotation_model, gdu_features_collection, line_features_collection, super_gdu_features_collection, common_filename_for_temporary_sgdu_and_members_csv, common_filename_for_invalid_con_ocn_line_csv, sgdu_distance_csv, maximum_accepted_angle_in_degrees, threshold_distance_in_km, begin_reconstruction_time, end_reconstruction_time, time_interval, reference, modelname,yearmonthday):
	#reconstruction_time,SGDU_1,SGDU_2,dist_km,lat1,lon1,lat2,lon2
	#sgdu_distance_df = pd.read_csv(sgdu_distance_csv,delimiter=';',header=0)
	reconstructed_sgdu_features = []
	reconstructed_gdu_features = []
	reconstructed_line_features = []
	valid_sgdu_features = []
	list_of_tuples_to_be_evaluated = []
	#output container
	output_list = []
	
	dict_of_sgdu_and_line_feats = None
	reconstruction_time = begin_reconstruction_time
	while (reconstruction_time >= end_reconstruction_time):
		print('reconstruction_time',reconstruction_time)
		valid_sgdu_features[:] = []
		reconstructed_sgdu_features[:] = []
		reconstructed_gdu_features[:] = []
		reconstructed_line_features[:] = []
		list_of_tuples_to_be_evaluated[:] = []
		#1) Find valid CON-OCN line features
		valid_line_features = None
		existing_line_features = [con_ocn_line_ft for con_ocn_line_ft in line_features_collection if con_ocn_line_ft.is_valid_at_time(reconstruction_time)]
		valid_line_features = find_valid_con_ocn_line_features(existing_line_features, common_filename_for_invalid_con_ocn_line_csv, reconstruction_time)
		#2) Reconstruct valid line features to reconstruction_time
		if (reference is not None):
			pygplates.reconstruct(valid_line_features, rotation_model, reconstructed_line_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_line_features, rotation_model, reconstructed_line_features, reconstruction_time, group_with_feature = True)
		#final_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_line_features, pygplates.PolylineOnSphere)
		#3) Select GDU features associated to valid con-ocn line features
		selected_gdu_features = None
		selected_gdu_features = find_gdu_features_associated_with_line_features(gdu_features_collection, valid_line_features)
		#4) Create temp_list_of_selected_gdu_fts to store selected gdu features and reconstruct them to reconstruction_time
		temp_list_of_selected_gdu_fts = []
		for polygid in selected_gdu_features:
			list_of_gdu_fts = selected_gdu_features[polygid]
			temp_list_of_selected_gdu_fts = temp_list_of_selected_gdu_fts+list_of_gdu_fts
		if (reference is not None):
			pygplates.reconstruct(temp_list_of_selected_gdu_fts, rotation_model, reconstructed_gdu_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(temp_list_of_selected_gdu_fts, rotation_model, reconstructed_gdu_features, reconstruction_time, group_with_feature = True)
		
		#debug
		feature_collection_of_selected_gdu_fts = pygplates.FeatureCollection(temp_list_of_selected_gdu_fts)
		feature_collection_of_selected_gdu_fts.write('selected_outer_gdu_'+str(reconstruction_time)+'_'+modelname+'_'+yearmonthday+'.shp')
		
		final_reconstructed_gdu_features = find_final_reconstructed_geometries(reconstructed_gdu_features, pygplates.PolygonOnSphere)
		#5) Find valid SuperGDU features at the reconstruction_time
		valid_sgdu_features = [sgdu_ft for sgdu_ft in super_gdu_features_collection if sgdu_ft.is_valid_at_time(reconstruction_time)]
		#6) Find gdu members of each valid_sgdu_features - make sure to avoid duplicated gdu member features
		dict_of_sgdu_and_members_ids = find_gdu_members_of_each_sgdu_feat(temp_list_of_selected_gdu_fts, valid_sgdu_features, common_filename_for_temporary_sgdu_and_members_csv, reconstruction_time)
		#7) Find interior centroid of each reconstructed gdu
		dict_of_gdu_and_centroid = find_centroid_of_each_reconstructed_gdu_ft(final_reconstructed_gdu_features)
		
		#RECORDING 
		#the gdu members for each sgdu stored in the dictionary are ONLY gdu members along the BOUNDARIES of sgdus. 
		for random_sgdu_key in dict_of_sgdu_and_members_ids:
			temp_list_of_outer_gdu_members = dict_of_sgdu_and_members_ids[random_sgdu_key]
			for member in temp_list_of_outer_gdu_members:
				temp_list_of_centroids_and_polygids_for_member = dict_of_gdu_and_centroid[str(member)]
				for c,polygid in temp_list_of_centroids_and_polygids_for_member:
					reconstructed_lat,reconstructed_lon = c.to_lat_lon()
					output_list.append((reconstruction_time,int(random_sgdu_key),member,reconstructed_lat,reconstructed_lon,polygid))
		# #8) Find appropriate pairs of sgdus first based on the distance
		# #8i) Find appropriate pairs of sgdus
		# #reconstruction_time,SGDU_1,SGDU_2,dist_km,lat1,lon1,lat2,lon2
		# interested_sgdu_records = sgdu_distance_df.loc[(sgdu_distance_df['reconstruction_time'] == reconstruction_time) & (sgdu_distance_df['dist_km'] > 0.00) & (sgdu_distance_df['SGDU_1'] != sgdu_distance_df['SGDU_2']),['SGDU_1','SGDU_2','lat_1','lon_1','lat_2','lon_2']]
		# if (len(interested_sgdu_records) > 0):
			# appropriate_pairs_of_sgdus = []
			# for sgdu_1,sgdu_2,lat_1,lon_1,lat_2,lon_2 in interested_sgdu_records.values:
				# temp_pt_1 = pygplates.PointOnSphere((lat_1,lon_1))
				# temp_pt_2 = pygpaltes.PointOnSphere((lat_2,lon_2))
				# is_valid = True
				# try:
					# temp_great_circle_arc = pygplates.GreatCircleArc(temp_pt_1,temp_pt_2)
				# except (IndeterminateResultError):
					# is_valid = False
				# if (is_valid == True):
					# appropriate_pairs_of_sgdus.append((sgdu_1,sgdu_2))
			# #8ii)
			# temp_list_of_centroids_and_polygids = []
			# for random_gdu_key in dict_of_gdu_and_centroid:
				# temp_list_of_tuples = dict_of_gdu_and_centroid[random_gdu_key]
				# for random_centroid,random_polygid in temp_list_of_tuples:
					# temp_list_of_centroids_and_polygids.append((random_centroid,random_polygid))
			# for sgdu_1,sgdu_2 in appropriate_pairs_of_sgdus:
				# list_of_gdus_for_sgdu1 = dict_of_sgdu_and_members_ids[str(sgdu_1)]
				# list_of_gdus_for_sgdu2 = dict_of_sgdu_and_members_ids[str(sgdu_2)]
				# for gdu1 in list_of_gdus_for_sgdu1:
					# list_of_centroid_and_polygid_for_gdu1 = dict_of_gdu_and_centroid[str(gdu1)]
					# closest_distance = -1.00
					# for gdu2 in list_of_gdus_for_sgdu2:
						# list_of_centroid_and_polygid_for_gdu2 = dict_of_gdu_and_centroid[str(gdu2)]
						# for c1,polygid1 in list_of_centroid_and_polygid_for_gdu1:
							# shapely_point_1 = convert_PointOnSphere_to_Point_in_Shapely(c1)
							# projected_c1 = project_any_Shapely_geometry_in_wgs84_lon_lat_coordinates_to_planar_projection(shapely_point_1, choosen_epsg_projection)
							# for c2,polygid2 in list_of_centroid_and_polygid_for_gdu2:
								# shapely_point_2 = convert_PointOnSphere_to_Point_in_Shapely(c2)
								# projected_c2 = project_any_Shapely_geometry_in_wgs84_lon_lat_coordinates_to_planar_projection(shapely_point_2, choosen_epsg_projection)
								# mag,azi,inc = find_magnitude_azimuth_inclination_from_a_ref_point_to_a_given_point(projected_c1, projected_c2)
								# if (azi >= (math.pi/4.00) and azi <= (math.pi*3.00/4.00)):
									# for unknown_c,unknown_polygid in temp_list_of_centroids_and_polygids:
										# if (unknown_polygid != polygid1 and unknown_polygid != polygid2):
											# shapely_point_unknown = convert_PointOnSphere_to_Point_in_Shapely(unknown_c)
											# projected_unknown = project_any_Shapely_geometry_in_wgs84_lon_lat_coordinates_to_planar_projection(shapely_point_unknown, choosen_epsg_projection)
											# result_of_examine_pos = examine_position_of_unknown_pt_relative_to_from_and_to_pts_in_planar_coordinates(projected_c1,projected_c2,projected_unknown,maximum_accepted_angle_in_degrees)
											# if (result_of_examine_pos != 'between'):
												# for reconstructed_gdu_ft,reconstructed_gdu_polygon in final_reconstructed_gdu_features:
													# shapely_polygon = convert_PolygonOnSphere_to_Polygon_in_Shapely(reconstructed_gdu_polygon)
													# projected_polygon = project_any_Shapely_geometry_in_wgs84_lon_lat_coordinates_to_planar_projection(shapely_polygon, choosen_epsg_projection)
													# result_of_examine_crossing_polygon = is_line_crossing_polygon(projected_c1, projected_c2, projected_polygon, threshold_distance_in_km)
													# if (result_of_examine_crossing_polygon == False):
														# list_of_tuples_to_be_evaluated.append((c1,polygid1,projected_c1,c2,polygid2,projected_c2))
		#Write recording at every reconstruction time to avoid a singel huge dataset
		# if (len(output_list) > 0):
			# output_dataframe = pd.DataFrame.from_records(output_list, columns = ['reconstruction_time','SGDU','GDU','rec_lat','rec_lon','polygid'])
			# filename = modelname+'_sgu_and_outer_gdu_members_at_'+str(reconstruction_time)+'_'+yearmonthday+'.csv'
			# output_dataframe.to_csv(filename,index=False)
		# output_list[:] = []
		reconstruction_time = reconstruction_time - time_interval
	
	#Write all records at the end
	if (len(output_list) > 0):
		output_dataframe = pd.DataFrame.from_records(output_list, columns = ['reconstruction_time','SGDU','GDU','rec_lat','rec_lon','polygid'])
		filename = modelname+'_sgu_and_outer_gdu_members_from_'+str(begin_reconstruction_time)+'_'+str(end_reconstruction_time)+'_'+yearmonthday+'.csv'
		output_dataframe.to_csv(filename,index=False)
		output_list[:] = []

def calculate_2D_velocity_of_two_given_points(shapely_from_time_point,shapely_to_time_point,time_interval):
	x_component = (shapely_to_time_point.x-shapely_from_time_point.x)/time_interval
	y_component = (shapely_to_time_point.y-shapely_from_time_point.y)/time_interval
	tuple_vel_vec = (x_component,y_component)
	return tuple_vel_vec

def evaluate_kinematics_between_two_2D_Shapely_pts(shapely_from_point,shapely_to_point,tuple_vel_vec_of_from_point,tuple_vel_vec_of_to_point,angle_window_for_transform):
	'''both shapely_from_point and shapely_to_point have the datatype as Point in Shapely
	kinematics is defined by the angle between the relative position vector and the relative velocity vector'''
	#calculate x and y components of the relative position vector 
	vec_x = shapely_to_point.x - shapely_from_point.x
	vec_y = shapely_to_point.y - shapely_from_point.y
	tuple_vec_pos = (vec_x,vec_y)
	#calculate relative velocity vector
	relative_vel_vector_x = tuple_vel_vec_of_to_point[0] - tuple_vel_vec_of_from_point[0]
	relative_vel_vector_y = tuple_vel_vec_of_to_point[1] - tuple_vel_vec_of_from_point[1]
	tuple_vec_vel = (relative_vel_vector_x,relative_vel_vector_y)
	theta = calculate_angle_between_two_planar_vectors(tuple_vec_pos, tuple_vec_vel)
	cutoff_value_of_angle_for_convergence = 90.00 - angle_window_for_transform
	cutoff_value_of_angle_for_divergence = 90.00 + angle_window_for_transform
	if (theta >= (90.00 - angle_window_for_transform) and theta <= (90.00 + angle_window_for_transform)):
		return 'Transform'
	elif (theta > cutoff_value_of_angle_for_divergence):
		if (cutoff_value_of_angle_for_divergence < 135.00):
			if (theta <= 180.00 and theta >= 135.00):
				return 'Divergence'
			else:
				return 'Oblique_divergence'
		else:
			if (theta <= 180.00 and theta >= cutoff_value_of_angle_for_divergence):
				return 'Divergence'
			else:
				return 'Oblique_divergence'
	elif (theta < (cutoff_value_of_angle_for_convergence)):
		if (cutoff_value_of_angle_for_convergence > 45.00):
			if (theta <= 45.00):
				return 'Convergence'
			else:
				return 'Oblique_convergence'
		else:
			if (theta <= cutoff_value_of_angle_for_convergence):
				return 'Convergence'
			else:
				return 'Oblique_convergence'

def find_the_mid_of_two_PointOnSphere(p1,p2):
	"""
		p1 and p2: pygplates.PointOnSphere
		Return: a mid point between p1 and p2 in the datatype pygplates.PointOnSphere
		
		p1 and p2 can be expressed as (x,y,z) coordinates in pygplates. Thus, mid_point(x,y,z) = (x1+x2/2.0, y1+y2/2.0, z1+z2/2.0)
	"""
	x1,y1,z1 = p1.to_xyz()
	x2,y2,z2 = p2.to_xyz()
	mid_point_x = (x1+x2)/2.00
	mid_point_y = (y1+y2)/2.00
	mid_point_z = (z1+z2)/2.00
	
	vector = pygplates.Vector3D([mid_point_x, mid_point_y, mid_point_z])
	normalized_vector = vector.to_normalised()
	
	mid_point = pygplates.PointOnSphere(normalized_vector.to_xyz())
	return mid_point

def identify_left_gdu_and_right_gdu(normal_unit_vector, rift_point_location, mid_point_line_1, mid_point_line_2, plate_id_1, plate_id_2):
	opposite_unit_vector = normal_unit_vector*(-1.00)
	#use this normal_unit_vector, from the rift_point_location, move to left line ft and move to right line ft 
	rift_point_location_x,rift_point_location_y,rift_point_location_z = rift_point_location.to_xyz()
	mid_point_line_1_x,mid_point_line_1_y,mid_point_line_1_z = mid_point_line_1.to_xyz()
	mid_point_line_2_x,mid_point_line_2_y,mid_point_line_2_z = mid_point_line_2.to_xyz()
	
	#identify left and right
	vector_to_line_1 = pygplates.Vector3D([(mid_point_line_1_x-rift_point_location_x),(mid_point_line_1_y-rift_point_location_y),(mid_point_line_1_z-rift_point_location_z)])
	normalized_vector_to_line_1 = vector_to_line_1.to_normalised()
	vector_to_line_2 = pygplates.Vector3D([(mid_point_line_2_x-rift_point_location_x),(mid_point_line_2_y-rift_point_location_y),(mid_point_line_2_z-rift_point_location_z)])
	normalized_vector_to_line_2 = vector_to_line_2.to_normalised()
	
	left = None
	right = None 

	if (pygplates.Vector3D.dot(normalized_vector_to_line_1,normal_unit_vector) > 0 and pygplates.Vector3D.dot(normalized_vector_to_line_2,opposite_unit_vector) > 0):
		left = plate_id_1
		right = plate_id_2
	elif (pygplates.Vector3D.dot(normalized_vector_to_line_1,opposite_unit_vector) > 0 and pygplates.Vector3D.dot(normalized_vector_to_line_2,normal_unit_vector) > 0):
		left = plate_id_2
		right = plate_id_1	
	else:
		print("Error in find_rift_segment_and_transform_faults")
		print("line_1 and line_2 are not located on two different sides relative to the mid_point")
		print("dot product of unit vectors for line_1")
		print(pygplates.Vector3D.dot(normalized_vector_to_line_1,normal_unit_vector))
		print("dot product of unit vectors for line_2")
		print(pygplates.Vector3D.dot(normalized_vector_to_line_2,normal_unit_vector))
		
		print ('rift_point_location')
		print(rift_point_location)
		
		print('mid_point_line_1')
		print(mid_point_line_1)
		
		print('mid_point_line_2')
		print(mid_point_line_2)
		
		print('plate_id_1')
		print(plate_id_1)
		print('plate_id_2')
		print(plate_id_2)
		exit()
	return (left,right)

def identify_left_gdu_and_right_gdu(normal_unit_vector, rift_point_location, mid_point_line_1, mid_point_line_2, plate_id_1, plate_id_2):
	#Method 1:
	opposite_unit_vector = normal_unit_vector*(-1.00)
	#use this normal_unit_vector, from the rift_point_location, move to left line ft and move to right line ft 
	rift_point_location_x,rift_point_location_y,rift_point_location_z = rift_point_location.to_xyz()
	mid_point_line_1_x,mid_point_line_1_y,mid_point_line_1_z = mid_point_line_1.to_xyz()
	mid_point_line_2_x,mid_point_line_2_y,mid_point_line_2_z = mid_point_line_2.to_xyz()
	
	#identify left and right
	vector_to_line_1 = pygplates.Vector3D([(mid_point_line_1_x-rift_point_location_x),(mid_point_line_1_y-rift_point_location_y),(mid_point_line_1_z-rift_point_location_z)])
	normalized_vector_to_line_1 = vector_to_line_1.to_normalised()
	vector_to_line_2 = pygplates.Vector3D([(mid_point_line_2_x-rift_point_location_x),(mid_point_line_2_y-rift_point_location_y),(mid_point_line_2_z-rift_point_location_z)])
	normalized_vector_to_line_2 = vector_to_line_2.to_normalised()
	
	left = None
	right = None 

	if (pygplates.Vector3D.dot(normalized_vector_to_line_1,normal_unit_vector) > 0 and pygplates.Vector3D.dot(normalized_vector_to_line_2,opposite_unit_vector) > 0):
		left = plate_id_1
		right = plate_id_2
	elif (pygplates.Vector3D.dot(normalized_vector_to_line_1,opposite_unit_vector) > 0 and pygplates.Vector3D.dot(normalized_vector_to_line_2,normal_unit_vector) > 0):
		left = plate_id_2
		right = plate_id_1
	
	if (left is not None and right is not None):
		return (left,right)

	magnitude, azimuth, inclination = pygplates.LocalCartesian.convert_from_geocentric_to_magnitude_azimuth_inclination(rift_point_location,mid_point_line_1_x,mid_point_line_1_y,mid_point_line_1_z)
	if (azimuth <= math.pi or azimuth == 2*math.pi):
		right = plate_id_1
	elif (azimuth > math.pi):
		left = plate_id_1
	magnitude, azimuth, inclination = pygplates.LocalCartesian.convert_from_geocentric_to_magnitude_azimuth_inclination(rift_point_location,mid_point_line_2_x,mid_point_line_2_y,mid_point_line_2_z)
	if (azimuth <= math.pi or azimuth == 2*math.pi):
		right = plate_id_2
	elif (azimuth > math.pi):
		left = plate_id_2
	return (left,right)


def find_total_relative_reconstruction_rotation_(rotation_model,moving_plate_id,fixed_plate_id,reconstruction_time,reference_frame):
	"""
	Total reconstruction is a reconstruction relative to the present (in time) and relative to any reference frame (spin axis or mantle or anything else)
	rotation_model: A pygplates.RotationModel
	moving_plate_id, fixed_plate_id: an int of a plate id or a gdu id - depends on the model
	reconstruction_time: a float - from present to reconstruction_time
	reference_frame: if reference_frame is None, pygplates will use 0 as the reference_frame
	"""
	finite_rotation_1 = None
	if (reference_frame is None):
		#finite_rotation_1 = rotation_model.get_rotation(reconstruction_time, plat_id_or_gdu_id, 0.00, anchor_plate_id = 0)
		finite_rotation_1 = rotation_model.get_rotation(reconstruction_time, moving_plate_id, 0.00, fixed_plate_id,anchor_plate_id = 0)
	else:
		finite_rotation_1 = rotation_model.get_rotation(reconstruction_time, moving_plate_id, 0.00, fixed_plate_id,anchor_plate_id = reference_frame)
	if (finite_rotation_1.represents_identity_rotation() == False):
		# print('moving_plate_id')
		# print(moving_plate_id)
		# print('fixed_plate_id')
		# print(fixed_plate_id)
		Euler_pole,angle_rads = finite_rotation_1.get_euler_pole_and_angle()
		# print("Euler_pole,angle_rads")
		# print(Euler_pole,angle_rads)
		lat,lon,angle_degrees = finite_rotation_1.get_lat_lon_euler_pole_and_angle_degrees()
		# print("lat,lon,angle_degrees")
		# print(lat,lon,angle_degrees)
		return finite_rotation_1
	else:
		#print("Warning in find_rift_segment_and_transform_faults")
		#print("Warning finite_rotation_1 is identity")
		#print(moving_plate_id, fixed_plate_id, reference_frame)
		#print("reconstruction_time")
		#print(reconstruction_time)
		# print('moving_plate_id')
		# print(moving_plate_id)
		# print('fixed_plate_id')
		# print(fixed_plate_id)
		Euler_pole,angle_rads = finite_rotation_1.get_euler_pole_and_angle()
		# print("Euler_pole,angle_rads")
		# print(Euler_pole,angle_rads)
		lat,lon,angle_degrees = finite_rotation_1.get_lat_lon_euler_pole_and_angle_degrees()
		# print("lat,lon,angle_degrees")
		# print(lat,lon,angle_degrees)
		return finite_rotation_1

def find_stage_relative_reconstruction_rotation_(rotation_model,moving_plate_id,fixed_plate_id,from_time,to_time,reference_frame):
	"""
	Relative stage reconstruction is a reconstruction from any from_time to any to_time between any two GDUIDS
	rotation_model: A pygplates.RotationModel
	moving_plate_id, fixed_plate_id: an int of a plate id or a gdu id - depends on the model
	reconstruction_time: a float - from present to reconstruction_time
	reference_frame: if reference_frame is None, pygplates will use 0 as the reference_frame
	"""
	finite_rotation_1 = None
	if (reference_frame is None):
		#finite_rotation_1 = rotation_model.get_rotation(reconstruction_time, plat_id_or_gdu_id, 0.00, anchor_plate_id = 0)
		finite_rotation_1 = rotation_model.get_rotation(to_time, moving_plate_id, from_time, fixed_plate_id,anchor_plate_id = 0)
	else:
		finite_rotation_1 = rotation_model.get_rotation(to_time, moving_plate_id, from_time, fixed_plate_id,anchor_plate_id = reference_frame)
	if (finite_rotation_1.represents_identity_rotation() == False):
		#print('moving_plate_id')
		#print(moving_plate_id)
		#print('fixed_plate_id')
		#print(fixed_plate_id)
		Euler_pole,angle_rads = finite_rotation_1.get_euler_pole_and_angle()
		#print("Euler_pole,angle_rads")
		#print(Euler_pole,angle_rads)
		lat,lon,angle_degrees = finite_rotation_1.get_lat_lon_euler_pole_and_angle_degrees()
		#print("lat,lon,angle_degrees")
		#print(lat,lon,angle_degrees)
		return finite_rotation_1
	else:
		#print("Warning in find_rift_segment_and_transform_faults")
		#print("Warning finite_rotation_1 is identity")
		#print(moving_plate_id, fixed_plate_id, reference_frame)
		#print("from_time,to_time")
		#print(from_time,to_time)
		# print('moving_plate_id')
		# print(moving_plate_id)
		# print('fixed_plate_id')
		# print(fixed_plate_id)
		Euler_pole,angle_rads = finite_rotation_1.get_euler_pole_and_angle()
		# print("Euler_pole,angle_rads")
		# print(Euler_pole,angle_rads)
		lat,lon,angle_degrees = finite_rotation_1.get_lat_lon_euler_pole_and_angle_degrees()
		# print("lat,lon,angle_degrees")
		# print(lat,lon,angle_degrees)
		return finite_rotation_1

def convert_LineOnSphere_in_pygplates_to_LineString_in_Shapely(line):
	if (line.get_arc_length() > 0.00):
		list_of_lon_lat_vertices = [(lon,lat) for lat,lon in line.to_lat_lon_list()]
		linestr = LineString(list_of_lon_lat_vertices)
		if (linestr is None):
			print ("Error to convert convert_LineOnSphere_in_pygplates_to_LineString_in_Shapely")
			print ("Here is a list_of_lon_lat_vertices")
			print (list_of_lon_lat_vertices)
			exit()
		return linestr
	else:
		print ("Error in convert_LineOnSphere_in_pygplates_to_LineString_in_Shapely")
		print ("line.get_arc_length == 0")
		print ("here are coords for line:")
		print((line.to_lat_lon_list()))
		print ("here is line")
		print (line)
		exit()

def are_two_PolylineOnSphere_similar(geom1,geom2):
	line_in_LineStr = convert_LineOnSphere_in_pygplates_to_LineString_in_Shapely(geom1)
	other_line_in_LineStr = convert_LineOnSphere_in_pygplates_to_LineString_in_Shapely(geom2)
	result_of_geom_rlx = line_in_LineStr.equals(other_line_in_LineStr) or line_in_LineStr.within(other_line_in_LineStr)
	if (result_of_geom_rlx == False):
		result_of_geom_rlx = line_in_LineStr.equals_exact(other_line_in_LineStr,tolerance=0.500)
		if (result_of_geom_rlx == False):
			coords_other_LineString = list(other_line_in_LineStr.coords)
			coords_other_LineString.reverse()
			other_line_in_LineStr_reversed = LineString(coords_other_LineString)
			result_of_geom_rlx = line_in_LineStr.equals(other_line_in_LineStr_reversed)
			if (result_of_geom_rlx == False):
				result_of_geom_rlx = line_in_LineStr.equals_exact(other_line_in_LineStr_reversed,tolerance=0.500)
				if (result_of_geom_rlx == False):
					result_of_geom_rlx = line_in_LineStr.covers(other_line_in_LineStr_reversed)
					if (result_of_geom_rlx == False):
						result_of_geom_rlx = other_line_in_LineStr_reversed.covers(line_in_LineStr)
	return result_of_geom_rlx

def is_point_in_between_point_A_and_B_using_greatcirclearc(suspected_point,point_B,point_A):
	if (point_B == point_A or point_B == suspected_point):
		return None
	greatcirclearc_from_B_to_A = pygplates.GreatCircleArc(point_B,point_A)
	rad_arc_len_from_B_to_A = greatcirclearc_from_B_to_A.get_arc_length()
	greatcirclearc_from_B_to_suspected = pygplates.GreatCircleArc(point_B,suspected_point)
	rad_arc_len_from_B_to_suspected = greatcirclearc_from_B_to_suspected.get_arc_length()
	if (rad_arc_len_from_B_to_suspected <= rad_arc_len_from_B_to_A):
		dir_at_suspected = greatcirclearc_from_B_to_suspected.get_arc_direction(1.00)
		dir_at_A = greatcirclearc_from_B_to_A.get_arc_direction(1.00)
		angle = pygplates.Vector3D.angle_between(dir_at_A,dir_at_suspected)
		if (angle <= (math.pi/4.00)):
			return True
		else:
			return False
	else:
		return None
		
def quickly_derive_mid_point_and_order_of_mid_point_from_two_divergent_points(pt_1,pt_2,Euler_pole):
	approx_mid_point = find_the_mid_of_two_PointOnSphere(pt_1,pt_2)
	vec_E_pole = pygplates.Vector3D(Euler_pole.to_xyz())
	vec_mid_point = pygplates.Vector3D(approx_mid_point.to_xyz())
	angle_rads = pygplates.Vector3D.angle_between(vec_mid_point,vec_E_pole)
	#convert angle_rads to degrees
	theta_degrees = math.degrees(angle_rads)
	return (approx_mid_point,theta_degrees)

def find_divergent_line_features(rotation_model, sgdu_history_csv, start_time_of_div_csv, common_filename_for_temporary_sgdu_and_members_csv, sgdu_features, gdu_features_collection, line_features_collection, begin_reconstruction_time, end_reconstruction_time, time_interval, reference, angle_window_for_transform, maximum_accepted_angle_in_degrees, choosen_epsg_projection, threshold_distance_in_km_for_neighbour, threshold_distance_in_km, yearmonthday, modelname):
	#original_present_day_line_fts_df = gpd.read_file(original_present_day_line_fts_shp)
	#sgdu_distance_df = pd.read_csv(sgdu_distance_csv, delimiter=',', header = 0)
	#framework_dic = {'origin_lv':[],'SGDU':[],'parent':[],'from_time':[],'to_time':[],'repGDUID':[]}
	sgdu_history_df = pd.read_csv(sgdu_history_csv, delimiter=',', header = 0)
	#SGDU,start_div,repGDUID
	start_time_of_div_df = pd.read_csv(start_time_of_div_csv, delimiter = ',', header = 0)
	print('finished reading dataframe')
	dict_of_polygid_and_Shapely_centroid = {}
	dic_of_gdu_members_for_each_sgdu = {}
	dic_prev_div_line_feats = {}
	previous_diverging_line_feats = []
	temp_list_of_centroids_and_polygids = []
	reconstructed_sgdu_features = []
	output_kinematics = []
	suspected_output = []
	appropriate_pairs_of_sgdus = []
	key_of_sgdus = []
	reconstructed_gdu_fts_for_sgdu1 = []
	reconstructed_gdu_fts_for_sgdu2 = []
	prev_reconstructed_gdu_fts_for_sgdu1 = []
	prev_reconstructed_gdu_fts_for_sgdu2 = []
	reconstructed_gdu_features = []
	reconstructed_gdu_features_ynger = []
	reconstructed_line_features = []
	reconstructed_line_features_ynger = []
	other_reconstructed_gdu_features = []
	output_rift_point_features = pygplates.FeatureCollection()
	output_diverging_line_features = pygplates.FeatureCollection()
	unsure_topology_for_MOR_fts = pygplates.FeatureCollection()
	kin_line_feats_at_reconstruction_time = []
	list_of_ordered_pairs_gdu_fts = []
	output_temporary_MOR_line_feats = []
	dic_kin_line_feats = {}
	output_records_for_kin_feats = []
	output_collision = []
	results_of_all_possible_tectonic_motion = []
	list_dot_prod = []
	pairs_of_kin_line_fts = []
	if (end_reconstruction_time <= 0.00):
		end_reconstruction_time = time_interval #if end_reconstruction_time == 0.00 and time_interval is 5.00, then update the last time instant to be evaluate to be 5.00
	reconstruction_time = begin_reconstruction_time
	while(reconstruction_time >= end_reconstruction_time):
		#debug
		temporary_output_pair_div_line_fts = pygplates.FeatureCollection()
		print('reconstruction_time',reconstruction_time)
		list_dot_prod[:] = []
		dic_of_gdu_members_for_each_sgdu.clear()
		reconstructed_sgdu_features[:] = []
		reconstructed_gdu_features[:] = []
		reconstructed_line_features[:] = []
		other_reconstructed_gdu_features[:] = []
		results_of_all_possible_tectonic_motion[:] = []
		# #8) Find appropriate pairs of sgdus first based on the distance
		# #8i) Find valid sgdu features
		valid_sgdu_features = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(reconstruction_time))]
		# #8ii) Reconstruct sgdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_sgdu_features = find_final_reconstructed_geometries(reconstructed_sgdu_features, pygplates.PolygonOnSphere)
		#Find valid gdu features with con-ocn line features
		valid_con_ocn_line_features = [con_ocn_ft for con_ocn_ft in line_features_collection if con_ocn_ft.is_valid_at_time(reconstruction_time)]
		if (reference is not None):
			pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_line_features, pygplates.PolylineOnSphere)
		# #8i) Find valid gdu features at reconstruction_time 
		valid_in_time_gdu_features = [gdu_ft for gdu_ft in gdu_features_collection if (gdu_ft.is_valid_at_time(reconstruction_time))]
		valid_gdu_features = []
		already_included_gdu_fts = []
		for valid_line_ft,valid_line in final_reconstructed_line_features:
			#debug
			#if (valid_line_ft.get_reconstruction_plate_id() == 19508):
			#	print(valid_line_ft.get_reconstruction_plate_id())
			
			for gdu_ft in valid_in_time_gdu_features:
				if (valid_line_ft.get_shapefile_attribute('polygid') == gdu_ft.get_shapefile_attribute('POLYGID')):
					if (gdu_ft.get_shapefile_attribute('POLYGID') not in already_included_gdu_fts):
						valid_gdu_features.append(gdu_ft)
						already_included_gdu_fts.append(gdu_ft.get_shapefile_attribute('POLYGID'))
					# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
						# valid_gdu_features.append(gdu_ft)
						#already_included_gdu_fts.append(gdu_ft.get_feature_id())
				# else:
					# if (gdu_ft.get_reconstruction_plate_id() == valid_line_ft.get_reconstruction_plate_id()):
						# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
							# valid_gdu_features.append(gdu_ft)
							# already_included_gdu_fts.append(gdu_ft.get_feature_id())
		print('len(valid_gdu_features)',len(valid_gdu_features))
		print('len(valid_con_ocn_line_features)',len(valid_con_ocn_line_features))
						
		# #8ii) Reconstruct gdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_gdu_features, rotation_model, reconstructed_gdu_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_gdu_features, rotation_model, reconstructed_gdu_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_gdu_features = find_final_reconstructed_geometries(reconstructed_gdu_features, pygplates.PolygonOnSphere)
		dict_of_gdu_and_centroid = find_centroid_of_each_reconstructed_gdu_ft(final_reconstructed_gdu_features)
		#dict_of_neighbours = find_neighbours_of_each_reconstructed_gdu_ft(dict_of_gdu_and_centroid,threshold_distance_in_km_for_neighbour)
		dic_of_gdu_members_for_each_sgdu = find_gdu_members_of_each_sgdu_feat(valid_gdu_features, valid_sgdu_features, common_filename_for_temporary_sgdu_and_members_csv, reconstruction_time)
		print('number of sgdu features in dic_of_gdu_members_for_each_sgdu',len(dic_of_gdu_members_for_each_sgdu))
		
		# #8i) Find valid gdu features at reconstruction_time - time_interval
		valid_in_time_gdu_features_in_ynger = [gdu_ft for gdu_ft in gdu_features_collection if (gdu_ft.is_valid_at_time(reconstruction_time-time_interval))]
		valid_gdu_features_ynger = []
		already_included_gdu_fts_ynger = []
		reconstructed_gdu_features_ynger[:] = []
		reconstructed_line_features_ynger[:] = []
		#Find valid gdu features with con-ocn line features
		valid_con_ocn_line_features_ynger = [con_ocn_ft for con_ocn_ft in line_features_collection if con_ocn_ft.is_valid_at_time(reconstruction_time-time_interval)]
		if (reference is not None):
			pygplates.reconstruct(valid_con_ocn_line_features_ynger, rotation_model, reconstructed_line_features_ynger, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_con_ocn_line_features_ynger, rotation_model, reconstructed_line_features_ynger, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_line_features_ynger = find_final_reconstructed_geometries(reconstructed_line_features_ynger, pygplates.PolylineOnSphere)
		for valid_line_ft,valid_line in final_reconstructed_line_features_ynger:
			for gdu_ft in valid_in_time_gdu_features_in_ynger:
				if (valid_line_ft.get_shapefile_attribute('polygid') == gdu_ft.get_shapefile_attribute('POLYGID')):
					if (gdu_ft.get_shapefile_attribute('POLYGID') not in already_included_gdu_fts_ynger):
						valid_gdu_features_ynger.append(gdu_ft)
						already_included_gdu_fts_ynger.append(gdu_ft.get_shapefile_attribute('POLYGID'))
					# if (gdu_ft.get_feature_id() not in already_included_gdu_fts_ynger):
						# valid_gdu_features_ynger.append(gdu_ft)
						#already_included_gdu_fts_ynger.append(gdu_ft.get_feature_id())
				# else:
					# if (gdu_ft.get_reconstruction_plate_id() == valid_line_ft.get_reconstruction_plate_id()):
						# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
							# valid_gdu_features.append(gdu_ft)
							# already_included_gdu_fts.append(gdu_ft.get_feature_id())
		print('len(valid_gdu_features_ynger)',len(valid_gdu_features_ynger))
		print('len(valid_con_ocn_line_features_ynger)',len(valid_con_ocn_line_features_ynger))
		# #8ii) Reconstruct gdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_gdu_features_ynger, rotation_model, reconstructed_gdu_features_ynger, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_gdu_features_ynger, rotation_model, reconstructed_gdu_features_ynger, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_gdu_features_ynger = find_final_reconstructed_geometries(reconstructed_gdu_features_ynger, pygplates.PolygonOnSphere)
		valid_sgdu_features_ynger = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(reconstruction_time-time_interval))]
		dic_of_gdu_members_for_each_sgdu_ynger = find_gdu_members_of_each_sgdu_feat(valid_gdu_features_ynger, valid_sgdu_features_ynger, common_filename_for_temporary_sgdu_and_members_csv, reconstruction_time-time_interval)
		print('number of sgdu features in dic_of_gdu_members_for_each_sgdu_ynger',len(dic_of_gdu_members_for_each_sgdu_ynger))
		reconstructed_sgdu_features[:] = []
		if (reference is not None):
			pygplates.reconstruct(valid_sgdu_features_ynger, rotation_model, reconstructed_sgdu_features, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_sgdu_features_ynger, rotation_model, reconstructed_sgdu_features, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_sgdu_features_ynger = find_final_reconstructed_geometries(reconstructed_sgdu_features, pygplates.PolygonOnSphere)

		# #8iii) Find appropriate pairs of sgdus
		#SGDU,start_div,repGDUID
		polygid_all_valid_line_features = [con_ocn_ft.get_shapefile_attribute('polygid') for con_ocn_ft in valid_con_ocn_line_features]
		array_of_all_valid_polygid = np.array(polygid_all_valid_line_features)
		#print('array_of_all_valid_polygid',array_of_all_valid_polygid)
		already_evaluated_pairs_of_sgdus = []
		records_of_sgdus_diverging = start_time_of_div_df.loc[abs(start_time_of_div_df['start_div'] - reconstruction_time) <= 0.500, ['SGDU','repGDUID','start_div']]
		if (len(records_of_sgdus_diverging) > 0):
			for tuple_of_sgdu_repgdu in records_of_sgdus_diverging.itertuples(index = False, name = None):
				parent_div_sgdu, parent_repgduid, start_div = tuple_of_sgdu_repgdu
				#use sgdu history to find the sgdu children 
				children_sgdus = sgdu_history_df.loc[(sgdu_history_df['parent'] == parent_div_sgdu),['SGDU','repGDUID','from_time']]
				if (len(children_sgdus) >= 2):
					for child_1,child_repgduid_1,from_time_div in children_sgdus.itertuples(index = False, name = None):
						if (str(child_1) not in dic_of_gdu_members_for_each_sgdu):
							continue
						gdu_features_for_sgdu1 = dic_of_gdu_members_for_each_sgdu[str(child_1)]
						if (len(gdu_features_for_sgdu1) == 0):
							continue
						for child_2,child_repgduid_2,from_time_div in children_sgdus.itertuples(index = False, name = None):
							if (str(child_2) not in dic_of_gdu_members_for_each_sgdu):
								continue
							gdu_features_for_sgdu2 = dic_of_gdu_members_for_each_sgdu[str(child_2)]
							if (len(gdu_features_for_sgdu2) == 0):
								continue
							if (child_1 != child_2):
								key = str(child_1)+'_'+str(child_2)
								rev_key = str(child_2)+'_'+str(child_1)
								if (key not in already_evaluated_pairs_of_sgdus and rev_key not in already_evaluated_pairs_of_sgdus):
									already_evaluated_pairs_of_sgdus.append(key)
									#use the two repgduids from the two children 
									total_relative_reconstruction_rotation = find_total_relative_reconstruction_rotation_(rotation_model, child_repgduid_1, child_repgduid_2, float(from_time_div), reference)
									total_stage_rel_rot_of_1_to_2 = find_stage_relative_reconstruction_rotation_(rotation_model,child_repgduid_1,child_repgduid_2,float(from_time_div),float(from_time_div)-time_interval,reference)
									total_stage_rel_rot_of_2_to_1 = find_stage_relative_reconstruction_rotation_(rotation_model,child_repgduid_2,child_repgduid_1,float(from_time_div),float(from_time_div)-time_interval,reference)
									if (total_relative_reconstruction_rotation is not None):
										if (total_relative_reconstruction_rotation.represents_identity_rotation() == False):
											list_of_rift_points = []
											#check whether the pair of sgdus is valid
											child_sgud_1 = []
											child_sgud_2 = []
											non_related = []
											#for yng_sgdu_ft,yng_sgdu in final_reconstructed_sgdu_features_ynger:
											for yng_sgdu_ft,yng_sgdu in final_reconstructed_sgdu_features:
												if (yng_sgdu_ft.get_name() == str(child_1)):
													child_sgud_1.append(yng_sgdu)
												elif (yng_sgdu_ft.get_name() == str(child_2)):
													child_sgud_2.append(yng_sgdu)
												else:
													non_related.append(yng_sgdu)
											reconstructed_gdu_fts_for_sgdu1[:] = []
											reconstructed_gdu_fts_for_sgdu2[:] = []
											prev_reconstructed_gdu_fts_for_sgdu1[:] = []
											prev_reconstructed_gdu_fts_for_sgdu2[:] = []
											#list_of_ordered_pairs_gdu_fts = []
											list_of_already_used_line_fts = []
											#gdu_features_for_sgdu1 = dic_of_gdu_members_for_each_sgdu[str(child_1)]
											#gdu_features_for_sgdu1_valid_at_prev_time = [current_gdu_ft_1 for current_gdu_ft_1 in gdu_features_for_sgdu1 if current_gdu_ft_1.is_valid_at_time(reconstruction_time + time_interval)]
											#gdu_features_for_sgdu2 = dic_of_gdu_members_for_each_sgdu[str(child_2)]
											#gdu_features_for_sgdu2_valid_at_prev_time = [current_gdu_ft_2 for current_gdu_ft_2 in gdu_features_for_sgdu2 if current_gdu_ft_2.is_valid_at_time(reconstruction_time + time_interval)]
											final_reconstructed_gdu_features_for_sgdu1 = []
											final_reconstructed_gdu_features_for_sgdu2 = []
											prev_final_reconstructed_gdu_features_for_sgdu1 = []
											prev_final_reconstructed_gdu_features_for_sgdu2 = []
											polygid_features_for_sgdu1 = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu1]
											array_for_polygid_ft_sgdu1 = np.array(polygid_features_for_sgdu1)
											#polygid_features_for_sgdu1_at_prev_time = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu1_valid_at_prev_time]
											wanted_gdu_members_for_sgdu1 = np.intersect1d(array_for_polygid_ft_sgdu1,array_of_all_valid_polygid)
											polygid_features_for_sgdu2 = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu2]
											array_for_polygid_ft_sgdu2 = np.array(polygid_features_for_sgdu2)
											wanted_gdu_members_for_sgdu2 = np.intersect1d(array_for_polygid_ft_sgdu2,array_of_all_valid_polygid)
											#polygid_features_for_sgdu2_at_prev_time = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu2_valid_at_prev_time]
											
											#CON-OCN line features that exit at the younger time (i.e. reconstruction_time - time_interval) and invalid at reconstruction_time
											#for child_gdu_ft_1, child_line_gdu_1 in final_reconstructed_line_features_ynger:
											for child_gdu_ft_1, child_line_gdu_1 in final_reconstructed_line_features:
												polygid_for_child_1 = child_gdu_ft_1.get_shapefile_attribute('polygid')
												#if ((polygid_for_child_1 in wanted_gdu_members_for_sgdu1) and (polygid_for_child_1 not in polygid_features_for_sgdu1_at_prev_time)):
												if (polygid_for_child_1 in wanted_gdu_members_for_sgdu1):
													for reconstructed_sgdu_1 in child_sgud_1:
														if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_1,child_line_gdu_1) == 0.00):
															reconstructed_gdu_fts_for_sgdu1.append((child_gdu_ft_1, child_line_gdu_1))
															break
											#for child_gdu_ft_2, child_line_gdu_2 in final_reconstructed_line_features_ynger:
											for child_gdu_ft_2, child_line_gdu_2 in final_reconstructed_line_features:
												polygid_for_child_2 = child_gdu_ft_2.get_shapefile_attribute('polygid')
												#if ((polygid_for_child_2 in polygid_features_for_sgdu2) and (polygid_for_child_2 not in polygid_features_for_sgdu2_at_prev_time)):
												if (polygid_for_child_2 in wanted_gdu_members_for_sgdu2):
													for reconstructed_sgdu_2 in child_sgud_2:
														if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_2,child_line_gdu_2) == 0.00):
															reconstructed_gdu_fts_for_sgdu2.append((child_gdu_ft_2, child_line_gdu_2))
															break
											# print('len(reconstructed_gdu_fts_for_sgdu1)',len(reconstructed_gdu_fts_for_sgdu1))
											# print('len(reconstructed_gdu_fts_for_sgdu2)',len(reconstructed_gdu_fts_for_sgdu2))
											
											#debug
											# if ((child_1 == 71261 and child_2 == 71252) or (child_2 == 71261 and child_1 == 71252)):
												# for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
													# temporary_output_pair_div_line_fts.add(gdu_line_ft_1)
												# for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
													# temporary_output_pair_div_line_fts.add(gdu_line_ft_2)
											
											E_pole,angle_rads = total_relative_reconstruction_rotation.get_euler_pole_and_angle()
											stage_rel_E_pole = None
											if (total_stage_rel_rot_of_1_to_2 is not None):
												if (total_stage_rel_rot_of_1_to_2.represents_identity_rotation() == False):
													stage_rel_E_pole,_ = total_stage_rel_rot_of_1_to_2.get_euler_pole_and_angle()
											elif (total_stage_rel_rot_of_2_to_1 is not None):
												if (total_stage_rel_rot_of_2_to_1.represents_identity_rotation() == False):
													stage_rel_E_pole,_ = total_stage_rel_rot_of_2_to_1.get_euler_pole_and_angle()
											if (stage_rel_E_pole is None):
												stage_rel_E_pole = E_pole
											result_of_tectonic_motion = None
											for reconstructed_sgdu_1 in child_sgud_1:
												centroid_sgdu_1 = reconstructed_sgdu_1.get_interior_centroid()
												for reconstructed_sgdu_2 in child_sgud_2:
													centroid_sgdu_2 = reconstructed_sgdu_2.get_interior_centroid()
													#evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time, Euler_pole):
													# A.(E_of_B_rel_to_A x B) or 1.(E_of_2_rel_to_1 x 2)
													if (total_stage_rel_rot_of_1_to_2 is not None and total_stage_rel_rot_of_1_to_2.represents_identity_rotation() == False):
														result_of_tectonic_motion,dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_2, centroid_sgdu_1, stage_rel_E_pole)
														list_dot_prod.append((reconstruction_time,child_repgduid_1,child_repgduid_2,dot_prod_btw_tectonic_motion))
													elif (total_stage_rel_rot_of_2_to_1 is not None and total_stage_rel_rot_of_2_to_1.represents_identity_rotation() == False):
														result_of_tectonic_motion,dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_1, centroid_sgdu_2, stage_rel_E_pole)
														list_dot_prod.append((reconstruction_time,child_repgduid_1,child_repgduid_2,dot_prod_btw_tectonic_motion))
													else:
														result_of_tectonic_motion,dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_2, centroid_sgdu_1, stage_rel_E_pole)
														list_dot_prod.append((reconstruction_time,child_repgduid_1,child_repgduid_2,dot_prod_btw_tectonic_motion))
													if (result_of_tectonic_motion == 'D'):
														break
													else:
														if (total_stage_rel_rot_of_1_to_2 is not None and total_stage_rel_rot_of_2_to_1 is not None):
															stage_rel_E_pole,_ = total_stage_rel_rot_of_2_to_1.get_euler_pole_and_angle()
															result_of_tectonic_motion,dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_1, centroid_sgdu_2, stage_rel_E_pole)
															list_dot_prod.append((reconstruction_time,child_repgduid_1,child_repgduid_2,dot_prod_btw_tectonic_motion))
														else:
															stage_rel_E_pole = E_pole
															result_of_tectonic_motion, dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_2, centroid_sgdu_1, stage_rel_E_pole)
															list_dot_prod.append((reconstruction_time,child_repgduid_1,child_repgduid_2,dot_prod_btw_tectonic_motion))
														if (result_of_tectonic_motion == 'D'):
															break
												if (result_of_tectonic_motion == 'D'):
													break
											#record all possible values of tectonic-motion to double-check with results when running identify_convergent_boundaries which is processing from present-day to the past
											results_of_all_possible_tectonic_motion.append((reconstruction_time,child_1,child_2,result_of_tectonic_motion))
											if (result_of_tectonic_motion != 'D'):
												continue
											smallest_circle_angular_radius_degrees = 178.00
											while (smallest_circle_angular_radius_degrees > 0.00):
												small_circle_boundary = rotation_utility.create_small_circle_PolylineOnSphere(E_pole,smallest_circle_angular_radius_degrees)
												found_pair_of_line_feats = None
												valid_pair_of_line_fts = True
												#find gdu polygon features for each line feature 
												valid_mid_point_feat = False 
												for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
													polylid_of_gdu_line_ft_1 = gdu_line_ft_1.get_shapefile_attribute('polygid')
													#list_of_neighbours_for_polylid_1 = dict_of_neighbours[polylid_of_gdu_line_ft_1]
													for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
														polylid_of_gdu_line_ft_2 = gdu_line_ft_2.get_shapefile_attribute('polygid')
														#if (polylid_of_gdu_line_ft_2 not in list_of_neighbours_for_polylid_1):
														#	continue
														approx_rad_closest_dist_neighbour,closest_point_on_gdu1,_ = pygplates.GeometryOnSphere.distance(line_gdu_1, small_circle_boundary,return_closest_positions = True)
														approx_rad_closest_dist_ref,closest_point_on_gdu2,_= pygplates.GeometryOnSphere.distance(line_gdu_2, small_circle_boundary,return_closest_positions = True)
														# calculate distance by map projection
														# lat1,lon1 = closest_point_on_gdu1.to_lat_lon()
														# lat2,lon2 = closest_point_on_gdu2.to_lat_lon()
														# choosen_epsg_projection = 'ESRI:54009'
														# if (lat1 > 0.00 and lat2 > 0.00):
															# if (abs(lat1 - 90.00) <= 10.00 or abs(lat2 - 90.00) <= 10.00):
																# choosen_epsg_projection = 'EPSG:3995'
														# elif (lat1 < 0.00 and lat2 < 0.00):
															# if (abs(lat1 + 90.00) <= 10.00 or abs(lat2 + 90.00) <= 10.00):
																# choosen_epsg_projection = 'EPSG:3031'
														# wgs84_shapely_point_1 = convert_PointOnSphere_to_Point_in_Shapely(closest_point_on_gdu1)
														# projected_c1 = project_any_Shapely_geometry_in_wgs84_lon_lat_coordinates_to_planar_projection(wgs84_shapely_point_1, choosen_epsg_projection)
														# wgs84_shapely_point_2 = convert_PointOnSphere_to_Point_in_Shapely(closest_point_on_gdu2)
														# projected_c2 = project_any_Shapely_geometry_in_wgs84_lon_lat_coordinates_to_planar_projection(wgs84_shapely_point_2, choosen_epsg_projection)
														# approx_distance_btw_lines_kms = projected_c1.distance(projected_c2)
														
														#calculate distance by haversine
														lat1,lon1 = closest_point_on_gdu1.to_lat_lon()
														lat2,lon2 = closest_point_on_gdu2.to_lat_lon()
														approx_distance_btw_lines_kms = calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2)
														
														# #debug
														# print('gdu_line_ft_1.get_shapefile_attribute(POLYLID)',gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
														# print('gdu_line_ft_2.get_shapefile_attribute(POLYLID)',gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
														# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
															# print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
															# print('approx_rad_closest_dist_neighbour',approx_rad_closest_dist_neighbour)
															# print('approx_rad_closest_dist_ref',approx_rad_closest_dist_ref)
															#exit()
														# else:
															# print ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274'))
															# print ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938'))
															
														# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12009_13906_1773' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17300_14793_2185') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '12009_13906_1773' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '17300_14793_2185')):
															# gdu_line_ft_1.set_description(gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
															# gdu_line_ft_1.set_name(key)
															# gdu_line_ft_2.set_description(gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
															# gdu_line_ft_2.set_name(key)
															#temporary_output_pair_div_line_fts.add(gdu_line_ft_1)
															#temporary_output_pair_div_line_fts.add(gdu_line_ft_2)
															# print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
															# print('approx_rad_closest_dist_neighbour',approx_rad_closest_dist_neighbour)
															# print('approx_rad_closest_dist_ref',approx_rad_closest_dist_ref)
														#debug
														#if (parent_div_sgdu == 70591 and ((child_1 == 70638 and child_2 == 70637) or (child_1 == 70637 and child_2 == 70638))):
														#	print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
														
														#approx_distance_btw_lines_kms = approx_distance_btw_lines*pygplates.Earth.mean_radius_in_kms
														if (approx_rad_closest_dist_neighbour == 0.000 and approx_rad_closest_dist_ref == 0.000): 
															#debug
															# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
																# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
															if ((approx_distance_btw_lines_kms <= 1000.00) or (gdu_line_ft_1.is_valid_at_time(reconstruction_time + time_interval)==False) or (gdu_line_ft_2.is_valid_at_time(reconstruction_time + time_interval)==False)):
																valid_pair_of_line_fts = True
																#find gdu polygon features for each line feature 
																temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = None,None
																temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = None,None
																for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
																	if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_1.get_shapefile_attribute('polygid')):
																		temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = temp_gdu_ft,temp_reconstruct_gdu_polygon
																		break
																for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
																	if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_2.get_shapefile_attribute('polygid')):
																		temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = temp_gdu_ft,temp_reconstruct_gdu_polygon
																		break
																distance_btw_two_gdus = pygplates.GeometryOnSphere.distance(temp_reconstruct_gdu_polygon_1,temp_reconstruct_gdu_polygon_2)
																if (distance_btw_two_gdus > 0.00):
																	valid_pair_of_line_fts = False
																if (valid_pair_of_line_fts == False):
																	temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
																	valid_pair_of_line_fts = True
																	for random_sgdu in non_related:
																		if (random_sgdu.partition(temporary_PolylineOnSphere) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
																			valid_pair_of_line_fts = False
																			break
																#debug
																# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
																	# print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
																	# print('approx_rad_closest_dist_neighbour',approx_rad_closest_dist_neighbour)
																	# print('approx_rad_closest_dist_ref',approx_rad_closest_dist_ref)
																	# print('distance_btw_two_gdus',distance_btw_two_gdus)
																	# print('valid_pair_of_line_fts',valid_pair_of_line_fts)
																	# #exit()
																
																if (valid_pair_of_line_fts == True):
																	if (found_pair_of_line_feats is None):
																		if (distance_btw_two_gdus == 0.00):
																			#have to double check whether the point feature fall within both superGDU or just one superGDU
																			approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
																			found_in_sgdu_1 = False
																			found_in_sgdu_2 = False
																			for temp_sgdu_1 in child_sgud_1:
																				if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																					found_in_sgdu_1 = True
																					break
																			for temp_sgdu_2 in child_sgud_2:
																				if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																					found_in_sgdu_2 = True
																					break
																			if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																				found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																				valid_mid_point_feat = True
																				#debug
																				# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
																					# print('valid_mid_point_feat',valid_mid_point_feat)
																				break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																			else:
																				found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																		else:
																			found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																		# if (gdu_line_ft_1.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																			# list_of_already_used_line_fts.append(gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
																		# if (gdu_line_ft_2.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																			# list_of_already_used_line_fts.append(gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
																	else:
																		if (distance_btw_two_gdus == 0.00):
																			#have to double check whether the point feature fall within both superGDU or just one superGDU
																			approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
																			found_in_sgdu_1 = False
																			found_in_sgdu_2 = False
																			for temp_sgdu_1 in child_sgud_1:
																				if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																					found_in_sgdu_1 = True
																					break
																			for temp_sgdu_2 in child_sgud_2:
																				if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																					found_in_sgdu_2 = True
																					break
																			if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																				found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																				valid_mid_point_feat = True
																				break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																			# else:#maybe we do not need this
																				# prev_approx_distance_btw_line_kmns = found_pair_of_line_feats[4]
																				# if (prev_approx_distance_btw_line_kmns > approx_distance_btw_lines_kms or valid_mid_point_feat == False):
																					# if (gdu_line_ft_1.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts and gdu_line_ft_2.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																						# found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																		else:
																			prev_approx_distance_btw_line_kmns = found_pair_of_line_feats[4]
																			if (prev_approx_distance_btw_line_kmns > approx_distance_btw_lines_kms or valid_mid_point_feat == False):
																				if (gdu_line_ft_1.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts and gdu_line_ft_2.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																					found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																				# list_of_already_used_line_fts.append(gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
																				# list_of_already_used_line_fts.append(gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
															#debug
															# if (smallest_circle_angular_radius_degrees == 73.00 and ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945'))):
																# print("smallest_circle_angular_radius_degrees == 73.00 12404_11454_2945 and 17023_14194_2053")
															
													#NEW---
													if (valid_mid_point_feat == True):
														#debug
														# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
															# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
																# print('before')
																# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
																# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
														break # break out of the for-loop of for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1
														
												if (found_pair_of_line_feats is not None):
													#debug
													# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
														# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
														# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
														# print('valid_mid_point_feat',valid_mid_point_feat)
													
													gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2 = found_pair_of_line_feats
													temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
													# # #debug
													# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
														# # gdu_line_ft_1.set_description(gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
														# # gdu_line_ft_1.set_name(key)
														# # gdu_line_ft_2.set_description(gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
														# # gdu_line_ft_2.set_name(key)
														# # temporary_output_pair_div_line_fts.add(gdu_line_ft_1)
														# # temporary_output_pair_div_line_fts.add(gdu_line_ft_2)
														# #print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
														# print('found_pair_of_line_feats')
														#find the mid_point between two points
													
													approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
													if (approx_mid_point == closest_point_on_gdu1 or approx_mid_point == closest_point_on_gdu2):
														temp_list_of_closest_point_on_gdu1 = dict_of_gdu_and_centroid[gdu_line_ft_1.get_shapefile_attribute('polygid')]
														closest_point_on_gdu1 = temp_list_of_closest_point_on_gdu1[0][0]
														temp_list_of_closest_point_on_gdu2 = dict_of_gdu_and_centroid[gdu_line_ft_2.get_shapefile_attribute('polygid')]
														closest_point_on_gdu2 = temp_list_of_closest_point_on_gdu2[0][0]
														if (valid_mid_point_feat == False):
															valid_mid_point_feat = True
													#debug
													# # #debug
													# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
														# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
														# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
														# print('valid_mid_point_feat at 140',valid_mid_point_feat)
														# exit()
														
													if (valid_mid_point_feat == False):
														if (pygplates.GeometryOnSphere.distance(line_gdu_1,line_gdu_2) == 0.00):
															valid_mid_point_feat = True
														# else:
															# #NEW - check whether two sgdus and their line features cross each other --- NO NEED TO DO THIS ANYMORE because we have done the check when we tried to fine the pair of line features
															# for reconstructed_sgdu_1 in child_sgud_1:
																# if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_1,line_gdu_2) == 0.00):
																	# valid_mid_point_feat = True
																	# break
															# if (valid_mid_point_feat == True):
																# temp_valid_mid_point_feat = False
																# for reconstructed_sgdu_2 in child_sgud_2:
																	# if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_2,line_gdu_1) == 0.00):
																		# temp_valid_mid_point_feat = True
																		# break
																# if (temp_valid_mid_point_feat == False):
																	# valid_mid_point_feat = False
																# else:
																	# #check to make sure the two supergdus are crossing each other
																	# if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_1,reconstructed_sgdu_2) == 0.00):
																		# valid_mid_point_feat = True
																	# else:
																		# valid_mid_point_feat = False
															# # elif (valid_mid_point_feat == False):
																# # for reconstructed_sgdu_2 in child_sgud_2:
																	# # if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_2,line_gdu_1) == 0.00):
																		# # valid_mid_point_feat = True
																		# # break
													# # #debug
													# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
														# print('valid_mid_point_feat at 1315',valid_mid_point_feat)
													#NEW - check whether approx_mid_point positioned within any SGDUs
													if (valid_mid_point_feat == False):
														are_lines_similar = are_two_PolylineOnSphere_similar(line_gdu_1,line_gdu_2)
														if (are_lines_similar == True):
															valid_mid_point_feat = True
														elif (valid_mid_point_feat == False):
															#temporarily set valid_mid_point_feat to True
															valid_mid_point_feat = True
															for random_sgdu in non_related:
																if (random_sgdu.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
																	valid_mid_point_feat = False
																	break
															if (valid_mid_point_feat == True):
																for reconstructed_sgdu_2 in child_sgud_2:
																	if (reconstructed_sgdu_2.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
																		valid_mid_point_feat = False
																		break
																# # #debug
																# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
																	# print('valid_mid_point_feat at 1335',valid_mid_point_feat)
																# # # #debug
																# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
																	# print('valid_mid_point_feat at 1338',valid_mid_point_feat)
																
															if (valid_mid_point_feat == True):
																for reconstructed_sgdu_1 in child_sgud_1:
																	if (reconstructed_sgdu_1.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
																		valid_mid_point_feat = False
																		break
																# # #debug
																# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
																	# print('valid_mid_point_feat at 1347',valid_mid_point_feat)
													if (valid_mid_point_feat == True):
														#create an arc
														temporary_GreatCircleArc = pygplates.GreatCircleArc(approx_mid_point,E_pole)
														normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
														left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, approx_mid_point, closest_point_on_gdu1, closest_point_on_gdu2, gdu_line_ft_1.get_reconstruction_plate_id(), gdu_line_ft_2.get_reconstruction_plate_id())
														list_of_rift_points.append(approx_mid_point)
														#create point feature
														#name = 'R'+str(child_1)+'_'+str(child_2)+'_'+str(smallest_circle_angular_radius_degrees)
														name = 'R'+key+'_'+str(smallest_circle_angular_radius_degrees)
														rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, approx_mid_point, name = name, valid_time = (reconstruction_time,0.00))
														if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
															rift_point_ft.set_left_plate(gdu_line_ft_1.get_reconstruction_plate_id())
															rift_point_ft.set_right_plate(gdu_line_ft_2.get_reconstruction_plate_id())
														else:
															rift_point_ft.set_left_plate(left_gduid)
															rift_point_ft.set_right_plate(right_gduid)
														rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
														rift_point_ft.set_description(str(smallest_circle_angular_radius_degrees))
														if (reference is None):
															pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
														else:
															pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
														output_rift_point_features.add(rift_point_ft)
														if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
															unsure_topology_for_MOR_fts.add(rift_point_ft)
														if ((left_gduid == gdu_line_ft_1.get_reconstruction_plate_id() and right_gduid == gdu_line_ft_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
															list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2))
														else:
															list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
													
														#create pair of line features associated with the rift point ft
														_,con_ocn_to_time = gdu_line_ft_1.get_valid_time()
														line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_1,name=gdu_line_ft_1.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
														line_feature_1.set_reconstruction_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
														line_feature_1.set_conjugate_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
														line_feature_1.set_description('divergent_margin')
														_,con_ocn_to_time = gdu_line_ft_2.get_valid_time()
														line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_2,name=gdu_line_ft_2.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
														line_feature_2.set_reconstruction_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
														line_feature_2.set_conjugate_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
														line_feature_2.set_description('divergent_margin')
														if (reference is None):
															pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time)
														else:
															pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time,reference)
														#output_diverging_line_features.add(line_feature_1)
														#output_diverging_line_features.add(line_feature_2)
														previous_diverging_line_feats.append((line_feature_1,line_feature_2,'D',reconstruction_time,pygplates.GeometryOnSphere.distance(line_gdu_1.get_centroid(),line_gdu_2.get_centroid())))
												else:
													#try a higher resolution of smallest_circle_angular_radius_degrees
													temp_small_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees
													#prev_small_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees + 1.000
													prev_small_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees + 0.500
													found_pair_of_line_feats = None
													while (temp_small_circle_angular_radius_degrees < prev_small_circle_angular_radius_degrees):
														temp_small_circle_angular_radius_degrees = temp_small_circle_angular_radius_degrees + 0.200
														small_circle_boundary = rotation_utility.create_small_circle_PolylineOnSphere(E_pole,temp_small_circle_angular_radius_degrees)
														valid_mid_point_feat = False 
														for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
															polylid_of_gdu_line_ft_1 = gdu_line_ft_1.get_shapefile_attribute('polygid')
															#list_of_neighbours_for_polylid_1 = dict_of_neighbours[polylid_of_gdu_line_ft_1]
															for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
																polylid_of_gdu_line_ft_2 = gdu_line_ft_2.get_shapefile_attribute('polygid')
																#if (polylid_of_gdu_line_ft_2 not in list_of_neighbours_for_polylid_1):
																#	continue
																approx_rad_closest_dist_neighbour, closest_point_on_gdu1, _ = pygplates.GeometryOnSphere.distance(line_gdu_1, small_circle_boundary,return_closest_positions = True)
																approx_rad_closest_dist_ref, closest_point_on_gdu2, _= pygplates.GeometryOnSphere.distance(line_gdu_2, small_circle_boundary,return_closest_positions = True)
																#calculate distance by haversine
																lat1,lon1 = closest_point_on_gdu1.to_lat_lon()
																lat2,lon2 = closest_point_on_gdu2.to_lat_lon()
																approx_distance_btw_lines_kms = calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2)
																if (approx_rad_closest_dist_neighbour == 0.000 and approx_rad_closest_dist_ref == 0.000): 
																	if ((approx_distance_btw_lines_kms <= 1000.00) or (gdu_line_ft_1.is_valid_at_time(reconstruction_time + time_interval)==False) or (gdu_line_ft_2.is_valid_at_time(reconstruction_time + time_interval)==False)):
																		valid_pair_of_line_fts = True
																		#find gdu polygon features for each line feature 
																		temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = None,None
																		temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = None,None
																		for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
																			if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_1.get_shapefile_attribute('polygid')):
																				temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = temp_gdu_ft,temp_reconstruct_gdu_polygon
																				break
																		for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
																			if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_2.get_shapefile_attribute('polygid')):
																				temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = temp_gdu_ft,temp_reconstruct_gdu_polygon
																				break
																		distance_btw_two_gdus = pygplates.GeometryOnSphere.distance(temp_reconstruct_gdu_polygon_1,temp_reconstruct_gdu_polygon_2)
																		if (distance_btw_two_gdus > 0.00):
																			valid_pair_of_line_fts = False
																		if (valid_pair_of_line_fts == False):
																			temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
																			valid_pair_of_line_fts = True
																			for random_sgdu in non_related:
																				if (random_sgdu.partition(temporary_PolylineOnSphere) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
																					valid_pair_of_line_fts = False
																					break
																		if (valid_pair_of_line_fts == True):
																			if (found_pair_of_line_feats is None):
																				if (distance_btw_two_gdus == 0.00):
																					#have to double check whether the point feature fall within both superGDU or just one superGDU
																					approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
																					found_in_sgdu_1 = False
																					found_in_sgdu_2 = False
																					for temp_sgdu_1 in child_sgud_1:
																						if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																							found_in_sgdu_1 = True
																							break
																					for temp_sgdu_2 in child_sgud_2:
																						if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																							found_in_sgdu_2 = True
																							break
																					if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																						found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																						valid_mid_point_feat = True
																						break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																					else:
																						found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																				else:
																					found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																			else:
																				if (distance_btw_two_gdus == 0.00):
																					#have to double check whether the point feature fall within both superGDU or just one superGDU
																					approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
																					found_in_sgdu_1 = False
																					found_in_sgdu_2 = False
																					for temp_sgdu_1 in child_sgud_1:
																						if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																							found_in_sgdu_1 = True
																							break
																					for temp_sgdu_2 in child_sgud_2:
																						if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																							found_in_sgdu_2 = True
																							break
																					if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																						found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																						valid_mid_point_feat = True
																						break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																					#else:#maybe I don't need this
																					#	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																				else:
																					prev_approx_distance_btw_line_kmns = found_pair_of_line_feats[4]
																					if (prev_approx_distance_btw_line_kmns > approx_distance_btw_lines_kms or valid_mid_point_feat == False):
																						if (gdu_line_ft_1.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts and gdu_line_ft_2.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																							found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																							# list_of_already_used_line_fts.append(gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
																							# list_of_already_used_line_fts.append(gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
															if (valid_mid_point_feat == True):
																# #debug
																# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
																	# print('before')
																	# print('temp_small_circle_angular_radius_degrees',temp_small_circle_angular_radius_degrees)
																	# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
																break
														if (found_pair_of_line_feats is not None):
															break
													if (found_pair_of_line_feats is not None):
														valid_pair_of_line_fts = True
														gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2 = found_pair_of_line_feats
														temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
														#debug
														# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
															# print('temp_small_circle_angular_radius_degrees',temp_small_circle_angular_radius_degrees)
															# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
															# print('valid_mid_point_feat',valid_mid_point_feat)
														# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
															# print('found expected_pair_divergent_line_features')
															# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),' and ', gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
														#find the mid_point between two points 
														approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
														#valid_mid_point_feat = False --- already initalized
														if (approx_mid_point == closest_point_on_gdu1 or approx_mid_point == closest_point_on_gdu2):
															temp_list_of_closest_point_on_gdu1 = dict_of_gdu_and_centroid[gdu_line_ft_1.get_shapefile_attribute('polygid')]
															closest_point_on_gdu1 = temp_list_of_closest_point_on_gdu1[0][0]
															temp_list_of_closest_point_on_gdu2 = dict_of_gdu_and_centroid[gdu_line_ft_2.get_shapefile_attribute('polygid')]
															closest_point_on_gdu2 = temp_list_of_closest_point_on_gdu2[0][0]
															if (valid_mid_point_feat == False):
																valid_mid_point_feat = True
														if (valid_mid_point_feat == False):
															if (pygplates.GeometryOnSphere.distance(line_gdu_1,line_gdu_2) == 0.00):
																valid_mid_point_feat = True
															# else:
																# #NEW - check whether two sgdus and their line features cross each other --- NO NEED TO DO THIS ANYMORE because we have done the check when we tried to fine the pair of line features
																# for reconstructed_sgdu_1 in child_sgud_1:
																	# if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_1,line_gdu_2) == 0.00):
																		# valid_mid_point_feat = True
																		# break
																# if (valid_mid_point_feat == True):
																	# temp_valid_mid_point_feat = False
																	# for reconstructed_sgdu_2 in child_sgud_2:
																		# if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_2,line_gdu_1) == 0.00):
																			# temp_valid_mid_point_feat = True
																			# break
																	# if (temp_valid_mid_point_feat == False):
																		# valid_mid_point_feat = False
																	# else:
																		# #check to make sure the two supergdus are crossing each other
																		# if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_1,reconstructed_sgdu_2) == 0.00):
																			# valid_mid_point_feat = True
																		# else:
																			# valid_mid_point_feat = False
																# # if (valid_mid_point_feat == False):
																	# # for reconstructed_sgdu_2 in child_sgud_2:
																		# # if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_2,line_gdu_1) == 0.00):
																			# # valid_mid_point_feat = True
																			# # break
														# #NEW - check whether approx_mid_point positioned within any SGDUs
														# if (valid_mid_point_feat == False):
															# are_lines_similar = are_two_PolylineOnSphere_similar(line_gdu_1,line_gdu_2)
															# if (are_lines_similar == True):
																# valid_mid_point_feat = True
															# elif (valid_mid_point_feat == False):
																# #temporarily set valid_mid_point_feat to True
																# valid_mid_point_feat = True
																# for random_sgdu in non_related:
																	# if (random_sgdu.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
																		# valid_mid_point_feat = False
																		# break
																# if (valid_mid_point_feat == True):
																	# for reconstructed_sgdu_2 in child_sgud_2:
																		# if (reconstructed_sgdu_2.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
																			# valid_mid_point_feat = False
																			# break
																# if (valid_mid_point_feat == True):
																	# for reconstructed_sgdu_1 in child_sgud_1:
																		# if (reconstructed_sgdu_1.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
																			# valid_mid_point_feat = False
																			# break
														
														if (valid_mid_point_feat == True):
															#create an arc
															list_of_rift_points.append(approx_mid_point)
															temporary_GreatCircleArc = pygplates.GreatCircleArc(approx_mid_point,E_pole)
															normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
															left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, approx_mid_point, closest_point_on_gdu1, closest_point_on_gdu2, gdu_line_ft_1.get_reconstruction_plate_id(), gdu_line_ft_2.get_reconstruction_plate_id())
															#create point feature
															#name = 'R'+str(child_1)+'_'+str(child_2)+'_'+str(smallest_circle_angular_radius_degrees)
															name = 'R'+key+'_'+str(smallest_circle_angular_radius_degrees)
															rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, approx_mid_point, name = name, valid_time = (reconstruction_time,0.00))
															if ((left_gduid == right_gduid)or (left_gduid is None) or (right_gduid is None)):
																rift_point_ft.set_left_plate(gdu_line_ft_1.get_reconstruction_plate_id())
																rift_point_ft.set_right_plate(gdu_line_ft_2.get_reconstruction_plate_id())
															else:
																rift_point_ft.set_left_plate(left_gduid)
																rift_point_ft.set_right_plate(right_gduid)
															rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
															rift_point_ft.set_description(str(smallest_circle_angular_radius_degrees))
															if (reference is None):
																pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
															else:
																pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
															output_rift_point_features.add(rift_point_ft)
															if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
																unsure_topology_for_MOR_fts.add(rift_point_ft)
															if ((left_gduid == gdu_line_ft_1.get_reconstruction_plate_id() and right_gduid == gdu_line_ft_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
																list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2))
															else:
																list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
															#create pair of line features associated with the rift point ft
															_,con_ocn_to_time = gdu_line_ft_1.get_valid_time()
															line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_1,name=gdu_line_ft_1.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
															line_feature_1.set_reconstruction_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
															line_feature_1.set_conjugate_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
															line_feature_1.set_description('divergent_margin')
															
															_,con_ocn_to_time = gdu_line_ft_2.get_valid_time()
															line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_2,name=gdu_line_ft_2.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
															line_feature_2.set_reconstruction_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
															line_feature_2.set_conjugate_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
															line_feature_2.set_description('divergent_margin')
															if (reference is None):
																pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time)
															else:
																pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time,reference)
															#output_diverging_line_features.add(line_feature_1)
															#output_diverging_line_features.add(line_feature_2)
															previous_diverging_line_feats.append((line_feature_1,line_feature_2,'D',reconstruction_time,pygplates.GeometryOnSphere.distance(line_gdu_1.get_centroid(),line_gdu_2.get_centroid())))
												#smallest_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees - 1.00
												smallest_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees - 0.50
											#create temporary MOR features from list_of_rift_points
											if (len(list_of_rift_points) > 0):
												list_of_distinct_rift_points = []
												for temporary_rift_pt in list_of_rift_points:
													if (len(list_of_distinct_rift_points) == 0):
														list_of_distinct_rift_points.append(temporary_rift_pt)
													else:
														last_rift_pt = list_of_distinct_rift_points[-1]
														if (last_rift_pt != temporary_rift_pt):
															list_of_distinct_rift_points.append(temporary_rift_pt)
												if (len(list_of_distinct_rift_points) >= 2):
													temporary_MOR_line = pygplates.PolylineOnSphere(list_of_rift_points)
													temporary_MOR_line_feat = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_mid_ocean_ridge,temporary_MOR_line,name='R'+key,valid_time = (reconstruction_time,0.00))
													mid_point_of_temporary_MOR_line_feat = temporary_MOR_line.get_centroid()
													#create an arc
													temporary_GreatCircleArc = pygplates.GreatCircleArc(mid_point_of_temporary_MOR_line_feat,E_pole)
													normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
													#rep_point_of_sgdu_1 = child_sgud_1[0].get_interior_centroid() 
													#rep_point_of_sgdu_2 = child_sgud_2[0].get_interior_centroid()
													#MOR_left_gduid, MOR_right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, mid_point_of_temporary_MOR_line_feat, rep_point_of_sgdu_1, rep_point_of_sgdu_2, child_repgduid_1, child_repgduid_2)
													#temporarily set left and right 
													MOR_left_gduid, MOR_right_gduid = child_repgduid_1,child_repgduid_2
													temporary_MOR_line_feat.set_left_plate(MOR_left_gduid)
													temporary_MOR_line_feat.set_right_plate(MOR_right_gduid)
													temporary_MOR_line_feat.set_reconstruction_method('HalfStageRotationVersion2')
													if (reference is None):
														pygplates.reverse_reconstruct(temporary_MOR_line_feat,rotation_model,reconstruction_time)
													else:
														pygplates.reverse_reconstruct(temporary_MOR_line_feat,rotation_model,reconstruction_time,reference)
													output_temporary_MOR_line_feats.append(temporary_MOR_line_feat)
		#check the end_time of diverging line features
		#list_of_already_evaluated_pairs = []
		#debug
		#print('number of features in previous_diverging_line_feats before update',len(previous_diverging_line_feats))
		if (len(previous_diverging_line_feats) > 0):
			#;from_time;to_time;SGDUID;GDUID;buffer_distance_km;repGDUID
			temporary_sgdu_and_member_csv_at_time = common_filename_for_temporary_sgdu_and_members_csv.format(time = str(reconstruction_time))
			temp_sgdu_and_gdu_df = pd.read_csv(temporary_sgdu_and_member_csv_at_time, delimiter = ';', header = 0)
			remaining_diverging_line_feats = []
			recorded_distance = -1.00
			if (len(dic_prev_div_line_feats) == 0):
				for line_feature_1,line_feature_2,_,prev_begin_age,prev_distance in previous_diverging_line_feats:
					pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
					rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
					if (pair_polylids not in dic_prev_div_line_feats and rev_pair_of_polylids not in dic_prev_div_line_feats):
						dic_prev_div_line_feats[pair_polylids] = {'line_feats':(line_feature_1,line_feature_2),'prev_motion':'D', 'age':prev_begin_age, 'dist':prev_distance}
			else:
				for line_feature_1,line_feature_2,prev_motion,prev_begin_age,prev_distance in previous_diverging_line_feats:
					pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
					rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
					if (pair_polylids in dic_prev_div_line_feats):
						dic_prev_div_line_feats[pair_polylids]['prev_motion'] = prev_motion
						dic_prev_div_line_feats[pair_polylids]['age'] = prev_begin_age
						current_line_feature_1,current_line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
						if (current_line_feature_1.is_valid_at_time(reconstruction_time) == False or current_line_feature_2.is_valid_at_time(reconstruction_time) == False):
							output_diverging_line_features.add(current_line_feature_1)
							output_diverging_line_features.add(current_line_feature_2)
							output_begin_age,output_end_age = current_line_feature_1.get_valid_time()
							pairs_of_kin_line_fts.append((output_begin_age,output_end_age,current_line_feature_1.get_description(),current_line_feature_1.get_name(),current_line_feature_2.get_name(),current_line_feature_1.get_feature_id().get_string(),current_line_feature_2.get_feature_id().get_string()))
						if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
							dic_prev_div_line_feats[pair_polylids]['line_feats'] = (line_feature_1,line_feature_2)
						else:
							del dic_prev_div_line_feats[pair_polylids]
					elif (rev_pair_of_polylids in dic_prev_div_line_feats):
						dic_prev_div_line_feats[rev_pair_of_polylids]['prev_motion'] = prev_motion
						dic_prev_div_line_feats[rev_pair_of_polylids]['age'] = prev_begin_age
						current_line_feature_1,current_line_feature_2 = dic_prev_div_line_feats[rev_pair_of_polylids]['line_feats']
						if (current_line_feature_1.is_valid_at_time(reconstruction_time) == False or current_line_feature_2.is_valid_at_time(reconstruction_time) == False):
							output_diverging_line_features.add(current_line_feature_1)
							output_diverging_line_features.add(current_line_feature_2)
							output_begin_age,output_end_age = current_line_feature_1.get_valid_time()
							pairs_of_kin_line_fts.append((output_begin_age,output_end_age,current_line_feature_1.get_description(),current_line_feature_1.get_name(),current_line_feature_2.get_name(),current_line_feature_1.get_feature_id().get_string(),current_line_feature_2.get_feature_id().get_string()))
						if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
							dic_prev_div_line_feats[rev_pair_of_polylids]['line_feats'] = (line_feature_1,line_feature_2)
						else:
							del dic_prev_div_line_feats[rev_pair_of_polylids]
					else:
						if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
							dic_prev_div_line_feats[pair_polylids] = {'line_feats':(line_feature_1,line_feature_2),'prev_motion':prev_motion, 'age':prev_begin_age, 'dist':prev_distance}
			list_of_pair_polyids_to_be_deleted = []
			for pair_polylids in dic_prev_div_line_feats:
				#pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
				#rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
				
				print('pair_polylids',pair_polylids)
				line_feature_1,line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
				prev_tectonic_motion = dic_prev_div_line_feats[pair_polylids]['prev_motion']
				prev_distance = dic_prev_div_line_feats[pair_polylids]['dist']
				prev_begin_age = dic_prev_div_line_feats[pair_polylids]['age']
				#debug
				# if (pair_polylids == '17300_13241_9277+12009_13906_7560' or pair_polylids == '12009_13906_7560+17300_13241_9277'):
					# print('line_feature_1.get_description()',line_feature_1.get_description())
					# print('line_feature_2.get_description()',line_feature_2.get_description())
					# print('prev_begin_age',prev_begin_age)
					# print('prev_motion',prev_tectonic_motion)
					
				
				SGDUID_for_line_ft_1 = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == line_feature_1.get_reconstruction_plate_id(),'SGDUID'].unique()
				SGDUID_for_line_ft_2 = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == line_feature_2.get_reconstruction_plate_id(),'SGDUID'].unique()
				# if (pair_polylids in list_of_already_evaluated_pairs or rev_pair_of_polylids in list_of_already_evaluated_pairs):
					# continue #these two line features have already been evaluated at this reconstruction time thus take the new tuple
				# else:
					# list_of_already_evaluated_pairs.append(pair_polylids)
				
				#NO NEED TO find the original line features
				# original_con_ocn_line_ft_1 = None
				# original_con_ocn_line_ft_2 = None
				# for con_ocn_line_ft in valid_con_ocn_line_features:
					# if (line_feature_1.get_name() == con_ocn_line_ft.get_shapefile_attribute('POLYLID')):
						# original_con_ocn_line_ft_1 = con_ocn_line_ft
					# elif (line_feature_2.get_name() == con_ocn_line_ft.get_shapefile_attribute('POLYLID')):
						# original_con_ocn_line_ft_2 = con_ocn_line_ft
					# if (original_con_ocn_line_ft_1 is not None and original_con_ocn_line_ft_2 is not None):
						# break
				
				if (recorded_distance == -1.00):
					recorded_distance = prev_distance
				if ((prev_begin_age - reconstruction_time) > time_interval and line_feature_1.is_valid_at_time(reconstruction_time) and line_feature_2.is_valid_at_time(reconstruction_time)):
					reconstructed_current_div_line_features = []
					if (reference is not None):
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_current_div_line_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
					else:
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_current_div_line_features, reconstruction_time, group_with_feature = True)
					final_current_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_current_div_line_features, pygplates.PolylineOnSphere)
					current_reconstr_ft_1, current_reconstr_line_1 = final_current_reconstructed_line_features[0]
					current_reconstr_ft_2, current_reconstr_line_2 = final_current_reconstructed_line_features[1]
					#current_distance = pygplates.GeometryOnSphere.distance(current_reconstr_line_1.get_centroid(),current_reconstr_line_2.get_centroid())
					#recorded_distance = current_distance
					
					reconstructed_prev_div_line_features = []
					if (reference is not None):
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_prev_div_line_features, reconstruction_time + time_interval, anchor_plate_id = reference, group_with_feature = True)
					else:
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_prev_div_line_features, reconstruction_time + time_interval, group_with_feature = True)
					final_prev_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_prev_div_line_features,pygplates.PolylineOnSphere)
					prev_reconstr_ft_1,prev_reconstr_line_1 = final_prev_reconstructed_line_features[0]
					prev_reconstr_ft_2,prev_reconstr_line_2 = final_prev_reconstructed_line_features[1]
					
					reconstructed_point_A_at_from_time = prev_reconstr_line_1.get_centroid()
					reconstructed_point_B_at_from_time = prev_reconstr_line_2.get_centroid()
					reconstructed_point_A_at_to_time = current_reconstr_line_1.get_centroid()
					reconstructed_point_B_at_to_time = current_reconstr_line_2.get_centroid()
					#result_of_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_pos_and_angular_vel_vec(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time, reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time, reconstruction_time, reconstruction_time-time_interval)
					result_of_tectonic_motion,dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_pos_and_angular_vel_vec(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time, reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time, reconstruction_time+time_interval, reconstruction_time)
					list_dot_prod.append((reconstruction_time,line_feature_1.get_reconstruction_plate_id(),line_feature_2.get_reconstruction_plate_id(),dot_prod_btw_tectonic_motion))
					#debug
					# print('reconstruction_time',reconstruction_time)
					# print('result_of_tectonic_motion',result_of_tectonic_motion)
					
					
					latA,lonA = reconstructed_point_A_at_from_time.to_lat_lon()
					latB,lonB = reconstructed_point_B_at_from_time.to_lat_lon()
					at_prev_time_distance_in_km_btw_A_and_B = calculate_distance_km_between_two_points_from_haversine_formula(latA,lonA,latB,lonB)
					cur_latA,cur_lonA = reconstructed_point_A_at_to_time.to_lat_lon()
					cur_latB,cur_lonB = reconstructed_point_B_at_to_time.to_lat_lon()
					at_current_time_distance_in_km_btw_A_and_B = calculate_distance_km_between_two_points_from_haversine_formula(cur_latA,cur_lonA,cur_latB,cur_lonB)
					current_distance = at_current_time_distance_in_km_btw_A_and_B
					recorded_distance = current_distance
					
					is_valid_pair_of_line_fts = True
					# for reconstructed_gdu_ft, reconstructed_gdu in final_reconstructed_gdu_features:
						# polygid_of_original_con_ocn_line_ft_1 = original_con_ocn_line_ft_1.get_shapefile_attribute('polygid')
						# polygid_of_original_con_ocn_line_ft_2 = original_con_ocn_line_ft_2.get_shapefile_attribute('polygid')
						# polygid_of_gdu_ft = reconstructed_gdu_ft.get_shapefile_attribute('POLYGID')
						# if (polygid_of_original_con_ocn_line_ft_1 == polygid_of_gdu_ft or polygid_of_original_con_ocn_line_ft_2 == polygid_of_gdu_ft):
							# continue
						# SGDUID_for_gdu_ft = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == reconstructed_gdu_ft.get_reconstruction_plate_id(),'SGDUID'].unique()
						# #find the same value between SGDUID_for_gdu_ft and SGDUID_for_line_ft_1; SGDUID_for_gdu_ft and SGDUID_for_line_ft_2
						# intersection_w_line_ft_1 = np.intersect1d(SGDUID_for_gdu_ft, SGDUID_for_line_ft_1)
						# intersection_w_line_ft_2 = np.intersect1d(SGDUID_for_gdu_ft, SGDUID_for_line_ft_2)
						# if ((intersection_w_line_ft_1 is None or len(intersection_w_line_ft_1) == 0) and (intersection_w_line_ft_2 is None or len(intersection_w_line_ft_2) == 0)):
							# centroid_of_gdu = reconstructed_gdu.get_interior_centroid()
							# result_of_valid_test = is_point_in_between_point_A_and_B_using_greatcirclearc(centroid_of_gdu,reconstructed_point_B_at_to_time,reconstructed_point_A_at_to_time)
							# if (result_of_valid_test is not None):
								# if (result_of_valid_test == True):
									# is_valid_pair_of_line_fts = False
							# if (is_valid_pair_of_line_fts == False):
								# break
							
					#polygid_of_original_con_ocn_line_ft_1 = original_con_ocn_line_ft_1.get_shapefile_attribute('polygid')
					#polygid_of_original_con_ocn_line_ft_2 = original_con_ocn_line_ft_2.get_shapefile_attribute('polygid')
					total_stage_rel_rot_of_1_to_2 = find_stage_relative_reconstruction_rotation_(rotation_model,line_feature_1.get_reconstruction_plate_id(),line_feature_2.get_reconstruction_plate_id(),float(reconstruction_time+time_interval),reconstruction_time,reference)
					total_stage_rel_rot_of_2_to_1 = find_stage_relative_reconstruction_rotation_(rotation_model,line_feature_2.get_reconstruction_plate_id(),line_feature_1.get_reconstruction_plate_id(),float(reconstruction_time+time_interval),reconstruction_time,reference)
					if (total_stage_rel_rot_of_1_to_2 is not None):
						if (total_stage_rel_rot_of_1_to_2.represents_identity_rotation() == True):
							is_valid_pair_of_line_fts = False
						else:
							if (total_stage_rel_rot_of_2_to_1 is not None):
								if (total_stage_rel_rot_of_2_to_1.represents_identity_rotation() == True):
									is_valid_pair_of_line_fts = False
							else:
								is_valid_pair_of_line_fts = False
					else:
						is_valid_pair_of_line_fts = False
					if (is_valid_pair_of_line_fts == True):
						final_SGDUID_for_line_1 = None
						final_SGDUID_for_line_2 = None
						for reconstructed_sgdu_ft_at_reconstruction_time, reconstructed_sgdu_at_reconstruction_time in final_reconstructed_sgdu_features:
							SGDUID_of_reconstructed_sgdu_ft = int(reconstructed_sgdu_ft_at_reconstruction_time.get_name())
							SGDUID_for_rand_sgdu_ft = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == reconstructed_sgdu_ft_at_reconstruction_time.get_reconstruction_plate_id(),'SGDUID'].unique()
							# #find the same value between SGDUID_for_gdu_ft and SGDUID_for_line_ft_1; SGDUID_for_gdu_ft and SGDUID_for_line_ft_2
							intersection_w_line_ft_1 = np.intersect1d(SGDUID_for_rand_sgdu_ft, SGDUID_for_line_ft_1)
							intersection_w_line_ft_2 = np.intersect1d(SGDUID_for_rand_sgdu_ft, SGDUID_for_line_ft_2)
							#if ((SGDUID_of_reconstructed_sgdu_ft not in SGDUID_for_line_ft_1) and (SGDUID_of_reconstructed_sgdu_ft not in SGDUID_for_line_ft_2)):
							#if ((SGDUID_of_reconstructed_sgdu_ft not in intersection_w_line_ft_1) and (SGDUID_of_reconstructed_sgdu_ft not in intersection_w_line_ft_2)):
							if (len(intersection_w_line_ft_1) == 0 and len(intersection_w_line_ft_2) == 0):
								temporary_line_connecting_A_and_B = pygplates.PolylineOnSphere([reconstructed_point_A_at_to_time,reconstructed_point_B_at_to_time])
								if (reconstructed_sgdu_at_reconstruction_time.partition(temporary_line_connecting_A_and_B) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
									is_valid_pair_of_line_fts = False
									break
							else:
								if (len(intersection_w_line_ft_1) > 0):
									final_SGDUID_for_line_1 = reconstructed_sgdu_ft_at_reconstruction_time
								if (len(intersection_w_line_ft_2) > 0):
									final_SGDUID_for_line_2 = reconstructed_sgdu_ft_at_reconstruction_time
						
						if (final_SGDUID_for_line_1 is None or final_SGDUID_for_line_2 is None):
							is_valid_pair_of_line_fts = False
						else:
							if (final_SGDUID_for_line_1.get_name() == final_SGDUID_for_line_2.get_name()):
								is_valid_pair_of_line_fts = False
								
					#debug
					# if (pair_polylids == '17300_13241_9277+12009_13906_7560' or pair_polylids == '12009_13906_7560+17300_13241_9277'):
						# print('line_feature_1.get_description()',line_feature_1.get_description())
						# print('line_feature_2.get_description()',line_feature_2.get_description())
						# print('is_valid_pair_of_line_fts',is_valid_pair_of_line_fts)
						# print('prev_begin_age',prev_begin_age)
						# print('prev_motion',prev_motion)
						# print('result_of_tectonic_motion',result_of_tectonic_motion)
					
					
					has_modified_line_feats = False 
					if (((prev_begin_age - reconstruction_time) >= 3.00*(time_interval)) and prev_tectonic_motion != 'D'and result_of_tectonic_motion != 'D' and is_valid_pair_of_line_fts == True):
						#debug
						#print('Enter this')
						#need to check the type of kinematic boundary in previous time
						if (line_feature_1.get_description() == 'plate_boundary_zone' and line_feature_2.get_description() == 'plate_boundary_zone'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							if (result_of_tectonic_motion == 'C'):
								line_feature_1.set_description('convergent_margin')
								line_feature_2.set_description('convergent_margin')
								has_modified_line_feats = True
							elif (result_of_tectonic_motion == 'T'):
								line_feature_1.set_description('transform_fault')
								line_feature_2.set_description('transform_fault')
								has_modified_line_feats = True
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
						elif (line_feature_1.get_description() != 'convergent_margin' and line_feature_2.get_description() != 'convergent_margin'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							if (result_of_tectonic_motion == 'C' and line_feature_1.get_description() == 'divergent_margin'):
								line_feature_1.set_description('plate_boundary_zone')
								line_feature_2.set_description('plate_boundary_zone')
								has_modified_line_feats = True
							else:
								line_feature_1.set_description('transform_fault')
								line_feature_2.set_description('transform_fault')
								has_modified_line_feats = True
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
						elif (line_feature_1.get_description() == 'convergent_margin' and line_feature_2.get_description() == 'convergent_margin'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							if (result_of_tectonic_motion == 'T'):
								line_feature_1.set_description('transform_fault')
								line_feature_2.set_description('transform_fault')
								has_modified_line_feats = True
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
					elif (result_of_tectonic_motion == 'D' and prev_tectonic_motion == 'D' and (prev_distance == 0.00 or at_prev_time_distance_in_km_btw_A_and_B <= 50.00 or is_valid_pair_of_line_fts == True)):
						if (((prev_begin_age - reconstruction_time) >= 3.00*(time_interval)) and line_feature_1.get_description() == 'convergent_margin' and line_feature_2.get_description() == 'convergent_margin'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
							line_feature_1.set_description('plate_boundary_zone')
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							line_feature_2.set_description('plate_boundary_zone')
							has_modified_line_feats = True
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
						elif (line_feature_1.get_description() != 'divergent_margin' and line_feature_1.get_description() != 'convergent_margin' and line_feature_2.get_description() != 'divergent_margin' and line_feature_2.get_description() != 'convergent_margin'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
							line_feature_1.set_description('divergent_margin')
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							line_feature_2.set_description('divergent_margin')
							has_modified_line_feats = True
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
							#quickly find mid-point feature
							total_relative_reconstruction_rotation = find_total_relative_reconstruction_rotation_(rotation_model, line_feature_1.get_reconstruction_plate_id(), line_feature_2.get_reconstruction_plate_id(), reconstruction_time, reference)
							if (total_relative_reconstruction_rotation is not None):
								if (total_relative_reconstruction_rotation.represents_identity_rotation() == False):
									#find mid point
									E_pole,_ = total_relative_reconstruction_rotation.get_euler_pole_and_angle()
									quick_mid_pt,mid_pt_order = quickly_derive_mid_point_and_order_of_mid_point_from_two_divergent_points(reconstructed_point_A_at_to_time,reconstructed_point_B_at_to_time,E_pole)
									mid_pt_order = round(mid_pt_order,2)
									#create rift point ft
									# #create an arc
									temporary_GreatCircleArc = pygplates.GreatCircleArc(quick_mid_pt,E_pole)
									normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
									left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, quick_mid_pt, reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time, line_feature_1.get_reconstruction_plate_id(), line_feature_2.get_reconstruction_plate_id())
									#create point feature
									name = 'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name()+'_'+str(mid_pt_order)
									rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, quick_mid_pt, name = name, valid_time = (reconstruction_time,0.00))
									if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
										rift_point_ft.set_left_plate(line_feature_1.get_reconstruction_plate_id())
										rift_point_ft.set_right_plate(line_feature_2.get_reconstruction_plate_id())
									else:
										rift_point_ft.set_left_plate(left_gduid)
										rift_point_ft.set_right_plate(right_gduid)
									rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
									rift_point_ft.set_description(str(mid_pt_order))
									if (reference is None):
										pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
									else:
										pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
									output_rift_point_features.add(rift_point_ft)
									if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
										unsure_topology_for_MOR_fts.add(rift_point_ft)
									if ((left_gduid == line_feature_1.get_reconstruction_plate_id() and right_gduid == line_feature_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
										list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name(),mid_pt_order, line_feature_1.get_name(), line_feature_1.get_reconstruction_plate_id(), final_SGDUID_for_line_1.get_reconstruction_plate_id(), line_feature_2.get_name(), line_feature_2.get_reconstruction_plate_id(), final_SGDUID_for_line_2.get_reconstruction_plate_id()))
									else:
										list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name(),mid_pt_order, line_feature_2.get_name(), line_feature_2.get_reconstruction_plate_id(), final_SGDUID_for_line_2.get_reconstruction_plate_id(), line_feature_1.get_name(), line_feature_1.get_reconstruction_plate_id(), final_SGDUID_for_line_1.get_reconstruction_plate_id()))
							
					if ((prev_distance == 0.00 or at_prev_time_distance_in_km_btw_A_and_B <= 50.00 or is_valid_pair_of_line_fts == True)):
						# print('prev_distance',prev_distance)
						# print('recorded_distance',recorded_distance)
						#remaining_diverging_line_feats.append((line_feature_1,line_feature_2,prev_begin_age,recorded_distance))
						if (has_modified_line_feats == True):
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
						else:
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
					elif (is_valid_pair_of_line_fts == False):
						if (line_feature_1.get_description() != 'plate_boundary_zone' and line_feature_2.get_description() != 'plate_boundary_zone'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							if (line_feature_1_begin_time > reconstruction_time):
								cloned_line_ft_1 = line_feature_1.clone()
								cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
								cloned_line_ft_2 = line_feature_2.clone()
								cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
								pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
								output_diverging_line_features.add(cloned_line_ft_1)
								output_diverging_line_features.add(cloned_line_ft_2)
							if (pygplates.GeometryOnSphere.distance(current_reconstr_line_1.get_centroid(),current_reconstr_line_2.get_centroid()) == 0.00):
								if (line_feature_1.get_description() == 'convergent_margin' and line_feature_2.get_description() == 'convergent_margin'):
									output_collision.append((reconstruction_time,line_feature_1.get_name(),line_feature_2.get_name()))
							line_feature_1.set_description('plate_boundary_zone')
							line_feature_2.set_description('plate_boundary_zone')
							has_modified_line_feats = True
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
						
						# if (current_distance > 0.00 and at_current_time_distance_in_km_btw_A_and_B >= 50.00):
							# if (has_modified_line_feats == True):
								# remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
							# else:
								# remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
						
						if (has_modified_line_feats == True):
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
						else:
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
						
				elif (prev_begin_age > reconstruction_time and (line_feature_1.is_valid_at_time(reconstruction_time) == False or line_feature_2.is_valid_at_time(reconstruction_time) == False)):
					line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
					line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
					cloned_line_ft_1 = line_feature_1.clone()
					cloned_line_ft_1.set_valid_time(prev_begin_age,reconstruction_time+0.100)
					cloned_line_ft_2 = line_feature_2.clone()
					cloned_line_ft_2.set_valid_time(prev_begin_age,reconstruction_time+0.100)
					output_diverging_line_features.add(cloned_line_ft_1)
					output_diverging_line_features.add(cloned_line_ft_2)
					pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
					list_of_pair_polyids_to_be_deleted.append(pair_polylids)
				elif (prev_begin_age == reconstruction_time):
					remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
			for pair_polylids in list_of_pair_polyids_to_be_deleted:
				del dic_prev_div_line_feats[pair_polylids]
			previous_diverging_line_feats = remaining_diverging_line_feats
		
		#debug
		# print('number of features in previous_diverging_line_feats',len(previous_diverging_line_feats))
		# print('number of features in output_diverging_line_features', len(output_diverging_line_features))
		# temporary_output_pair_div_line_fts.write('expected_pair_divergent_line_features_but_failed_at_'+str(reconstruction_time)+'_'+modelname+'_'+yearmonthday+'.shp')
		#temporary_output_pair_div_line_fts = None
		
		#write out the results of all possibile tectonic motion for every pair of SuperGDUs that possibly diverge from each other according to SuperGDU history records
		output_dataframe = pd.DataFrame.from_records(results_of_all_possible_tectonic_motion, columns = ['reconstruction_time','SGDU1','SGDU2','tectonic_motion'])
		filename = 'possible_tectonic_motion_from_div_bdn_process_at_'+str(reconstruction_time)+'_for_'+modelname+'_'+yearmonthday+'.csv'
		output_dataframe.to_csv(filename,index=False)
		output_dataframe = None
		
		output_dot_prod_tectonic_motion_df = pd.DataFrame.from_records(list_dot_prod, columns = ['reconstruction_time','child_repgduid_1','child_repgduid_2','dot_prod'])
		filename = 'dot_prod_tectonic_motion_for_'+modelname+'_'+yearmonthday+'.csv'
		if (os.path.isfile(filename)):
			output_dot_prod_tectonic_motion_df = pd.read_csv(filename)
			output_dot_prod_tectonic_motion_df = pd.concat([pd.DataFrame([[list_dot_prod]]), output_dot_prod_tectonic_motion_df], ignore_index=True)
			output_dot_prod_tectonic_motion_df.to_csv(filename)
		else:
			output_dot_prod_tectonic_motion_df = pd.DataFrame([[list_dot_prod]])
			output_dot_prod_tectonic_motion_df.to_csv(filename)
		
		#update reconstruction_time for the main while-loop
		reconstruction_time = reconstruction_time - time_interval
	output_rift_point_features.write('rift_point_features_for_'+modelname+'_'+yearmonthday+'.shp')
	unsure_topology_for_MOR_fts.write('unsure_topology_for_MOR_fts_'+modelname+'_'+yearmonthday+'.shp')
	temporary_MOR_featurecollection = pygplates.FeatureCollection(output_temporary_MOR_line_feats)
	temporary_MOR_featurecollection.write('temporary_MOR_line_feat_for_'+modelname+'_'+yearmonthday+'.shp')
	if (len(dic_prev_div_line_feats) > 0):
		for pair_polylids in dic_prev_div_line_feats:
			line_feature_1,line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
			prev_tectonic_motion = dic_prev_div_line_feats[pair_polylids]['prev_motion']
			prev_distance = dic_prev_div_line_feats[pair_polylids]['dist']
			prev_begin_age = dic_prev_div_line_feats[pair_polylids]['age']
			output_diverging_line_features.add(line_feature_1)
			output_diverging_line_features.add(line_feature_2)
			line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
			pairs_of_kin_line_fts.append((line_feature_1_begin_time,line_feature_1_end_time,line_feature_1.get_description(),line_feature_1.get_name(),line_feature_2.get_name(),line_feature_1.get_feature_id().get_string(),line_feature_2.get_feature_id().get_string()))
	output_diverging_line_features.write('diverging_line_features_for_'+str(begin_reconstruction_time)+'_'+str(end_reconstruction_time)+'_'+modelname+'_'+yearmonthday+'.shp')
	
	#list_of_ordered_pairs_gdu_fts.append((start_div,name,smallest_circle_angular_radius_degrees, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
	output_dataframe = pd.DataFrame.from_records(list_of_ordered_pairs_gdu_fts, columns = ['start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'])
	filename = 'rift_point_features_records_for_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	
	output_dataframe = pd.DataFrame.from_records(output_collision, columns = ['reconstruction_time','polylid1','polylid2'])
	filename = 'collisions_zone_for_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	
	#line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()
	output_dataframe = pd.DataFrame.from_records(pairs_of_kin_line_fts, columns = ['from_time','to_time','type_kin','polylid1','polylid2','fid1','fid2'])
	filename = 'pairs_of_kin_line_fts_from_div_bdn_process_for_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	


def find_additional_rift_point_features_from_initial_rift_point_features(threshold_diff_small_circle,rift_point_features_records_csv, line_features_collection, sgdu_features, gdu_features, common_filename_for_temporary_sgdu_and_members_csv, time_interval, max_reconstruction_time_for_start_div, min_reconstruction_time_for_start_div, rotation_model, reference, modelname, yearmonthday):
	list_dot_prod = []
	pairs_of_kin_line_fts = []
	list_of_ordered_pairs_gdu_fts = []
	previous_diverging_line_feats = []
	output_diverging_line_features = pygplates.FeatureCollection()
	unsure_topology_for_MOR_fts = pygplates.FeatureCollection()
	output_rift_point_features = pygplates.FeatureCollection()
	dic_of_new_kin_fts = {}
	dic_of_supergdu_and_gdu_members = {}
	dic_prev_div_line_feats = {}
	reconstructed_sgdu_features = []
	reconstructed_gdu_features = []
	reconstructed_div_features = []
	reconstructed_line_features = []
	reconstructed_rift_point_features = []
	reconstructed_gdu_fts_for_sgdu2 = []
	reconstructed_gdu_fts_for_sgdu1 = []
	already_examined_record = []
	#list_of_unwanted_rift_point_features = []
	#start_div,rift_name,order,lpolylid,left_gdu,lrepgduid,rpolylid,right_gdu,rrepgduid
	rift_history_df = pd.read_csv(rift_point_features_records_csv, delimiter=',', header = 0)
	selected_rift_history_df = None
	if (max_reconstruction_time_for_start_div is not None):
		selected_rift_history_df = rift_history_df.loc[rift_history_df['start_div'] <= max_reconstruction_time_for_start_div]
	if (min_reconstruction_time_for_start_div is not None):
		new_selected_rift_history_df = None
		if (selected_rift_history_df is not None):
			new_selected_rift_history_df = selected_rift_history_df.loc[selected_rift_history_df['start_div'] > min_reconstruction_time_for_start_div]
		else:
			new_selected_rift_history_df = rift_history_df.loc[rift_history_df['start_div'] > min_reconstruction_time_for_start_div]
		if (new_selected_rift_history_df is not None):
			selected_rift_history_df = new_selected_rift_history_df
	if (selected_rift_history_df is not None):
		rift_history_df = selected_rift_history_df
	series_of_unique_rift_name = rift_history_df['rift_name'].unique()
	for rift_name in series_of_unique_rift_name:
		# div_line_names_for_left_of_MOR = rift_history_df.loc[rift_history_df['rift_name'] == rift_name,'lpolylid'].unique()
		# div_line_names_for_right_of_MOR = rift_history_df.loc[rift_history_df['rift_name'] == rift_name,'rpolylid'].unique()
		# array_of_order_for_rift_points = rift_history_df.loc[rift_history_df['rift_name'] == rift_name,'order'].to_numpy()
		records_for_rift_name = rift_history_df.loc[(rift_history_df['rift_name'] == rift_name) & (rift_history_df['lpolylid'].notna()) & (rift_history_df['rpolylid'].notna())]
		sorted_records_for_rift_name = records_for_rift_name.sort_values(by = ['order'], ascending = False)
		unique_records_for_sgdus = records_for_rift_name.drop_duplicates(subset=['lrepgduid','rrepgduid'])
		selected_pairs_of_sgdus = unique_records_for_sgdus[['start_div','lrepgduid','rrepgduid']]
		for start_div, lrepgduid, rrepgduid in selected_pairs_of_sgdus.itertuples(index = False, name = None):
			already_examined_record[:] = []
			reconstructed_sgdu_features[:] = []
			previous_diverging_line_feats[:] = []
			final_start_div = -1.00
			if (final_start_div == -1.00):
				final_start_div = start_div
			reconstruction_time = final_start_div
			valid_sgdu_features = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(final_start_div))]
			# #8ii) Reconstruct sgdu features to reconstruction time
			if (reference is not None):
				pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, final_start_div, anchor_plate_id = reference, group_with_feature = True)
			else:
				pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, final_start_div, group_with_feature = True)
			final_reconstructed_sgdu_features = find_final_reconstructed_geometries(reconstructed_sgdu_features, pygplates.PolygonOnSphere)
			total_relative_reconstruction_rotation = find_total_relative_reconstruction_rotation_(rotation_model, lrepgduid, rrepgduid, float(final_start_div), reference)
			E_pole,_ = total_relative_reconstruction_rotation.get_euler_pole_and_angle()
			splited_str = rift_name.split('_')
			part_1 = splited_str[0]
			splited_str_part_1 = part_1.split('R')
			child_1 = splited_str_part_1[1]
			child_2 = splited_str[1]
			valid_sgdu_features = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(final_start_div))]
			wanted_sgdu_features = []
			non_related = []
			for valid_sgdu_ft in valid_sgdu_features:
				if (valid_sgdu_ft.get_reconstruction_plate_id() == lrepgduid or valid_sgdu_ft.get_reconstruction_plate_id() == rrepgduid):
					wanted_sgdu_features.append(valid_sgdu_ft)
			#Find valid gdu features with con-ocn line features
			valid_con_ocn_line_features = [con_ocn_ft for con_ocn_ft in line_features_collection if con_ocn_ft.is_valid_at_time(final_start_div)]
			polygid_all_valid_line_features = [con_ocn_ft.get_shapefile_attribute('polygid') for con_ocn_ft in valid_con_ocn_line_features]
			array_of_all_valid_polygid = np.array(polygid_all_valid_line_features)
			reconstructed_line_features[:] = []
			if (reference is not None):
				pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, final_start_div, anchor_plate_id = reference, group_with_feature = True)
			else:
				pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, final_start_div, group_with_feature = True)
			final_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_line_features, pygplates.PolylineOnSphere)
			# #8i) Find valid gdu features at reconstruction_time 
			valid_in_time_gdu_features = [gdu_ft for gdu_ft in gdu_features if (gdu_ft.is_valid_at_time(final_start_div))]
			valid_gdu_features = []
			already_included_gdu_fts = []
			for valid_line_ft,valid_line in final_reconstructed_line_features:
				for gdu_ft in valid_in_time_gdu_features:
					if (valid_line_ft.get_shapefile_attribute('polygid') == gdu_ft.get_shapefile_attribute('POLYGID')):
						if (gdu_ft.get_shapefile_attribute('POLYGID') not in already_included_gdu_fts):
							valid_gdu_features.append(gdu_ft)
							already_included_gdu_fts.append(gdu_ft.get_shapefile_attribute('POLYGID'))
			print('len(valid_gdu_features)',len(valid_gdu_features))
			print('len(valid_con_ocn_line_features)',len(valid_con_ocn_line_features))
			polygid_features_for_sgdu1 = None
			polygid_features_for_sgdu2 = None
			dic_of_gdu_members_for_each_sgdu = find_gdu_members_of_each_sgdu_feat(valid_gdu_features, wanted_sgdu_features, common_filename_for_temporary_sgdu_and_members_csv, final_start_div)
			
			gdu_features_for_sgdu1 = dic_of_gdu_members_for_each_sgdu[str(child_1)]
			polygid_features_for_sgdu1 = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu1]
			array_for_polygid_ft_sgdu1 = np.array(polygid_features_for_sgdu1)
			wanted_gdu_members_for_sgdu1 = np.intersect1d(array_for_polygid_ft_sgdu1,array_of_all_valid_polygid)
			
			gdu_features_for_sgdu2 = dic_of_gdu_members_for_each_sgdu[str(child_2)]
			polygid_features_for_sgdu2 = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu2]
			array_for_polygid_ft_sgdu2 = np.array(polygid_features_for_sgdu2)
			wanted_gdu_members_for_sgdu2 = np.intersect1d(array_for_polygid_ft_sgdu2,array_of_all_valid_polygid)
			reconstructed_gdu_fts_for_sgdu1 = []
			#CON-OCN line features that exit at the younger time (i.e. reconstruction_time - time_interval) and invalid at reconstruction_time
			for child_gdu_ft_1, child_line_gdu_1 in final_reconstructed_line_features:
				polygid_for_child_1 = child_gdu_ft_1.get_shapefile_attribute('polygid')
				if (polygid_for_child_1 in wanted_gdu_members_for_sgdu1):
					# for reconstructed_sgdu_1 in child_sgud_1:
						# if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_1,child_line_gdu_1) == 0.00):
					reconstructed_gdu_fts_for_sgdu1.append((child_gdu_ft_1, child_line_gdu_1))
			reconstructed_gdu_fts_for_sgdu2 = []
			for child_gdu_ft_2, child_line_gdu_2 in final_reconstructed_line_features:
				polygid_for_child_2 = child_gdu_ft_2.get_shapefile_attribute('polygid')
				if (polygid_for_child_2 in wanted_gdu_members_for_sgdu2):
					# for reconstructed_sgdu_2 in child_sgud_2:
						# if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_2,child_line_gdu_2) == 0.00):
					reconstructed_gdu_fts_for_sgdu2.append((child_gdu_ft_2, child_line_gdu_2))
			records_of_order_and_line_feats = sorted_records_for_rift_name[['order','lpolylid','left_gdu','rpolylid','right_gdu']]
			prev_order = -1.00
			
			for order,lpolylid,left_gdu,rpolylid,right_gdu in records_of_order_and_line_feats.itertuples(index = False, name = None):
				current_record = str(order)+"_"+lpolylid+"_"+rpolylid
				current_rev_record = str(order)+"_"+rpolylid+"_"+lpolylid
				if (current_record in already_examined_record or current_rev_record in already_examined_record):
					continue
				already_examined_record.append(current_record)
				current_order = -1.00
				if (prev_order == -1.00):
					prev_order = order
					current_order = order
				else:
					if (prev_order - order > threshold_diff_small_circle):
						current_order = prev_order - (threshold_diff_small_circle/2.00)
						#reset prev_order 
						prev_order = -1.00
					else:
						current_order = order
				while (current_order >= order):
					small_circle_boundary = rotation_utility.create_small_circle_PolylineOnSphere(E_pole,current_order)
					smallest_circle_angular_radius_degrees = current_order
					new_line_features_from_sgdu1 = []
					new_line_features_from_sgdu2 = []
					for line_ft_1,line_1 in reconstructed_gdu_fts_for_sgdu1:
						if (pygplates.GeometryOnSphere.distance(line_1, small_circle_boundary) == 0.00):
							new_line_features_from_sgdu1.append((line_ft_1,line_1))
					for line_ft_2,line_2 in reconstructed_gdu_fts_for_sgdu2:
						if (pygplates.GeometryOnSphere.distance(line_2, small_circle_boundary) == 0.00):
							new_line_features_from_sgdu2.append((line_ft_2,line_2))
					for line_ft_1,line_1 in new_line_features_from_sgdu1:
						for line_ft_2,line_2 in new_line_features_from_sgdu2:
							if (((line_ft_1.get_name() != lpolylid and line_ft_1.get_name() != rpolylid) and (line_ft_2.get_name() != lpolylid and line_ft_2.get_name() != rpolylid))\
								or (line_ft_1.get_name() == lpolylid and line_ft_2.get_name() != rpolylid) or (line_ft_1.get_name() == rpolylid and line_ft_2.get_name() != lpolylid)\
								or (line_ft_2.get_name() == lpolylid and line_ft_1.get_name() != rpolylid) or (line_ft_2.get_name() == rpolylid and line_ft_1.get_name() != lpolylid)):
									#new mid-point but have to validate the point feature 
									_,closest_point_on_gdu1,_ = pygplates.GeometryOnSphere.distance(line_1, small_circle_boundary,return_closest_positions = True)
									_,closest_point_on_gdu2,_ = pygplates.GeometryOnSphere.distance(line_2, small_circle_boundary,return_closest_positions = True)
									temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
									#find the mid_point between two points 
									approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
									#temporarily set valid_mid_point_feat to True
									valid_mid_point_feat = True
									for random_sgdu_ft, random_sgdu in final_reconstructed_sgdu_features:
										if (random_sgdu_ft.get_name() != child_1 and random_sgdu_ft.get_name() != child_2):
											#if (random_sgdu.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
											if (pygplates.GeometryOnSphere.distance(temporary_PolylineOnSphere, random_sgdu) == 0.00):
												valid_mid_point_feat = False
												break
										if (random_sgdu.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
											valid_mid_point_feat = False
											break
										if (random_sgdu.partition(temporary_PolylineOnSphere) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
											geometry_inside = []
											random_sgdu.partition(temporary_PolylineOnSphere, partitioned_geometries_inside = geometry_inside)
											if (len(geometry_inside) > 0):
												valid_mid_point_feat = False
												break
									if (valid_mid_point_feat == True):
										#create an arc
										temporary_GreatCircleArc = pygplates.GreatCircleArc(approx_mid_point,E_pole)
										normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
										#left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, approx_mid_point, closest_point_on_gdu1, closest_point_on_gdu2, line_ft_1.get_reconstruction_plate_id(), line_ft_2.get_reconstruction_plate_id())
										#create point feature
										#name = 'R'+str(child_1)+'_'+str(child_2)+'_'+str(smallest_circle_angular_radius_degrees)
										left_gduid, right_gduid = left_gdu, right_gdu
									
										total_stage_rel_rot_of_1_to_left_gdu = find_stage_relative_reconstruction_rotation_(rotation_model,left_gdu,line_ft_1.get_reconstruction_plate_id(),float(final_start_div)+time_interval,float(final_start_div),reference)
										total_stage_rel_rot_of_1_to_right_gdu = find_stage_relative_reconstruction_rotation_(rotation_model,right_gdu,line_ft_1.get_reconstruction_plate_id(),float(final_start_div)+time_interval,float(final_start_div),reference)
									
										if (total_stage_rel_rot_of_1_to_left_gdu is not None):
											if (total_stage_rel_rot_of_1_to_left_gdu.represents_identity_rotation()):
												left_gduid, right_gduid = line_ft_1.get_reconstruction_plate_id(), line_ft_2.get_reconstruction_plate_id()
											else:
												left_gduid, right_gduid = line_ft_2.get_reconstruction_plate_id(), line_ft_1.get_reconstruction_plate_id()
										else:
											left_gduid, right_gduid = line_ft_1.get_reconstruction_plate_id(), line_ft_2.get_reconstruction_plate_id()
										name = rift_name+'_'+str(smallest_circle_angular_radius_degrees)
										rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, approx_mid_point, name = name, valid_time = (reconstruction_time,0.00))
										if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
											rift_point_ft.set_left_plate(line_ft_1.get_reconstruction_plate_id())
											rift_point_ft.set_right_plate(line_ft_2.get_reconstruction_plate_id())
										else:
											rift_point_ft.set_left_plate(left_gduid)
											rift_point_ft.set_right_plate(right_gduid)
										rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
										rift_point_ft.set_description(str(smallest_circle_angular_radius_degrees))
										if (reference is None):
											pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
										else:
											pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
										output_rift_point_features.add(rift_point_ft)
										if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
											unsure_topology_for_MOR_fts.add(rift_point_ft)
										if ((left_gduid == line_ft_1.get_reconstruction_plate_id() and right_gduid == line_ft_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
											list_of_ordered_pairs_gdu_fts.append((final_start_div, rift_name, smallest_circle_angular_radius_degrees, line_ft_1.get_shapefile_attribute('POLYLID'), line_ft_1.get_reconstruction_plate_id(), lrepgduid, line_ft_2.get_shapefile_attribute('POLYLID'), line_ft_2.get_reconstruction_plate_id(), rrepgduid))
										else:
											list_of_ordered_pairs_gdu_fts.append((final_start_div, rift_name, smallest_circle_angular_radius_degrees, line_ft_2.get_shapefile_attribute('POLYLID'), line_ft_2.get_reconstruction_plate_id(), lrepgduid, line_ft_1.get_shapefile_attribute('POLYLID'), line_ft_1.get_reconstruction_plate_id(), rrepgduid))
										#create pair of line features associated with the rift point ft
										_,con_ocn_to_time = line_ft_1.get_valid_time()
										line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_1,name= line_ft_1.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
										line_feature_1.set_reconstruction_plate_id(line_ft_1.get_reconstruction_plate_id())
										line_feature_1.set_conjugate_plate_id(line_ft_2.get_reconstruction_plate_id())
										line_feature_1.set_description('divergent_margin')
															
										_,con_ocn_to_time = line_ft_2.get_valid_time()
										line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_2,name= line_ft_2.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
										line_feature_2.set_reconstruction_plate_id(line_ft_2.get_reconstruction_plate_id())
										line_feature_2.set_conjugate_plate_id(line_ft_1.get_reconstruction_plate_id())
										line_feature_2.set_description('divergent_margin')
										if (reference is None):
											pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,final_start_div)
										else:
											pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,final_start_div,reference)
										output_diverging_line_features.add(line_feature_1)
										output_diverging_line_features.add(line_feature_2)
										previous_diverging_line_feats.append((line_feature_1,line_feature_2,'D',final_start_div,pygplates.GeometryOnSphere.distance(line_1.get_centroid(), line_2.get_centroid())))
					
					current_order = current_order - (threshold_diff_small_circle/2.00)
			reconstruction_time = final_start_div
			while (reconstruction_time >= 0.00):
				if (len(previous_diverging_line_feats) > 0):
					#;from_time;to_time;SGDUID;GDUID;buffer_distance_km;repGDUID
					temporary_sgdu_and_member_csv_at_time = common_filename_for_temporary_sgdu_and_members_csv.format(time = str(reconstruction_time))
					temp_sgdu_and_gdu_df = pd.read_csv(temporary_sgdu_and_member_csv_at_time, delimiter = ';', header = 0)
					remaining_diverging_line_feats = []
					recorded_distance = -1.00
					if (len(dic_prev_div_line_feats) == 0):
						for line_feature_1,line_feature_2,_,prev_begin_age,prev_distance in previous_diverging_line_feats:
							pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
							rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
							if (pair_polylids not in dic_prev_div_line_feats and rev_pair_of_polylids not in dic_prev_div_line_feats):
								dic_prev_div_line_feats[pair_polylids] = {'line_feats':(line_feature_1,line_feature_2),'prev_motion':'D', 'age':prev_begin_age, 'dist':prev_distance}
					else:
						for line_feature_1,line_feature_2,prev_motion,prev_begin_age,prev_distance in previous_diverging_line_feats:
							pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
							rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
							if (pair_polylids in dic_prev_div_line_feats):
								dic_prev_div_line_feats[pair_polylids]['prev_motion'] = prev_motion
								dic_prev_div_line_feats[pair_polylids]['age'] = prev_begin_age
								current_line_feature_1,current_line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
								if (current_line_feature_1.is_valid_at_time(reconstruction_time) == False or current_line_feature_2.is_valid_at_time(reconstruction_time) == False):
									output_diverging_line_features.add(current_line_feature_1)
									output_diverging_line_features.add(current_line_feature_2)
									output_begin_age,output_end_age = current_line_feature_1.get_valid_time()
									pairs_of_kin_line_fts.append((output_begin_age,output_end_age,current_line_feature_1.get_description(),current_line_feature_1.get_name(),current_line_feature_2.get_name(),current_line_feature_1.get_feature_id().get_string(),current_line_feature_2.get_feature_id().get_string()))
								if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
									dic_prev_div_line_feats[pair_polylids]['line_feats'] = (line_feature_1,line_feature_2)
								else:
									del dic_prev_div_line_feats[pair_polylids]
							elif (rev_pair_of_polylids in dic_prev_div_line_feats):
								dic_prev_div_line_feats[rev_pair_of_polylids]['prev_motion'] = prev_motion
								dic_prev_div_line_feats[rev_pair_of_polylids]['age'] = prev_begin_age
								current_line_feature_1,current_line_feature_2 = dic_prev_div_line_feats[rev_pair_of_polylids]['line_feats']
								if (current_line_feature_1.is_valid_at_time(reconstruction_time) == False or current_line_feature_2.is_valid_at_time(reconstruction_time) == False):
									output_diverging_line_features.add(current_line_feature_1)
									output_diverging_line_features.add(current_line_feature_2)
									output_begin_age,output_end_age = current_line_feature_1.get_valid_time()
									pairs_of_kin_line_fts.append((output_begin_age,output_end_age,current_line_feature_1.get_description(),current_line_feature_1.get_name(),current_line_feature_2.get_name(),current_line_feature_1.get_feature_id().get_string(),current_line_feature_2.get_feature_id().get_string()))
								if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
									dic_prev_div_line_feats[rev_pair_of_polylids]['line_feats'] = (line_feature_1,line_feature_2)
								else:
									del dic_prev_div_line_feats[rev_pair_of_polylids]
							else:
								if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
									dic_prev_div_line_feats[pair_polylids] = {'line_feats':(line_feature_1,line_feature_2),'prev_motion':prev_motion, 'age':prev_begin_age, 'dist':prev_distance}
					list_of_pair_polyids_to_be_deleted = []
					for pair_polylids in dic_prev_div_line_feats:
						#pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
						#rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
				
						print('pair_polylids',pair_polylids)
						line_feature_1,line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
						prev_tectonic_motion = dic_prev_div_line_feats[pair_polylids]['prev_motion']
						prev_distance = dic_prev_div_line_feats[pair_polylids]['dist']
						prev_begin_age = dic_prev_div_line_feats[pair_polylids]['age']
						#debug
						# if (pair_polylids == '17300_13241_9277+12009_13906_7560' or pair_polylids == '12009_13906_7560+17300_13241_9277'):
							# print('line_feature_1.get_description()',line_feature_1.get_description())
							# print('line_feature_2.get_description()',line_feature_2.get_description())
							# print('prev_begin_age',prev_begin_age)
							# print('prev_motion',prev_tectonic_motion)
						
					
						SGDUID_for_line_ft_1 = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == line_feature_1.get_reconstruction_plate_id(),'SGDUID'].unique()
						SGDUID_for_line_ft_2 = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == line_feature_2.get_reconstruction_plate_id(),'SGDUID'].unique()
						# if (pair_polylids in list_of_already_evaluated_pairs or rev_pair_of_polylids in list_of_already_evaluated_pairs):
							# continue #these two line features have already been evaluated at this reconstruction time thus take the new tuple
						# else:
							# list_of_already_evaluated_pairs.append(pair_polylids)
				
						#NO NEED TO find the original line features
						# original_con_ocn_line_ft_1 = None
						# original_con_ocn_line_ft_2 = None
						# for con_ocn_line_ft in valid_con_ocn_line_features:
							# if (line_feature_1.get_name() == con_ocn_line_ft.get_shapefile_attribute('POLYLID')):
								# original_con_ocn_line_ft_1 = con_ocn_line_ft
							# elif (line_feature_2.get_name() == con_ocn_line_ft.get_shapefile_attribute('POLYLID')):
								# original_con_ocn_line_ft_2 = con_ocn_line_ft
							# if (original_con_ocn_line_ft_1 is not None and original_con_ocn_line_ft_2 is not None):
								# break
					
						if (recorded_distance == -1.00):
							recorded_distance = prev_distance
						if ((prev_begin_age - reconstruction_time) > time_interval and line_feature_1.is_valid_at_time(reconstruction_time) and line_feature_2.is_valid_at_time(reconstruction_time)):
							reconstructed_current_div_line_features = []
							if (reference is not None):
								pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_current_div_line_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
							else:
								pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_current_div_line_features, reconstruction_time, group_with_feature = True)
							final_current_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_current_div_line_features, pygplates.PolylineOnSphere)
							current_reconstr_ft_1, current_reconstr_line_1 = final_current_reconstructed_line_features[0]
							current_reconstr_ft_2, current_reconstr_line_2 = final_current_reconstructed_line_features[1]
							#current_distance = pygplates.GeometryOnSphere.distance(current_reconstr_line_1.get_centroid(),current_reconstr_line_2.get_centroid())
							#recorded_distance = current_distance
						
							current_reconstr_line_1_centroid = current_reconstr_line_1.get_centroid()
							centroid_1_lat, centroid_1_lon = current_reconstr_line_1_centroid.to_lat_lon()
							current_reconstr_line_2_centroid = current_reconstr_line_2.get_centroid()
							centroid_2_lat, centroid_2_lon = current_reconstr_line_2_centroid.to_lat_lon()
							distance_btw_current_centroids = calculate_distance_km_between_two_points_from_haversine_formula(centroid_1_lat,centroid_1_lon,centroid_2_lat,centroid_2_lon)
						
							reconstructed_prev_div_line_features = []
							if (reference is not None):
								pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_prev_div_line_features, reconstruction_time + time_interval, anchor_plate_id = reference, group_with_feature = True)
							else:
								pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_prev_div_line_features, reconstruction_time + time_interval, group_with_feature = True)
							final_prev_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_prev_div_line_features,pygplates.PolylineOnSphere)
							prev_reconstr_ft_1,prev_reconstr_line_1 = final_prev_reconstructed_line_features[0]
							prev_reconstr_ft_2,prev_reconstr_line_2 = final_prev_reconstructed_line_features[1]
					
							reconstructed_point_A_at_from_time = prev_reconstr_line_1.get_centroid()
							reconstructed_point_B_at_from_time = prev_reconstr_line_2.get_centroid()
							reconstructed_point_A_at_to_time = current_reconstr_line_1.get_centroid()
							reconstructed_point_B_at_to_time = current_reconstr_line_2.get_centroid()
							#result_of_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_pos_and_angular_vel_vec(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time, reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time, reconstruction_time, reconstruction_time-time_interval)
							result_of_tectonic_motion, dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_pos_and_angular_vel_vec(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time, reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time, reconstruction_time+time_interval, reconstruction_time)
							list_dot_prod.append((reconstruction_time,line_feature_1.get_reconstruction_plate_id(),line_feature_2.get_reconstruction_plate_id(),dot_prod_btw_tectonic_motion))
							#debug
							# print('reconstruction_time',reconstruction_time)
							# print('result_of_tectonic_motion',result_of_tectonic_motion)
						
						
							latA,lonA = reconstructed_point_A_at_from_time.to_lat_lon()
							latB,lonB = reconstructed_point_B_at_from_time.to_lat_lon()
							at_prev_time_distance_in_km_btw_A_and_B = calculate_distance_km_between_two_points_from_haversine_formula(latA,lonA,latB,lonB)
							cur_latA,cur_lonA = reconstructed_point_A_at_to_time.to_lat_lon()
							cur_latB,cur_lonB = reconstructed_point_B_at_to_time.to_lat_lon()
							at_current_time_distance_in_km_btw_A_and_B = calculate_distance_km_between_two_points_from_haversine_formula(cur_latA,cur_lonA,cur_latB,cur_lonB)
							current_distance = at_current_time_distance_in_km_btw_A_and_B
							recorded_distance = current_distance
						
							is_valid_pair_of_line_fts = True
						
							#polygid_of_original_con_ocn_line_ft_1 = original_con_ocn_line_ft_1.get_shapefile_attribute('polygid')
							#polygid_of_original_con_ocn_line_ft_2 = original_con_ocn_line_ft_2.get_shapefile_attribute('polygid')
							total_stage_rel_rot_of_1_to_2 = find_stage_relative_reconstruction_rotation_(rotation_model,line_feature_1.get_reconstruction_plate_id(),line_feature_2.get_reconstruction_plate_id(),float(reconstruction_time+time_interval),reconstruction_time,reference)
							total_stage_rel_rot_of_2_to_1 = find_stage_relative_reconstruction_rotation_(rotation_model,line_feature_2.get_reconstruction_plate_id(),line_feature_1.get_reconstruction_plate_id(),float(reconstruction_time+time_interval),reconstruction_time,reference)
							if (total_stage_rel_rot_of_1_to_2 is not None):
								if (total_stage_rel_rot_of_1_to_2.represents_identity_rotation() == True):
									is_valid_pair_of_line_fts = False
								else:
									if (total_stage_rel_rot_of_2_to_1 is not None):
										if (total_stage_rel_rot_of_2_to_1.represents_identity_rotation() == True):
											is_valid_pair_of_line_fts = False
									else:
										is_valid_pair_of_line_fts = False
							else:
								is_valid_pair_of_line_fts = False
							if (is_valid_pair_of_line_fts == True):
								final_SGDUID_for_line_1 = None
								final_SGDUID_for_line_2 = None
								for reconstructed_sgdu_ft_at_reconstruction_time, reconstructed_sgdu_at_reconstruction_time in final_reconstructed_sgdu_features:
									SGDUID_of_reconstructed_sgdu_ft = int(reconstructed_sgdu_ft_at_reconstruction_time.get_name())
									SGDUID_for_rand_sgdu_ft = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == reconstructed_sgdu_ft_at_reconstruction_time.get_reconstruction_plate_id(),'SGDUID'].unique()
									# #find the same value between SGDUID_for_gdu_ft and SGDUID_for_line_ft_1; SGDUID_for_gdu_ft and SGDUID_for_line_ft_2
									intersection_w_line_ft_1 = np.intersect1d(SGDUID_for_rand_sgdu_ft, SGDUID_for_line_ft_1)
									intersection_w_line_ft_2 = np.intersect1d(SGDUID_for_rand_sgdu_ft, SGDUID_for_line_ft_2)
									#if ((SGDUID_of_reconstructed_sgdu_ft not in SGDUID_for_line_ft_1) and (SGDUID_of_reconstructed_sgdu_ft not in SGDUID_for_line_ft_2)):
									#if ((SGDUID_of_reconstructed_sgdu_ft not in intersection_w_line_ft_1) and (SGDUID_of_reconstructed_sgdu_ft not in intersection_w_line_ft_2)):
									if (len(intersection_w_line_ft_1) == 0 and len(intersection_w_line_ft_2) == 0):
										temporary_line_connecting_A_and_B = pygplates.PolylineOnSphere([reconstructed_point_A_at_to_time,reconstructed_point_B_at_to_time])
										if (reconstructed_sgdu_at_reconstruction_time.partition(temporary_line_connecting_A_and_B) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
											is_valid_pair_of_line_fts = False
											break
									else:
										if (len(intersection_w_line_ft_1) > 0):
											final_SGDUID_for_line_1 = reconstructed_sgdu_ft_at_reconstruction_time
										if (len(intersection_w_line_ft_2) > 0):
											final_SGDUID_for_line_2 = reconstructed_sgdu_ft_at_reconstruction_time
						
								if (final_SGDUID_for_line_1 is None or final_SGDUID_for_line_2 is None):
									is_valid_pair_of_line_fts = False
								else:
									if (final_SGDUID_for_line_1.get_name() == final_SGDUID_for_line_2.get_name()):
										is_valid_pair_of_line_fts = False
								
							#debug
							# if (pair_polylids == '17300_13241_9277+12009_13906_7560' or pair_polylids == '12009_13906_7560+17300_13241_9277'):
								# print('line_feature_1.get_description()',line_feature_1.get_description())
								# print('line_feature_2.get_description()',line_feature_2.get_description())
								# print('is_valid_pair_of_line_fts',is_valid_pair_of_line_fts)
								# print('prev_begin_age',prev_begin_age)
								# print('prev_motion',prev_motion)
								# print('result_of_tectonic_motion',result_of_tectonic_motion)
					
					
							has_modified_line_feats = False 
							if (((prev_begin_age - reconstruction_time) >= 3.00*(time_interval)) and prev_tectonic_motion != 'D'and result_of_tectonic_motion != 'D' and is_valid_pair_of_line_fts == True):
								#debug
								#print('Enter this')
								#need to check the type of kinematic boundary in previous time
								if (line_feature_1.get_description() == 'plate_boundary_zone' and line_feature_2.get_description() == 'plate_boundary_zone'):
									line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
									line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
									cloned_line_ft_1 = line_feature_1.clone()
									cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
									cloned_line_ft_2 = line_feature_2.clone()
									cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
									output_diverging_line_features.add(cloned_line_ft_1)
									output_diverging_line_features.add(cloned_line_ft_2)
									pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
									if (result_of_tectonic_motion == 'C'):
										line_feature_1.set_description('convergent_margin')
										line_feature_2.set_description('convergent_margin')
										has_modified_line_feats = True
									elif (result_of_tectonic_motion == 'T'):
										line_feature_1.set_description('transform_fault')
										line_feature_2.set_description('transform_fault')
										has_modified_line_feats = True
									if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
										line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
										line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
								elif (line_feature_1.get_description() != 'convergent_margin' and line_feature_2.get_description() != 'convergent_margin'):
									line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
									line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
									cloned_line_ft_1 = line_feature_1.clone()
									cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
									cloned_line_ft_2 = line_feature_2.clone()
									cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
									output_diverging_line_features.add(cloned_line_ft_1)
									output_diverging_line_features.add(cloned_line_ft_2)
									pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
									if (result_of_tectonic_motion == 'C' and line_feature_1.get_description() == 'divergent_margin'):
										line_feature_1.set_description('plate_boundary_zone')
										line_feature_2.set_description('plate_boundary_zone')
										has_modified_line_feats = True
									else:
										line_feature_1.set_description('transform_fault')
										line_feature_2.set_description('transform_fault')
										has_modified_line_feats = True
									if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
										line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
										line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
								elif (line_feature_1.get_description() == 'convergent_margin' and line_feature_2.get_description() == 'convergent_margin'):
									line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
									line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
									cloned_line_ft_1 = line_feature_1.clone()
									cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
									cloned_line_ft_2 = line_feature_2.clone()
									cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
									output_diverging_line_features.add(cloned_line_ft_1)
									output_diverging_line_features.add(cloned_line_ft_2)
									pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
									if (result_of_tectonic_motion == 'T'):
										line_feature_1.set_description('transform_fault')
										line_feature_2.set_description('transform_fault')
										has_modified_line_feats = True
									if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
										line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
										line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
							#elif (result_of_tectonic_motion == 'D' and prev_tectonic_motion == 'D' and is_valid_pair_of_line_fts == True and (prev_distance == 0.00 or at_prev_time_distance_in_km_btw_A_and_B <= 50.00)):
							elif (result_of_tectonic_motion == 'D' and prev_tectonic_motion == 'D' and is_valid_pair_of_line_fts == True):
								if (((prev_begin_age - reconstruction_time) >= 3.00*(time_interval)) and line_feature_1.get_description() == 'convergent_margin' and line_feature_2.get_description() == 'convergent_margin'):
									line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
									line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
									cloned_line_ft_1 = line_feature_1.clone()
									cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
									line_feature_1.set_description('plate_boundary_zone')
									cloned_line_ft_2 = line_feature_2.clone()
									cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
									output_diverging_line_features.add(cloned_line_ft_1)
									output_diverging_line_features.add(cloned_line_ft_2)
									line_feature_2.set_description('plate_boundary_zone')
									has_modified_line_feats = True
									pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
									if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
										line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
										line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
								elif (line_feature_1.get_description() != 'divergent_margin' and line_feature_1.get_description() != 'convergent_margin' and line_feature_2.get_description() != 'divergent_margin' and line_feature_2.get_description() != 'convergent_margin'):
									line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
									line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
									cloned_line_ft_1 = line_feature_1.clone()
									cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
									line_feature_1.set_description('divergent_margin')
									cloned_line_ft_2 = line_feature_2.clone()
									cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
									output_diverging_line_features.add(cloned_line_ft_1)
									output_diverging_line_features.add(cloned_line_ft_2)
									line_feature_2.set_description('divergent_margin')
									has_modified_line_feats = True
									pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
									if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
										line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
										line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
									#quickly find mid-point feature
									total_relative_reconstruction_rotation = find_total_relative_reconstruction_rotation_(rotation_model, line_feature_1.get_reconstruction_plate_id(), line_feature_2.get_reconstruction_plate_id(), reconstruction_time, reference)
									if (total_relative_reconstruction_rotation is not None):
										if (total_relative_reconstruction_rotation.represents_identity_rotation() == False):
											#find mid point
											E_pole,_ = total_relative_reconstruction_rotation.get_euler_pole_and_angle()
											quick_mid_pt,mid_pt_order = quickly_derive_mid_point_and_order_of_mid_point_from_two_divergent_points(reconstructed_point_A_at_to_time,reconstructed_point_B_at_to_time,E_pole)
											mid_pt_order = round(mid_pt_order,2)
											#create rift point ft
											# #create an arc
											temporary_GreatCircleArc = pygplates.GreatCircleArc(quick_mid_pt,E_pole)
											normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
											left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, quick_mid_pt, reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time, line_feature_1.get_reconstruction_plate_id(), line_feature_2.get_reconstruction_plate_id())
											name = 'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name()+'_'+str(mid_pt_order)
											rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, quick_mid_pt, name = name, valid_time = (reconstruction_time,0.00))
											if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
												rift_point_ft.set_left_plate(line_feature_1.get_reconstruction_plate_id())
												rift_point_ft.set_right_plate(line_feature_2.get_reconstruction_plate_id())
											else:
												rift_point_ft.set_left_plate(left_gduid)
												rift_point_ft.set_right_plate(right_gduid)
											rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
											rift_point_ft.set_description(str(mid_pt_order))
											if (reference is None):
												pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
											else:
												pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
											output_rift_point_features.add(rift_point_ft)
											if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
												unsure_topology_for_MOR_fts.add(rift_point_ft)
											if ((left_gduid == line_feature_1.get_reconstruction_plate_id() and right_gduid == line_feature_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
												list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name(),mid_pt_order, line_feature_1.get_name(), line_feature_1.get_reconstruction_plate_id(), final_SGDUID_for_line_1.get_reconstruction_plate_id(), line_feature_2.get_name(), line_feature_2.get_reconstruction_plate_id(), final_SGDUID_for_line_2.get_reconstruction_plate_id()))
											else:
												list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name(),mid_pt_order, line_feature_2.get_name(), line_feature_2.get_reconstruction_plate_id(), final_SGDUID_for_line_2.get_reconstruction_plate_id(), line_feature_1.get_name(), line_feature_1.get_reconstruction_plate_id(), final_SGDUID_for_line_1.get_reconstruction_plate_id()))
							
							#if ((prev_distance == 0.00 or at_prev_time_distance_in_km_btw_A_and_B <= 50.00 or is_valid_pair_of_line_fts == True)):
							if (is_valid_pair_of_line_fts == True):
								# print('prev_distance',prev_distance)
								# print('recorded_distance',recorded_distance)
								#remaining_diverging_line_feats.append((line_feature_1,line_feature_2,prev_begin_age,recorded_distance))
								if (has_modified_line_feats == True):
									remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
								else:
									remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
							elif (is_valid_pair_of_line_fts == False):
								if (line_feature_1.get_description() != 'plate_boundary_zone' and line_feature_2.get_description() != 'plate_boundary_zone'):
									line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
									line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
									if (line_feature_1_begin_time > reconstruction_time):
										cloned_line_ft_1 = line_feature_1.clone()
										cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
										cloned_line_ft_2 = line_feature_2.clone()
										cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
										pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
										output_diverging_line_features.add(cloned_line_ft_1)
										output_diverging_line_features.add(cloned_line_ft_2)
									if (pygplates.GeometryOnSphere.distance(current_reconstr_line_1.get_centroid(),current_reconstr_line_2.get_centroid()) == 0.00):
										if (line_feature_1.get_description() == 'convergent_margin' and line_feature_2.get_description() == 'convergent_margin'):
											output_collision.append((reconstruction_time,line_feature_1.get_name(),line_feature_2.get_name()))
									line_feature_1.set_description('plate_boundary_zone')
									line_feature_2.set_description('plate_boundary_zone')
									has_modified_line_feats = True
									if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
										line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
										line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
						
								# if (current_distance > 0.00 and at_current_time_distance_in_km_btw_A_and_B >= 50.00):
									# if (has_modified_line_feats == True):
										# remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
									# else:
										# remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
						
								if (has_modified_line_feats == True):
									remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
								else:
									remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
						
						elif (prev_begin_age > reconstruction_time and (line_feature_1.is_valid_at_time(reconstruction_time) == False or line_feature_2.is_valid_at_time(reconstruction_time) == False)):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(prev_begin_age,reconstruction_time+0.100)
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(prev_begin_age,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							list_of_pair_polyids_to_be_deleted.append(pair_polylids)
						elif (prev_begin_age == reconstruction_time):
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,prev_tectonic_motion,prev_begin_age,recorded_distance))
					for pair_polylids in list_of_pair_polyids_to_be_deleted:
						del dic_prev_div_line_feats[pair_polylids]
					previous_diverging_line_feats = remaining_diverging_line_feats
				
				
				output_dot_prod_tectonic_motion_df = pd.DataFrame.from_records(list_dot_prod, columns = ['reconstruction_time','child_repgduid_1','child_repgduid_2','dot_prod'])
				filename = 'dot_prod_tectonic_motion_for_'+modelname+'_'+yearmonthday+'.csv'
				if (os.path.isfile(filename)):
					output_dot_prod_tectonic_motion_df = pd.read_csv(filename)
					output_dot_prod_tectonic_motion_df = pd.concat([pd.DataFrame([[list_dot_prod]]), output_dot_prod_tectonic_motion_df], ignore_index=True)
					output_dot_prod_tectonic_motion_df.to_csv(filename)
				else:
					output_dot_prod_tectonic_motion_df = pd.DataFrame([[list_dot_prod]])
					output_dot_prod_tectonic_motion_df.to_csv(filename)
				
				reconstruction_time = reconstruction_time-time_interval
	output_rift_point_features.write('additional_rift_point_features_for_'+str(max_reconstruction_time_for_start_div)+'_'+str(min_reconstruction_time_for_start_div)+'_'+modelname+'_'+yearmonthday+'.shp')
	unsure_topology_for_MOR_fts.write('unsure_topology_for_MOR_fts_'+str(max_reconstruction_time_for_start_div)+'_'+str(min_reconstruction_time_for_start_div)+'_'+modelname+'_'+yearmonthday+'.shp')
	if (len(dic_prev_div_line_feats) > 0):
		for pair_polylids in dic_prev_div_line_feats:
			line_feature_1,line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
			prev_tectonic_motion = dic_prev_div_line_feats[pair_polylids]['prev_motion']
			prev_distance = dic_prev_div_line_feats[pair_polylids]['dist']
			prev_begin_age = dic_prev_div_line_feats[pair_polylids]['age']
			output_diverging_line_features.add(line_feature_1)
			output_diverging_line_features.add(line_feature_2)
			line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
			pairs_of_kin_line_fts.append((line_feature_1_begin_time,line_feature_1_end_time,line_feature_1.get_description(),line_feature_1.get_name(),line_feature_2.get_name(),line_feature_1.get_feature_id().get_string(),line_feature_2.get_feature_id().get_string()))
	output_diverging_line_features.write('additional_diverging_line_features_for_'+str(max_reconstruction_time_for_start_div)+'_'+str(min_reconstruction_time_for_start_div)+'_'+modelname+'_'+yearmonthday+'.shp')
	
	#list_of_ordered_pairs_gdu_fts.append((start_div,name,smallest_circle_angular_radius_degrees, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
	output_dataframe = pd.DataFrame.from_records(list_of_ordered_pairs_gdu_fts, columns = ['start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'])
	filename = 'additional_rift_point_features_records_for_'+str(max_reconstruction_time_for_start_div)+'_'+str(min_reconstruction_time_for_start_div)+'_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)

	#line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()
	output_dataframe = pd.DataFrame.from_records(pairs_of_kin_line_fts, columns = ['from_time','to_time','type_kin','polylid1','polylid2','fid1','fid2'])
	filename = 'additional_pairs_of_kin_line_fts_from_div_bdn_process_for_'+str(max_reconstruction_time_for_start_div)+'_'+str(min_reconstruction_time_for_start_div)+'_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	
def evaluate_kinematic_between_pairs_of_unrelated_SuperGDUa(pairs_of_sgdu_csv, line_features_collection, sgdu_features, gdu_features_collection, common_filename_for_temporary_sgdu_and_members_csv, time_interval, begin_reconstruction_time, end_reconstruction_time, rotation_model, reference, modelname, yearmonthday):
	reconstruction_time = begin_reconstruction_time
	pairs_of_sgdu_df = pd.read_csv(pairs_of_sgdu_csv)
	dict_of_polygid_and_Shapely_centroid = {}
	dic_of_gdu_members_for_each_sgdu = {}
	dic_prev_div_line_feats = {}
	previous_diverging_line_feats = []
	temp_list_of_centroids_and_polygids = []
	reconstructed_sgdu_features = []
	output_kinematics = []
	suspected_output = []
	appropriate_pairs_of_sgdus = []
	key_of_sgdus = []
	reconstructed_gdu_fts_for_sgdu1 = []
	reconstructed_gdu_fts_for_sgdu2 = []
	prev_reconstructed_gdu_fts_for_sgdu1 = []
	prev_reconstructed_gdu_fts_for_sgdu2 = []
	reconstructed_gdu_features = []
	reconstructed_gdu_features_ynger = []
	reconstructed_line_features = []
	reconstructed_line_features_ynger = []
	other_reconstructed_gdu_features = []
	output_rift_point_features = pygplates.FeatureCollection()
	output_subseq_rift_point_features = pygplates.FeatureCollection()
	output_diverging_line_features = pygplates.FeatureCollection()
	unsure_topology_for_MOR_fts = pygplates.FeatureCollection()
	kin_line_feats_at_reconstruction_time = []
	list_of_ordered_pairs_gdu_fts = []
	list_of_ordered_non_rift_pairs_gdu_fts = []
	list_of_subseq_ordered_pairs_gdu_fts = []
	output_temporary_MOR_line_feats = []
	dic_kin_line_feats = {}
	output_records_for_kin_feats = []
	output_collision = []
	results_of_all_possible_tectonic_motion = []
	pairs_of_kin_line_fts = []
	list_dot_prod = []
	if (end_reconstruction_time <= 0.00):
		end_reconstruction_time = time_interval #if end_reconstruction_time == 0.00 and time_interval is 5.00, then update the last time instant to be evaluate to be 5.00
	reconstruction_time = begin_reconstruction_time
	while(reconstruction_time >= end_reconstruction_time):
		#debug
		#temporary_output_pair_div_line_fts = pygplates.FeatureCollection()
		
		print('reconstruction_time',reconstruction_time)
		list_dot_prod[:] = []
		
		dic_of_gdu_members_for_each_sgdu.clear()
		reconstructed_sgdu_features[:] = []
		reconstructed_gdu_features[:] = []
		reconstructed_line_features[:] = []
		other_reconstructed_gdu_features[:] = []
		results_of_all_possible_tectonic_motion[:] = []
		# #8) Find appropriate pairs of sgdus first based on the distance
		# #8i) Find valid sgdu features
		valid_sgdu_features = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(reconstruction_time))]
		# #8ii) Reconstruct sgdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_sgdu_features = find_final_reconstructed_geometries(reconstructed_sgdu_features, pygplates.PolygonOnSphere)
		#Find valid gdu features with con-ocn line features
		valid_con_ocn_line_features = [con_ocn_ft for con_ocn_ft in line_features_collection if con_ocn_ft.is_valid_at_time(reconstruction_time)]
		if (reference is not None):
			pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_line_features, pygplates.PolylineOnSphere)
		# #8i) Find valid gdu features at reconstruction_time 
		valid_in_time_gdu_features = [gdu_ft for gdu_ft in gdu_features_collection if (gdu_ft.is_valid_at_time(reconstruction_time))]
		valid_gdu_features = []
		already_included_gdu_fts = []
		for valid_line_ft,valid_line in final_reconstructed_line_features:
			#debug
			#if (valid_line_ft.get_reconstruction_plate_id() == 19508):
			#	print(valid_line_ft.get_reconstruction_plate_id())
			
			for gdu_ft in valid_in_time_gdu_features:
				if (valid_line_ft.get_shapefile_attribute('polygid') == gdu_ft.get_shapefile_attribute('POLYGID')):
					if (gdu_ft.get_shapefile_attribute('POLYGID') not in already_included_gdu_fts):
						valid_gdu_features.append(gdu_ft)
						already_included_gdu_fts.append(gdu_ft.get_shapefile_attribute('POLYGID'))
					# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
						# valid_gdu_features.append(gdu_ft)
						#already_included_gdu_fts.append(gdu_ft.get_feature_id())
				# else:
					# if (gdu_ft.get_reconstruction_plate_id() == valid_line_ft.get_reconstruction_plate_id()):
						# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
							# valid_gdu_features.append(gdu_ft)
							# already_included_gdu_fts.append(gdu_ft.get_feature_id())
		print('len(valid_gdu_features)',len(valid_gdu_features))
		print('len(valid_con_ocn_line_features)',len(valid_con_ocn_line_features))
						
		# #8ii) Reconstruct gdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_gdu_features, rotation_model, reconstructed_gdu_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_gdu_features, rotation_model, reconstructed_gdu_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_gdu_features = find_final_reconstructed_geometries(reconstructed_gdu_features, pygplates.PolygonOnSphere)
		dict_of_gdu_and_centroid = find_centroid_of_each_reconstructed_gdu_ft(final_reconstructed_gdu_features)
		#dict_of_neighbours = find_neighbours_of_each_reconstructed_gdu_ft(dict_of_gdu_and_centroid,threshold_distance_in_km_for_neighbour)
		dic_of_gdu_members_for_each_sgdu = find_gdu_members_of_each_sgdu_feat(valid_gdu_features, valid_sgdu_features, common_filename_for_temporary_sgdu_and_members_csv, reconstruction_time)
		print('number of sgdu features in dic_of_gdu_members_for_each_sgdu',len(dic_of_gdu_members_for_each_sgdu))
		
		# #8i) Find valid gdu features at reconstruction_time - time_interval
		valid_in_time_gdu_features_in_ynger = [gdu_ft for gdu_ft in gdu_features_collection if (gdu_ft.is_valid_at_time(reconstruction_time-time_interval))]
		valid_gdu_features_ynger = []
		already_included_gdu_fts_ynger = []
		reconstructed_gdu_features_ynger[:] = []
		reconstructed_line_features_ynger[:] = []
		#Find valid gdu features with con-ocn line features
		valid_con_ocn_line_features_ynger = [con_ocn_ft for con_ocn_ft in line_features_collection if con_ocn_ft.is_valid_at_time(reconstruction_time-time_interval)]
		if (reference is not None):
			pygplates.reconstruct(valid_con_ocn_line_features_ynger, rotation_model, reconstructed_line_features_ynger, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_con_ocn_line_features_ynger, rotation_model, reconstructed_line_features_ynger, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_line_features_ynger = find_final_reconstructed_geometries(reconstructed_line_features_ynger, pygplates.PolylineOnSphere)
		for valid_line_ft,valid_line in final_reconstructed_line_features_ynger:
			for gdu_ft in valid_in_time_gdu_features_in_ynger:
				if (valid_line_ft.get_shapefile_attribute('polygid') == gdu_ft.get_shapefile_attribute('POLYGID')):
					if (gdu_ft.get_shapefile_attribute('POLYGID') not in already_included_gdu_fts_ynger):
						valid_gdu_features_ynger.append(gdu_ft)
						already_included_gdu_fts_ynger.append(gdu_ft.get_shapefile_attribute('POLYGID'))
					# if (gdu_ft.get_feature_id() not in already_included_gdu_fts_ynger):
						# valid_gdu_features_ynger.append(gdu_ft)
						#already_included_gdu_fts_ynger.append(gdu_ft.get_feature_id())
				# else:
					# if (gdu_ft.get_reconstruction_plate_id() == valid_line_ft.get_reconstruction_plate_id()):
						# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
							# valid_gdu_features.append(gdu_ft)
							# already_included_gdu_fts.append(gdu_ft.get_feature_id())
		print('len(valid_gdu_features_ynger)',len(valid_gdu_features_ynger))
		print('len(valid_con_ocn_line_features_ynger)',len(valid_con_ocn_line_features_ynger))
		# #8ii) Reconstruct gdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_gdu_features_ynger, rotation_model, reconstructed_gdu_features_ynger, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_gdu_features_ynger, rotation_model, reconstructed_gdu_features_ynger, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_gdu_features_ynger = find_final_reconstructed_geometries(reconstructed_gdu_features_ynger, pygplates.PolygonOnSphere)
		valid_sgdu_features_ynger = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(reconstruction_time-time_interval))]
		dic_of_gdu_members_for_each_sgdu_ynger = find_gdu_members_of_each_sgdu_feat(valid_gdu_features_ynger, valid_sgdu_features_ynger, common_filename_for_temporary_sgdu_and_members_csv, reconstruction_time-time_interval)
		print('number of sgdu features in dic_of_gdu_members_for_each_sgdu_ynger',len(dic_of_gdu_members_for_each_sgdu_ynger))
		reconstructed_sgdu_features[:] = []
		if (reference is not None):
			pygplates.reconstruct(valid_sgdu_features_ynger, rotation_model, reconstructed_sgdu_features, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_sgdu_features_ynger, rotation_model, reconstructed_sgdu_features, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_sgdu_features_ynger = find_final_reconstructed_geometries(reconstructed_sgdu_features, pygplates.PolygonOnSphere)

		# #8iii) Find appropriate pairs of sgdus
		#SGDU,start_div,repGDUID
		polygid_all_valid_line_features = [con_ocn_ft.get_shapefile_attribute('polygid') for con_ocn_ft in valid_con_ocn_line_features]
		array_of_all_valid_polygid = np.array(polygid_all_valid_line_features)
		#print('array_of_all_valid_polygid',array_of_all_valid_polygid)
		already_evaluated_pairs_of_sgdus = []
		#records_of_sgdus_diverging = pairs_of_sgdu_df.loc[abs(pairs_of_sgdu_df['reconstruction_time'] - reconstruction_time) <= 0.500, ['ref_sgdu','other_sgdu']]
		#,reconstruction_time,ref_sgdu,ref_sgduid,other_sgdu,other_sgduid
		records_of_sgdus_diverging = pairs_of_sgdu_df.loc[abs(pairs_of_sgdu_df['reconstruction_time'] - reconstruction_time) <= 0.500, ['ref_sgdu','other_sgdu','ref_sgduid','other_sgduid']]
		start_div = reconstruction_time
		if (len(records_of_sgdus_diverging) > 0):
			for tuple_of_sgdu_repgdu in records_of_sgdus_diverging.itertuples(index = False, name = None):
				child_1, child_2, child_ref_sgduid, child_other_sgduid = tuple_of_sgdu_repgdu
				#use sgdu history to find the sgdu children 
				if (child_1 != child_2):
					key = str(child_1)+'_'+str(child_2)
					rev_key = str(child_2)+'_'+str(child_1)
					print('key',key)
					if (key not in already_evaluated_pairs_of_sgdus and rev_key not in already_evaluated_pairs_of_sgdus):
						already_evaluated_pairs_of_sgdus.append(key)
						#use the two repgduids from the two children 
						child_sgdu_1 = None
						child_sgdu_2 = None
						for valid_ft in valid_sgdu_features:
							if (valid_ft.get_name() == str(child_1) and valid_ft.get_reconstruction_plate_id() == child_ref_sgduid):
								child_sgdu_1 = valid_ft
							elif (valid_ft.get_name() == str(child_2) and valid_ft.get_reconstruction_plate_id() == child_other_sgduid):
								child_sgdu_2 = valid_ft
							if (child_sgdu_1 is not None and child_sgdu_2 is not None):
								break
						if (child_sgdu_1 is None or child_sgdu_2 is None):
							continue #take a different record to process - mistake in manually finding pairs of unrelated SuperGDUs
						child_repgduid_1 = child_sgdu_1.get_reconstruction_plate_id()
						child_repgduid_2 = child_sgdu_2.get_reconstruction_plate_id()
						total_relative_reconstruction_rotation = find_total_relative_reconstruction_rotation_(rotation_model, child_repgduid_1, child_repgduid_2, float(reconstruction_time), reference)
						total_stage_rel_rot_of_1_to_2 = find_stage_relative_reconstruction_rotation_(rotation_model, child_repgduid_1, child_repgduid_2, float(reconstruction_time)+time_interval, float(reconstruction_time), reference)
						total_stage_rel_rot_of_2_to_1 = find_stage_relative_reconstruction_rotation_(rotation_model, child_repgduid_2, child_repgduid_1, float(reconstruction_time)+time_interval, float(reconstruction_time), reference)
						if (total_relative_reconstruction_rotation is not None):
							if (total_relative_reconstruction_rotation.represents_identity_rotation() == False):
								list_of_rift_points = []
								#check whether the pair of sgdus is valid
								child_sgud_1 = []
								child_sgud_2 = []
								non_related = []
								#for yng_sgdu_ft,yng_sgdu in final_reconstructed_sgdu_features_ynger:
								for yng_sgdu_ft,yng_sgdu in final_reconstructed_sgdu_features:
									if (yng_sgdu_ft.get_name() == str(child_1)):
										child_sgud_1.append(yng_sgdu)
									elif (yng_sgdu_ft.get_name() == str(child_2)):
										child_sgud_2.append(yng_sgdu)
									else:
										non_related.append(yng_sgdu)
								reconstructed_gdu_fts_for_sgdu1[:] = []
								reconstructed_gdu_fts_for_sgdu2[:] = []
								prev_reconstructed_gdu_fts_for_sgdu1[:] = []
								prev_reconstructed_gdu_fts_for_sgdu2[:] = []
								#list_of_ordered_pairs_gdu_fts = []
								list_of_already_used_line_fts = []
								gdu_features_for_sgdu1 = dic_of_gdu_members_for_each_sgdu[str(child_1)]
								#gdu_features_for_sgdu1_valid_at_prev_time = [current_gdu_ft_1 for current_gdu_ft_1 in gdu_features_for_sgdu1 if current_gdu_ft_1.is_valid_at_time(reconstruction_time + time_interval)]
								gdu_features_for_sgdu2 = dic_of_gdu_members_for_each_sgdu[str(child_2)]
								#gdu_features_for_sgdu2_valid_at_prev_time = [current_gdu_ft_2 for current_gdu_ft_2 in gdu_features_for_sgdu2 if current_gdu_ft_2.is_valid_at_time(reconstruction_time + time_interval)]
								final_reconstructed_gdu_features_for_sgdu1 = []
								final_reconstructed_gdu_features_for_sgdu2 = []
								prev_final_reconstructed_gdu_features_for_sgdu1 = []
								prev_final_reconstructed_gdu_features_for_sgdu2 = []
								polygid_features_for_sgdu1 = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu1]
								array_for_polygid_ft_sgdu1 = np.array(polygid_features_for_sgdu1)
								#polygid_features_for_sgdu1_at_prev_time = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu1_valid_at_prev_time]
								wanted_gdu_members_for_sgdu1 = np.intersect1d(array_for_polygid_ft_sgdu1,array_of_all_valid_polygid)
								polygid_features_for_sgdu2 = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu2]
								array_for_polygid_ft_sgdu2 = np.array(polygid_features_for_sgdu2)
								wanted_gdu_members_for_sgdu2 = np.intersect1d(array_for_polygid_ft_sgdu2,array_of_all_valid_polygid)
								#polygid_features_for_sgdu2_at_prev_time = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu2_valid_at_prev_time]
								
								#CON-OCN line features that exit at the younger time (i.e. reconstruction_time - time_interval) and invalid at reconstruction_time
								#for child_gdu_ft_1, child_line_gdu_1 in final_reconstructed_line_features_ynger:
								for child_gdu_ft_1, child_line_gdu_1 in final_reconstructed_line_features:
									polygid_for_child_1 = child_gdu_ft_1.get_shapefile_attribute('polygid')
									#if ((polygid_for_child_1 in wanted_gdu_members_for_sgdu1) and (polygid_for_child_1 not in polygid_features_for_sgdu1_at_prev_time)):
									if (polygid_for_child_1 in wanted_gdu_members_for_sgdu1):
										for reconstructed_sgdu_1 in child_sgud_1:
											if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_1,child_line_gdu_1) == 0.00):
												reconstructed_gdu_fts_for_sgdu1.append((child_gdu_ft_1, child_line_gdu_1))
												break
								#for child_gdu_ft_2, child_line_gdu_2 in final_reconstructed_line_features_ynger:
								for child_gdu_ft_2, child_line_gdu_2 in final_reconstructed_line_features:
									polygid_for_child_2 = child_gdu_ft_2.get_shapefile_attribute('polygid')
									#if ((polygid_for_child_2 in polygid_features_for_sgdu2) and (polygid_for_child_2 not in polygid_features_for_sgdu2_at_prev_time)):
									if (polygid_for_child_2 in wanted_gdu_members_for_sgdu2):
										for reconstructed_sgdu_2 in child_sgud_2:
											if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_2,child_line_gdu_2) == 0.00):
												reconstructed_gdu_fts_for_sgdu2.append((child_gdu_ft_2, child_line_gdu_2))
												break
								#print('len(reconstructed_gdu_fts_for_sgdu1)',len(reconstructed_gdu_fts_for_sgdu1))
								#print('len(reconstructed_gdu_fts_for_sgdu2)',len(reconstructed_gdu_fts_for_sgdu2))
								
								#debug
								# if ((child_1 == 71261 and child_2 == 71252) or (child_2 == 71261 and child_1 == 71252)):
									# for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
										# temporary_output_pair_div_line_fts.add(gdu_line_ft_1)
									# for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
										# temporary_output_pair_div_line_fts.add(gdu_line_ft_2)
								
								E_pole,angle_rads = total_relative_reconstruction_rotation.get_euler_pole_and_angle()
								stage_rel_E_pole = None
								if (total_stage_rel_rot_of_1_to_2 is not None):
									if (total_stage_rel_rot_of_1_to_2.represents_identity_rotation() == False):
										stage_rel_E_pole,_ = total_stage_rel_rot_of_1_to_2.get_euler_pole_and_angle()
								elif (total_stage_rel_rot_of_2_to_1 is not None):
									if (total_stage_rel_rot_of_2_to_1.represents_identity_rotation() == False):
										stage_rel_E_pole,_ = total_stage_rel_rot_of_2_to_1.get_euler_pole_and_angle()
								if (stage_rel_E_pole is None):
									stage_rel_E_pole = E_pole
								result_of_tectonic_motion = None
								final_sgdu_1_for_eval = None
								centroid_sgdu_1 = None
								final_sgdu_2_for_eval = None
								centroid_sgdu_2 = None
								for reconstructed_sgdu_1 in child_sgud_1:
									centroid_sgdu_1 = reconstructed_sgdu_1.get_interior_centroid()
									final_sgdu_1_for_eval = reconstructed_sgdu_1
									for reconstructed_sgdu_2 in child_sgud_2:
										centroid_sgdu_2 = reconstructed_sgdu_2.get_interior_centroid()
										final_sgdu_2_for_eval = reconstructed_sgdu_2
										if (total_stage_rel_rot_of_1_to_2 is not None and total_stage_rel_rot_of_1_to_2.represents_identity_rotation() == False):
											result_of_tectonic_motion, dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_2, centroid_sgdu_1, stage_rel_E_pole)
										elif (total_stage_rel_rot_of_2_to_1 is not None and total_stage_rel_rot_of_2_to_1.represents_identity_rotation() == False):
											result_of_tectonic_motion, dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_1, centroid_sgdu_2, stage_rel_E_pole)
										else:
											result_of_tectonic_motion, dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_2, centroid_sgdu_1, stage_rel_E_pole)
										if (result_of_tectonic_motion == 'D'):
											break
										else:
											if (total_stage_rel_rot_of_1_to_2 is not None and total_stage_rel_rot_of_2_to_1 is not None):
												stage_rel_E_pole,_ = total_stage_rel_rot_of_2_to_1.get_euler_pole_and_angle()
												result_of_tectonic_motion, dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_1, centroid_sgdu_2, stage_rel_E_pole)
											else:
												stage_rel_E_pole = E_pole
												result_of_tectonic_motion, dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_2, centroid_sgdu_1, stage_rel_E_pole)
											if (result_of_tectonic_motion == 'D'):
												break
									if (result_of_tectonic_motion == 'D'):
										break
								#print('result_of_tectonic_motion',result_of_tectonic_motion)
								#print('child_repgduid_2',child_repgduid_2,'child_repgduid_1',child_repgduid_1)
								#record all possible values of tectonic-motion to double-check with results when running identify_convergent_boundaries which is processing from present-day to the past
								results_of_all_possible_tectonic_motion.append((reconstruction_time,child_1,child_2,result_of_tectonic_motion))
								smallest_circle_angular_radius_degrees = -1.00
								if (result_of_tectonic_motion == 'D'):
									smallest_circle_angular_radius_degrees = 178.00
								elif (result_of_tectonic_motion == 'T'):
									smallest_circle_angular_radius_degrees = 0.00
								#print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
								while (smallest_circle_angular_radius_degrees > 0.00):
									small_circle_boundary = rotation_utility.create_small_circle_PolylineOnSphere(E_pole,smallest_circle_angular_radius_degrees)
									found_pair_of_line_feats = None
									valid_pair_of_line_fts = True
									#find gdu polygon features for each line feature 
									valid_mid_point_feat = False 
									for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
										
										polylid_of_gdu_line_ft_1 = gdu_line_ft_1.get_shapefile_attribute('polygid')
										#list_of_neighbours_for_polylid_1 = dict_of_neighbours[polylid_of_gdu_line_ft_1]
										for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
											polylid_of_gdu_line_ft_2 = gdu_line_ft_2.get_shapefile_attribute('polygid')
											#if (polylid_of_gdu_line_ft_2 not in list_of_neighbours_for_polylid_1):
											#	continue
											approx_rad_closest_dist_neighbour,closest_point_on_gdu1,_ = pygplates.GeometryOnSphere.distance(line_gdu_1, small_circle_boundary,return_closest_positions = True)
											approx_rad_closest_dist_ref,closest_point_on_gdu2,_= pygplates.GeometryOnSphere.distance(line_gdu_2, small_circle_boundary,return_closest_positions = True)
											# calculate distance by map projection
											# lat1,lon1 = closest_point_on_gdu1.to_lat_lon()
											# lat2,lon2 = closest_point_on_gdu2.to_lat_lon()
											# choosen_epsg_projection = 'ESRI:54009'
											# if (lat1 > 0.00 and lat2 > 0.00):
												# if (abs(lat1 - 90.00) <= 10.00 or abs(lat2 - 90.00) <= 10.00):
													# choosen_epsg_projection = 'EPSG:3995'
											# elif (lat1 < 0.00 and lat2 < 0.00):
												# if (abs(lat1 + 90.00) <= 10.00 or abs(lat2 + 90.00) <= 10.00):
													# choosen_epsg_projection = 'EPSG:3031'
											# wgs84_shapely_point_1 = convert_PointOnSphere_to_Point_in_Shapely(closest_point_on_gdu1)
											# projected_c1 = project_any_Shapely_geometry_in_wgs84_lon_lat_coordinates_to_planar_projection(wgs84_shapely_point_1, choosen_epsg_projection)
											# wgs84_shapely_point_2 = convert_PointOnSphere_to_Point_in_Shapely(closest_point_on_gdu2)
											# projected_c2 = project_any_Shapely_geometry_in_wgs84_lon_lat_coordinates_to_planar_projection(wgs84_shapely_point_2, choosen_epsg_projection)
											# approx_distance_btw_lines_kms = projected_c1.distance(projected_c2)
											
											#calculate distance by haversine
											lat1,lon1 = closest_point_on_gdu1.to_lat_lon()
											lat2,lon2 = closest_point_on_gdu2.to_lat_lon()
											approx_distance_btw_lines_kms = calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2)
											
											# #debug
											# print('gdu_line_ft_1.get_shapefile_attribute(POLYLID)',gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
											# print('gdu_line_ft_2.get_shapefile_attribute(POLYLID)',gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
											# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
												# print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
												# print('approx_rad_closest_dist_neighbour',approx_rad_closest_dist_neighbour)
												# print('approx_rad_closest_dist_ref',approx_rad_closest_dist_ref)
												#exit()
											# else:
												# print ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274'))
												# print ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938'))
												
											# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12009_13906_1773' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17300_14793_2185') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '12009_13906_1773' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '17300_14793_2185')):
												# gdu_line_ft_1.set_description(gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
												# gdu_line_ft_1.set_name(key)
												# gdu_line_ft_2.set_description(gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
												# gdu_line_ft_2.set_name(key)
												#temporary_output_pair_div_line_fts.add(gdu_line_ft_1)
												#temporary_output_pair_div_line_fts.add(gdu_line_ft_2)
												# print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
												# print('approx_rad_closest_dist_neighbour',approx_rad_closest_dist_neighbour)
												# print('approx_rad_closest_dist_ref',approx_rad_closest_dist_ref)
											#debug
											#if (parent_div_sgdu == 70591 and ((child_1 == 70638 and child_2 == 70637) or (child_1 == 70637 and child_2 == 70638))):
											#	print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
											# if (key == '69184_71420'):
												# print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
												# print('approx_rad_closest_dist_neighbour',approx_rad_closest_dist_neighbour)
												# print('approx_rad_closest_dist_ref',approx_rad_closest_dist_ref)
											#approx_distance_btw_lines_kms = approx_distance_btw_lines*pygplates.Earth.mean_radius_in_kms
											
											if (approx_rad_closest_dist_neighbour == 0.000 and approx_rad_closest_dist_ref == 0.000): 
												#debug
												# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
													# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
												# if ((approx_distance_btw_lines_kms <= 10000.00) or (gdu_line_ft_1.is_valid_at_time(reconstruction_time + time_interval)==False) or (gdu_line_ft_2.is_valid_at_time(reconstruction_time + time_interval)==False)):
													# valid_pair_of_line_fts = True
												if (valid_pair_of_line_fts == True):
													#find gdu polygon features for each line feature 
													temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = None,None
													temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = None,None
													for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
														if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_1.get_shapefile_attribute('polygid')):
															temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = temp_gdu_ft,temp_reconstruct_gdu_polygon
															break
													for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
														if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_2.get_shapefile_attribute('polygid')):
															temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = temp_gdu_ft,temp_reconstruct_gdu_polygon
															break
													distance_btw_two_gdus = pygplates.GeometryOnSphere.distance(temp_reconstruct_gdu_polygon_1,temp_reconstruct_gdu_polygon_2)
													if (distance_btw_two_gdus > 0.00):
														valid_pair_of_line_fts = False
													if (valid_pair_of_line_fts == False):
														temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
														valid_pair_of_line_fts = True
														for random_sgdu in non_related:
															if (random_sgdu.partition(temporary_PolylineOnSphere) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
																valid_pair_of_line_fts = False
																break
													#debug
													# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
														# print('approx_distance_btw_lines_kms',approx_distance_btw_lines_kms)
														# print('approx_rad_closest_dist_neighbour',approx_rad_closest_dist_neighbour)
														# print('approx_rad_closest_dist_ref',approx_rad_closest_dist_ref)
														# print('distance_btw_two_gdus',distance_btw_two_gdus)
														# print('valid_pair_of_line_fts',valid_pair_of_line_fts)
														# #exit()
													# if (key == '69184_69741'):
														# print('valid_pair_of_line_fts',valid_pair_of_line_fts)
														
													if (valid_pair_of_line_fts == True):
														if (found_pair_of_line_feats is None):
															#have to double check whether the point feature fall within both superGDU or just one superGDU
															approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
															found_in_sgdu_1 = False
															found_in_sgdu_2 = False
															for temp_sgdu_1 in child_sgud_1:
																if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																	found_in_sgdu_1 = True
																	break
															for temp_sgdu_2 in child_sgud_2:
																if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																	found_in_sgdu_2 = True
																	break
															if (distance_btw_two_gdus == 0.00):
																if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																	valid_mid_point_feat = True
																	#debug
																	# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
																		# print('valid_mid_point_feat',valid_mid_point_feat)
																	break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																else:
																	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
															else:
																if (found_in_sgdu_1 == True or found_in_sgdu_2 == True):
																	valid_mid_point_feat = False
																found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
															# if (gdu_line_ft_1.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																# list_of_already_used_line_fts.append(gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
															# if (gdu_line_ft_2.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																# list_of_already_used_line_fts.append(gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
														else:
															#have to double check whether the point feature fall within both superGDU or just one superGDU
															approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
															found_in_sgdu_1 = False
															found_in_sgdu_2 = False
															for temp_sgdu_1 in child_sgud_1:
																if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																	found_in_sgdu_1 = True
																	break
															for temp_sgdu_2 in child_sgud_2:
																if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																	found_in_sgdu_2 = True
																	break
															if (distance_btw_two_gdus == 0.00):
																if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																	valid_mid_point_feat = True
																	break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																# else:#maybe we do not need this
																	# prev_approx_distance_btw_line_kmns = found_pair_of_line_feats[4]
																	# if (prev_approx_distance_btw_line_kmns > approx_distance_btw_lines_kms or valid_mid_point_feat == False):
																		# if (gdu_line_ft_1.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts and gdu_line_ft_2.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																			# found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																else:
																	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
															else:
																if (found_in_sgdu_1 == True or found_in_sgdu_2 == True):
																	valid_mid_point_feat = False
																if (valid_mid_point_feat == True):
																	prev_approx_distance_btw_line_kmns = found_pair_of_line_feats[4]
																	if (prev_approx_distance_btw_line_kmns > approx_distance_btw_lines_kms or valid_mid_point_feat == False):
																		if (gdu_line_ft_1.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts and gdu_line_ft_2.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																			found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																	# list_of_already_used_line_fts.append(gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
																	# list_of_already_used_line_fts.append(gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
													#debug
													# if (key == '69184_69741'):
														# print("valid_pair_of_line_fts",valid_pair_of_line_fts)
														# print("valid_mid_point_feat",valid_mid_point_feat)
												#debug
												# if (smallest_circle_angular_radius_degrees == 73.00 and ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945'))):
													# print("smallest_circle_angular_radius_degrees == 73.00 12404_11454_2945 and 17023_14194_2053")
												
										#NEW---
										if (valid_mid_point_feat == True):
											#debug
											# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
												# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
													# print('before')
													# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
													# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
											break # break out of the for-loop of for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1
										
									if (found_pair_of_line_feats is not None):
										#debug
										# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
											# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
											# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
											# print('valid_mid_point_feat',valid_mid_point_feat)
										
										gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2 = found_pair_of_line_feats
										temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
										#debug
										# if (key == '69184_69741'):
											# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
										
										approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
										if (approx_mid_point == closest_point_on_gdu1 or approx_mid_point == closest_point_on_gdu2):
											temp_list_of_closest_point_on_gdu1 = dict_of_gdu_and_centroid[gdu_line_ft_1.get_shapefile_attribute('polygid')]
											closest_point_on_gdu1 = temp_list_of_closest_point_on_gdu1[0][0]
											temp_list_of_closest_point_on_gdu2 = dict_of_gdu_and_centroid[gdu_line_ft_2.get_shapefile_attribute('polygid')]
											closest_point_on_gdu2 = temp_list_of_closest_point_on_gdu2[0][0]
											if (valid_mid_point_feat == False):
												valid_mid_point_feat = True
												
										if (valid_mid_point_feat == False):
											if (pygplates.GeometryOnSphere.distance(line_gdu_1,line_gdu_2) == 0.00):
												valid_mid_point_feat = True
												
										#NEW - check whether approx_mid_point positioned within any SGDUs
										if (valid_mid_point_feat == False):
											are_lines_similar = are_two_PolylineOnSphere_similar(line_gdu_1,line_gdu_2)
											if (are_lines_similar == True):
												valid_mid_point_feat = True
											elif (valid_mid_point_feat == False):
												#temporarily set valid_mid_point_feat to True
												valid_mid_point_feat = True
												for random_sgdu in non_related:
													if (random_sgdu.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
														valid_mid_point_feat = False
														break
												if (valid_mid_point_feat == True):
													for reconstructed_sgdu_2 in child_sgud_2:
														if (reconstructed_sgdu_2.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
															valid_mid_point_feat = False
															break
													# # #debug
													# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
														# print('valid_mid_point_feat at 1335',valid_mid_point_feat)
													# # # #debug
													# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
														# print('valid_mid_point_feat at 1338',valid_mid_point_feat)
													
												if (valid_mid_point_feat == True):
													for reconstructed_sgdu_1 in child_sgud_1:
														if (reconstructed_sgdu_1.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
															valid_mid_point_feat = False
															break
													# # #debug
													# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
														# print('valid_mid_point_feat at 1347',valid_mid_point_feat)
										# if (valid_mid_point_feat == True):
											# if (key == '69184_69741'):
												# print('valid_mid_point_feat',valid_mid_point_feat)
												# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
											
											#create an arc
											temporary_GreatCircleArc = pygplates.GreatCircleArc(approx_mid_point,E_pole)
											normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
											left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, approx_mid_point, closest_point_on_gdu1, closest_point_on_gdu2, gdu_line_ft_1.get_reconstruction_plate_id(), gdu_line_ft_2.get_reconstruction_plate_id())
											list_of_rift_points.append(approx_mid_point)
											#create point feature
											#name = 'R'+str(child_1)+'_'+str(child_2)+'_'+str(smallest_circle_angular_radius_degrees)
											name = 'R'+key+'_'+str(smallest_circle_angular_radius_degrees)
											rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, approx_mid_point, name = name, valid_time = (reconstruction_time,0.00))
											if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
												rift_point_ft.set_left_plate(gdu_line_ft_1.get_reconstruction_plate_id())
												rift_point_ft.set_right_plate(gdu_line_ft_2.get_reconstruction_plate_id())
											else:
												rift_point_ft.set_left_plate(left_gduid)
												rift_point_ft.set_right_plate(right_gduid)
											rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
											rift_point_ft.set_description(str(smallest_circle_angular_radius_degrees))
											if (reference is None):
												pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
											else:
												pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
											output_rift_point_features.add(rift_point_ft)
											if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
												unsure_topology_for_MOR_fts.add(rift_point_ft)
											if ((left_gduid == gdu_line_ft_1.get_reconstruction_plate_id() and right_gduid == gdu_line_ft_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
												list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2))
											else:
												list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
										
											#create pair of line features associated with the rift point ft
											_,con_ocn_to_time = gdu_line_ft_1.get_valid_time()
											line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_1,name=gdu_line_ft_1.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
											line_feature_1.set_reconstruction_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
											line_feature_1.set_conjugate_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
											line_feature_1.set_description('divergent_margin')
											_,con_ocn_to_time = gdu_line_ft_2.get_valid_time()
											line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_2,name=gdu_line_ft_2.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
											line_feature_2.set_reconstruction_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
											line_feature_2.set_conjugate_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
											line_feature_2.set_description('divergent_margin')
											if (reference is None):
												pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time)
											else:
												pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time,reference)
											#output_diverging_line_features.add(line_feature_1)
											#output_diverging_line_features.add(line_feature_2)
											previous_diverging_line_feats.append((line_feature_1,line_feature_2,'D',reconstruction_time,pygplates.GeometryOnSphere.distance(line_gdu_1.get_centroid(),line_gdu_2.get_centroid())))
									else:
										#try a higher resolution of smallest_circle_angular_radius_degrees
										temp_small_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees
										#prev_small_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees + 1.000
										prev_small_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees + 0.500
										found_pair_of_line_feats = None
										while (temp_small_circle_angular_radius_degrees < prev_small_circle_angular_radius_degrees):
											temp_small_circle_angular_radius_degrees = temp_small_circle_angular_radius_degrees + 0.200
											small_circle_boundary = rotation_utility.create_small_circle_PolylineOnSphere(E_pole,temp_small_circle_angular_radius_degrees)
											valid_mid_point_feat = False 
											for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
												polylid_of_gdu_line_ft_1 = gdu_line_ft_1.get_shapefile_attribute('polygid')
												#list_of_neighbours_for_polylid_1 = dict_of_neighbours[polylid_of_gdu_line_ft_1]
												for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
													polylid_of_gdu_line_ft_2 = gdu_line_ft_2.get_shapefile_attribute('polygid')
													#if (polylid_of_gdu_line_ft_2 not in list_of_neighbours_for_polylid_1):
													#	continue
													approx_rad_closest_dist_neighbour, closest_point_on_gdu1, _ = pygplates.GeometryOnSphere.distance(line_gdu_1, small_circle_boundary,return_closest_positions = True)
													approx_rad_closest_dist_ref, closest_point_on_gdu2, _= pygplates.GeometryOnSphere.distance(line_gdu_2, small_circle_boundary,return_closest_positions = True)
													#calculate distance by haversine
													lat1,lon1 = closest_point_on_gdu1.to_lat_lon()
													lat2,lon2 = closest_point_on_gdu2.to_lat_lon()
													approx_distance_btw_lines_kms = calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2)
													if (approx_rad_closest_dist_neighbour == 0.000 and approx_rad_closest_dist_ref == 0.000): 
														# if ((approx_distance_btw_lines_kms <= 10000.00) or (gdu_line_ft_1.is_valid_at_time(reconstruction_time + time_interval)==False) or (gdu_line_ft_2.is_valid_at_time(reconstruction_time + time_interval)==False)):
															# valid_pair_of_line_fts = True
														if (valid_pair_of_line_fts == True):
															#find gdu polygon features for each line feature 
															temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = None,None
															temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = None,None
															for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
																if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_1.get_shapefile_attribute('polygid')):
																	temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = temp_gdu_ft,temp_reconstruct_gdu_polygon
																	break
															for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
																if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_2.get_shapefile_attribute('polygid')):
																	temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = temp_gdu_ft,temp_reconstruct_gdu_polygon
																	break
															distance_btw_two_gdus = pygplates.GeometryOnSphere.distance(temp_reconstruct_gdu_polygon_1,temp_reconstruct_gdu_polygon_2)
															if (distance_btw_two_gdus > 0.00):
																valid_pair_of_line_fts = False
															if (valid_pair_of_line_fts == False):
																temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
																valid_pair_of_line_fts = True
																for random_sgdu in non_related:
																	if (random_sgdu.partition(temporary_PolylineOnSphere) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
																		valid_pair_of_line_fts = False
																		break
															if (valid_pair_of_line_fts == True):
																if (found_pair_of_line_feats is None):
																	#have to double check whether the point feature fall within both superGDU or just one superGDU
																	approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
																	found_in_sgdu_1 = False
																	found_in_sgdu_2 = False
																	for temp_sgdu_1 in child_sgud_1:
																		if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																			found_in_sgdu_1 = True
																			break
																	for temp_sgdu_2 in child_sgud_2:
																		if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																			found_in_sgdu_2 = True
																			break
																	
																	if (distance_btw_two_gdus == 0.00):
																		if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																			found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																			valid_mid_point_feat = True
																			break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																		else:
																			found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																			valid_mid_point_feat = False
																	else:
																		if (found_in_sgdu_1 == True or found_in_sgdu_2 == True):
																			valid_mid_point_feat = False
																		found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																else:
																	approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
																	found_in_sgdu_1 = False
																	found_in_sgdu_2 = False
																	for temp_sgdu_1 in child_sgud_1:
																		if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																			found_in_sgdu_1 = True
																			break
																	for temp_sgdu_2 in child_sgud_2:
																		if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																			found_in_sgdu_2 = True
																			break
																	if (distance_btw_two_gdus == 0.00):
																		if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																			found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																			valid_mid_point_feat = True
																			break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																		#else:#maybe I don't need this
																		#	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																	else:
																		#have to double check whether the point feature fall within both superGDU or just one superGDU
																		if (found_in_sgdu_1 == True or found_in_sgdu_2 == True):
																			found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																			valid_mid_point_feat = False
																			break
																		if (valid_mid_point_feat == True):
																			prev_approx_distance_btw_line_kmns = found_pair_of_line_feats[4]
																			if (prev_approx_distance_btw_line_kmns > approx_distance_btw_lines_kms or valid_mid_point_feat == False):
																				if (gdu_line_ft_1.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts and gdu_line_ft_2.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																					found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
																					# list_of_already_used_line_fts.append(gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
																					# list_of_already_used_line_fts.append(gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
												if (valid_mid_point_feat == True):
													# #debug
													# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
														# print('before')
														# print('temp_small_circle_angular_radius_degrees',temp_small_circle_angular_radius_degrees)
														# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
													break
											if (found_pair_of_line_feats is not None and valid_mid_point_feat == True):
												break
										if (found_pair_of_line_feats is not None):
											valid_pair_of_line_fts = True
											gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2 = found_pair_of_line_feats
											temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
											#debug
											# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
												# print('temp_small_circle_angular_radius_degrees',temp_small_circle_angular_radius_degrees)
												# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
												# print('valid_mid_point_feat',valid_mid_point_feat)
											# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
												# print('found expected_pair_divergent_line_features')
												# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),' and ', gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
												#find the mid_point between two points 
											approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
											#valid_mid_point_feat = False --- already initalized
											if (approx_mid_point == closest_point_on_gdu1 or approx_mid_point == closest_point_on_gdu2):
												temp_list_of_closest_point_on_gdu1 = dict_of_gdu_and_centroid[gdu_line_ft_1.get_shapefile_attribute('polygid')]
												closest_point_on_gdu1 = temp_list_of_closest_point_on_gdu1[0][0]
												temp_list_of_closest_point_on_gdu2 = dict_of_gdu_and_centroid[gdu_line_ft_2.get_shapefile_attribute('polygid')]
												closest_point_on_gdu2 = temp_list_of_closest_point_on_gdu2[0][0]
												if (valid_mid_point_feat == False):
													valid_mid_point_feat = True
											if (valid_mid_point_feat == False):
												if (pygplates.GeometryOnSphere.distance(line_gdu_1,line_gdu_2) == 0.00):
													valid_mid_point_feat = True
												
											if (valid_mid_point_feat == True):
												#create an arc
												list_of_rift_points.append(approx_mid_point)
												temporary_GreatCircleArc = pygplates.GreatCircleArc(approx_mid_point,E_pole)
												normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
												left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, approx_mid_point, closest_point_on_gdu1, closest_point_on_gdu2, gdu_line_ft_1.get_reconstruction_plate_id(), gdu_line_ft_2.get_reconstruction_plate_id())
												#create point feature
												#name = 'R'+str(child_1)+'_'+str(child_2)+'_'+str(smallest_circle_angular_radius_degrees)
												name = 'R'+key+'_'+str(smallest_circle_angular_radius_degrees)
												rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, approx_mid_point, name = name, valid_time = (reconstruction_time,0.00))
												if ((left_gduid == right_gduid)or (left_gduid is None) or (right_gduid is None)):
													rift_point_ft.set_left_plate(gdu_line_ft_1.get_reconstruction_plate_id())
													rift_point_ft.set_right_plate(gdu_line_ft_2.get_reconstruction_plate_id())
												else:
													rift_point_ft.set_left_plate(left_gduid)
													rift_point_ft.set_right_plate(right_gduid)
												rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
												rift_point_ft.set_description(str(smallest_circle_angular_radius_degrees))
												if (reference is None):
													pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
												else:
													pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
												output_rift_point_features.add(rift_point_ft)
												if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
													unsure_topology_for_MOR_fts.add(rift_point_ft)
												if ((left_gduid == gdu_line_ft_1.get_reconstruction_plate_id() and right_gduid == gdu_line_ft_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
													list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2))
												else:
													list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
												#create pair of line features associated with the rift point ft
												_,con_ocn_to_time = gdu_line_ft_1.get_valid_time()
												line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_1,name=gdu_line_ft_1.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
												line_feature_1.set_reconstruction_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
												line_feature_1.set_conjugate_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
												line_feature_1.set_description('divergent_margin')
															
												_,con_ocn_to_time = gdu_line_ft_2.get_valid_time()
												line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_2,name=gdu_line_ft_2.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
												line_feature_2.set_reconstruction_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
												line_feature_2.set_conjugate_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
												line_feature_2.set_description('divergent_margin')
												if (reference is None):
													pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time)
												else:
													pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time,reference)
												#output_diverging_line_features.add(line_feature_1)
												#output_diverging_line_features.add(line_feature_2)
												previous_diverging_line_feats.append((line_feature_1,line_feature_2,'D',reconstruction_time,pygplates.GeometryOnSphere.distance(line_gdu_1.get_centroid(),line_gdu_2.get_centroid())))
									#smallest_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees - 1.00
									smallest_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees - 0.50
								#create temporary MOR features from list_of_rift_points
								if (len(list_of_rift_points) > 0):
									list_of_distinct_rift_points = []
									for temporary_rift_pt in list_of_rift_points:
										if (len(list_of_distinct_rift_points) == 0):
											list_of_distinct_rift_points.append(temporary_rift_pt)
										else:
											last_rift_pt = list_of_distinct_rift_points[-1]
											if (last_rift_pt != temporary_rift_pt):
												list_of_distinct_rift_points.append(temporary_rift_pt)
									if (len(list_of_distinct_rift_points) >= 2):
										temporary_MOR_line = pygplates.PolylineOnSphere(list_of_rift_points)
										temporary_MOR_line_feat = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_mid_ocean_ridge,temporary_MOR_line,name='R'+key,valid_time = (reconstruction_time,0.00))
										mid_point_of_temporary_MOR_line_feat = temporary_MOR_line.get_centroid()
										#create an arc
										temporary_GreatCircleArc = pygplates.GreatCircleArc(mid_point_of_temporary_MOR_line_feat,E_pole)
										normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
										#rep_point_of_sgdu_1 = child_sgud_1[0].get_interior_centroid() 
										#rep_point_of_sgdu_2 = child_sgud_2[0].get_interior_centroid()
										#MOR_left_gduid, MOR_right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, mid_point_of_temporary_MOR_line_feat, rep_point_of_sgdu_1, rep_point_of_sgdu_2, child_repgduid_1, child_repgduid_2)
										#temporarily set left and right 
										MOR_left_gduid, MOR_right_gduid = child_repgduid_1,child_repgduid_2
										temporary_MOR_line_feat.set_left_plate(MOR_left_gduid)
										temporary_MOR_line_feat.set_right_plate(MOR_right_gduid)
										temporary_MOR_line_feat.set_reconstruction_method('HalfStageRotationVersion2')
										if (reference is None):
											pygplates.reverse_reconstruct(temporary_MOR_line_feat,rotation_model,reconstruction_time)
										else:
											pygplates.reverse_reconstruct(temporary_MOR_line_feat,rotation_model,reconstruction_time,reference)
										output_temporary_MOR_line_feats.append(temporary_MOR_line_feat)
								# else:
									# if (result_of_tectonic_motion == 'D'):
										# #transform-divergence so none of the small circle cuts line features of two diverging SuperGDUs
										# smallest_circle_angular_radius_degrees = 0.00
										# result_of_tectonic_motion = 'T'
								# if (smallest_circle_angular_radius_degrees == -1.00 or smallest_circle_angular_radius_degrees == 0.00):#RESULT into too many transform line features
									# for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
										# polylid_of_gdu_line_ft_1 = gdu_line_ft_1.get_shapefile_attribute('polygid')
										# closest_point_on_gdu1 = None
										# for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
											# closest_point_on_gdu2 = None
											# polylid_of_gdu_line_ft_2 = gdu_line_ft_2.get_shapefile_attribute('polygid')
											# approx_rad_closest_dist_neighbour,closest_point_on_gdu1,_ = pygplates.GeometryOnSphere.distance(line_gdu_1, small_circle_boundary,return_closest_positions = True)
											# approx_rad_closest_dist_ref,closest_point_on_gdu2,_= pygplates.GeometryOnSphere.distance(line_gdu_2, small_circle_boundary,return_closest_positions = True)
											# valid_pair_of_line_fts = True
											# #calculate distance by haversine
											# lat1,lon1 = closest_point_on_gdu1.to_lat_lon()
											# lat2,lon2 = closest_point_on_gdu2.to_lat_lon()
											# approx_distance_btw_lines_kms = calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2)
											
											# if (approx_rad_closest_dist_neighbour == 0.000 and approx_rad_closest_dist_ref == 0.000): 
												
												# #find gdu polygon features for each line feature 
												# temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = None,None
												# temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = None,None
												# for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
													# if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_1.get_shapefile_attribute('polygid')):
														# temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = temp_gdu_ft,temp_reconstruct_gdu_polygon
														# break
												# for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
													# if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_2.get_shapefile_attribute('polygid')):
														# temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = temp_gdu_ft,temp_reconstruct_gdu_polygon
														# break
												# distance_btw_two_gdus = pygplates.GeometryOnSphere.distance(temp_reconstruct_gdu_polygon_1,temp_reconstruct_gdu_polygon_2)
												# if (distance_btw_two_gdus > 0.00):
													# valid_pair_of_line_fts = False
												# if (valid_pair_of_line_fts == False):
													# temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
													# valid_pair_of_line_fts = True
													# for random_sgdu in non_related:
														# if (random_sgdu.partition(temporary_PolylineOnSphere) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
															# valid_pair_of_line_fts = False
															# break
											# else:
												# if (approx_distance_btw_lines_kms <= 10000.00):
													# temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
													# valid_pair_of_line_fts = True
													# for random_sgdu in non_related:
														# if (random_sgdu.partition(temporary_PolylineOnSphere) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
															# valid_pair_of_line_fts = False
															# break
											# if (valid_pair_of_line_fts == True):
												# #find the mid_point between two points 
												# approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
												# #create an arc
												# temporary_GreatCircleArc = pygplates.GreatCircleArc(approx_mid_point,E_pole)
												# normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
												# left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, approx_mid_point, closest_point_on_gdu1, closest_point_on_gdu2, child_repgduid_1, child_repgduid_2)
												# parent_gdu_ft_1 = gdu_line_ft_1
												# parent_line_gdu_1 = line_gdu_1
												# parent_gdu_ft_2 = gdu_line_ft_2
												# parent_line_gdu_2 = line_gdu_2
												
												# if (smallest_circle_angular_radius_degrees == -1.00):
													# # #create point feature
													# name = 'C'+str(child_1)+'_'+str(child_2)+'_'+parent_gdu_ft_1.get_shapefile_attribute('POLYLID')+'_'+parent_gdu_ft_2.get_shapefile_attribute('POLYLID')
													# if (left_gduid == parent_gdu_ft_1.get_reconstruction_plate_id() and right_gduid == parent_gdu_ft_2.get_reconstruction_plate_id()):
														# list_of_ordered_non_rift_pairs_gdu_fts.append((reconstruction_time,name, -1, parent_gdu_ft_1.get_shapefile_attribute('POLYLID'), parent_gdu_ft_1.get_reconstruction_plate_id(), child_repgduid_1, parent_gdu_ft_2.get_shapefile_attribute('POLYLID'), parent_gdu_ft_2.get_reconstruction_plate_id(), child_repgduid_2))
													# else:
														# list_of_ordered_non_rift_pairs_gdu_fts.append((reconstruction_time,name, -1, parent_gdu_ft_2.get_shapefile_attribute('POLYLID'), parent_gdu_ft_2.get_reconstruction_plate_id(), child_repgduid_2, parent_gdu_ft_1.get_shapefile_attribute('POLYLID'), parent_gdu_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
													# #create pair of line features associated with the rift point ft
													# begin_age_line_ft_1,_ = parent_gdu_ft_1.get_valid_time()
													# line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,parent_line_gdu_1,name=parent_gdu_ft_1.get_shapefile_attribute('POLYLID'),valid_time = (begin_age_line_ft_1,reconstruction_time))
													# line_feature_1.set_reconstruction_plate_id(parent_gdu_ft_1.get_reconstruction_plate_id())
													# line_feature_1.set_conjugate_plate_id(parent_gdu_ft_2.get_reconstruction_plate_id())
													# line_feature_1.set_description('convergent_margin')
													
													# begin_age_line_ft_2,_ = parent_gdu_ft_2.get_valid_time()
													# line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,parent_line_gdu_2,name=parent_gdu_ft_2.get_shapefile_attribute('POLYLID'),valid_time = (begin_age_line_ft_2,reconstruction_time))
													# line_feature_2.set_reconstruction_plate_id(parent_gdu_ft_2.get_reconstruction_plate_id())
													# line_feature_2.set_conjugate_plate_id(parent_gdu_ft_1.get_reconstruction_plate_id())
													# line_feature_2.set_description('convergent_margin')
													
													# if (begin_age_line_ft_1 > begin_age_line_ft_2):
														# line_feature_1.set_valid_time(begin_age_line_ft_2,reconstruction_time)
														# line_feature_2.set_valid_time(begin_age_line_ft_2,reconstruction_time)
													# else:
														# line_feature_1.set_valid_time(begin_age_line_ft_1,reconstruction_time)
														# line_feature_2.set_valid_time(begin_age_line_ft_1,reconstruction_time)

													# if (reference is None):
														# pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time)
													# else:
														# pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time,reference)
													# previous_diverging_line_feats.append((line_feature_1,line_feature_2,'C',reconstruction_time,pygplates.GeometryOnSphere.distance(parent_line_gdu_1.get_centroid(),parent_line_gdu_2.get_centroid())))
												# elif (smallest_circle_angular_radius_degrees == 0.00):
													# # #create point feature
													# name = 'T'+str(child_1)+'_'+str(child_2)+'_'+parent_gdu_ft_1.get_shapefile_attribute('POLYLID')+'_'+parent_gdu_ft_2.get_shapefile_attribute('POLYLID')
													# if (left_gduid == parent_gdu_ft_1.get_reconstruction_plate_id() and right_gduid == parent_gdu_ft_2.get_reconstruction_plate_id()):
														# list_of_ordered_non_rift_pairs_gdu_fts.append((reconstruction_time,name, -1, parent_gdu_ft_1.get_shapefile_attribute('POLYLID'), parent_gdu_ft_1.get_reconstruction_plate_id(), child_repgduid_1, parent_gdu_ft_2.get_shapefile_attribute('POLYLID'), parent_gdu_ft_2.get_reconstruction_plate_id(), child_repgduid_2))
													# else:
														# list_of_ordered_non_rift_pairs_gdu_fts.append((reconstruction_time,name, -1, parent_gdu_ft_2.get_shapefile_attribute('POLYLID'), parent_gdu_ft_2.get_reconstruction_plate_id(), child_repgduid_2, parent_gdu_ft_1.get_shapefile_attribute('POLYLID'), parent_gdu_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
													# #create pair of line features associated with the rift point ft
													# begin_age_line_ft_1,_ = parent_gdu_ft_1.get_valid_time()
													# line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary, parent_line_gdu_1, name=parent_gdu_ft_1.get_shapefile_attribute('POLYLID'), valid_time = (begin_age_line_ft_1,reconstruction_time))
													# line_feature_1.set_reconstruction_plate_id(parent_gdu_ft_1.get_reconstruction_plate_id())
													# line_feature_1.set_conjugate_plate_id(parent_gdu_ft_2.get_reconstruction_plate_id())
													# line_feature_1.set_description('transform_fault')
													
													# begin_age_line_ft_2,_ = parent_gdu_ft_2.get_valid_time()
													# line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary, parent_line_gdu_2, name=parent_gdu_ft_2.get_shapefile_attribute('POLYLID'), valid_time = (begin_age_line_ft_2,reconstruction_time))
													# line_feature_2.set_reconstruction_plate_id(parent_gdu_ft_2.get_reconstruction_plate_id())
													# line_feature_2.set_conjugate_plate_id(parent_gdu_ft_1.get_reconstruction_plate_id())
													# line_feature_2.set_description('transform_fault')
													
													# if (begin_age_line_ft_1 > begin_age_line_ft_2):
														# line_feature_1.set_valid_time(begin_age_line_ft_2,reconstruction_time)
														# line_feature_2.set_valid_time(begin_age_line_ft_2,reconstruction_time)
													# else:
														# line_feature_1.set_valid_time(begin_age_line_ft_1,reconstruction_time)
														# line_feature_2.set_valid_time(begin_age_line_ft_1,reconstruction_time)

													# if (reference is None):
														# pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time)
													# else:
														# pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time,reference)
													# previous_diverging_line_feats.append((line_feature_1,line_feature_2,'T',reconstruction_time,pygplates.GeometryOnSphere.distance(parent_line_gdu_1.get_centroid(),parent_line_gdu_2.get_centroid())))

		#check the end_time of diverging line features
		#list_of_already_evaluated_pairs = []
		#debug
		#print('number of features in previous_diverging_line_feats before update',len(previous_diverging_line_feats))
		if (len(previous_diverging_line_feats) > 0):
			#;from_time;to_time;SGDUID;GDUID;buffer_distance_km;repGDUID
			temporary_sgdu_and_member_csv_at_time = common_filename_for_temporary_sgdu_and_members_csv.format(time = str(reconstruction_time))
			temp_sgdu_and_gdu_df = pd.read_csv(temporary_sgdu_and_member_csv_at_time, delimiter = ';', header = 0)
			remaining_diverging_line_feats = []
			recorded_distance = -1.00
			if (len(dic_prev_div_line_feats) == 0):
				for line_feature_1,line_feature_2,prev_motion,prev_begin_age,prev_distance in previous_diverging_line_feats:
					pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
					rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
					if (pair_polylids not in dic_prev_div_line_feats and rev_pair_of_polylids not in dic_prev_div_line_feats):
						dic_prev_div_line_feats[pair_polylids] = {'line_feats':(line_feature_1,line_feature_2),'prev_motion':prev_motion, 'age':prev_begin_age, 'dist':prev_distance}
			else:
				for line_feature_1,line_feature_2,prev_motion,prev_begin_age,prev_distance in previous_diverging_line_feats:
					pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
					rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
					if (pair_polylids in dic_prev_div_line_feats):
						dic_prev_div_line_feats[pair_polylids]['prev_motion'] = prev_motion
						dic_prev_div_line_feats[pair_polylids]['age'] = prev_begin_age
						current_line_feature_1,current_line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
						if (current_line_feature_1.is_valid_at_time(reconstruction_time) == False or current_line_feature_2.is_valid_at_time(reconstruction_time) == False):
							output_diverging_line_features.add(current_line_feature_1)
							output_diverging_line_features.add(current_line_feature_2)
							output_begin_age,output_end_age = current_line_feature_1.get_valid_time()
							pairs_of_kin_line_fts.append((output_begin_age,output_end_age,current_line_feature_1.get_description(),current_line_feature_1.get_name(),current_line_feature_2.get_name(),current_line_feature_1.get_feature_id().get_string(),current_line_feature_2.get_feature_id().get_string()))
						if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
							dic_prev_div_line_feats[pair_polylids]['line_feats'] = (line_feature_1,line_feature_2)
						else:
							del dic_prev_div_line_feats[pair_polylids]
					elif (rev_pair_of_polylids in dic_prev_div_line_feats):
						dic_prev_div_line_feats[rev_pair_of_polylids]['prev_motion'] = prev_motion
						dic_prev_div_line_feats[rev_pair_of_polylids]['age'] = prev_begin_age
						current_line_feature_1,current_line_feature_2 = dic_prev_div_line_feats[rev_pair_of_polylids]['line_feats']
						if (current_line_feature_1.is_valid_at_time(reconstruction_time) == False or current_line_feature_2.is_valid_at_time(reconstruction_time) == False):
							output_diverging_line_features.add(current_line_feature_1)
							output_diverging_line_features.add(current_line_feature_2)
							output_begin_age,output_end_age = current_line_feature_1.get_valid_time()
							pairs_of_kin_line_fts.append((output_begin_age,output_end_age,current_line_feature_1.get_description(),current_line_feature_1.get_name(),current_line_feature_2.get_name(),current_line_feature_1.get_feature_id().get_string(),current_line_feature_2.get_feature_id().get_string()))
						if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
							dic_prev_div_line_feats[rev_pair_of_polylids]['line_feats'] = (line_feature_1,line_feature_2)
						else:
							del dic_prev_div_line_feats[rev_pair_of_polylids]
					else:
						if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
							dic_prev_div_line_feats[pair_polylids] = {'line_feats':(line_feature_1,line_feature_2),'prev_motion':prev_motion, 'age':prev_begin_age, 'dist':prev_distance}
			list_of_pair_polyids_to_be_deleted = []
			for pair_polylids in dic_prev_div_line_feats:
				#pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
				#rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
				
				#print('pair_polylids',pair_polylids)
				line_feature_1,line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
				prev_tectonic_motion = dic_prev_div_line_feats[pair_polylids]['prev_motion']
				prev_distance = dic_prev_div_line_feats[pair_polylids]['dist']
				prev_begin_age = dic_prev_div_line_feats[pair_polylids]['age']
				#debug
				# if (pair_polylids == '17300_13241_9277+12009_13906_7560' or pair_polylids == '12009_13906_7560+17300_13241_9277'):
					# print('line_feature_1.get_description()',line_feature_1.get_description())
					# print('line_feature_2.get_description()',line_feature_2.get_description())
					# print('prev_begin_age',prev_begin_age)
					# print('prev_motion',prev_tectonic_motion)
					
				
				SGDUID_for_line_ft_1 = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == line_feature_1.get_reconstruction_plate_id(),'SGDUID'].unique()
				SGDUID_for_line_ft_2 = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == line_feature_2.get_reconstruction_plate_id(),'SGDUID'].unique()
				# if (pair_polylids in list_of_already_evaluated_pairs or rev_pair_of_polylids in list_of_already_evaluated_pairs):
					# continue #these two line features have already been evaluated at this reconstruction time thus take the new tuple
				# else:
					# list_of_already_evaluated_pairs.append(pair_polylids)
				
				#NO NEED TO find the original line features
				# original_con_ocn_line_ft_1 = None
				# original_con_ocn_line_ft_2 = None
				# for con_ocn_line_ft in valid_con_ocn_line_features:
					# if (line_feature_1.get_name() == con_ocn_line_ft.get_shapefile_attribute('POLYLID')):
						# original_con_ocn_line_ft_1 = con_ocn_line_ft
					# elif (line_feature_2.get_name() == con_ocn_line_ft.get_shapefile_attribute('POLYLID')):
						# original_con_ocn_line_ft_2 = con_ocn_line_ft
					# if (original_con_ocn_line_ft_1 is not None and original_con_ocn_line_ft_2 is not None):
						# break
				
				if (recorded_distance == -1.00):
					recorded_distance = prev_distance
				if ((prev_begin_age - reconstruction_time) > time_interval and line_feature_1.is_valid_at_time(reconstruction_time) and line_feature_2.is_valid_at_time(reconstruction_time)):
					reconstructed_current_div_line_features = []
					if (reference is not None):
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_current_div_line_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
					else:
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_current_div_line_features, reconstruction_time, group_with_feature = True)
					final_current_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_current_div_line_features, pygplates.PolylineOnSphere)
					current_reconstr_ft_1, current_reconstr_line_1 = final_current_reconstructed_line_features[0]
					current_reconstr_ft_2, current_reconstr_line_2 = final_current_reconstructed_line_features[1]
					#current_distance = pygplates.GeometryOnSphere.distance(current_reconstr_line_1.get_centroid(),current_reconstr_line_2.get_centroid())
					#recorded_distance = current_distance
					
					reconstructed_prev_div_line_features = []
					if (reference is not None):
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_prev_div_line_features, reconstruction_time + time_interval, anchor_plate_id = reference, group_with_feature = True)
					else:
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_prev_div_line_features, reconstruction_time + time_interval, group_with_feature = True)
					final_prev_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_prev_div_line_features,pygplates.PolylineOnSphere)
					prev_reconstr_ft_1,prev_reconstr_line_1 = final_prev_reconstructed_line_features[0]
					prev_reconstr_ft_2,prev_reconstr_line_2 = final_prev_reconstructed_line_features[1]
					
					reconstructed_point_A_at_from_time = prev_reconstr_line_1.get_centroid()
					reconstructed_point_B_at_from_time = prev_reconstr_line_2.get_centroid()
					reconstructed_point_A_at_to_time = current_reconstr_line_1.get_centroid()
					reconstructed_point_B_at_to_time = current_reconstr_line_2.get_centroid()
					#result_of_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_pos_and_angular_vel_vec(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time, reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time, reconstruction_time, reconstruction_time-time_interval)
					result_of_tectonic_motion, dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_pos_and_angular_vel_vec(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time, reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time, reconstruction_time+time_interval, reconstruction_time)
					list_dot_prod.append((reconstruction_time,line_feature_1.get_reconstruction_plate_id(),line_feature_2.get_reconstruction_plate_id(),dot_prod_btw_tectonic_motion))
					#debug
					# print('reconstruction_time',reconstruction_time)
					# print('result_of_tectonic_motion',result_of_tectonic_motion)
					
					
					latA,lonA = reconstructed_point_A_at_from_time.to_lat_lon()
					latB,lonB = reconstructed_point_B_at_from_time.to_lat_lon()
					at_prev_time_distance_in_km_btw_A_and_B = calculate_distance_km_between_two_points_from_haversine_formula(latA,lonA,latB,lonB)
					cur_latA,cur_lonA = reconstructed_point_A_at_to_time.to_lat_lon()
					cur_latB,cur_lonB = reconstructed_point_B_at_to_time.to_lat_lon()
					at_current_time_distance_in_km_btw_A_and_B = calculate_distance_km_between_two_points_from_haversine_formula(cur_latA,cur_lonA,cur_latB,cur_lonB)
					current_distance = at_current_time_distance_in_km_btw_A_and_B
					recorded_distance = current_distance
					
					is_valid_pair_of_line_fts = True
					# for reconstructed_gdu_ft, reconstructed_gdu in final_reconstructed_gdu_features:
						# polygid_of_original_con_ocn_line_ft_1 = original_con_ocn_line_ft_1.get_shapefile_attribute('polygid')
						# polygid_of_original_con_ocn_line_ft_2 = original_con_ocn_line_ft_2.get_shapefile_attribute('polygid')
						# polygid_of_gdu_ft = reconstructed_gdu_ft.get_shapefile_attribute('POLYGID')
						# if (polygid_of_original_con_ocn_line_ft_1 == polygid_of_gdu_ft or polygid_of_original_con_ocn_line_ft_2 == polygid_of_gdu_ft):
							# continue
						# SGDUID_for_gdu_ft = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == reconstructed_gdu_ft.get_reconstruction_plate_id(),'SGDUID'].unique()
						# #find the same value between SGDUID_for_gdu_ft and SGDUID_for_line_ft_1; SGDUID_for_gdu_ft and SGDUID_for_line_ft_2
						# intersection_w_line_ft_1 = np.intersect1d(SGDUID_for_gdu_ft, SGDUID_for_line_ft_1)
						# intersection_w_line_ft_2 = np.intersect1d(SGDUID_for_gdu_ft, SGDUID_for_line_ft_2)
						# if ((intersection_w_line_ft_1 is None or len(intersection_w_line_ft_1) == 0) and (intersection_w_line_ft_2 is None or len(intersection_w_line_ft_2) == 0)):
							# centroid_of_gdu = reconstructed_gdu.get_interior_centroid()
							# result_of_valid_test = is_point_in_between_point_A_and_B_using_greatcirclearc(centroid_of_gdu,reconstructed_point_B_at_to_time,reconstructed_point_A_at_to_time)
							# if (result_of_valid_test is not None):
								# if (result_of_valid_test == True):
									# is_valid_pair_of_line_fts = False
							# if (is_valid_pair_of_line_fts == False):
								# break
							
					#polygid_of_original_con_ocn_line_ft_1 = original_con_ocn_line_ft_1.get_shapefile_attribute('polygid')
					#polygid_of_original_con_ocn_line_ft_2 = original_con_ocn_line_ft_2.get_shapefile_attribute('polygid')
					total_stage_rel_rot_of_1_to_2 = find_stage_relative_reconstruction_rotation_(rotation_model,line_feature_1.get_reconstruction_plate_id(),line_feature_2.get_reconstruction_plate_id(),float(reconstruction_time+time_interval),reconstruction_time,reference)
					total_stage_rel_rot_of_2_to_1 = find_stage_relative_reconstruction_rotation_(rotation_model,line_feature_2.get_reconstruction_plate_id(),line_feature_1.get_reconstruction_plate_id(),float(reconstruction_time+time_interval),reconstruction_time,reference)
					if (total_stage_rel_rot_of_1_to_2 is not None):
						if (total_stage_rel_rot_of_1_to_2.represents_identity_rotation() == True):
							is_valid_pair_of_line_fts = False
						else:
							if (total_stage_rel_rot_of_2_to_1 is not None):
								if (total_stage_rel_rot_of_2_to_1.represents_identity_rotation() == True):
									is_valid_pair_of_line_fts = False
							else:
								is_valid_pair_of_line_fts = False
					else:
						is_valid_pair_of_line_fts = False
					if (is_valid_pair_of_line_fts == True):
						final_SGDUID_for_line_1 = None
						final_SGDUID_for_line_2 = None
						for reconstructed_sgdu_ft_at_reconstruction_time, reconstructed_sgdu_at_reconstruction_time in final_reconstructed_sgdu_features:
							SGDUID_of_reconstructed_sgdu_ft = int(reconstructed_sgdu_ft_at_reconstruction_time.get_name())
							SGDUID_for_rand_sgdu_ft = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == reconstructed_sgdu_ft_at_reconstruction_time.get_reconstruction_plate_id(),'SGDUID'].unique()
							# #find the same value between SGDUID_for_gdu_ft and SGDUID_for_line_ft_1; SGDUID_for_gdu_ft and SGDUID_for_line_ft_2
							intersection_w_line_ft_1 = np.intersect1d(SGDUID_for_rand_sgdu_ft, SGDUID_for_line_ft_1)
							intersection_w_line_ft_2 = np.intersect1d(SGDUID_for_rand_sgdu_ft, SGDUID_for_line_ft_2)
							#if ((SGDUID_of_reconstructed_sgdu_ft not in SGDUID_for_line_ft_1) and (SGDUID_of_reconstructed_sgdu_ft not in SGDUID_for_line_ft_2)):
							#if ((SGDUID_of_reconstructed_sgdu_ft not in intersection_w_line_ft_1) and (SGDUID_of_reconstructed_sgdu_ft not in intersection_w_line_ft_2)):
							if (len(intersection_w_line_ft_1) == 0 and len(intersection_w_line_ft_2) == 0):
								temporary_line_connecting_A_and_B = pygplates.PolylineOnSphere([reconstructed_point_A_at_to_time,reconstructed_point_B_at_to_time])
								if (reconstructed_sgdu_at_reconstruction_time.partition(temporary_line_connecting_A_and_B) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
									is_valid_pair_of_line_fts = False
									break
							else:
								if (len(intersection_w_line_ft_1) > 0):
									final_SGDUID_for_line_1 = reconstructed_sgdu_ft_at_reconstruction_time
								if (len(intersection_w_line_ft_2) > 0):
									final_SGDUID_for_line_2 = reconstructed_sgdu_ft_at_reconstruction_time
						
						if (final_SGDUID_for_line_1 is None or final_SGDUID_for_line_2 is None):
							is_valid_pair_of_line_fts = False
						else:
							if (final_SGDUID_for_line_1.get_name() == final_SGDUID_for_line_2.get_name()):
								is_valid_pair_of_line_fts = False
								
					#debug
					# if (pair_polylids == '17300_13241_9277+12009_13906_7560' or pair_polylids == '12009_13906_7560+17300_13241_9277'):
						# print('line_feature_1.get_description()',line_feature_1.get_description())
						# print('line_feature_2.get_description()',line_feature_2.get_description())
						# print('is_valid_pair_of_line_fts',is_valid_pair_of_line_fts)
						# print('prev_begin_age',prev_begin_age)
						# print('prev_motion',prev_motion)
						# print('result_of_tectonic_motion',result_of_tectonic_motion)
					
					
					has_modified_line_feats = False 
					if ((result_of_tectonic_motion != prev_tectonic_motion) and (prev_distance == 0.00 or at_prev_time_distance_in_km_btw_A_and_B <= 50.00 or is_valid_pair_of_line_fts == True)):
						if ((prev_begin_age - reconstruction_time) >= 3.00*(time_interval)):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
							line_feature_1.set_description('plate_boundary_zone')
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							line_feature_2.set_description('plate_boundary_zone')
							has_modified_line_feats = True
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
						elif (line_feature_1.get_description() == 'plate_boundary_zone' and line_feature_2.get_description() == 'plate_boundary_zone'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							if (result_of_tectonic_motion == 'D'):
								line_feature_1.set_description('divergent_margin')
								line_feature_2.set_description('divergent_margin')
							elif (result_of_tectonic_motion == 'C'):
								line_feature_1.set_description('convergent_margin')
								line_feature_2.set_description('convergent_margin')
							elif (result_of_tectonic_motion == 'T'):
								line_feature_1.set_description('transform_fault')
								line_feature_2.set_description('transform_fault')
							has_modified_line_feats = True
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
							if (result_of_tectonic_motion == 'D'):
								#quickly find mid-point feature
								total_relative_reconstruction_rotation = find_total_relative_reconstruction_rotation_(rotation_model, line_feature_1.get_reconstruction_plate_id(), line_feature_2.get_reconstruction_plate_id(), reconstruction_time, reference)
								if (total_relative_reconstruction_rotation is not None):
									if (total_relative_reconstruction_rotation.represents_identity_rotation() == False):
										#find mid point
										E_pole,_ = total_relative_reconstruction_rotation.get_euler_pole_and_angle()
										quick_mid_pt,mid_pt_order = quickly_derive_mid_point_and_order_of_mid_point_from_two_divergent_points(reconstructed_point_A_at_to_time,reconstructed_point_B_at_to_time,E_pole)
										mid_pt_order = round(mid_pt_order,2)
										#create rift point ft
										# #create an arc
										temporary_GreatCircleArc = pygplates.GreatCircleArc(quick_mid_pt,E_pole)
										normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
										left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, quick_mid_pt, reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time, line_feature_1.get_reconstruction_plate_id(), line_feature_2.get_reconstruction_plate_id())
										#create point feature
										name = 'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name()+'_'+str(mid_pt_order)
										rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, quick_mid_pt, name = name, valid_time = (reconstruction_time,0.00))
										if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
											rift_point_ft.set_left_plate(line_feature_1.get_reconstruction_plate_id())
											rift_point_ft.set_right_plate(line_feature_2.get_reconstruction_plate_id())
										else:
											rift_point_ft.set_left_plate(left_gduid)
											rift_point_ft.set_right_plate(right_gduid)
										rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
										rift_point_ft.set_description(str(mid_pt_order))
										if (reference is None):
											pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
										else:
											pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
										output_subseq_rift_point_features.add(rift_point_ft)
										if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
											unsure_topology_for_MOR_fts.add(rift_point_ft)
										if ((left_gduid == line_feature_1.get_reconstruction_plate_id() and right_gduid == line_feature_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
											#'start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'
											list_of_subseq_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name(),mid_pt_order, line_feature_1.get_name(), line_feature_1.get_reconstruction_plate_id(), final_SGDUID_for_line_1.get_reconstruction_plate_id(), line_feature_2.get_name(), line_feature_2.get_reconstruction_plate_id(), final_SGDUID_for_line_2.get_reconstruction_plate_id()))
										else:
											list_of_subseq_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name(),mid_pt_order, line_feature_2.get_name(), line_feature_2.get_reconstruction_plate_id(), final_SGDUID_for_line_2.get_reconstruction_plate_id(), line_feature_1.get_name(), line_feature_1.get_reconstruction_plate_id(), final_SGDUID_for_line_1.get_reconstruction_plate_id()))
					if ((prev_distance == 0.00 or at_prev_time_distance_in_km_btw_A_and_B <= 50.00 or is_valid_pair_of_line_fts == True)):
						# print('prev_distance',prev_distance)
						# print('recorded_distance',recorded_distance)
						#remaining_diverging_line_feats.append((line_feature_1,line_feature_2,prev_begin_age,recorded_distance))
						if (has_modified_line_feats == True):
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
						else:
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
					elif (is_valid_pair_of_line_fts == False):
						if (line_feature_1.get_description() != 'plate_boundary_zone' and line_feature_2.get_description() != 'plate_boundary_zone'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							if (line_feature_1_begin_time > reconstruction_time):
								cloned_line_ft_1 = line_feature_1.clone()
								cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
								cloned_line_ft_2 = line_feature_2.clone()
								cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
								pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
								output_diverging_line_features.add(cloned_line_ft_1)
								output_diverging_line_features.add(cloned_line_ft_2)
							if (pygplates.GeometryOnSphere.distance(current_reconstr_line_1.get_centroid(),current_reconstr_line_2.get_centroid()) == 0.00):
								if (line_feature_1.get_description() == 'convergent_margin' and line_feature_2.get_description() == 'convergent_margin'):
									output_collision.append((reconstruction_time,line_feature_1.get_name(),line_feature_2.get_name()))
							line_feature_1.set_description('plate_boundary_zone')
							line_feature_2.set_description('plate_boundary_zone')
							has_modified_line_feats = True
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
						
						# if (current_distance > 0.00 and at_current_time_distance_in_km_btw_A_and_B >= 50.00):
							# if (has_modified_line_feats == True):
								# remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
							# else:
								# remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
						
						if (has_modified_line_feats == True):
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
						else:
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
						
				elif (prev_begin_age > reconstruction_time and (line_feature_1.is_valid_at_time(reconstruction_time) == False or line_feature_2.is_valid_at_time(reconstruction_time) == False)):
					line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
					line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
					cloned_line_ft_1 = line_feature_1.clone()
					cloned_line_ft_1.set_valid_time(prev_begin_age,reconstruction_time+0.100)
					cloned_line_ft_2 = line_feature_2.clone()
					cloned_line_ft_2.set_valid_time(prev_begin_age,reconstruction_time+0.100)
					output_diverging_line_features.add(cloned_line_ft_1)
					output_diverging_line_features.add(cloned_line_ft_2)
					pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
					list_of_pair_polyids_to_be_deleted.append(pair_polylids)
				elif (prev_begin_age == reconstruction_time):
					remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
			for pair_polylids in list_of_pair_polyids_to_be_deleted:
				del dic_prev_div_line_feats[pair_polylids]
			previous_diverging_line_feats = remaining_diverging_line_feats
		
		#debug
		# print('number of features in previous_diverging_line_feats',len(previous_diverging_line_feats))
		# print('number of features in output_diverging_line_features', len(output_diverging_line_features))
		# temporary_output_pair_div_line_fts.write('expected_pair_divergent_line_features_but_failed_at_'+str(reconstruction_time)+'_'+modelname+'_'+yearmonthday+'.shp')
		#temporary_output_pair_div_line_fts = None
		
		#write out the results of all possibile tectonic motion for every pair of SuperGDUs that possibly diverge from each other according to SuperGDU history records
		output_dataframe = pd.DataFrame.from_records(results_of_all_possible_tectonic_motion, columns = ['reconstruction_time','SGDU1','SGDU2','tectonic_motion'])
		filename = 'possible_tectonic_motion_from_additional_eval_process_at_'+str(reconstruction_time)+'_for_'+modelname+'_'+yearmonthday+'.csv'
		output_dataframe.to_csv(filename,index=False)
		output_dataframe = None
		
		
		filename = 'dot_prod_tectonic_motion_for_'+modelname+'_'+yearmonthday+'.csv'
		if (os.path.isfile(filename)):
			output_dot_prod_tectonic_motion_df = pd.read_csv(filename)
			temporary_df = pd.DataFrame.from_records(list_dot_prod, columns = ['reconstruction_time','child_repgduid_1','child_repgduid_2','dot_prod'])
			output_dot_prod_tectonic_motion_df = pd.concat([temporary_df, output_dot_prod_tectonic_motion_df], ignore_index=True)
			output_dot_prod_tectonic_motion_df.to_csv(filename)
		else:
			#output_dot_prod_tectonic_motion_df = pd.DataFrame([[list_dot_prod]])
			output_dot_prod_tectonic_motion_df = pd.DataFrame.from_records(list_dot_prod, columns = ['reconstruction_time','child_repgduid_1','child_repgduid_2','dot_prod'])
			output_dot_prod_tectonic_motion_df.to_csv(filename)
		
		#update reconstruction_time for the main while-loop
		reconstruction_time = reconstruction_time - time_interval
	output_rift_point_features.write('rift_point_features_from_unrelated_SGDU_for_'+modelname+'_'+yearmonthday+'.shp')
	output_subseq_rift_point_features.write('subseq_rift_point_features_from_unrelated_SGDU_for_'+modelname+'_'+yearmonthday+'.shp')
	unsure_topology_for_MOR_fts.write('unsure_topology_for_MOR_fts_from_unrelated_SGDU_'+modelname+'_'+yearmonthday+'.shp')
	temporary_MOR_featurecollection = pygplates.FeatureCollection(output_temporary_MOR_line_feats)
	temporary_MOR_featurecollection.write('temporary_MOR_line_feat_for_from_unrelated_SGDU_'+modelname+'_'+yearmonthday+'.shp')
	if (len(dic_prev_div_line_feats) > 0):
		for pair_polylids in dic_prev_div_line_feats:
			line_feature_1,line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
			prev_tectonic_motion = dic_prev_div_line_feats[pair_polylids]['prev_motion']
			prev_distance = dic_prev_div_line_feats[pair_polylids]['dist']
			prev_begin_age = dic_prev_div_line_feats[pair_polylids]['age']
			output_diverging_line_features.add(line_feature_1)
			output_diverging_line_features.add(line_feature_2)
			line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
			pairs_of_kin_line_fts.append((line_feature_1_begin_time,line_feature_1_end_time,line_feature_1.get_description(),line_feature_1.get_name(),line_feature_2.get_name(),line_feature_1.get_feature_id().get_string(),line_feature_2.get_feature_id().get_string()))
	output_diverging_line_features.write('additional_kin_line_features_from_unrelated_SGDU_for_'+str(begin_reconstruction_time)+'_'+str(end_reconstruction_time)+'_'+modelname+'_'+yearmonthday+'.shp')
	
	#list_of_ordered_pairs_gdu_fts.append((start_div,name,smallest_circle_angular_radius_degrees, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
	output_dataframe = pd.DataFrame.from_records(list_of_ordered_pairs_gdu_fts, columns = ['start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'])
	filename = 'rift_point_features_records_from_unrelated_SGDU_for_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	
	output_dataframe = pd.DataFrame.from_records(list_of_subseq_ordered_pairs_gdu_fts, columns = ['start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'])
	filename = 'subseq_rift_point_features_records_from_unrelated_SGDU_for_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	
	output_dataframe = pd.DataFrame.from_records(output_collision, columns = ['reconstruction_time','polylid1','polylid2'])
	filename = 'collisions_zone_for_from_unrelated_SGDU_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	
	#line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()
	output_dataframe = pd.DataFrame.from_records(pairs_of_kin_line_fts, columns = ['from_time','to_time','type_kin','polylid1','polylid2','fid1','fid2'])
	filename = 'pairs_of_kin_line_fts_from_unrelated_SGDU_for_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)


def evaluate_kinematic(neighbouring_distance_km, oldest_age_to_start_decaying_neighbouring_dist, decaying_rate, line_features_collection, sgdu_features, gdu_features_collection, input_rift_csv, common_filename_for_temporary_sgdu_and_members_csv, time_interval, begin_reconstruction_time, end_reconstruction_time, rotation_model, reference, modelname, yearmonthday):
#def evaluate_kinematic(neighbouring_distance_km, line_features_collection, sgdu_features, gdu_features_collection, common_filename_for_temporary_sgdu_and_members_csv, time_interval, begin_reconstruction_time, end_reconstruction_time, rotation_model, reference, modelname, yearmonthday):
	reconstruction_time = begin_reconstruction_time
	dict_of_polygid_and_Shapely_centroid = {}
	dic_of_gdu_members_for_each_sgdu = {}
	dic_prev_div_line_feats = {}
	previous_diverging_line_feats = []
	temp_list_of_centroids_and_polygids = []
	reconstructed_sgdu_features = []
	output_kinematics = []
	suspected_output = []
	appropriate_pairs_of_sgdus = []
	key_of_sgdus = []
	reconstructed_gdu_fts_for_sgdu1 = []
	reconstructed_gdu_fts_for_sgdu2 = []
	prev_reconstructed_gdu_fts_for_sgdu1 = []
	prev_reconstructed_gdu_fts_for_sgdu2 = []
	reconstructed_gdu_features = []
	reconstructed_gdu_features_ynger = []
	reconstructed_line_features = []
	reconstructed_line_features_ynger = []
	other_reconstructed_gdu_features = []
	output_rift_point_features = pygplates.FeatureCollection()
	output_subseq_rift_point_features = pygplates.FeatureCollection()
	output_diverging_line_features = pygplates.FeatureCollection()
	unsure_topology_for_MOR_fts = pygplates.FeatureCollection()
	kin_line_feats_at_reconstruction_time = []
	list_of_ordered_pairs_gdu_fts = []
	list_of_ordered_non_rift_pairs_gdu_fts = []
	list_of_subseq_ordered_pairs_gdu_fts = []
	output_temporary_MOR_line_feats = []
	dic_kin_line_feats = {}
	output_records_for_kin_feats = []
	output_collision = []
	results_of_all_possible_tectonic_motion = []
	pairs_of_kin_line_fts = []
	#list_dot_prod = []
	if (end_reconstruction_time <= 0.00):
		end_reconstruction_time = time_interval #if end_reconstruction_time == 0.00 and time_interval is 5.00, then update the last time instant to be evaluate to be 5.00
	#initial_neighbouring_distance_km = neighbouring_distance_km
	input_rift_dataframe = pd.read_csv(input_rift_csv)
	
	reconstruction_time = begin_reconstruction_time
	while(reconstruction_time >= end_reconstruction_time):
		#debug
		#temporary_output_pair_div_line_fts = pygplates.FeatureCollection()
		
		print('reconstruction_time',reconstruction_time)
		if (reconstruction_time < oldest_age_to_start_decaying_neighbouring_dist):
			if (neighbouring_distance_km >= 1000.00):
				neighbouring_distance_km = neighbouring_distance_km - (neighbouring_distance_km*decaying_rate)
		
		already_included_pairs_of_line_feats = []
		dic_of_gdu_members_for_each_sgdu.clear()
		reconstructed_sgdu_features[:] = []
		reconstructed_gdu_features[:] = []
		reconstructed_line_features[:] = []
		other_reconstructed_gdu_features[:] = []
		results_of_all_possible_tectonic_motion[:] = []
		# #8) Find appropriate pairs of sgdus first based on the distance
		# #8i) Find valid sgdu features
		valid_sgdu_features = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(reconstruction_time))]
		# #8ii) Reconstruct sgdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_sgdu_features = find_final_reconstructed_geometries(reconstructed_sgdu_features, pygplates.PolygonOnSphere)
		#Find valid gdu features with con-ocn line features
		valid_con_ocn_line_features = [con_ocn_ft for con_ocn_ft in line_features_collection if con_ocn_ft.is_valid_at_time(reconstruction_time)]
		if (reference is not None):
			pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_line_features, pygplates.PolylineOnSphere)
		# #8i) Find valid gdu features at reconstruction_time 
		valid_in_time_gdu_features = [gdu_ft for gdu_ft in gdu_features_collection if (gdu_ft.is_valid_at_time(reconstruction_time))]
		valid_gdu_features = []
		already_included_gdu_fts = []
		for valid_line_ft,valid_line in final_reconstructed_line_features:
			#debug
			#if (valid_line_ft.get_reconstruction_plate_id() == 19508):
			#	print(valid_line_ft.get_reconstruction_plate_id())
			
			for gdu_ft in valid_in_time_gdu_features:
				if (valid_line_ft.get_shapefile_attribute('polygid') == gdu_ft.get_shapefile_attribute('POLYGID')):
					if (gdu_ft.get_shapefile_attribute('POLYGID') not in already_included_gdu_fts):
						valid_gdu_features.append(gdu_ft)
						already_included_gdu_fts.append(gdu_ft.get_shapefile_attribute('POLYGID'))
					# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
						# valid_gdu_features.append(gdu_ft)
						#already_included_gdu_fts.append(gdu_ft.get_feature_id())
				# else:
					# if (gdu_ft.get_reconstruction_plate_id() == valid_line_ft.get_reconstruction_plate_id()):
						# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
							# valid_gdu_features.append(gdu_ft)
							# already_included_gdu_fts.append(gdu_ft.get_feature_id())
		#print('len(valid_gdu_features)',len(valid_gdu_features))
		#print('len(valid_con_ocn_line_features)',len(valid_con_ocn_line_features))
						
		# #8ii) Reconstruct gdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_gdu_features, rotation_model, reconstructed_gdu_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_gdu_features, rotation_model, reconstructed_gdu_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_gdu_features = find_final_reconstructed_geometries(reconstructed_gdu_features, pygplates.PolygonOnSphere)
		dict_of_gdu_and_centroid = find_centroid_of_each_reconstructed_gdu_ft(final_reconstructed_gdu_features)
		#dict_of_neighbours = find_neighbours_of_each_reconstructed_gdu_ft(dict_of_gdu_and_centroid,threshold_distance_in_km_for_neighbour)
		dic_of_gdu_members_for_each_sgdu = find_gdu_members_of_each_sgdu_feat(valid_gdu_features, valid_sgdu_features, common_filename_for_temporary_sgdu_and_members_csv, reconstruction_time)
		#print('number of sgdu features in dic_of_gdu_members_for_each_sgdu',len(dic_of_gdu_members_for_each_sgdu))
		
		# #8i) Find valid gdu features at reconstruction_time - time_interval
		valid_in_time_gdu_features_in_ynger = [gdu_ft for gdu_ft in gdu_features_collection if (gdu_ft.is_valid_at_time(reconstruction_time-time_interval))]
		valid_gdu_features_ynger = []
		already_included_gdu_fts_ynger = []
		reconstructed_gdu_features_ynger[:] = []
		reconstructed_line_features_ynger[:] = []
		#Find valid gdu features with con-ocn line features
		valid_con_ocn_line_features_ynger = [con_ocn_ft for con_ocn_ft in line_features_collection if con_ocn_ft.is_valid_at_time(reconstruction_time-time_interval)]
		if (reference is not None):
			pygplates.reconstruct(valid_con_ocn_line_features_ynger, rotation_model, reconstructed_line_features_ynger, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_con_ocn_line_features_ynger, rotation_model, reconstructed_line_features_ynger, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_line_features_ynger = find_final_reconstructed_geometries(reconstructed_line_features_ynger, pygplates.PolylineOnSphere)
		for valid_line_ft,valid_line in final_reconstructed_line_features_ynger:
			for gdu_ft in valid_in_time_gdu_features_in_ynger:
				if (valid_line_ft.get_shapefile_attribute('polygid') == gdu_ft.get_shapefile_attribute('POLYGID')):
					if (gdu_ft.get_shapefile_attribute('POLYGID') not in already_included_gdu_fts_ynger):
						valid_gdu_features_ynger.append(gdu_ft)
						already_included_gdu_fts_ynger.append(gdu_ft.get_shapefile_attribute('POLYGID'))
					# if (gdu_ft.get_feature_id() not in already_included_gdu_fts_ynger):
						# valid_gdu_features_ynger.append(gdu_ft)
						#already_included_gdu_fts_ynger.append(gdu_ft.get_feature_id())
				# else:
					# if (gdu_ft.get_reconstruction_plate_id() == valid_line_ft.get_reconstruction_plate_id()):
						# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
							# valid_gdu_features.append(gdu_ft)
							# already_included_gdu_fts.append(gdu_ft.get_feature_id())
		#print('len(valid_gdu_features_ynger)',len(valid_gdu_features_ynger))
		#print('len(valid_con_ocn_line_features_ynger)',len(valid_con_ocn_line_features_ynger))
		# #8ii) Reconstruct gdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_gdu_features_ynger, rotation_model, reconstructed_gdu_features_ynger, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_gdu_features_ynger, rotation_model, reconstructed_gdu_features_ynger, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_gdu_features_ynger = find_final_reconstructed_geometries(reconstructed_gdu_features_ynger, pygplates.PolygonOnSphere)
		valid_sgdu_features_ynger = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(reconstruction_time-time_interval))]
		dic_of_gdu_members_for_each_sgdu_ynger = find_gdu_members_of_each_sgdu_feat(valid_gdu_features_ynger, valid_sgdu_features_ynger, common_filename_for_temporary_sgdu_and_members_csv, reconstruction_time-time_interval)
		#print('number of sgdu features in dic_of_gdu_members_for_each_sgdu_ynger',len(dic_of_gdu_members_for_each_sgdu_ynger))
		reconstructed_sgdu_features[:] = []
		if (reference is not None):
			pygplates.reconstruct(valid_sgdu_features_ynger, rotation_model, reconstructed_sgdu_features, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_sgdu_features_ynger, rotation_model, reconstructed_sgdu_features, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_sgdu_features_ynger = find_final_reconstructed_geometries(reconstructed_sgdu_features, pygplates.PolygonOnSphere)

		records_of_sgdus_diverging = []
		already_recorded_pairs = []
		if (len(final_reconstructed_sgdu_features) > 0):
			for child_sgdu_1_ft, child_sgdu_1_geom in final_reconstructed_sgdu_features:
				for child_sgdu_2_ft, child_sgdu_2_geom in final_reconstructed_sgdu_features:
					if (child_sgdu_1_ft.get_name() != child_sgdu_2_ft.get_name()):
						child_1 = child_sgdu_1_ft.get_name()
						child_2 = child_sgdu_2_ft.get_name()
						pair_of_sgdu_childs = child_1+'_'+child_2
						rev_pair_of_sgdu_childs = child_2+'_'+child_1
						if (pair_of_sgdu_childs in already_recorded_pairs or rev_pair_of_sgdu_childs in already_recorded_pairs):
							continue
						else:
							already_recorded_pairs.append(pair_of_sgdu_childs)
						child_ref_sgduid = child_sgdu_1_ft.get_reconstruction_plate_id()
						child_other_sgduid = child_sgdu_2_ft.get_reconstruction_plate_id()
						
						#'start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'
						#check whether the two SuperGDUs have been previously evaluated:
						records_of_prev_rifts = input_rift_dataframe.loc[((input_rift_dataframe['start_div'] - reconstruction_time) <= 1.00) & (((input_rift_dataframe['lrepgduid']== child_ref_sgduid) & (input_rift_dataframe['rrepgduid']== child_other_sgduid)) |((input_rift_dataframe['rrepgduid']== child_ref_sgduid) & (input_rift_dataframe['lrepgduid']== child_other_sgduid)))]
						if (len(records_of_prev_rifts) == 0):
							#records_of_sgdus_diverging.append((child_1, child_2, child_ref_sgduid, child_other_sgduid))
							#check whether in the last 5 periods whether the two SuperGDU rotate reltaive to each other
							total_stage_rel_rot_of_other_to_ref = None
							for p in range(0,5):
								total_intervals = (p + 1) * time_interval
								from_rot_time = float(reconstruction_time+total_intervals)
								to_rot_time = from_rot_time-time_interval
								total_stage_rel_rot_of_other_to_ref = find_stage_relative_reconstruction_rotation_(rotation_model,child_other_sgduid,child_ref_sgduid,from_rot_time,to_rot_time,reference)
								if (total_stage_rel_rot_of_other_to_ref is not None):
									if (total_stage_rel_rot_of_other_to_ref.represents_identity_rotation() == False):
										break
							if (total_stage_rel_rot_of_other_to_ref is not None):
								if (total_stage_rel_rot_of_other_to_ref.represents_identity_rotation() == False):
									
									distance_between_sgdu = pygplates.GeometryOnSphere.distance(child_sgdu_1_geom,child_sgdu_2_geom)*pygplates.Earth.mean_radius_in_kms
									#print('distance_between_sgdu',distance_between_sgdu,'neighbouring_distance_km',neighbouring_distance_km)
									if (distance_between_sgdu <= neighbouring_distance_km):
										centroid_sgdu_1 = child_sgdu_1_geom.get_interior_centroid()
										centroid_sgdu_2 = child_sgdu_2_geom.get_interior_centroid()
										E_pole,angle_rads = total_stage_rel_rot_of_other_to_ref.get_euler_pole_and_angle()
										result_of_tectonic_motion,result_of_dot_prod = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_2, centroid_sgdu_1, E_pole)
										records_of_sgdus_diverging.append((child_1, child_2, child_ref_sgduid, child_other_sgduid, result_of_tectonic_motion, result_of_dot_prod))
						# if (reconstruction_time < oldest_age_to_start_decaying_neighbouring_dist):
							# if (neighbouring_distance_km > 0.25*initial_neighbouring_distance_km):
								# neighbouring_distance_km = neighbouring_distance_km - (neighbouring_distance_km*decaying_rate)
						# distance_between_sgdu = pygplates.GeometryOnSphere.distance(child_sgdu_1_geom,child_sgdu_2_geom)*pygplates.Earth.mean_radius_in_kms
						# #print('distance_between_sgdu',distance_between_sgdu,'neighbouring_distance_km',neighbouring_distance_km)
						# if (distance_between_sgdu < neighbouring_distance_km):
							# child_1 = child_sgdu_1_ft.get_name()
							# child_2 = child_sgdu_2_ft.get_name()
							# child_ref_sgduid = child_sgdu_1_ft.get_reconstruction_plate_id()
							# child_other_sgduid = child_sgdu_2_ft.get_reconstruction_plate_id()
							# records_of_sgdus_diverging.append((child_1, child_2, child_ref_sgduid, child_other_sgduid))
						
						# child_1 = child_sgdu_1_ft.get_name()
						# child_2 = child_sgdu_2_ft.get_name()
						# child_ref_sgduid = child_sgdu_1_ft.get_reconstruction_plate_id()
						# child_other_sgduid = child_sgdu_2_ft.get_reconstruction_plate_id()
						# #records_of_sgdus_diverging.append((child_1, child_2, child_ref_sgduid, child_other_sgduid))
						# total_stage_rel_rot_of_other_to_ref = find_stage_relative_reconstruction_rotation_(rotation_model,child_other_sgduid,child_ref_sgduid,float(reconstruction_time+time_interval),reconstruction_time,reference)
						# if (total_stage_rel_rot_of_other_to_ref is not None):
							# if (total_stage_rel_rot_of_other_to_ref.represents_identity_rotation() == False):
								# records_of_sgdus_diverging.append((child_1, child_2, child_ref_sgduid, child_other_sgduid))

		print('Number of records_of_sgdus_diverging',len(records_of_sgdus_diverging))
		# #8iii) Find appropriate pairs of sgdus
		#SGDU,start_div,repGDUID
		polygid_all_valid_line_features = [con_ocn_ft.get_shapefile_attribute('polygid') for con_ocn_ft in valid_con_ocn_line_features]
		array_of_all_valid_polygid = np.array(polygid_all_valid_line_features)
		#print('array_of_all_valid_polygid',array_of_all_valid_polygid)
		already_evaluated_pairs_of_sgdus = []
		start_div = reconstruction_time
		if (len(final_reconstructed_sgdu_features) > 0):
			for tuple_of_sgdu_repgdu in records_of_sgdus_diverging:
				child_1, child_2, child_ref_sgduid, child_other_sgduid, result_of_tectonic_motion, result_of_dot_prod = tuple_of_sgdu_repgdu
				#use sgdu history to find the sgdu children 
				if (child_1 != child_2):
					key = str(child_1)+'_'+str(child_2)
					rev_key = str(child_2)+'_'+str(child_1)
					#print('key',key)
					if (key not in already_evaluated_pairs_of_sgdus and rev_key not in already_evaluated_pairs_of_sgdus):
						already_evaluated_pairs_of_sgdus.append(key)
						#use the two repgduids from the two children 
						child_sgdu_1 = None
						child_sgdu_2 = None
						for valid_ft in valid_sgdu_features:
							if (valid_ft.get_name() == str(child_1) and valid_ft.get_reconstruction_plate_id() == child_ref_sgduid):
								child_sgdu_1 = valid_ft
							elif (valid_ft.get_name() == str(child_2) and valid_ft.get_reconstruction_plate_id() == child_other_sgduid):
								child_sgdu_2 = valid_ft
							if (child_sgdu_1 is not None and child_sgdu_2 is not None):
								break
						if (child_sgdu_1 is None or child_sgdu_2 is None):
							continue #take a different record to process - mistake in manually finding pairs of unrelated SuperGDUs
						child_repgduid_1 = child_sgdu_1.get_reconstruction_plate_id()
						child_repgduid_2 = child_sgdu_2.get_reconstruction_plate_id()
						total_relative_reconstruction_rotation = find_total_relative_reconstruction_rotation_(rotation_model, child_repgduid_1, child_repgduid_2, float(reconstruction_time), reference)
						total_stage_rel_rot_of_1_to_2 = find_stage_relative_reconstruction_rotation_(rotation_model, child_repgduid_1, child_repgduid_2, float(reconstruction_time)+time_interval, float(reconstruction_time), reference)
						total_stage_rel_rot_of_2_to_1 = find_stage_relative_reconstruction_rotation_(rotation_model, child_repgduid_2, child_repgduid_1, float(reconstruction_time)+time_interval, float(reconstruction_time), reference)
						if (total_relative_reconstruction_rotation is not None):
							if (total_relative_reconstruction_rotation.represents_identity_rotation() == False):
								list_of_rift_points = []
								#check whether the pair of sgdus is valid
								child_sgud_1 = []
								child_sgud_2 = []
								non_related = []
								#for yng_sgdu_ft,yng_sgdu in final_reconstructed_sgdu_features_ynger:
								for yng_sgdu_ft,yng_sgdu in final_reconstructed_sgdu_features:
									if (yng_sgdu_ft.get_name() == str(child_1)):
										child_sgud_1.append(yng_sgdu)
									elif (yng_sgdu_ft.get_name() == str(child_2)):
										child_sgud_2.append(yng_sgdu)
									else:
										non_related.append(yng_sgdu)
								reconstructed_gdu_fts_for_sgdu1[:] = []
								reconstructed_gdu_fts_for_sgdu2[:] = []
								prev_reconstructed_gdu_fts_for_sgdu1[:] = []
								prev_reconstructed_gdu_fts_for_sgdu2[:] = []
								#list_of_ordered_pairs_gdu_fts = []
								list_of_already_used_line_fts = []
								gdu_features_for_sgdu1 = dic_of_gdu_members_for_each_sgdu[str(child_1)]
								#gdu_features_for_sgdu1_valid_at_prev_time = [current_gdu_ft_1 for current_gdu_ft_1 in gdu_features_for_sgdu1 if current_gdu_ft_1.is_valid_at_time(reconstruction_time + time_interval)]
								gdu_features_for_sgdu2 = dic_of_gdu_members_for_each_sgdu[str(child_2)]
								#gdu_features_for_sgdu2_valid_at_prev_time = [current_gdu_ft_2 for current_gdu_ft_2 in gdu_features_for_sgdu2 if current_gdu_ft_2.is_valid_at_time(reconstruction_time + time_interval)]
								final_reconstructed_gdu_features_for_sgdu1 = []
								final_reconstructed_gdu_features_for_sgdu2 = []
								prev_final_reconstructed_gdu_features_for_sgdu1 = []
								prev_final_reconstructed_gdu_features_for_sgdu2 = []
								polygid_features_for_sgdu1 = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu1]
								array_for_polygid_ft_sgdu1 = np.array(polygid_features_for_sgdu1)
								#polygid_features_for_sgdu1_at_prev_time = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu1_valid_at_prev_time]
								wanted_gdu_members_for_sgdu1 = np.intersect1d(array_for_polygid_ft_sgdu1,array_of_all_valid_polygid)
								polygid_features_for_sgdu2 = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu2]
								array_for_polygid_ft_sgdu2 = np.array(polygid_features_for_sgdu2)
								wanted_gdu_members_for_sgdu2 = np.intersect1d(array_for_polygid_ft_sgdu2,array_of_all_valid_polygid)
								#polygid_features_for_sgdu2_at_prev_time = [child_gdu_ft.get_shapefile_attribute('POLYGID') for child_gdu_ft in gdu_features_for_sgdu2_valid_at_prev_time]
								
								#CON-OCN line features that exit at the younger time (i.e. reconstruction_time - time_interval) and invalid at reconstruction_time
								#for child_gdu_ft_1, child_line_gdu_1 in final_reconstructed_line_features_ynger:
								for child_gdu_ft_1, child_line_gdu_1 in final_reconstructed_line_features:
									polygid_for_child_1 = child_gdu_ft_1.get_shapefile_attribute('polygid')
									#if ((polygid_for_child_1 in wanted_gdu_members_for_sgdu1) and (polygid_for_child_1 not in polygid_features_for_sgdu1_at_prev_time)):
									if (polygid_for_child_1 in wanted_gdu_members_for_sgdu1):
										for reconstructed_sgdu_1 in child_sgud_1:
											if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_1,child_line_gdu_1) == 0.00):
												reconstructed_gdu_fts_for_sgdu1.append((child_gdu_ft_1, child_line_gdu_1))
												break
								#for child_gdu_ft_2, child_line_gdu_2 in final_reconstructed_line_features_ynger:
								for child_gdu_ft_2, child_line_gdu_2 in final_reconstructed_line_features:
									polygid_for_child_2 = child_gdu_ft_2.get_shapefile_attribute('polygid')
									#if ((polygid_for_child_2 in polygid_features_for_sgdu2) and (polygid_for_child_2 not in polygid_features_for_sgdu2_at_prev_time)):
									if (polygid_for_child_2 in wanted_gdu_members_for_sgdu2):
										for reconstructed_sgdu_2 in child_sgud_2:
											if (pygplates.GeometryOnSphere.distance(reconstructed_sgdu_2,child_line_gdu_2) == 0.00):
												reconstructed_gdu_fts_for_sgdu2.append((child_gdu_ft_2, child_line_gdu_2))
												break
								#print('len(reconstructed_gdu_fts_for_sgdu1)',len(reconstructed_gdu_fts_for_sgdu1))
								#print('len(reconstructed_gdu_fts_for_sgdu2)',len(reconstructed_gdu_fts_for_sgdu2))
								
								#debug
								# if ((child_1 == 71261 and child_2 == 71252) or (child_2 == 71261 and child_1 == 71252)):
									# for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
										# temporary_output_pair_div_line_fts.add(gdu_line_ft_1)
									# for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
										# temporary_output_pair_div_line_fts.add(gdu_line_ft_2)
								
								E_pole,angle_rads = total_relative_reconstruction_rotation.get_euler_pole_and_angle()
								
								stage_rel_E_pole = None
								
								# if (total_stage_rel_rot_of_1_to_2 is not None):
									# if (total_stage_rel_rot_of_1_to_2.represents_identity_rotation() == False):
										# stage_rel_E_pole,_ = total_stage_rel_rot_of_1_to_2.get_euler_pole_and_angle()
								# elif (total_stage_rel_rot_of_2_to_1 is not None):
									# if (total_stage_rel_rot_of_2_to_1.represents_identity_rotation() == False):
										# stage_rel_E_pole,_ = total_stage_rel_rot_of_2_to_1.get_euler_pole_and_angle()
								
								if (stage_rel_E_pole is None):
									stage_rel_E_pole = E_pole
								final_sgdu_1_for_eval = None
								centroid_sgdu_1 = None
								final_sgdu_2_for_eval = None
								centroid_sgdu_2 = None
								smallest_distance_btw_two_sgdu = -1.00
								for reconstructed_sgdu_1 in child_sgud_1:
									centroid_sgdu_1 = reconstructed_sgdu_1.get_interior_centroid()
									final_sgdu_1_for_eval = reconstructed_sgdu_1
									for reconstructed_sgdu_2 in child_sgud_2:
										centroid_sgdu_2 = reconstructed_sgdu_2.get_interior_centroid()
										final_sgdu_2_for_eval = reconstructed_sgdu_2
										distance_between_child_sgdu = pygplates.GeometryOnSphere.distance(centroid_sgdu_1,centroid_sgdu_2)*pygplates.Earth.mean_radius_in_kms
										if (smallest_distance_btw_two_sgdu == -1.00):
											smallest_distance_btw_two_sgdu = distance_between_child_sgdu
										elif (smallest_distance_btw_two_sgdu > 0.00 and smallest_distance_btw_two_sgdu > distance_between_child_sgdu):
											smallest_distance_btw_two_sgdu = distance_between_child_sgdu
										if (smallest_distance_btw_two_sgdu == 0.00):
											break
								
								print('result_of_tectonic_motion',result_of_tectonic_motion)
								#print('child_repgduid_2',child_repgduid_2,'child_repgduid_1',child_repgduid_1)
								#record all possible values of tectonic-motion to double-check with results when running identify_convergent_boundaries which is processing from present-day to the past
								results_of_all_possible_tectonic_motion.append((reconstruction_time,child_1,child_2,child_ref_sgduid, child_other_sgduid,result_of_tectonic_motion,result_of_dot_prod))
								#print('results_of_all_possible_tectonic_motion',results_of_all_possible_tectonic_motion)
								smallest_circle_angular_radius_degrees = -1.00
								if (result_of_tectonic_motion == 'D'):
									smallest_circle_angular_radius_degrees = 178.00
								elif (result_of_tectonic_motion == 'T' or result_of_tectonic_motion == 'C'):
									smallest_circle_angular_radius_degrees = 0.00
								#print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees,)
								while (smallest_circle_angular_radius_degrees > 0.00):
									small_circle_boundary = rotation_utility.create_small_circle_PolylineOnSphere(E_pole,smallest_circle_angular_radius_degrees)
									found_pair_of_line_feats = None
									valid_pair_of_line_fts = True
									#find gdu polygon features for each line feature 
									valid_mid_point_feat = False 
									for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
										
										polylid_of_gdu_line_ft_1 = gdu_line_ft_1.get_shapefile_attribute('polygid')
										#list_of_neighbours_for_polylid_1 = dict_of_neighbours[polylid_of_gdu_line_ft_1]
										for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
											polylid_of_gdu_line_ft_2 = gdu_line_ft_2.get_shapefile_attribute('polygid')
											#if (polylid_of_gdu_line_ft_2 not in list_of_neighbours_for_polylid_1):
											#	continue
											approx_rad_closest_dist_neighbour,closest_point_on_gdu1,_ = pygplates.GeometryOnSphere.distance(line_gdu_1, small_circle_boundary,return_closest_positions = True)
											approx_rad_closest_dist_ref,closest_point_on_gdu2,_= pygplates.GeometryOnSphere.distance(line_gdu_2, small_circle_boundary,return_closest_positions = True)
											
											#calculate distance by haversine
											lat1,lon1 = closest_point_on_gdu1.to_lat_lon()
											lat2,lon2 = closest_point_on_gdu2.to_lat_lon()
											approx_distance_btw_lines_kms = calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2)
											
											if (approx_rad_closest_dist_neighbour == 0.000 and approx_rad_closest_dist_ref == 0.000): 
												#debug
												# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
													# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
												# if ((approx_distance_btw_lines_kms <= 10000.00) or (gdu_line_ft_1.is_valid_at_time(reconstruction_time + time_interval)==False) or (gdu_line_ft_2.is_valid_at_time(reconstruction_time + time_interval)==False)):
													# valid_pair_of_line_fts = True
												if (valid_pair_of_line_fts == True):
													#find gdu polygon features for each line feature 
													temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = None,None
													temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = None,None
													for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
														if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_1.get_shapefile_attribute('polygid')):
															temp_gdu_ft_1,temp_reconstruct_gdu_polygon_1 = temp_gdu_ft,temp_reconstruct_gdu_polygon
															break
													for temp_gdu_ft,temp_reconstruct_gdu_polygon in final_reconstructed_gdu_features:
														if (temp_gdu_ft.get_shapefile_attribute('POLYGID') == gdu_line_ft_2.get_shapefile_attribute('polygid')):
															temp_gdu_ft_2,temp_reconstruct_gdu_polygon_2 = temp_gdu_ft,temp_reconstruct_gdu_polygon
															break
													distance_btw_two_gdus = pygplates.GeometryOnSphere.distance(temp_reconstruct_gdu_polygon_1,temp_reconstruct_gdu_polygon_2)
													if (distance_btw_two_gdus > 0.00):
														valid_pair_of_line_fts = False
													if (valid_pair_of_line_fts == False):
														temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
														valid_pair_of_line_fts = True
														for random_sgdu in non_related:
															if (random_sgdu.partition(temporary_PolylineOnSphere) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
																valid_pair_of_line_fts = False
																break
													
													if (valid_pair_of_line_fts == True):
														if (found_pair_of_line_feats is None):
															#have to double check whether the point feature fall within both superGDU or just one superGDU
															approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
															found_in_sgdu_1 = False
															found_in_sgdu_2 = False
															for temp_sgdu_1 in child_sgud_1:
																if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																	found_in_sgdu_1 = True
																	break
															for temp_sgdu_2 in child_sgud_2:
																if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																	found_in_sgdu_2 = True
																	break
															if (distance_btw_two_gdus == 0.00):
																if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																	valid_mid_point_feat = True
																	#debug
																	# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
																		# print('valid_mid_point_feat',valid_mid_point_feat)
																	break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																else:
																	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
															else:
																if (found_in_sgdu_1 == True or found_in_sgdu_2 == True):
																	valid_mid_point_feat = False
																found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
															
														else:
															#have to double check whether the point feature fall within both superGDU or just one superGDU
															approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
															found_in_sgdu_1 = False
															found_in_sgdu_2 = False
															for temp_sgdu_1 in child_sgud_1:
																if (temp_sgdu_1.is_point_in_polygon(approx_mid_point) == True):
																	found_in_sgdu_1 = True
																	break
															for temp_sgdu_2 in child_sgud_2:
																if (temp_sgdu_2.is_point_in_polygon(approx_mid_point) == True):
																	found_in_sgdu_2 = True
																	break
															if (distance_btw_two_gdus == 0.00):
																if (found_in_sgdu_1 == True and found_in_sgdu_2 == True):
																	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
																	valid_mid_point_feat = True
																	break # break out of the for-loop of for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2
																
																else:
																	found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,0.00,closest_point_on_gdu1,closest_point_on_gdu2)
															else:
																if (found_in_sgdu_1 == True or found_in_sgdu_2 == True):
																	valid_mid_point_feat = False
																if (valid_mid_point_feat == True):
																	prev_approx_distance_btw_line_kmns = found_pair_of_line_feats[4]
																	if (prev_approx_distance_btw_line_kmns > approx_distance_btw_lines_kms or valid_mid_point_feat == False):
																		if (gdu_line_ft_1.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts and gdu_line_ft_2.get_shapefile_attribute('POLYLID') not in list_of_already_used_line_fts):
																			found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
										#NEW---
										if (valid_mid_point_feat == True):
											#debug
											# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
												# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '701_154_14938' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '22052_53_12274') or (gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '22052_53_12274' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '701_154_14938')):
													# print('before')
													# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
													# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
											break # break out of the for-loop of for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1
										
									if (found_pair_of_line_feats is not None):
										#debug
										# if ((child_repgduid_1 == 77030 and child_repgduid_2 == 201) or (child_repgduid_2 == 77030 and child_repgduid_1 == 201)):
											# print('smallest_circle_angular_radius_degrees',smallest_circle_angular_radius_degrees)
											# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
											# print('valid_mid_point_feat',valid_mid_point_feat)
										
										gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2 = found_pair_of_line_feats
										temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
										#debug
										# if (key == '69184_69741'):
											# print(gdu_line_ft_1.get_shapefile_attribute('POLYLID'),gdu_line_ft_2.get_shapefile_attribute('POLYLID'))
										
										approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
										if (approx_mid_point == closest_point_on_gdu1 or approx_mid_point == closest_point_on_gdu2):
											temp_list_of_closest_point_on_gdu1 = dict_of_gdu_and_centroid[gdu_line_ft_1.get_shapefile_attribute('polygid')]
											closest_point_on_gdu1 = temp_list_of_closest_point_on_gdu1[0][0]
											temp_list_of_closest_point_on_gdu2 = dict_of_gdu_and_centroid[gdu_line_ft_2.get_shapefile_attribute('polygid')]
											closest_point_on_gdu2 = temp_list_of_closest_point_on_gdu2[0][0]
											if (valid_mid_point_feat == False):
												valid_mid_point_feat = True
												
										if (valid_mid_point_feat == False):
											if (pygplates.GeometryOnSphere.distance(line_gdu_1,line_gdu_2) == 0.00):
												valid_mid_point_feat = True
												
										#NEW - check whether approx_mid_point positioned within any SGDUs
										if (valid_mid_point_feat == False):
											are_lines_similar = are_two_PolylineOnSphere_similar(line_gdu_1,line_gdu_2)
											if (are_lines_similar == True):
												valid_mid_point_feat = True
											elif (valid_mid_point_feat == False):
												#temporarily set valid_mid_point_feat to True
												valid_mid_point_feat = True
												for random_sgdu in non_related:
													if (random_sgdu.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
														valid_mid_point_feat = False
														break
												if (valid_mid_point_feat == True):
													for reconstructed_sgdu_2 in child_sgud_2:
														if (reconstructed_sgdu_2.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
															valid_mid_point_feat = False
															break
													# # #debug
													# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
														# print('valid_mid_point_feat at 1335',valid_mid_point_feat)
													# # # #debug
													# if ((gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945' and gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053') or (gdu_line_ft_2.get_shapefile_attribute('POLYLID') == '17023_14194_2053' and gdu_line_ft_1.get_shapefile_attribute('POLYLID') == '12404_11454_2945')):
														# print('valid_mid_point_feat at 1338',valid_mid_point_feat)
													
												if (valid_mid_point_feat == True):
													for reconstructed_sgdu_1 in child_sgud_1:
														if (reconstructed_sgdu_1.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
															valid_mid_point_feat = False
															break
												
											#create an arc
											temporary_GreatCircleArc = pygplates.GreatCircleArc(approx_mid_point,E_pole)
											normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
											left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, approx_mid_point, closest_point_on_gdu1, closest_point_on_gdu2, gdu_line_ft_1.get_reconstruction_plate_id(), gdu_line_ft_2.get_reconstruction_plate_id())
											list_of_rift_points.append(approx_mid_point)
											#create point feature
											#name = 'R'+str(child_1)+'_'+str(child_2)+'_'+str(smallest_circle_angular_radius_degrees)
											name = 'R'+key+'_'+str(smallest_circle_angular_radius_degrees)
											rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, approx_mid_point, name = name, valid_time = (reconstruction_time,0.00))
											if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
												rift_point_ft.set_left_plate(gdu_line_ft_1.get_reconstruction_plate_id())
												rift_point_ft.set_right_plate(gdu_line_ft_2.get_reconstruction_plate_id())
											else:
												rift_point_ft.set_left_plate(left_gduid)
												rift_point_ft.set_right_plate(right_gduid)
											rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
											rift_point_ft.set_description(str(smallest_circle_angular_radius_degrees))
											if (reference is None):
												pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
											else:
												pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
											output_rift_point_features.add(rift_point_ft)
											if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
												unsure_topology_for_MOR_fts.add(rift_point_ft)
											if ((left_gduid == gdu_line_ft_1.get_reconstruction_plate_id() and right_gduid == gdu_line_ft_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
												list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2))
											else:
												list_of_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+key,smallest_circle_angular_radius_degrees, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
										
											#create pair of line features associated with the rift point ft
											_,con_ocn_to_time = gdu_line_ft_1.get_valid_time()
											line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_1,name=gdu_line_ft_1.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
											line_feature_1.set_reconstruction_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
											line_feature_1.set_conjugate_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
											line_feature_1.set_description('divergent_margin')
											_,con_ocn_to_time = gdu_line_ft_2.get_valid_time()
											line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_2,name=gdu_line_ft_2.get_shapefile_attribute('POLYLID'),valid_time = (reconstruction_time,con_ocn_to_time))
											line_feature_2.set_reconstruction_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
											line_feature_2.set_conjugate_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
											line_feature_2.set_description('divergent_margin')
											if (reference is None):
												pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time)
											else:
												pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time,reference)
											#output_diverging_line_features.add(line_feature_1)
											#output_diverging_line_features.add(line_feature_2)
											previous_diverging_line_feats.append((line_feature_1,line_feature_2,'D',reconstruction_time,pygplates.GeometryOnSphere.distance(line_gdu_1.get_centroid(),line_gdu_2.get_centroid())))
									smallest_circle_angular_radius_degrees = smallest_circle_angular_radius_degrees - 0.50
									
									#print('found_pair_of_line_feats',found_pair_of_line_feats)
									#print('valid_mid_point_feat',valid_mid_point_feat)
									
								#create temporary MOR features from list_of_rift_points
								if (len(list_of_rift_points) > 0):
									list_of_distinct_rift_points = []
									for temporary_rift_pt in list_of_rift_points:
										if (len(list_of_distinct_rift_points) == 0):
											list_of_distinct_rift_points.append(temporary_rift_pt)
										else:
											last_rift_pt = list_of_distinct_rift_points[-1]
											if (last_rift_pt != temporary_rift_pt):
												list_of_distinct_rift_points.append(temporary_rift_pt)
									if (len(list_of_distinct_rift_points) >= 2):
										temporary_MOR_line = pygplates.PolylineOnSphere(list_of_rift_points)
										temporary_MOR_line_feat = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_mid_ocean_ridge,temporary_MOR_line,name='R'+key,valid_time = (reconstruction_time,0.00))
										mid_point_of_temporary_MOR_line_feat = temporary_MOR_line.get_centroid()
										#create an arc
										temporary_GreatCircleArc = pygplates.GreatCircleArc(mid_point_of_temporary_MOR_line_feat,E_pole)
										normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
										#rep_point_of_sgdu_1 = child_sgud_1[0].get_interior_centroid() 
										#rep_point_of_sgdu_2 = child_sgud_2[0].get_interior_centroid()
										#MOR_left_gduid, MOR_right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, mid_point_of_temporary_MOR_line_feat, rep_point_of_sgdu_1, rep_point_of_sgdu_2, child_repgduid_1, child_repgduid_2)
										#temporarily set left and right 
										MOR_left_gduid, MOR_right_gduid = child_repgduid_1,child_repgduid_2
										temporary_MOR_line_feat.set_left_plate(MOR_left_gduid)
										temporary_MOR_line_feat.set_right_plate(MOR_right_gduid)
										temporary_MOR_line_feat.set_reconstruction_method('HalfStageRotationVersion2')
										if (reference is None):
											pygplates.reverse_reconstruct(temporary_MOR_line_feat,rotation_model,reconstruction_time)
										else:
											pygplates.reverse_reconstruct(temporary_MOR_line_feat,rotation_model,reconstruction_time,reference)
										output_temporary_MOR_line_feats.append(temporary_MOR_line_feat)
								if (result_of_tectonic_motion == 'T' or result_of_tectonic_motion == 'C'):
									for gdu_line_ft_1, line_gdu_1 in reconstructed_gdu_fts_for_sgdu1:
										#print('POLYLID1',gdu_line_ft_1.get_shapefile_attribute('POLYLID'))
										found_pair_of_line_feats = None
										valid_pair_of_line_fts = True
										list_of_line_ft_similar_to_line_gdu_1 = []
										list_of_polygid_of_line_ft_similar_to_line_gdu_1 = []
										for gdu_line_ft_2, line_gdu_2 in reconstructed_gdu_fts_for_sgdu2:
											approx_rad_closest_dist_neighbour,closest_point_on_gdu1,closest_point_on_gdu2 = pygplates.GeometryOnSphere.distance(line_gdu_1, line_gdu_2,return_closest_positions = True)
											#calculate distance by haversine
											lat1,lon1 = closest_point_on_gdu1.to_lat_lon()
											lat2,lon2 = closest_point_on_gdu2.to_lat_lon()
											approx_distance_btw_lines_kms = calculate_distance_km_between_two_points_from_haversine_formula(lat1,lon1,lat2,lon2)
											if ((approx_rad_closest_dist_neighbour == 0.00) or (gdu_line_ft_1.is_valid_at_time(reconstruction_time)== False) or (gdu_line_ft_2.is_valid_at_time(reconstruction_time)== False) or approx_distance_btw_lines_kms <= 350.00):
												temporary_PolylineOnSphere = pygplates.PolylineOnSphere([closest_point_on_gdu1,closest_point_on_gdu2])
												if (approx_rad_closest_dist_neighbour > 0.00 and approx_distance_btw_lines_kms > 50.00):
													if (approx_distance_btw_lines_kms <= neighbouring_distance_km):
														for random_sgdu in non_related:
															if (random_sgdu.partition(temporary_PolylineOnSphere) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
																valid_pair_of_line_fts = False
																break
													else:
														valid_pair_of_line_fts = False
												if (valid_pair_of_line_fts == True):
													#check whether pair of line features was already included
													polylid_1_polylid_2 = gdu_line_ft_1.get_shapefile_attribute('POLYLID')+'+'+gdu_line_ft_2.get_shapefile_attribute('POLYLID')
													polylid_2_polylid_1 = gdu_line_ft_2.get_shapefile_attribute('POLYLID')+'+'+gdu_line_ft_1.get_shapefile_attribute('POLYLID')
													if (polylid_1_polylid_2 not in already_included_pairs_of_line_feats and polylid_2_polylid_1 not in already_included_pairs_of_line_feats):
														already_included_pairs_of_line_feats.append(polylid_1_polylid_2)
													else:
														valid_pair_of_line_fts = False
												if (valid_pair_of_line_fts == True):
														
													#don't need to find the closest pair simply find the valid pair
													#find the mid_point between two points 
													approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
													
													valid_mid_point_feat = False
													if (approx_mid_point == closest_point_on_gdu1 or approx_mid_point == closest_point_on_gdu2):
														valid_mid_point_feat = True
														#but we also need to update the geometry of the mid point to find left and right sides for topology
														#temp_list_of_closest_point_on_gdu1 = dict_of_gdu_and_centroid_older[gdu_line_ft_1.get_shapefile_attribute('polygid')]
														#closest_point_on_gdu1 = temp_list_of_closest_point_on_gdu1[0][0]
														#temp_list_of_closest_point_on_gdu2 = dict_of_gdu_and_centroid_older[gdu_line_ft_2.get_shapefile_attribute('polygid')]
														#closest_point_on_gdu2 = temp_list_of_closest_point_on_gdu2[0][0]
														
														# #find the mid_point between two points 
														approx_mid_point = find_the_mid_of_two_PointOnSphere(closest_point_on_gdu1,closest_point_on_gdu2)
														if (approx_mid_point == closest_point_on_gdu1 or approx_mid_point == closest_point_on_gdu2):
															valid_mid_point_feat = False
														if (valid_mid_point_feat == False):
															line_ft_1_at_reconstruction_time = None
															line_ft_2_at_reconstruction_time = None
															if (gdu_line_ft_1.is_valid_at_time(reconstruction_time) == True and gdu_line_ft_2.is_valid_at_time(reconstruction_time) == True):
																for ynger_line_ft, ynger_line in final_reconstructed_line_features:
																	if (ynger_line_ft.get_shapefile_attribute('POLYLID') == gdu_line_ft_1.get_shapefile_attribute('POLYLID')):
																		line_ft_1_at_reconstruction_time = ynger_line
																	elif (ynger_line_ft.get_shapefile_attribute('POLYLID') == gdu_line_ft_2.get_shapefile_attribute('POLYLID')):
																		line_ft_2_at_reconstruction_time = ynger_line
																	if (line_ft_1_at_reconstruction_time is not None and line_ft_2_at_reconstruction_time is not None):
																		are_lines_similar = are_two_PolylineOnSphere_similar(line_ft_1_at_reconstruction_time,line_ft_2_at_reconstruction_time)
																		break
																		if (are_lines_similar == True):
																			valid_mid_point_feat = True
														if (valid_mid_point_feat == False):
															#temporarily set valid_mid_point_feat to True
															valid_mid_point_feat = True
															for random_sgdu in non_related:
																if (random_sgdu.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
																	valid_mid_point_feat = False
																	break
															if (valid_mid_point_feat == True):
																for reconstructed_sgdu_2 in child_sgud_2:
																	if (reconstructed_sgdu_2.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
																		valid_mid_point_feat = False
																		break
															if (valid_mid_point_feat == True):
																for reconstructed_sgdu_1 in child_sgud_1:
																	if (reconstructed_sgdu_1.partition(approx_mid_point) == pygplates.PolygonOnSphere.PartitionResult.inside):
																		valid_mid_point_feat = False
																		break
														if (valid_mid_point_feat == True):
															
															if (approx_mid_point == closest_point_on_gdu1 or approx_mid_point == closest_point_on_gdu2):
																temp_list_of_closest_point_on_gdu1 = dict_of_gdu_and_centroid[gdu_line_ft_1.get_shapefile_attribute('polygid')]
																closest_point_on_gdu1 = temp_list_of_closest_point_on_gdu1[0][0]
																temp_list_of_closest_point_on_gdu2 = dict_of_gdu_and_centroid[gdu_line_ft_2.get_shapefile_attribute('polygid')]
																closest_point_on_gdu2 = temp_list_of_closest_point_on_gdu2[0][0]
															
															found_pair_of_line_feats = (gdu_line_ft_1,gdu_line_ft_2,line_gdu_1,line_gdu_2,approx_distance_btw_lines_kms,closest_point_on_gdu1,closest_point_on_gdu2)
															#create an arc
															temporary_GreatCircleArc = None
															if (E_pole != stage_rel_E_pole):
																temporary_GreatCircleArc = pygplates.GreatCircleArc(approx_mid_point,stage_rel_E_pole)
															else:
																temporary_GreatCircleArc = pygplates.GreatCircleArc(approx_mid_point,E_pole)
															normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
															left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, approx_mid_point, closest_point_on_gdu1, closest_point_on_gdu2, gdu_line_ft_1.get_reconstruction_plate_id(), gdu_line_ft_2.get_reconstruction_plate_id())
															# #create point feature
															name = 'C'+key+'_'+gdu_line_ft_1.get_shapefile_attribute('POLYLID')+'_'+gdu_line_ft_1.get_shapefile_attribute('POLYLID')

															if (left_gduid == gdu_line_ft_1.get_reconstruction_plate_id() and right_gduid == gdu_line_ft_2.get_reconstruction_plate_id()):
																list_of_ordered_pairs_gdu_fts.append((reconstruction_time+time_interval,name, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2))
															else:
																list_of_ordered_pairs_gdu_fts.append((reconstruction_time+time_interval,name, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
																
															#create pair of line features associated with the rift point ft
															if (result_of_tectonic_motion == 'C'):
																begin_age_line_ft_1,_ = gdu_line_ft_1.get_valid_time()
																line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_1,name=gdu_line_ft_1.get_shapefile_attribute('POLYLID'),valid_time = (begin_age_line_ft_1,reconstruction_time+time_interval))
																line_feature_1.set_reconstruction_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
																line_feature_1.set_conjugate_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
																line_feature_1.set_description('convergent_margin')
													
																begin_age_line_ft_2,_ = gdu_line_ft_2.get_valid_time()
																line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_2,name=gdu_line_ft_2.get_shapefile_attribute('POLYLID'),valid_time = (begin_age_line_ft_2,reconstruction_time+time_interval))
																line_feature_2.set_reconstruction_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
																line_feature_2.set_conjugate_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
																line_feature_2.set_description('convergent_margin')
															
																if (begin_age_line_ft_1 > begin_age_line_ft_2):
																	line_feature_1.set_valid_time(begin_age_line_ft_2,reconstruction_time)
																	line_feature_2.set_valid_time(begin_age_line_ft_2,reconstruction_time)
																else:
																	line_feature_1.set_valid_time(begin_age_line_ft_1,reconstruction_time)
																	line_feature_2.set_valid_time(begin_age_line_ft_1,reconstruction_time)

																if (reference is None):
																	pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time+time_interval)
																else:
																	pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time+time_interval,reference)
																previous_diverging_line_feats.append((line_feature_1,line_feature_2,'C',reconstruction_time,pygplates.GeometryOnSphere.distance(line_gdu_1.get_centroid(),line_gdu_2.get_centroid())))
															#create pair of line features associated with the rift point ft
															if (result_of_tectonic_motion == 'T'):
																begin_age_line_ft_1,_ = gdu_line_ft_1.get_valid_time()
																line_feature_1 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_1,name=gdu_line_ft_1.get_shapefile_attribute('POLYLID'),valid_time = (begin_age_line_ft_1,reconstruction_time+time_interval))
																line_feature_1.set_reconstruction_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
																line_feature_1.set_conjugate_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
																line_feature_1.set_description('transform_fault')
													
																begin_age_line_ft_2,_ = gdu_line_ft_2.get_valid_time()
																line_feature_2 = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_passive_continental_boundary,line_gdu_2,name=gdu_line_ft_2.get_shapefile_attribute('POLYLID'),valid_time = (begin_age_line_ft_2,reconstruction_time+time_interval))
																line_feature_2.set_reconstruction_plate_id(gdu_line_ft_2.get_reconstruction_plate_id())
																line_feature_2.set_conjugate_plate_id(gdu_line_ft_1.get_reconstruction_plate_id())
																line_feature_2.set_description('transform_fault')
															
																if (begin_age_line_ft_1 > begin_age_line_ft_2):
																	line_feature_1.set_valid_time(begin_age_line_ft_2,reconstruction_time)
																	line_feature_2.set_valid_time(begin_age_line_ft_2,reconstruction_time)
																else:
																	line_feature_1.set_valid_time(begin_age_line_ft_1,reconstruction_time)
																	line_feature_2.set_valid_time(begin_age_line_ft_1,reconstruction_time)

																if (reference is None):
																	pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time+time_interval)
																else:
																	pygplates.reverse_reconstruct([line_feature_1,line_feature_2],rotation_model,reconstruction_time+time_interval,reference)
																previous_diverging_line_feats.append((line_feature_1,line_feature_2,'T',reconstruction_time,pygplates.GeometryOnSphere.distance(line_gdu_1.get_centroid(),line_gdu_2.get_centroid())))
												if (found_pair_of_line_feats is not None):
													break
								
		#check the end_time of diverging line features
		#list_of_already_evaluated_pairs = []
		#debug
		print('reconstruction_time',reconstruction_time)
		print('number of features in previous_diverging_line_feats before update',len(previous_diverging_line_feats))
		# for line_feature_1,line_feature_2,prev_motion,prev_begin_age,prev_distance in previous_diverging_line_feats:
			# prev_tectonic_motion = prev_motion
			# output_diverging_line_features.add(line_feature_1)
			# output_diverging_line_features.add(line_feature_2)
			# line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
			# pairs_of_kin_line_fts.append((line_feature_1_begin_time,line_feature_1_end_time,line_feature_1.get_description(),line_feature_1.get_name(),line_feature_2.get_name(),line_feature_1.get_feature_id().get_string(),line_feature_2.get_feature_id().get_string()))
	
		############################################################
		if (len(previous_diverging_line_feats) > 0):
			#;from_time;to_time;SGDUID;GDUID;buffer_distance_km;repGDUID
			temporary_sgdu_and_member_csv_at_time = common_filename_for_temporary_sgdu_and_members_csv.format(time = str(reconstruction_time))
			temp_sgdu_and_gdu_df = pd.read_csv(temporary_sgdu_and_member_csv_at_time, delimiter = ';', header = 0)
			remaining_diverging_line_feats = []
			recorded_distance = -1.00
			if (len(dic_prev_div_line_feats) == 0):
				for line_feature_1,line_feature_2,prev_motion,prev_begin_age,prev_distance in previous_diverging_line_feats:
					pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
					rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
					if (pair_polylids not in dic_prev_div_line_feats and rev_pair_of_polylids not in dic_prev_div_line_feats):
						dic_prev_div_line_feats[pair_polylids] = {'line_feats':(line_feature_1,line_feature_2),'prev_motion':prev_motion, 'age':prev_begin_age, 'dist':prev_distance}
			else:
				for line_feature_1,line_feature_2,prev_motion,prev_begin_age,prev_distance in previous_diverging_line_feats:
					pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
					rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
					if (pair_polylids in dic_prev_div_line_feats):
						dic_prev_div_line_feats[pair_polylids]['prev_motion'] = prev_motion
						dic_prev_div_line_feats[pair_polylids]['age'] = prev_begin_age
						current_line_feature_1,current_line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
						if (current_line_feature_1.is_valid_at_time(reconstruction_time) == False or current_line_feature_2.is_valid_at_time(reconstruction_time) == False):
							output_diverging_line_features.add(current_line_feature_1)
							output_diverging_line_features.add(current_line_feature_2)
							output_begin_age,output_end_age = current_line_feature_1.get_valid_time()
							pairs_of_kin_line_fts.append((output_begin_age,output_end_age,current_line_feature_1.get_description(),current_line_feature_1.get_name(),current_line_feature_2.get_name(),current_line_feature_1.get_feature_id().get_string(),current_line_feature_2.get_feature_id().get_string()))
						if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
							dic_prev_div_line_feats[pair_polylids]['line_feats'] = (line_feature_1,line_feature_2)
						else:
							del dic_prev_div_line_feats[pair_polylids]
					elif (rev_pair_of_polylids in dic_prev_div_line_feats):
						dic_prev_div_line_feats[rev_pair_of_polylids]['prev_motion'] = prev_motion
						dic_prev_div_line_feats[rev_pair_of_polylids]['age'] = prev_begin_age
						current_line_feature_1,current_line_feature_2 = dic_prev_div_line_feats[rev_pair_of_polylids]['line_feats']
						if (current_line_feature_1.is_valid_at_time(reconstruction_time) == False or current_line_feature_2.is_valid_at_time(reconstruction_time) == False):
							output_diverging_line_features.add(current_line_feature_1)
							output_diverging_line_features.add(current_line_feature_2)
							output_begin_age,output_end_age = current_line_feature_1.get_valid_time()
							pairs_of_kin_line_fts.append((output_begin_age,output_end_age,current_line_feature_1.get_description(),current_line_feature_1.get_name(),current_line_feature_2.get_name(),current_line_feature_1.get_feature_id().get_string(),current_line_feature_2.get_feature_id().get_string()))
						if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
							dic_prev_div_line_feats[rev_pair_of_polylids]['line_feats'] = (line_feature_1,line_feature_2)
						else:
							del dic_prev_div_line_feats[rev_pair_of_polylids]
					else:
						if (line_feature_1.is_valid_at_time(reconstruction_time) == True and line_feature_2.is_valid_at_time(reconstruction_time) == True):
							dic_prev_div_line_feats[pair_polylids] = {'line_feats':(line_feature_1,line_feature_2),'prev_motion':prev_motion, 'age':prev_begin_age, 'dist':prev_distance}
			list_of_pair_polyids_to_be_deleted = []
			for pair_polylids in dic_prev_div_line_feats:
				#pair_polylids = line_feature_1.get_name()+'+'+line_feature_2.get_name()
				#rev_pair_of_polylids = line_feature_2.get_name()+'+'+line_feature_1.get_name()
				
				#print('pair_polylids',pair_polylids)
				line_feature_1,line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
				prev_tectonic_motion = dic_prev_div_line_feats[pair_polylids]['prev_motion']
				prev_distance = dic_prev_div_line_feats[pair_polylids]['dist']
				prev_begin_age = dic_prev_div_line_feats[pair_polylids]['age']
				#debug
				# if (pair_polylids == '17300_13241_9277+12009_13906_7560' or pair_polylids == '12009_13906_7560+17300_13241_9277'):
					# print('line_feature_1.get_description()',line_feature_1.get_description())
					# print('line_feature_2.get_description()',line_feature_2.get_description())
					# print('prev_begin_age',prev_begin_age)
					# print('prev_motion',prev_tectonic_motion)
					
				
				SGDUID_for_line_ft_1 = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == line_feature_1.get_reconstruction_plate_id(),'SGDUID'].unique()
				SGDUID_for_line_ft_2 = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == line_feature_2.get_reconstruction_plate_id(),'SGDUID'].unique()
				# if (pair_polylids in list_of_already_evaluated_pairs or rev_pair_of_polylids in list_of_already_evaluated_pairs):
					# continue #these two line features have already been evaluated at this reconstruction time thus take the new tuple
				# else:
					# list_of_already_evaluated_pairs.append(pair_polylids)
				
				#NO NEED TO find the original line features
				# original_con_ocn_line_ft_1 = None
				# original_con_ocn_line_ft_2 = None
				# for con_ocn_line_ft in valid_con_ocn_line_features:
					# if (line_feature_1.get_name() == con_ocn_line_ft.get_shapefile_attribute('POLYLID')):
						# original_con_ocn_line_ft_1 = con_ocn_line_ft
					# elif (line_feature_2.get_name() == con_ocn_line_ft.get_shapefile_attribute('POLYLID')):
						# original_con_ocn_line_ft_2 = con_ocn_line_ft
					# if (original_con_ocn_line_ft_1 is not None and original_con_ocn_line_ft_2 is not None):
						# break
				
				if (recorded_distance == -1.00):
					recorded_distance = prev_distance
				if ((prev_begin_age - reconstruction_time) > time_interval and line_feature_1.is_valid_at_time(reconstruction_time) and line_feature_2.is_valid_at_time(reconstruction_time)):
					reconstructed_current_div_line_features = []
					if (reference is not None):
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_current_div_line_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
					else:
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_current_div_line_features, reconstruction_time, group_with_feature = True)
					final_current_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_current_div_line_features, pygplates.PolylineOnSphere)
					current_reconstr_ft_1, current_reconstr_line_1 = final_current_reconstructed_line_features[0]
					current_reconstr_ft_2, current_reconstr_line_2 = final_current_reconstructed_line_features[1]
					#current_distance = pygplates.GeometryOnSphere.distance(current_reconstr_line_1.get_centroid(),current_reconstr_line_2.get_centroid())
					#recorded_distance = current_distance
					
					reconstructed_prev_div_line_features = []
					if (reference is not None):
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_prev_div_line_features, reconstruction_time + time_interval, anchor_plate_id = reference, group_with_feature = True)
					else:
						pygplates.reconstruct([line_feature_1,line_feature_2], rotation_model, reconstructed_prev_div_line_features, reconstruction_time + time_interval, group_with_feature = True)
					final_prev_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_prev_div_line_features,pygplates.PolylineOnSphere)
					prev_reconstr_ft_1,prev_reconstr_line_1 = final_prev_reconstructed_line_features[0]
					prev_reconstr_ft_2,prev_reconstr_line_2 = final_prev_reconstructed_line_features[1]
					
					reconstructed_point_A_at_from_time = prev_reconstr_line_1.get_centroid()
					reconstructed_point_B_at_from_time = prev_reconstr_line_2.get_centroid()
					reconstructed_point_A_at_to_time = current_reconstr_line_1.get_centroid()
					reconstructed_point_B_at_to_time = current_reconstr_line_2.get_centroid()
					#result_of_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_pos_and_angular_vel_vec(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time, reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time, reconstruction_time, reconstruction_time-time_interval)
					result_of_tectonic_motion, dot_prod_btw_tectonic_motion = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_pos_and_angular_vel_vec(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time, reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time, reconstruction_time+time_interval, reconstruction_time)
					#list_dot_prod.append((reconstruction_time,SGDUID_for_line_ft_1[0],SGDUID_for_line_ft_2[0],line_feature_1.get_reconstruction_plate_id(),line_feature_2.get_reconstruction_plate_id(),dot_prod_btw_tectonic_motion))
					results_of_all_possible_tectonic_motion.append((reconstruction_time,SGDUID_for_line_ft_1[0],SGDUID_for_line_ft_2[0],line_feature_1.get_reconstruction_plate_id(), line_feature_2.get_reconstruction_plate_id(),result_of_tectonic_motion,dot_prod_btw_tectonic_motion))
					#debug
					# print('reconstruction_time',reconstruction_time)
					# print('result_of_tectonic_motion',result_of_tectonic_motion)
					
					
					latA,lonA = reconstructed_point_A_at_from_time.to_lat_lon()
					latB,lonB = reconstructed_point_B_at_from_time.to_lat_lon()
					at_prev_time_distance_in_km_btw_A_and_B = calculate_distance_km_between_two_points_from_haversine_formula(latA,lonA,latB,lonB)
					cur_latA,cur_lonA = reconstructed_point_A_at_to_time.to_lat_lon()
					cur_latB,cur_lonB = reconstructed_point_B_at_to_time.to_lat_lon()
					at_current_time_distance_in_km_btw_A_and_B = calculate_distance_km_between_two_points_from_haversine_formula(cur_latA,cur_lonA,cur_latB,cur_lonB)
					current_distance = at_current_time_distance_in_km_btw_A_and_B
					recorded_distance = current_distance
					
					is_valid_pair_of_line_fts = True
					
					total_stage_rel_rot_of_1_to_2 = find_stage_relative_reconstruction_rotation_(rotation_model,line_feature_1.get_reconstruction_plate_id(),line_feature_2.get_reconstruction_plate_id(),float(reconstruction_time+time_interval),reconstruction_time,reference)
					total_stage_rel_rot_of_2_to_1 = find_stage_relative_reconstruction_rotation_(rotation_model,line_feature_2.get_reconstruction_plate_id(),line_feature_1.get_reconstruction_plate_id(),float(reconstruction_time+time_interval),reconstruction_time,reference)
					if (total_stage_rel_rot_of_1_to_2 is not None):
						if (total_stage_rel_rot_of_1_to_2.represents_identity_rotation() == True):
							is_valid_pair_of_line_fts = False
						else:
							if (total_stage_rel_rot_of_2_to_1 is not None):
								if (total_stage_rel_rot_of_2_to_1.represents_identity_rotation() == True):
									is_valid_pair_of_line_fts = False
							else:
								is_valid_pair_of_line_fts = False
					else:
						is_valid_pair_of_line_fts = False
					if (is_valid_pair_of_line_fts == True):
						final_SGDUID_for_line_1 = None
						final_SGDUID_for_line_2 = None
						for reconstructed_sgdu_ft_at_reconstruction_time, reconstructed_sgdu_at_reconstruction_time in final_reconstructed_sgdu_features:
							SGDUID_of_reconstructed_sgdu_ft = int(reconstructed_sgdu_ft_at_reconstruction_time.get_name())
							SGDUID_for_rand_sgdu_ft = temp_sgdu_and_gdu_df.loc[temp_sgdu_and_gdu_df['GDUID'] == reconstructed_sgdu_ft_at_reconstruction_time.get_reconstruction_plate_id(),'SGDUID'].unique()
							# #find the same value between SGDUID_for_gdu_ft and SGDUID_for_line_ft_1; SGDUID_for_gdu_ft and SGDUID_for_line_ft_2
							intersection_w_line_ft_1 = np.intersect1d(SGDUID_for_rand_sgdu_ft, SGDUID_for_line_ft_1)
							intersection_w_line_ft_2 = np.intersect1d(SGDUID_for_rand_sgdu_ft, SGDUID_for_line_ft_2)
							#if ((SGDUID_of_reconstructed_sgdu_ft not in SGDUID_for_line_ft_1) and (SGDUID_of_reconstructed_sgdu_ft not in SGDUID_for_line_ft_2)):
							#if ((SGDUID_of_reconstructed_sgdu_ft not in intersection_w_line_ft_1) and (SGDUID_of_reconstructed_sgdu_ft not in intersection_w_line_ft_2)):
							if (len(intersection_w_line_ft_1) == 0 and len(intersection_w_line_ft_2) == 0):
								temporary_line_connecting_A_and_B = pygplates.PolylineOnSphere([reconstructed_point_A_at_to_time,reconstructed_point_B_at_to_time])
								if (reconstructed_sgdu_at_reconstruction_time.partition(temporary_line_connecting_A_and_B) == pygplates.PolygonOnSphere.PartitionResult.intersecting):
									is_valid_pair_of_line_fts = False
									break
							else:
								if (len(intersection_w_line_ft_1) > 0):
									final_SGDUID_for_line_1 = reconstructed_sgdu_ft_at_reconstruction_time
								if (len(intersection_w_line_ft_2) > 0):
									final_SGDUID_for_line_2 = reconstructed_sgdu_ft_at_reconstruction_time
						
						if (final_SGDUID_for_line_1 is None or final_SGDUID_for_line_2 is None):
							is_valid_pair_of_line_fts = False
						else:
							if (final_SGDUID_for_line_1.get_name() == final_SGDUID_for_line_2.get_name()):
								is_valid_pair_of_line_fts = False
								
					#debug
					# if (pair_polylids == '17300_13241_9277+12009_13906_7560' or pair_polylids == '12009_13906_7560+17300_13241_9277'):
						# print('line_feature_1.get_description()',line_feature_1.get_description())
						# print('line_feature_2.get_description()',line_feature_2.get_description())
						# print('is_valid_pair_of_line_fts',is_valid_pair_of_line_fts)
						# print('prev_begin_age',prev_begin_age)
						# print('prev_motion',prev_motion)
						# print('result_of_tectonic_motion',result_of_tectonic_motion)
					
					
					has_modified_line_feats = False 
					if ((result_of_tectonic_motion != prev_tectonic_motion) and (prev_distance == 0.00 or at_prev_time_distance_in_km_btw_A_and_B <= 50.00 or is_valid_pair_of_line_fts == True)):
						if ((prev_begin_age - reconstruction_time) >= 3.00*(time_interval)):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
							line_feature_1.set_description('plate_boundary_zone')
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							line_feature_2.set_description('plate_boundary_zone')
							has_modified_line_feats = True
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
						elif (line_feature_1.get_description() == 'plate_boundary_zone' and line_feature_2.get_description() == 'plate_boundary_zone'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							cloned_line_ft_1 = line_feature_1.clone()
							cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
							cloned_line_ft_2 = line_feature_2.clone()
							cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
							output_diverging_line_features.add(cloned_line_ft_1)
							output_diverging_line_features.add(cloned_line_ft_2)
							if (result_of_tectonic_motion == 'D'):
								line_feature_1.set_description('divergent_margin')
								line_feature_2.set_description('divergent_margin')
							elif (result_of_tectonic_motion == 'C'):
								line_feature_1.set_description('convergent_margin')
								line_feature_2.set_description('convergent_margin')
							elif (result_of_tectonic_motion == 'T'):
								line_feature_1.set_description('transform_fault')
								line_feature_2.set_description('transform_fault')
							has_modified_line_feats = True
							pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
							if (result_of_tectonic_motion == 'D'):
								#quickly find mid-point feature
								total_relative_reconstruction_rotation = find_total_relative_reconstruction_rotation_(rotation_model, line_feature_1.get_reconstruction_plate_id(), line_feature_2.get_reconstruction_plate_id(), reconstruction_time, reference)
								if (total_relative_reconstruction_rotation is not None):
									if (total_relative_reconstruction_rotation.represents_identity_rotation() == False):
										#find mid point
										E_pole,_ = total_relative_reconstruction_rotation.get_euler_pole_and_angle()
										quick_mid_pt,mid_pt_order = quickly_derive_mid_point_and_order_of_mid_point_from_two_divergent_points(reconstructed_point_A_at_to_time,reconstructed_point_B_at_to_time,E_pole)
										mid_pt_order = round(mid_pt_order,2)
										#create rift point ft
										# #create an arc
										temporary_GreatCircleArc = pygplates.GreatCircleArc(quick_mid_pt,E_pole)
										normal_unit_vector = temporary_GreatCircleArc.get_great_circle_normal()
										left_gduid, right_gduid = identify_left_gdu_and_right_gdu(normal_unit_vector, quick_mid_pt, reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time, line_feature_1.get_reconstruction_plate_id(), line_feature_2.get_reconstruction_plate_id())
										#create point feature
										name = 'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name()+'_'+str(mid_pt_order)
										rift_point_ft = pygplates.Feature.create_tectonic_section(pygplates.FeatureType.gpml_mid_ocean_ridge, quick_mid_pt, name = name, valid_time = (reconstruction_time,0.00))
										if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
											rift_point_ft.set_left_plate(line_feature_1.get_reconstruction_plate_id())
											rift_point_ft.set_right_plate(line_feature_2.get_reconstruction_plate_id())
										else:
											rift_point_ft.set_left_plate(left_gduid)
											rift_point_ft.set_right_plate(right_gduid)
										rift_point_ft.set_reconstruction_method('HalfStageRotationVersion2')
										rift_point_ft.set_description(str(mid_pt_order))
										if (reference is None):
											pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time)
										else:
											pygplates.reverse_reconstruct(rift_point_ft,rotation_model,reconstruction_time,reference)
										output_subseq_rift_point_features.add(rift_point_ft)
										if ((left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
											unsure_topology_for_MOR_fts.add(rift_point_ft)
										if ((left_gduid == line_feature_1.get_reconstruction_plate_id() and right_gduid == line_feature_2.get_reconstruction_plate_id()) or (left_gduid == right_gduid) or (left_gduid is None) or (right_gduid is None)):
											#'start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'
											list_of_subseq_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name(),mid_pt_order, line_feature_1.get_name(), line_feature_1.get_reconstruction_plate_id(), final_SGDUID_for_line_1.get_reconstruction_plate_id(), line_feature_2.get_name(), line_feature_2.get_reconstruction_plate_id(), final_SGDUID_for_line_2.get_reconstruction_plate_id()))
										else:
											list_of_subseq_ordered_pairs_gdu_fts.append((reconstruction_time,'R'+final_SGDUID_for_line_1.get_name()+'_'+final_SGDUID_for_line_2.get_name(),mid_pt_order, line_feature_2.get_name(), line_feature_2.get_reconstruction_plate_id(), final_SGDUID_for_line_2.get_reconstruction_plate_id(), line_feature_1.get_name(), line_feature_1.get_reconstruction_plate_id(), final_SGDUID_for_line_1.get_reconstruction_plate_id()))
					if ((prev_distance == 0.00 or at_prev_time_distance_in_km_btw_A_and_B <= 50.00 or is_valid_pair_of_line_fts == True)):
						# print('prev_distance',prev_distance)
						# print('recorded_distance',recorded_distance)
						#remaining_diverging_line_feats.append((line_feature_1,line_feature_2,prev_begin_age,recorded_distance))
						if (has_modified_line_feats == True):
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
						else:
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
					elif (is_valid_pair_of_line_fts == False):
						if (line_feature_1.get_description() != 'plate_boundary_zone' and line_feature_2.get_description() != 'plate_boundary_zone'):
							line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
							line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
							if (line_feature_1_begin_time > reconstruction_time):
								cloned_line_ft_1 = line_feature_1.clone()
								cloned_line_ft_1.set_valid_time(line_feature_1_begin_time,reconstruction_time+0.100)
								cloned_line_ft_2 = line_feature_2.clone()
								cloned_line_ft_2.set_valid_time(line_feature_2_begin_time,reconstruction_time+0.100)
								pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
								output_diverging_line_features.add(cloned_line_ft_1)
								output_diverging_line_features.add(cloned_line_ft_2)
							if (pygplates.GeometryOnSphere.distance(current_reconstr_line_1.get_centroid(),current_reconstr_line_2.get_centroid()) == 0.00):
								if (line_feature_1.get_description() == 'convergent_margin' and line_feature_2.get_description() == 'convergent_margin'):
									output_collision.append((reconstruction_time,line_feature_1.get_name(),line_feature_2.get_name()))
							line_feature_1.set_description('plate_boundary_zone')
							line_feature_2.set_description('plate_boundary_zone')
							has_modified_line_feats = True
							if (line_feature_1_end_time <= reconstruction_time and line_feature_2_end_time <= reconstruction_time):
								line_feature_1.set_valid_time(reconstruction_time,line_feature_1_end_time)
								line_feature_2.set_valid_time(reconstruction_time,line_feature_2_end_time)
						
						# if (current_distance > 0.00 and at_current_time_distance_in_km_btw_A_and_B >= 50.00):
							# if (has_modified_line_feats == True):
								# remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
							# else:
								# remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
						
						if (has_modified_line_feats == True):
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,reconstruction_time,recorded_distance))
						else:
							remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
						
				elif (prev_begin_age > reconstruction_time and (line_feature_1.is_valid_at_time(reconstruction_time) == False or line_feature_2.is_valid_at_time(reconstruction_time) == False)):
					line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
					line_feature_2_begin_time,line_feature_2_end_time = line_feature_2.get_valid_time()
					cloned_line_ft_1 = line_feature_1.clone()
					cloned_line_ft_1.set_valid_time(prev_begin_age,reconstruction_time+0.100)
					cloned_line_ft_2 = line_feature_2.clone()
					cloned_line_ft_2.set_valid_time(prev_begin_age,reconstruction_time+0.100)
					output_diverging_line_features.add(cloned_line_ft_1)
					output_diverging_line_features.add(cloned_line_ft_2)
					pairs_of_kin_line_fts.append((line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()))
					list_of_pair_polyids_to_be_deleted.append(pair_polylids)
				elif (prev_begin_age == reconstruction_time):
					remaining_diverging_line_feats.append((line_feature_1,line_feature_2,result_of_tectonic_motion,prev_begin_age,recorded_distance))
			for pair_polylids in list_of_pair_polyids_to_be_deleted:
				del dic_prev_div_line_feats[pair_polylids]
			previous_diverging_line_feats = remaining_diverging_line_feats
			##################################################################
		#debug
		# print('number of features in previous_diverging_line_feats',len(previous_diverging_line_feats))
		# print('number of features in output_diverging_line_features', len(output_diverging_line_features))
		# temporary_output_pair_div_line_fts.write('expected_pair_divergent_line_features_but_failed_at_'+str(reconstruction_time)+'_'+modelname+'_'+yearmonthday+'.shp')
		#temporary_output_pair_div_line_fts = None
		
		#write out the results of all possibile tectonic motion for every pair of SuperGDUs that possibly diverge from each other according to SuperGDU history records
		# output_dataframe = pd.DataFrame.from_records(results_of_all_possible_tectonic_motion, columns = ['reconstruction_time','SGDU1','SGDU2','tectonic_motion'])
		# filename = 'possible_tectonic_motion_from_eval_kin_at_'+str(reconstruction_time)+'_for_'+modelname+'_'+yearmonthday+'.csv'
		# #output_dataframe.to_csv(filename,index=False)
		# output_dataframe = None
		
		
		# filename = 'dot_prod_tectonic_motion_from_eval_kin_for_'+modelname+'_'+yearmonthday+'.csv'
		# if (os.path.isfile(filename)):
			# output_dot_prod_tectonic_motion_df = pd.read_csv(filename)
			# temporary_df = pd.DataFrame.from_records(list_dot_prod, columns = ['reconstruction_time','child_repgduid_1','child_repgduid_2','dot_prod'])
			# output_dot_prod_tectonic_motion_df = pd.concat([output_dot_prod_tectonic_motion_df,temporary_df], ignore_index=True)
			# output_dot_prod_tectonic_motion_df.to_csv(filename, index = False)
		# else:
			# output_dot_prod_tectonic_motion_df = pd.DataFrame.from_records(list_dot_prod, columns = ['reconstruction_time','child_repgduid_1','child_repgduid_2','dot_prod'])
			# output_dot_prod_tectonic_motion_df.to_csv(filename, index = False)
		# list_dot_prod[:] = []
		
		#MUST update reconstruction_time for the main while-loop
		reconstruction_time = reconstruction_time - time_interval
		
	output_rift_point_features.write('rift_point_features_from_eval_kin_for_'+modelname+'_'+yearmonthday+'.shp')
	output_subseq_rift_point_features.write('subseq_rift_point_features_from_eval_kin_for_'+modelname+'_'+yearmonthday+'.shp')
	unsure_topology_for_MOR_fts.write('unsure_topology_for_MOR_fts_from_eval_kin_'+modelname+'_'+yearmonthday+'.shp')
	temporary_MOR_featurecollection = pygplates.FeatureCollection(output_temporary_MOR_line_feats)
	temporary_MOR_featurecollection.write('temporary_MOR_line_feat_for_from_eval_kin_'+modelname+'_'+yearmonthday+'.shp')
	
	#output_diverging_line_features.write('additional_kin_line_features_from_eval_kin_for_'+str(begin_reconstruction_time)+'_'+str(end_reconstruction_time)+'_'+modelname+'_'+yearmonthday+'.shp')
	
	
	#####################
	if (len(dic_prev_div_line_feats) > 0):
		for pair_polylids in dic_prev_div_line_feats:
			line_feature_1,line_feature_2 = dic_prev_div_line_feats[pair_polylids]['line_feats']
			prev_tectonic_motion = dic_prev_div_line_feats[pair_polylids]['prev_motion']
			prev_distance = dic_prev_div_line_feats[pair_polylids]['dist']
			prev_begin_age = dic_prev_div_line_feats[pair_polylids]['age']
			output_diverging_line_features.add(line_feature_1)
			output_diverging_line_features.add(line_feature_2)
			line_feature_1_begin_time,line_feature_1_end_time = line_feature_1.get_valid_time()
			pairs_of_kin_line_fts.append((line_feature_1_begin_time,line_feature_1_end_time,line_feature_1.get_description(),line_feature_1.get_name(),line_feature_2.get_name(),line_feature_1.get_feature_id().get_string(),line_feature_2.get_feature_id().get_string()))
	output_diverging_line_features.write('additional_kin_line_features_from_eval_kin_for_'+str(begin_reconstruction_time)+'_'+str(end_reconstruction_time)+'_'+modelname+'_'+yearmonthday+'.shp')
	####################
	#list_of_ordered_pairs_gdu_fts.append((start_div,name,smallest_circle_angular_radius_degrees, gdu_line_ft_2.get_shapefile_attribute('POLYLID'), gdu_line_ft_2.get_reconstruction_plate_id(), child_repgduid_2, gdu_line_ft_1.get_shapefile_attribute('POLYLID'), gdu_line_ft_1.get_reconstruction_plate_id(), child_repgduid_1))
	output_dataframe = pd.DataFrame.from_records(list_of_ordered_pairs_gdu_fts, columns = ['start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'])
	filename = 'rift_point_features_records_from_eval_kin_for_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	
	####################
	# output_dataframe = pd.DataFrame.from_records(list_of_subseq_ordered_pairs_gdu_fts, columns = ['start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'])
	# filename = 'subseq_rift_point_features_records_from_eval_kin_for_'+modelname+'_'+yearmonthday+'.csv'
	# output_dataframe.to_csv(filename,index=False)
	#######################
	
	output_dataframe = pd.DataFrame.from_records(output_collision, columns = ['reconstruction_time','polylid1','polylid2'])
	filename = 'collisions_zone_for_from_eval_kin_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	
	#line_feature_1_begin_time,reconstruction_time+0.100,cloned_line_ft_1.get_description(),cloned_line_ft_1.get_name(),cloned_line_ft_2.get_name(),cloned_line_ft_1.get_feature_id().get_string(),cloned_line_ft_2.get_feature_id().get_string()
	
	output_dataframe = pd.DataFrame.from_records(pairs_of_kin_line_fts, columns = ['from_time','to_time','type_kin','polylid1','polylid2','fid1','fid2'])
	filename = 'pairs_of_kin_line_fts_from_eval_kin_for_'+modelname+'_'+yearmonthday+'.csv'
	output_dataframe.to_csv(filename,index=False)
	
	filename = "kinematic_btw_sgdus_from_eval_kin_"+modelname+"_"+str(begin_reconstruction_time)+"_"+str(end_reconstruction_time)+"_"+yearmonthday+".csv"
	output_kinematics_btw_sgdus_df = pd.DataFrame.from_records(records_of_sgdus_diverging, columns = ['reconstruction_time','child_1','child_2','child_repgduid_1','child_repgduid_2','tectonic_motion','dot_prod'])
	output_kinematics_btw_sgdus_df.to_csv(filename, index = False)
	
	


def quick_evaluate_kinematic_btw_sgdus(neighbouring_distance_km, oldest_age_to_start_decaying_neighbouring_dist, decaying_rate, line_features_collection, sgdu_features, gdu_features_collection, input_rift_csv, common_filename_for_temporary_sgdu_and_members_csv, time_interval, begin_reconstruction_time, end_reconstruction_time, rotation_model, reference, modelname, yearmonthday):
	reconstruction_time = begin_reconstruction_time
	records_of_sgdus_diverging = []
	dic_of_gdu_members_for_each_sgdu = {}
	reconstructed_sgdu_features = []
	reconstructed_gdu_features = []
	reconstructed_gdu_features_ynger = []
	reconstructed_line_features = []
	reconstructed_line_features_ynger = [] 
	other_reconstructed_gdu_features = []


	if (end_reconstruction_time <= 0.00):
		end_reconstruction_time = time_interval #if end_reconstruction_time == 0.00 and time_interval is 5.00, then update the last time instant to be evaluate to be 5.00
	#initial_neighbouring_distance_km = neighbouring_distance_km
	input_rift_dataframe = pd.read_csv(input_rift_csv)
	
	reconstruction_time = begin_reconstruction_time
	while(reconstruction_time >= end_reconstruction_time):
		#debug
		#temporary_output_pair_div_line_fts = pygplates.FeatureCollection()
		
		print('reconstruction_time',reconstruction_time)
		if (reconstruction_time < oldest_age_to_start_decaying_neighbouring_dist):
			if (neighbouring_distance_km >= 1000.00):
				neighbouring_distance_km = neighbouring_distance_km - (neighbouring_distance_km*decaying_rate)
		
		already_included_pairs_of_line_feats = []
		dic_of_gdu_members_for_each_sgdu.clear()
		reconstructed_sgdu_features[:] = []
		reconstructed_gdu_features[:] = []
		reconstructed_line_features[:] = []
		other_reconstructed_gdu_features[:] = []
		# #8) Find appropriate pairs of sgdus first based on the distance
		# #8i) Find valid sgdu features
		valid_sgdu_features = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(reconstruction_time))]
		# #8ii) Reconstruct sgdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_sgdu_features, rotation_model, reconstructed_sgdu_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_sgdu_features = find_final_reconstructed_geometries(reconstructed_sgdu_features, pygplates.PolygonOnSphere)
		#Find valid gdu features with con-ocn line features
		valid_con_ocn_line_features = [con_ocn_ft for con_ocn_ft in line_features_collection if con_ocn_ft.is_valid_at_time(reconstruction_time)]
		if (reference is not None):
			pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_con_ocn_line_features, rotation_model, reconstructed_line_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_line_features = find_final_reconstructed_geometries(reconstructed_line_features, pygplates.PolylineOnSphere)
		# #8i) Find valid gdu features at reconstruction_time 
		valid_in_time_gdu_features = [gdu_ft for gdu_ft in gdu_features_collection if (gdu_ft.is_valid_at_time(reconstruction_time))]
		valid_gdu_features = []
		already_included_gdu_fts = []
		for valid_line_ft,valid_line in final_reconstructed_line_features:
			#debug
			#if (valid_line_ft.get_reconstruction_plate_id() == 19508):
			#	print(valid_line_ft.get_reconstruction_plate_id())
			
			for gdu_ft in valid_in_time_gdu_features:
				if (valid_line_ft.get_shapefile_attribute('polygid') == gdu_ft.get_shapefile_attribute('POLYGID')):
					if (gdu_ft.get_shapefile_attribute('POLYGID') not in already_included_gdu_fts):
						valid_gdu_features.append(gdu_ft)
						already_included_gdu_fts.append(gdu_ft.get_shapefile_attribute('POLYGID'))
					# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
						# valid_gdu_features.append(gdu_ft)
						#already_included_gdu_fts.append(gdu_ft.get_feature_id())
				# else:
					# if (gdu_ft.get_reconstruction_plate_id() == valid_line_ft.get_reconstruction_plate_id()):
						# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
							# valid_gdu_features.append(gdu_ft)
							# already_included_gdu_fts.append(gdu_ft.get_feature_id())
		#print('len(valid_gdu_features)',len(valid_gdu_features))
		#print('len(valid_con_ocn_line_features)',len(valid_con_ocn_line_features))
						
		# #8ii) Reconstruct gdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_gdu_features, rotation_model, reconstructed_gdu_features, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_gdu_features, rotation_model, reconstructed_gdu_features, reconstruction_time, group_with_feature = True)
		final_reconstructed_gdu_features = find_final_reconstructed_geometries(reconstructed_gdu_features, pygplates.PolygonOnSphere)
		dict_of_gdu_and_centroid = find_centroid_of_each_reconstructed_gdu_ft(final_reconstructed_gdu_features)
		#dict_of_neighbours = find_neighbours_of_each_reconstructed_gdu_ft(dict_of_gdu_and_centroid,threshold_distance_in_km_for_neighbour)
		dic_of_gdu_members_for_each_sgdu = find_gdu_members_of_each_sgdu_feat(valid_gdu_features, valid_sgdu_features, common_filename_for_temporary_sgdu_and_members_csv, reconstruction_time)
		#print('number of sgdu features in dic_of_gdu_members_for_each_sgdu',len(dic_of_gdu_members_for_each_sgdu))
		
		# #8i) Find valid gdu features at reconstruction_time - time_interval
		valid_in_time_gdu_features_in_ynger = [gdu_ft for gdu_ft in gdu_features_collection if (gdu_ft.is_valid_at_time(reconstruction_time-time_interval))]
		valid_gdu_features_ynger = []
		already_included_gdu_fts_ynger = []
		reconstructed_gdu_features_ynger[:] = []
		reconstructed_line_features_ynger[:] = []
		#Find valid gdu features with con-ocn line features
		valid_con_ocn_line_features_ynger = [con_ocn_ft for con_ocn_ft in line_features_collection if con_ocn_ft.is_valid_at_time(reconstruction_time-time_interval)]
		if (reference is not None):
			pygplates.reconstruct(valid_con_ocn_line_features_ynger, rotation_model, reconstructed_line_features_ynger, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_con_ocn_line_features_ynger, rotation_model, reconstructed_line_features_ynger, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_line_features_ynger = find_final_reconstructed_geometries(reconstructed_line_features_ynger, pygplates.PolylineOnSphere)
		for valid_line_ft,valid_line in final_reconstructed_line_features_ynger:
			for gdu_ft in valid_in_time_gdu_features_in_ynger:
				if (valid_line_ft.get_shapefile_attribute('polygid') == gdu_ft.get_shapefile_attribute('POLYGID')):
					if (gdu_ft.get_shapefile_attribute('POLYGID') not in already_included_gdu_fts_ynger):
						valid_gdu_features_ynger.append(gdu_ft)
						already_included_gdu_fts_ynger.append(gdu_ft.get_shapefile_attribute('POLYGID'))
					# if (gdu_ft.get_feature_id() not in already_included_gdu_fts_ynger):
						# valid_gdu_features_ynger.append(gdu_ft)
						#already_included_gdu_fts_ynger.append(gdu_ft.get_feature_id())
				# else:
					# if (gdu_ft.get_reconstruction_plate_id() == valid_line_ft.get_reconstruction_plate_id()):
						# if (gdu_ft.get_feature_id() not in already_included_gdu_fts):
							# valid_gdu_features.append(gdu_ft)
							# already_included_gdu_fts.append(gdu_ft.get_feature_id())
		#print('len(valid_gdu_features_ynger)',len(valid_gdu_features_ynger))
		#print('len(valid_con_ocn_line_features_ynger)',len(valid_con_ocn_line_features_ynger))
		# #8ii) Reconstruct gdu features to reconstruction time
		if (reference is not None):
			pygplates.reconstruct(valid_gdu_features_ynger, rotation_model, reconstructed_gdu_features_ynger, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_gdu_features_ynger, rotation_model, reconstructed_gdu_features_ynger, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_gdu_features_ynger = find_final_reconstructed_geometries(reconstructed_gdu_features_ynger, pygplates.PolygonOnSphere)
		valid_sgdu_features_ynger = [sgdu_ft for sgdu_ft in sgdu_features if (sgdu_ft.is_valid_at_time(reconstruction_time-time_interval))]
		dic_of_gdu_members_for_each_sgdu_ynger = find_gdu_members_of_each_sgdu_feat(valid_gdu_features_ynger, valid_sgdu_features_ynger, common_filename_for_temporary_sgdu_and_members_csv, reconstruction_time-time_interval)
		#print('number of sgdu features in dic_of_gdu_members_for_each_sgdu_ynger',len(dic_of_gdu_members_for_each_sgdu_ynger))
		reconstructed_sgdu_features[:] = []
		if (reference is not None):
			pygplates.reconstruct(valid_sgdu_features_ynger, rotation_model, reconstructed_sgdu_features, reconstruction_time-time_interval, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct(valid_sgdu_features_ynger, rotation_model, reconstructed_sgdu_features, reconstruction_time-time_interval, group_with_feature = True)
		final_reconstructed_sgdu_features_ynger = find_final_reconstructed_geometries(reconstructed_sgdu_features, pygplates.PolygonOnSphere)

		already_recorded_pairs = []
		if (len(final_reconstructed_sgdu_features) > 0):
			for child_sgdu_1_ft, child_sgdu_1_geom in final_reconstructed_sgdu_features:
				for child_sgdu_2_ft, child_sgdu_2_geom in final_reconstructed_sgdu_features:
					if (child_sgdu_1_ft.get_name() != child_sgdu_2_ft.get_name()):
						child_1 = child_sgdu_1_ft.get_name()
						child_2 = child_sgdu_2_ft.get_name()
						pair_of_sgdu_childs = child_1+'_'+child_2
						rev_pair_of_sgdu_childs = child_2+'_'+child_1
						if (pair_of_sgdu_childs in already_recorded_pairs or rev_pair_of_sgdu_childs in already_recorded_pairs):
							continue
						else:
							already_recorded_pairs.append(pair_of_sgdu_childs)
						child_ref_sgduid = child_sgdu_1_ft.get_reconstruction_plate_id()
						child_other_sgduid = child_sgdu_2_ft.get_reconstruction_plate_id()
						
						#'start_div','rift_name','order','lpolylid','left_gdu','lrepgduid','rpolylid','right_gdu','rrepgduid'
						#check whether the two SuperGDUs have been previously evaluated:
						records_of_prev_rifts = input_rift_dataframe.loc[((input_rift_dataframe['start_div'] - reconstruction_time) <= 1.00) & (((input_rift_dataframe['lrepgduid']== child_ref_sgduid) & (input_rift_dataframe['rrepgduid']== child_other_sgduid)) |((input_rift_dataframe['rrepgduid']== child_ref_sgduid) & (input_rift_dataframe['lrepgduid']== child_other_sgduid)))]
						if (len(records_of_prev_rifts) == 0):
							#records_of_sgdus_diverging.append((child_1, child_2, child_ref_sgduid, child_other_sgduid))
							#check whether in the last 5 periods whether the two SuperGDU rotate reltaive to each other
							total_stage_rel_rot_of_other_to_ref = None
							for p in range(0,5):
								total_intervals = (p + 1) * time_interval
								from_rot_time = float(reconstruction_time+total_intervals)
								to_rot_time = from_rot_time-time_interval
								total_stage_rel_rot_of_other_to_ref = find_stage_relative_reconstruction_rotation_(rotation_model,child_other_sgduid,child_ref_sgduid,from_rot_time,to_rot_time,reference)
								if (total_stage_rel_rot_of_other_to_ref is not None):
									if (total_stage_rel_rot_of_other_to_ref.represents_identity_rotation() == False):
										break
							if (total_stage_rel_rot_of_other_to_ref is not None):
								if (total_stage_rel_rot_of_other_to_ref.represents_identity_rotation() == False):
									
									distance_between_sgdu = pygplates.GeometryOnSphere.distance(child_sgdu_1_geom,child_sgdu_2_geom)*pygplates.Earth.mean_radius_in_kms
									#print('distance_between_sgdu',distance_between_sgdu,'neighbouring_distance_km',neighbouring_distance_km)
									if (distance_between_sgdu <= neighbouring_distance_km):
										centroid_sgdu_1 = child_sgdu_1_geom.get_interior_centroid()
										centroid_sgdu_2 = child_sgdu_2_geom.get_interior_centroid()
										E_pole,angle_rads = total_stage_rel_rot_of_other_to_ref.get_euler_pole_and_angle()
										result_of_tectonic_motion,result_of_dot_prod = tectonic_motion.evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(centroid_sgdu_2, centroid_sgdu_1, E_pole)
										records_of_sgdus_diverging.append((reconstruction_time,child_1, child_2, child_ref_sgduid, child_other_sgduid, result_of_tectonic_motion, result_of_dot_prod))
		print('Number of records_of_sgdus_diverging',len(records_of_sgdus_diverging))
		#update reconstruction time
		reconstruction_time = reconstruction_time - time_interval
	filename = "kinematic_btw_sgdus_"+modelname+"_"+str(begin_reconstruction_time)+"_"+str(end_reconstruction_time)+"_"+yearmonthday+".csv"
	output_kinematics_btw_sgdus_df = pd.DataFrame.from_records(records_of_sgdus_diverging, columns = ['reconstruction_time','child_1','child_2','child_repgduid_1','child_repgduid_2','tectonic_motion','dot_prod'])
	output_kinematics_btw_sgdus_df.to_csv(filename, index = False)