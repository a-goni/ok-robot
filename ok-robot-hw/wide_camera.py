import cv2
import subprocess
from robot import HelloRobot

class WideCamera:
    def __init__(self, camera1_index=6, camera2_index=8, brightness=-50):
        self.camera1_device = f'/dev/video{camera1_index}'
        self.camera2_device = f'/dev/video{camera2_index}'
        
        self.camera1 = cv2.VideoCapture(camera1_index)
        self.camera2 = cv2.VideoCapture(camera2_index)
        
        if not self.camera1.isOpened() or not self.camera2.isOpened():
            print("Error: Unable to open one or both cameras")
            return
        
        # Setting the camera brightness using v4l2-ctl
        self.set_camera_brightness(self.camera1_device, brightness)
        self.set_camera_brightness(self.camera2_device, brightness)

    def set_camera_brightness(self, device_path, brightness_value):
        subprocess.run(['v4l2-ctl', '-d', device_path, '--set-ctrl', f'brightness={brightness_value}'], check=True)

    def capture_image(self):
        # Optionally clear the cache by grabbing a few frames
        for _ in range(5):
            self.camera1.grab()
            self.camera2.grab()

        # Now capture the actual images
        ret1, rgb_image1 = self.camera1.read()
        if not ret1:
            print("Failed to capture image from camera 1")
            return None

        ret2, rgb_image2 = self.camera2.read()
        if not ret2:
            print("Failed to capture image from camera 2")
            return None

        return rgb_image1, rgb_image2

    def save_images(self, image1, image2, path1, path2):
        # Save the images to the specified paths
        cv2.imwrite(path1, image1)
        cv2.imwrite(path2, image2)

    def release(self):
        # Release the camera resources
        self.camera1.release()
        self.camera2.release()
        cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    wide_cam = WideCamera()  # using the correct camera indices now
    hello_robot = HelloRobot()
    hello_robot.robot.move_to_new_nav_posture()
    images = wide_cam.capture_image()
    if images:
        wide_cam.save_images(images[0], images[1], "path_to_save_image1.jpg", "path_to_save_image2.jpg")
    wide_cam.release()
