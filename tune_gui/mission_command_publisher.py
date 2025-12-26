import rclpy
from rclpy.node import Node

from okmr_msgs import MissionCommand

class MissionCommandPublisher(Node):
    def __init__(self):
        super().__init__('publisher')
        self.publisher_ = self.create_publisher("okmr_msgs/msg/MissionCommand", "/mission_command", 2)
        
    def toggle_mission_control(self):
        self.subscription = self.create_subscription(
            MissionCommand,
            '/mission_command',
            self.sub_callback,
            10
        )
        self.subscription
    
    def sub_callback(self, msg):
        msg = MissionCommand()
        if(msg.command == 1):
            msg.command = 2
            self.publisher_.publish(msg)
        else:
            msg.command = 1
            self.publisher_.publish(msg)
        
def main(args=None):
    rclpy.init(args=args)
    
    mission_command_publisher = MissionCommandPublisher()
    
    rclpy.spin(mission_command_publisher)
    
    mission_command_publisher.destroy_node()
    rclpy.shutdown()
    
if __name__ == '__main__':
    main()