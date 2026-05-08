# -*- coding: utf-8 -*-
# --------------------------
# 简化修复版：确保车辆正确生成
# --------------------------

import carla
import time
import numpy as np
import cv2
import math
from collections import deque
import random
import os

class SimpleController:
    """简化控制器类"""
    
    def __init__(self):
        self.waypoint_queue = deque()
        self.target_speed = 50.0  # km/h
        self.manual_reverse = False
    
    def set_waypoints(self, waypoints):
        """设置路点队列"""
        self.waypoint_queue.clear()
        for wp in waypoints:
            self.waypoint_queue.append(wp)
    
    def get_control(self):
        """获取控制指令"""
        throttle = 0.3
        brake = 0.0
        steer = 0.0
        
        if self.waypoint_queue:
            target_waypoint = self.waypoint_queue[0]
            
            # 计算转向
            steer = self._calculate_steer(target_waypoint)
            
            # 速度控制
            if self.manual_reverse:
                throttle = 0.2
            else:
                throttle = 0.3
            
            # 到达路点后移除
            if self._distance_to_waypoint(target_waypoint) < 2.0:
                self.waypoint_queue.popleft()
        
        return throttle, brake, steer, self.manual_reverse
    
    def _calculate_steer(self, waypoint):
        """计算转向角度"""
        return 0.0
    
    def _distance_to_waypoint(self, waypoint):
        """计算到路点的距离"""
        return 1.0
    
    def toggle_reverse(self):
        """切换倒车模式"""
        self.manual_reverse = not self.manual_reverse
        if self.manual_reverse:
            print("已切换到倒车模式")
        else:
            print("已切换到前进模式")

