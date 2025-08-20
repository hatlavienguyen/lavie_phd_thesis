import sys
#pygplates is a specific package for plate tectonic study
#sys.path.insert(1,r'C:\Users\Lavie\Desktop\Research\GPlates\pygplates_rev28_python38_win64\pygplates_rev28_python38_win64')
import pygplates
import calculate_position_and_angular_velocity_vector as vec_cal

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
				mean_lat = mean(lat_values)
				mean_lon = mean(lon_values)
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

def find_position_vector_from_point_A_to_point_B(reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time):
	temp_greatcirclearc = pygplates.GreatCircleArc(reconstructed_point_A_at_to_time,reconstructed_point_B_at_to_time)
	if (temp_greatcirclearc.is_zero_length()):
		return None
	vector = temp_greatcirclearc.get_arc_direction(0.00)
	return vector

def evaluate_tectonic_motion_btw_A_and_B_within_period(point_ft_A, point_ft_B , from_time, to_time, rotation_model ,reference):
	reconstructed_features_at_from_time = []
	reconstructed_features_at_to_time = []
	if (reference is not None):
		pygplates.reconstruct([point_ft_A,point_ft_B], rotation_model, reconstructed_features_at_from_time, from_time, anchor_plate_id = reference, group_with_feature = True)
		pygplates.reconstruct([point_ft_A,point_ft_B], rotation_model, reconstructed_features_at_to_time, to_time, anchor_plate_id = reference, group_with_feature = True)
	else:
		pygplates.reconstruct([point_ft_A,point_ft_B], rotation_model, reconstructed_features_at_from_time, from_time, group_with_feature = True)
		pygplates.reconstruct([point_ft_A,point_ft_B], rotation_model, reconstructed_features_at_to_time, to_time, group_with_feature = True)
	
	final_reconstructed_point_features_at_from_time = find_final_reconstructed_geometries(reconstructed_features_at_from_time,pygplates.PointOnSphere)
	final_reconstructed_point_features_at_to_time = find_final_reconstructed_geometries(reconstructed_features_at_to_time,pygplates.PointOnSphere)
	
	#double check which reconstructed feature for A and for B
	first_point_ft_at_from_time,first_reconstructed_point_at_from_time = final_reconstructed_point_features_at_from_time[0]
	second_point_ft_at_from_time,second_reconstructed_point_at_from_time = final_reconstructed_point_features_at_from_time[1]
	
	reconstructed_point_ft_A_at_from_time, reconstructed_point_A_at_from_time = None,None
	reconstructed_point_ft_B_at_from_time, reconstructed_point_B_at_from_time = None,None
	if (first_point_ft_at_from_time.get_reconstruction_plate_id() == point_ft_A.get_reconstruction_plate_id()):
		reconstructed_point_ft_A_at_from_time, reconstructed_point_A_at_from_time = first_point_ft_at_from_time, first_reconstructed_point_at_from_time
		reconstructed_point_ft_B_at_from_time, reconstructed_point_B_at_from_time = second_point_ft_at_from_time, second_reconstructed_point_at_from_time
	else:
		reconstructed_point_ft_B_at_from_time, reconstructed_point_B_at_from_time = first_point_ft_at_from_time, first_reconstructed_point_at_from_time
		reconstructed_point_ft_A_at_from_time, reconstructed_point_A_at_from_time = second_point_ft_at_from_time, second_reconstructed_point_at_from_time
	
	first_point_ft_at_to_time,first_reconstructed_point_at_to_time = final_reconstructed_point_features_at_to_time[0]
	second_point_ft_at_to_time,second_reconstructed_point_at_to_time = final_reconstructed_point_features_at_to_time[1]
	
	reconstructed_point_ft_A_at_to_time, reconstructed_point_A_at_to_time = None,None
	reconstructed_point_ft_B_at_to_time, reconstructed_point_B_at_to_time = None,None
	
	if (first_point_ft_at_to_time.get_reconstruction_plate_id() == point_ft_A.get_reconstruction_plate_id()):
		reconstructed_point_ft_A_at_to_time, reconstructed_point_A_at_to_time = first_point_ft_at_to_time, first_reconstructed_point_at_to_time
		reconstructed_point_ft_B_at_to_time, reconstructed_point_B_at_to_time = second_point_ft_at_to_time, second_reconstructed_point_at_to_time
	else:
		reconstructed_point_ft_B_at_to_time, reconstructed_point_B_at_to_time = first_point_ft_at_to_time, first_reconstructed_point_at_to_time
		reconstructed_point_ft_A_at_to_time, reconstructed_point_A_at_to_time = second_point_ft_at_to_time, second_reconstructed_point_at_to_time
	time_interval = from_time - to_time
	angular_vel_tuple_for_A_rel_to_Earth_center = vec_cal.find_angular_velocity_vector_of_a_PointOnSphere(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time,time_interval)
	dir_angular_vel_for_A_rel_to_Earth_center = angular_vel_tuple_for_A_rel_to_Earth_center[0]
	angular_vel_tuple_for_B_rel_to_Earth_center = vec_cal.find_angular_velocity_vector_of_a_PointOnSphere(reconstructed_point_ft_B_at_from_time, reconstructed_point_B_at_to_time,time_interval)
	dir_angular_vel_for_B_rel_to_Earth_center = angular_vel_tuple_for_B_rel_to_Earth_center[0]
	#apply vector addition rule to find the dir_angular_vel_for_B_rel_to_A: AB + Bc +cA = 0 hence AB = -Bc - cA = cB - cA
	dir_angular_vel_for_B_rel_to_A = dir_angular_vel_for_B_rel_to_Earth_center - dir_angular_vel_for_A_rel_to_Earth_center
	
	position_vec_from_A_to_B_at_to_time = find_position_vector_from_point_A_to_point_B(reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time)
	dir_position_vec_from_A_to_B = position_vec_from_A_to_B_at_to_time[0]
	dot_product = pygplates.Vector3D(dir_position_vec_from_A_to_B,position_vec_from_A_to_B_at_to_time)
	#this dot product is between direction of relative velocity vector and relative position vector NOT between the Euler pole vector and position vector
	if (dot_product > 0.00):
		return 'D'
	elif (dot_product < 0.00):
		return 'C'
	elif (dot_product == 0.00):
		return 'T'

