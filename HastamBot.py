import numpy as np
import math

UCONST_Pi = 3.1415926
URotation180 = 32768
URotationToRadians = UCONST_Pi / URotation180

TARGET_BALL = 0
GRAB_BOOST = 1
RETREAT = 2
class Vector3d:
	def __init__(self,x,y,z):
		self.X = x
		self.Y = y
		self.Z = z

class Entity:
	def __init__(self,vec):
		self.Location = vec
		
class Agent:
	def __init__(self, name, team, index):

		self.name = name
		self.team = team  # 0 towards positive goal, 1 towards negative goal.
		self.index = index

		self.step = 0

		if self.team == 1:
			self.goal = Vector3d(-0.43,-120.17,0)
		if self.team == 0:
			self.goal = Vector3d(0.09,120.34,0)

	def get_me_car(self,game_tick_packet): return game_tick_packet.gamecars[self.index]
	def get_car(self,index,game_tick_packet): return game_tick_packet.gamecars[index]
	def get_ball(self,game_tick_packet): return game_tick_packet.gameball
	def predict_ball(self,ball):
		future_ball = Entity(Vector3d(
			ball.Location.X + 0.5 * ball.Velocity.X,
			ball.Location.Y + 0.5 * ball.Velocity.Y,
			ball.Location.Z + 0.5 * ball.Velocity.Z))
		return future_ball

	def angle(self, Ea, Eb):

		# Nose vector x component
		a_rot1 = math.cos(Ea.Rotation.Pitch * URotationToRadians) * math.cos(Ea.Rotation.Yaw * URotationToRadians)
		# Nose vector y component
		a_rot4 = math.cos(Ea.Rotation.Pitch * URotationToRadians) * math.sin(Ea.Rotation.Yaw * URotationToRadians)
		# Nose vector z component
		# a_rot2 = math.sin(Ea.Rotation.Pitch * URotationToRadians)

		# Need to handle atan2(0,0) case, aka straight up or down, eventually
		a_front_direction = math.atan2(a_rot1, a_rot4)
		angle_to_b = math.atan2((Eb.Location.X - Ea.Location.X), (Eb.Location.Y - Ea.Location.Y))

		#a_front_direction_XZ = math.atan2(a_rot1, a_rot2)
		#angle_to_b_XZ = math.atan2((Eb.Location.X - Ea.Location.X), (Eb.Location.Z - Ea.Location.Z))

		if (not (abs(a_front_direction - angle_to_b) < math.pi)):
			# Add 2pi to negative values
			if (a_front_direction < 0):
				a_front_direction += 2 * math.pi
			if (angle_to_b < 0):
				angle_to_b += 2 * math.pi

		return a_front_direction - angle_to_b #In Radians

	def distance(self, Ea, Eb):

		DX = Ea.Location.X - Eb.Location.X
		DY = Ea.Location.Y - Eb.Location.Y
		DZ = Ea.Location.Z - Eb.Location.Z

		return np.sqrt(DX**2 + DY**2 + DZ**2)

	def create_hit_location(self,me,ball):

		dx = (ball.Location.X - self.goal.X)/(ball.Location.Y - self.goal.Y)
		dy = (ball.Location.Y - self.goal.Y)/(ball.Location.X - self.goal.X)
		
		return Entity(Vector3d(dx * 2 + ball.Location.X,dy * 2 + ball.Location.Y,0))

	def get_output_vector(self, game_tick_packet):
		act_turn = 0
		act_jump = 0
		act_boost = 0
		gas = 1

		self.strat = TARGET_BALL

		ball = self.get_ball(game_tick_packet)
		me = self.get_me_car(game_tick_packet)

		ball_pos = self.predict_ball(ball)
		a_ball = self.angle(me, ball_pos)
		d_ball = self.distance(me,ball_pos)

		for car in game_tick_packet.gamecars:
			if self.distance(car, ball_pos) > d_ball * 2:
				self.strat = RETREAT

		a_target = a_ball

		target_boost = None
		target_dist = 10e8
		for boost in game_tick_packet.gameBoosts:

			d_boost = self.distance(me,boost)
			a_boost = self.angle(me,boost)

			if d_boost < target_dist and abs(a_boost) < math.pi / 2.5 + a_ball and d_boost < a_ball:
				a_target = a_boost

		
		if self.step >= 25:
			self.step = 0
		else:
			self.step += 1


		if d_ball > 1000:
			hit_correction = self.create_hit_location(me,ball_pos)
			d_ball = self.distance(me, hit_correction)
			a_target = self.angle(me, hit_correction)
			gas = 1

		act_turn = np.clip(a_target * 1.2 ,-1 ,1)
		if abs(act_turn) < 0.5 and ball_pos.Location.Z > 1000 and d_ball <1500:
			gas = -0.1


		if abs(act_turn) < 0.1:
			act_boost = 1
		else :
			act_boost = 0

		if d_ball < 700 and abs(act_turn) > 0.2:
			gas = 0
			act_turn = np.clip(act_turn * 6,-1 ,1)

		if d_ball < 400 and ball_pos.Location.Z>20:
			act_jump = 1

		return [gas,act_turn,0,0,0 ,act_jump,act_boost,0]