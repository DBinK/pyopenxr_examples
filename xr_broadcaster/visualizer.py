import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial.transform import Rotation as R

class ControllerVisualizer:
    def __init__(self):
        # 创建图形和3D轴
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_title('VR Controllers 3D Visualization')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        # 设置坐标轴范围
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(0, 2)
        self.ax.set_zlim(-1, 1)
        
        # 初始化图形元素
        self.left_controller_scatter = None
        self.right_controller_scatter = None
        self.left_axes_lines = [[], [], []]  # X, Y, Z轴线条
        self.right_axes_lines = [[], [], []]  # X, Y, Z轴线条
        
        # 显示图形
        plt.ion()  # 开启交互模式
        plt.show()

    def update(self, left_controller, right_controller):
        """
        更新可视化界面
        
        参数:
        left_controller: xr.Posef 对象，包含orientation和position属性
        right_controller: xr.Posef 对象，包含orientation和position属性
        """
        # 清除旧的轴向线条
        for i in range(3):
            # 删除左控制器的轴线
            for line in self.left_axes_lines[i][:]:  # 使用[:]创建副本以避免迭代时修改列表
                if line in self.ax.lines:
                    line.remove()
            self.left_axes_lines[i].clear()
            
            # 删除右控制器的轴线
            for line in self.right_axes_lines[i][:]:  # 使用[:]创建副本以避免迭代时修改列表
                if line in self.ax.lines:
                    line.remove()
            self.right_axes_lines[i].clear()
        
        # 更新左控制器
        left_pos = left_controller.position
        left_ori = left_controller.orientation
        
        # 绘制左控制器位置点
        if self.left_controller_scatter:
            self.left_controller_scatter.remove()
        self.left_controller_scatter = self.ax.scatter(
            left_pos.x, left_pos.y, left_pos.z, 
            c='blue', s=100, label='Left Controller'
        )
        
        # 绘制左控制器坐标轴
        self._draw_coordinate_system(
            (left_pos.x, left_pos.y, left_pos.z),
            (left_ori.x, left_ori.y, left_ori.z, left_ori.w),
            self.left_axes_lines,
            length=0.1
        )
        
        # 更新右控制器
        right_pos = right_controller.position
        right_ori = right_controller.orientation
        
        # 绘制右控制器位置点
        if self.right_controller_scatter:
            self.right_controller_scatter.remove()
        self.right_controller_scatter = self.ax.scatter(
            right_pos.x, right_pos.y, right_pos.z, 
            c='red', s=100, label='Right Controller'
        )
        
        # 绘制右控制器坐标轴
        self._draw_coordinate_system(
            (right_pos.x, right_pos.y, right_pos.z),
            (right_ori.x, right_ori.y, right_ori.z, right_ori.w),
            self.right_axes_lines,
            length=0.1
        )
        
        # 添加图例
        # 只在第一次添加图例，避免重复
        if not self.ax.get_legend():
            self.ax.legend()
        
        # 更新图形
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
        # 自动调整视角范围
        self._adjust_view_range(left_pos, right_pos)

    def _draw_coordinate_system(self, position, orientation, axes_lines, length=0.1):
        """
        绘制坐标系
        
        参数:
        position: tuple, (x, y, z) 位置坐标
        orientation: tuple, (x, y, z, w) 四元数方向
        axes_lines: list, 存储轴线的列表
        length: float, 坐标轴长度
        """
        # 使用scipy处理四元数旋转
        rotation = R.from_quat(orientation)  # scipy使用(x, y, z, w)格式
        
        # 定义坐标轴方向 (X, Y, Z)
        axes = [
            np.array([length, 0, 0]),  # X轴 - 红色
            np.array([0, length, 0]),  # Y轴 - 绿色
            np.array([0, 0, length])   # Z轴 - 蓝色
        ]
        
        # 旋转坐标轴向量
        rotated_axes = rotation.apply(axes)
        
        # 绘制每条轴线
        colors = ['red', 'green', 'blue']
        for i, (axis, color) in enumerate(zip(rotated_axes, colors)):
            line = self.ax.plot(
                [position[0], position[0] + axis[0]],
                [position[1], position[1] + axis[1]],
                [position[2], position[2] + axis[2]],
                color=color, linewidth=2
            )[0]
            axes_lines[i].append(line)

    def _adjust_view_range(self, left_pos, right_pos):
        """
        自动调整视角范围以适应控制器位置
        
        参数:
        left_pos: 左控制器位置
        right_pos: 右控制器位置
        """
        # 计算所有控制器的坐标范围
        all_x = [left_pos.x, right_pos.x]
        all_y = [left_pos.y, right_pos.y]
        all_z = [left_pos.z, right_pos.z]
        
        # 添加边距
        margin = 0.3
        x_range = (min(all_x) - margin, max(all_x) + margin)
        y_range = (min(all_y) - margin, max(all_y) + margin)
        z_range = (min(all_z) - margin, max(all_z) + margin)
        
        # 更新坐标轴范围
        self.ax.set_xlim(x_range)
        self.ax.set_ylim(y_range)
        self.ax.set_zlim(z_range)

# 示例用法
if __name__ == "__main__":
    # 创建可视化器实例
    visualizer = ControllerVisualizer()
    
    # 示例数据
    from collections import namedtuple
    
    Vector3f = namedtuple('Vector3f', ['x', 'y', 'z'])
    Quaternionf = namedtuple('Quaternionf', ['x', 'y', 'z', 'w'])
    Posef = namedtuple('Posef', ['orientation', 'position'])
    
    # 创建示例Posef对象
    left_pose = Posef(
        orientation=Quaternionf(x=0.435, y=-0.074, z=-0.450, w=0.777),
        position=Vector3f(x=0.151, y=0.909, z=-0.752)
    )
    
    right_pose = Posef(
        orientation=Quaternionf(x=0.493, y=0.330, z=0.317, w=0.740),
        position=Vector3f(x=0.309, y=0.905, z=-0.823)
    )
    
    # 更新可视化
    visualizer.update(left_pose, right_pose)
    
    # 保持窗口开启
    plt.ioff()
    plt.show()