def evaluate_tectonic_motion_btw_A_and_B_at_reconstruction_time_using_Euler_rot(point_ft_A, point_ft_B , reconstruction_time, rotation_model, reference):
	moving_plate_id = point_ft_B.get_reconstruction_plate_id()
	fixed_plate_id = point_ft_A.get_reconstruction_plate_id()
	finite_rotation_1 = None
	finite_rotation_1 = rotation_model.get_rotation(reconstruction_time, moving_plate_id, 0.00, fixed_plate_id, anchor_plate_id = reference)
	if (finite_rotation_1.represents_identity_rotation() == False):
		Euler_pole,angle_rads = finite_rotation_1.get_euler_pole_and_angle()
		
		reconstructed_features_at_to_time = []
		
		if (reference is not None):
			pygplates.reconstruct([point_ft_A,point_ft_B], rotation_model, reconstructed_features_at_to_time, reconstruction_time, anchor_plate_id = reference, group_with_feature = True)
		else:
			pygplates.reconstruct([point_ft_A,point_ft_B], rotation_model, reconstructed_features_at_to_time, reconstruction_time, group_with_feature = True)
		final_reconstructed_point_features_at_to_time = find_final_reconstructed_geometries(reconstructed_features_at_to_time,pygplates.PointOnSphere)
		reconstructed_point_ft_A_at_to_time, reconstructed_point_A_at_to_time = None,None
		reconstructed_point_ft_B_at_to_time, reconstructed_point_B_at_to_time = None,None
		if (first_point_ft_at_to_time.get_reconstruction_plate_id() == point_ft_A.get_reconstruction_plate_id()):
			reconstructed_point_ft_A_at_to_time, reconstructed_point_A_at_to_time = first_point_ft_at_to_time, first_reconstructed_point_at_to_time
			reconstructed_point_ft_B_at_to_time, reconstructed_point_B_at_to_time = second_point_ft_at_to_time, second_reconstructed_point_at_to_time
		else:
			reconstructed_point_ft_B_at_to_time, reconstructed_point_B_at_to_time = first_point_ft_at_to_time, first_reconstructed_point_at_to_time
			reconstructed_point_ft_A_at_to_time, reconstructed_point_A_at_to_time = second_point_ft_at_to_time, second_reconstructed_point_at_to_time
		
		# A.(E_of_B_rel_to_A x B)
		cross_product = pygplates.Vector3D.cross(Euler_pole.to_xyz(),reconstructed_point_B_at_to_time.to_xyz())
		dot_product = pygplates.Vector3D.dot(reconstructed_point_A_at_to_time.to_xyz(),cross_product)
		#original - between the Euler pole vector and position vector of the reference A
		if (dot_product < 0.00):
			return 'D'
		elif (dot_product > 0.00):
			return 'C'
		elif (dot_product == 0.00):
			return 'T'
	else:
		return None

def evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_Euler_pole(reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time, Euler_pole):
	# A.(E_of_B_rel_to_A x B)
	cross_product = pygplates.Vector3D.cross(Euler_pole.to_xyz(),reconstructed_point_B_at_to_time.to_xyz())
	dot_product = pygplates.Vector3D.dot(reconstructed_point_A_at_to_time.to_xyz(),cross_product)
	round_dot_product = round(dot_product, 9)
	#original - between the Euler pole vector and position vector of the reference A
	# if (dot_product > 0.00):
		# return 'C'
	# elif (dot_product < 0.00):
		# return 'D'
	# elif (dot_product == 0.00):
		# return 'T'
	
	#new: Everything is transform - also incorrect signs >0 is convergence <0 is divergence
	# if (round_dot_product > 0.100):
		# return ('D',round_dot_product)
	# elif (round_dot_product < -0.100):
		# return ('C',round_dot_product)
	# elif (round_dot_product <= 0.100 and round_dot_product >= -0.100):
		# return ('T',round_dot_product)
	
	
	#new: 
	if (round_dot_product > 0.00125):
		return ('C',round_dot_product)
	elif (round_dot_product < -0.00125):
		return ('D',round_dot_product)
	elif (round_dot_product <= 0.00125 and round_dot_product >= -0.00125): #
		return ('T',round_dot_product)