class SimpleDrivingSystem:
    """简化自动驾驶系统"""
    
    def __init__(self):
        self.client = None
        self.world = None
        self.vehicle = None
        self.cameras = {}
        self.camera_image = None
        self.controller = None
        self.current_view = 'third_person'
        self.current_map = 'Town01'
        self.current_weather = 'Clear'
        self.current_color_index = 0
        self.screenshot_dir = 'screenshots'
    
    def connect(self):
        """连接到CARLA服务器"""
        try:
            self.client = carla.Client('localhost', 2000)
            self.client.set_timeout(10.0)
            self.world = self.client.get_world()
            self.current_map = self.world.get_map().name.split('/')[-1]
            print(f"成功连接到CARLA服务器，当前地图: {self.current_map}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def spawn_vehicle(self):
        """生成车辆"""
        try:
            blueprint_library = self.world.get_blueprint_library()
            vehicle_bp = blueprint_library.find('vehicle.tesla.model3')
            
            colors = ['255,0,0', '0,0,255', '0,255,0', '255,255,0', 
                      '255,0,255', '0,255,255', '128,0,128', '255,128,0', 
                      '128,128,128', '255,255,255']
            vehicle_bp.set_attribute('color', colors[self.current_color_index])
            
            spawn_points = self.world.get_map().get_spawn_points()
            if spawn_points:
                self.vehicle = self.world.spawn_actor(vehicle_bp, spawn_points[0])
                print("车辆生成成功")
                return True
            else:
                print("没有找到生成点")
                return False
        except Exception as e:
            print(f"生成车辆失败: {e}")
            return False
    
    def setup_camera(self):
        """设置相机"""
        try:
            blueprint_library = self.world.get_blueprint_library()
            camera_bp = blueprint_library.find('sensor.camera.rgb')
            camera_bp.set_attribute('image_size_x', '800')
            camera_bp.set_attribute('image_size_y', '600')
            camera_bp.set_attribute('fov', '110')
            
            # 第一人称视角
            first_person_transform = carla.Transform(
                carla.Location(x=2.0, z=1.2),
                carla.Rotation(pitch=-15)
            )
            first_person_camera = self.world.spawn_actor(
                camera_bp, first_person_transform, attach_to=self.vehicle
            )
            first_person_camera.listen(lambda image: self.camera_callback(image))
            
            # 第三人称视角
            third_person_transform = carla.Transform(
                carla.Location(x=-8.0, z=6.0),
                carla.Rotation(pitch=-20)
            )
            third_person_camera = self.world.spawn_actor(
                camera_bp, third_person_transform, attach_to=self.vehicle
            )
            third_person_camera.listen(lambda image: self.camera_callback(image))
            
            # 鸟瞰视角
            birdseye_transform = carla.Transform(
                carla.Location(x=0.0, z=30.0),
                carla.Rotation(pitch=-90)
            )
            birdseye_camera = self.world.spawn_actor(
                camera_bp, birdseye_transform, attach_to=self.vehicle
            )
            birdseye_camera.listen(lambda image: self.camera_callback(image, 'birdseye'))
            
            self.cameras['first_person'] = first_person_camera
            self.cameras['third_person'] = third_person_camera
            self.cameras['birdseye'] = birdseye_camera
            
            print("相机设置完成")
            return True
        except Exception as e:
            print(f"设置相机失败: {e}")
            return False
    
    def camera_callback(self, image, view_mode='third_person'):
        """相机回调函数"""
        if view_mode == self.current_view:
            array = np.frombuffer(image.raw_data, dtype=np.dtype('uint8'))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            self.camera_image = array
    
    def setup_controller(self):
        """设置控制器"""
        self.controller = SimpleController()
        print("控制器设置完成")
    
    def update_camera_view(self):
        """更新相机视角"""
        print(f"当前视角: {self.get_view_name()}")
    
    def get_view_name(self):
        """获取视角名称"""
        view_names = {
            'first_person': '第一人称',
            'third_person': '第三人称',
            'birdseye': '鸟瞰图'
        }
        return view_names.get(self.current_view, self.current_view)
    
    def switch_map(self):
        """切换地图"""
        maps = ['Town01', 'Town02', 'Town03']
        current_idx = maps.index(self.current_map) if self.current_map in maps else 0
        next_idx = (current_idx + 1) % len(maps)
        self.current_map = maps[next_idx]
        print(f"已切换到地图: {self.current_map}")
    
    def switch_weather(self):
        """切换天气"""
        weathers = ['Clear', 'Rain', 'Cloudy', 'Wet']
        current_idx = weathers.index(self.current_weather) if self.current_weather in weathers else 0
        next_idx = (current_idx + 1) % len(weathers)
        self.current_weather = weathers[next_idx]
        print(f"已切换到天气: {self.current_weather}")
        
        # 设置天气参数
        weather_params = {
            'Clear': carla.WeatherParameters(cloudiness=10, precipitation=0),
            'Rain': carla.WeatherParameters(cloudiness=80, precipitation=80),
            'Cloudy': carla.WeatherParameters(cloudiness=70, precipitation=0),
            'Wet': carla.WeatherParameters(cloudiness=50, precipitation=30)
        }
        if self.world and self.current_weather in weather_params:
            self.world.set_weather(weather_params[self.current_weather])
    
    def switch_color(self):
        """切换车辆颜色"""
        colors = ['Red', 'Blue', 'Green', 'Yellow', 'Magenta', 'Cyan', 
                  'Purple', 'Orange', 'Gray', 'White']
        self.current_color_index = (self.current_color_index + 1) % len(colors)
        print(f"已切换到颜色: {colors[self.current_color_index]}")
    
    def take_screenshot(self, image):
        """保存截图功能"""
        try:
            os.makedirs(self.screenshot_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            color_names = ['Red', 'Blue', 'Green', 'Yellow', 'Magenta', 'Cyan', 
                          'Purple', 'Orange', 'Gray', 'White']
            color_name = color_names[self.current_color_index]
            filename = f"screenshot_{timestamp}_{self.current_map}_{self.current_weather}_{color_name}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            cv2.imwrite(filepath, image)
            print(f"截图已保存: {filepath}")
        except Exception as e:
            print(f"保存截图时出错: {e}")
    
    def run(self):
        """运行系统"""
        if not self.connect():
            return
        
        if not self.spawn_vehicle():
            return
        
        if not self.setup_camera():
            print("警告：相机设置失败，继续运行...")
        
        self.setup_controller()
        
        print("\n系统准备就绪！")
        print("控制指令:")
        print("  q - 退出程序")
        print("  r - 重置车辆")
        print("  s - 紧急停止")
        print("  x - 切换倒车/前进模式（速度接近0时生效）")
        print("  v - 切换视角（第一人称/第三人称/鸟瞰图）")
        print("  m - 切换地图")
        print("  w - 切换天气")
        print("  c - 切换车辆颜色")
        print("  p - 保存当前画面截图")
        print("\n开始自动行驶...\n")
        
        frame_count = 0
        running = True
        
        try:
            while running:
                velocity = self.vehicle.get_velocity()
                speed = math.sqrt(velocity.x ** 2 + velocity.y ** 2) * 3.6
                
                throttle, brake, steer, reverse = self.controller.get_control()
                control = carla.VehicleControl(
                    throttle=float(throttle),
                    brake=float(brake),
                    steer=float(steer),
                    hand_brake=False,
                    reverse=reverse
                )
                self.vehicle.apply_control(control)
                
                if self.camera_image is not None:
                    display_img = self.camera_image.copy()
                    
                    cv2.putText(display_img, f"Speed: {speed:.1f} km/h",
                                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    cv2.putText(display_img, f"View: {self.get_view_name()}",
                                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.putText(display_img, f"Map: {self.current_map}",
                                (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                    cv2.putText(display_img, f"Weather: {self.current_weather}",
                                (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
                    
                    color_names = ['Red', 'Blue', 'Green', 'Yellow', 'Magenta', 'Cyan', 
                                  'Purple', 'Orange', 'Gray', 'White']
                    cv2.putText(display_img, f"Color: {color_names[self.current_color_index]}",
                                (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 128, 255), 2)
                    
                    if self.controller.manual_reverse:
                        cv2.putText(display_img, "REVERSE MODE",
                                    (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    
                    cv2.imshow('Autonomous Driving', display_img)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("正在退出...")
                    running = False
                elif key == ord('r'):
                    self.reset_vehicle()
                elif key == ord('s'):
                    self.vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0, hand_brake=True))
                    print("紧急停止")
                elif key == ord('x'):
                    if speed < 1.0:
                        self.controller.toggle_reverse()
                    else:
                        print("请先减速到接近停止（速度<1km/h）再切换倒车模式")
                elif key == ord('v'):
                    view_modes = ['third_person', 'first_person', 'birdseye']
                    current_idx = view_modes.index(self.current_view)
                    self.current_view = view_modes[(current_idx + 1) % len(view_modes)]
                    self.update_camera_view()
                elif key == ord('m'):
                    self.switch_map()
                elif key == ord('w'):
                    self.switch_weather()
                elif key == ord('c'):
                    self.switch_color()
                elif key == ord('p'):
                    if self.camera_image is not None:
                        self.take_screenshot(self.camera_image)
                    else:
                        print("当前没有图像可保存")
                
                frame_count += 1
                if frame_count % 100 == 0:
                    print(f"运行中... 帧数: {frame_count}, 速度: {speed:.1f} km/h")
                
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\n用户中断")
        except Exception as e:
            print(f"运行错误: {e}")
        finally:
            self.cleanup()
    
    def reset_vehicle(self):
        """重置车辆位置"""
        print("重置车辆...")
        spawn_points = self.world.get_map().get_spawn_points()
        if spawn_points:
            self.vehicle.set_transform(spawn_points[0])
            print("车辆已重置")
    
    def cleanup(self):
        """清理资源"""
        print("\n正在清理资源...")
        for camera in self.cameras.values():
            if camera:
                camera.stop()
                camera.destroy()
        if self.vehicle:
            self.vehicle.destroy()
        cv2.destroyAllWindows()
        print("清理完成")

def main():
    """主函数"""
    print("自动驾驶系统 - 简化版本")
    print("确保CARLA服务器正在运行...")
    
    system = SimpleDrivingSystem()
    system.run()

if __name__ == "__main__":
    main()