def evaluate_tectonic_motion_btw_reconstructed_point_A_and_B_using_pos_and_angular_vel_vec(reconstructed_point_A_at_from_time,reconstructed_point_A_at_to_time,reconstructed_point_B_at_from_time,reconstructed_point_B_at_to_time,from_time,to_time):
	time_interval = from_time - to_time
	# angular_vel_tuple_for_A_rel_to_Earth_center = vec_cal.find_angular_velocity_vector_of_a_PointOnSphere(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time,time_interval)
	# dir_angular_vel_for_A_rel_to_Earth_center = angular_vel_tuple_for_A_rel_to_Earth_center[0]
	# angular_vel_tuple_for_B_rel_to_Earth_center = vec_cal.find_angular_velocity_vector_of_a_PointOnSphere(reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time,time_interval)
	# dir_angular_vel_for_B_rel_to_Earth_center = angular_vel_tuple_for_B_rel_to_Earth_center[0]
	
	dir_vel_for_A_rel_to_Earth_center = vec_cal.approx_direction_of_velocity_vector_of_a_PointOnSphere(reconstructed_point_A_at_from_time, reconstructed_point_A_at_to_time, time_interval)
	dir_vel_for_B_rel_to_Earth_center = vec_cal.approx_direction_of_velocity_vector_of_a_PointOnSphere(reconstructed_point_B_at_from_time, reconstructed_point_B_at_to_time, time_interval)
	
	#apply vector addition rule to find the dir_angular_vel_for_B_rel_to_A: vecB/A = vecB/O - vecA/O
	#start point is A and end point is B
	#dir_angular_vel_for_B_rel_to_A = dir_angular_vel_for_B_rel_to_Earth_center - dir_angular_vel_for_A_rel_to_Earth_center
	dir_vel_for_B_rel_to_A = dir_vel_for_B_rel_to_Earth_center - dir_vel_for_A_rel_to_Earth_center
	
	# position_vec_from_A_to_B_at_to_time = find_position_vector_from_point_A_to_point_B(reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time)
	# position_vec_from_A_to_B_at_from_time = find_position_vector_from_point_A_to_point_B(reconstructed_point_A_at_from_time, reconstructed_point_B_at_from_time)
	
	position_vec_from_A_to_B_at_to_time = vec_cal.approx_dir_position_vector_from_point_A_to_point_B(reconstructed_point_A_at_to_time, reconstructed_point_B_at_to_time)
	position_vec_from_A_to_B_at_from_time = vec_cal.approx_dir_position_vector_from_point_A_to_point_B(reconstructed_point_A_at_from_time, reconstructed_point_B_at_from_time)
	
	if (position_vec_from_A_to_B_at_to_time is None and position_vec_from_A_to_B_at_from_time is not None):
		return 'C'
	elif (position_vec_from_A_to_B_at_to_time is not None and position_vec_from_A_to_B_at_from_time is None):
		return 'D'
	elif (position_vec_from_A_to_B_at_to_time is None and position_vec_from_A_to_B_at_from_time is None):
		return 'C'
	
	dir_position_vec_from_A_to_B = position_vec_from_A_to_B_at_to_time
	#dot_product = pygplates.Vector3D.dot(dir_position_vec_from_A_to_B,dir_angular_vel_for_B_rel_to_A)
	dot_product = pygplates.Vector3D.dot(dir_position_vec_from_A_to_B,dir_vel_for_B_rel_to_A)
	round_dot_product = round(dot_product, 9)
	#debug
	#print('dot_product',dot_product)
	#print('round_dot_product',round_dot_product)
	
	#original
	# if (round_dot_product > 0.00):
		# return 'D'
	# elif (round_dot_product < 0.00):
		# return 'C'
	# elif (round_dot_product == 0.00):
		# return 'T'
		
	#new: Everything is transform
	# if (round_dot_product > 0.100):
		# return ('D',round_dot_product)
	# elif (round_dot_product < -0.100):
		# return ('C',round_dot_product)
	# elif (round_dot_product <= 0.100 and round_dot_product >= -0.100):
		# return ('T',round_dot_product)
	
	#new: Every
	#this dot product is between direction of relative velocity vector and relative position vector NOT between the Euler pole vector and position vector
	if (round_dot_product > 0.00125): 
		return ('D',round_dot_product)
	elif (round_dot_product < -0.00125):
		return ('C',round_dot_product)
	elif (round_dot_product <= 0.00125 and round_dot_product >= -0.00125):
		return ('T',round_dot_product)