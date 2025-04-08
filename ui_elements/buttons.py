from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty, NumericProperty, ColorProperty, BooleanProperty
from kivy.metrics import dp
from kivy.animation import Animation

class RoundButton(Button):
    """
    自定义圆角按钮增强版，新增功能：
    5. 点击缩放动画
    6. 颜色渐变效果
    7. 按压波纹效果
    """
    scale = NumericProperty(1.0)
    radius = ListProperty([dp(15)]*4)
    border_width = NumericProperty(0)
    border_color = ColorProperty((0, 0, 0, 1))
    bg_color = ColorProperty((0.4, 0.8, 1, 1))
    pressed_color = ColorProperty((0.1, 0.5, 0.9, 1))
    animation_duration = NumericProperty(0.1)  # 动画时长
    scale_factor = NumericProperty(0.95)       # 按压缩放比例
    enable_ripple = BooleanProperty(True)      # 是否启用波纹效果
    ripple_color = ColorProperty([1, 1, 1, 0.3])  # 波纹颜色
    ripple_duration = NumericProperty(0.5)  # 从父类继承
    ripple_scale = NumericProperty(2.0)  # 从父类继承

    # 黑色 0, 0, 0, 1
    # 白色 1, 1, 1, 1
    # 红色 1, 0, 0, 1
    # 绿色 0, 1, 0, 1
    # 蓝色 0, 0, 1, 1
    # 紫色 1, 0, 1, 1
    # 黄色 1, 1, 0, 1
    # 青色 0, 1, 1, 1
    # 灰色 0.5, 0.5, 0.5, 1
    # 透明 0, 0, 0, 0

    def __init__(self, **kwargs):
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_color', (0, 0, 0, 0))
        kwargs.setdefault('ripple_duration', 0.4)  # 设置默认值
        super().__init__(**kwargs)
        self.original_scale = self.scale  # 初始化原始缩放值
        self._init_canvas()
        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas,
            state=self._update_state
        )

    def _init_canvas(self):
        with self.canvas.before:
            # 先画边框
            if self.border_width > 0:
                self.border_color_inst = Color(*self.border_color)
                self.border_rect = RoundedRectangle(
                    pos=self.pos,
                    size=self.size,
                    radius=self.radius
                )

            # 再画背景
            self.bg_color_inst = Color(*self.bg_color)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=self.radius
            )


    def _update_canvas(self, *args):
        """更新图形元素"""
        offset = self.border_width * 2
        self.bg_rect.pos = (self.x + self.border_width, self.y + self.border_width)
        self.bg_rect.size = (self.width - offset, self.height - offset)
        if self.border_width > 0:
            self.border_rect.pos = self.pos
            self.border_rect.size = self.size

    def _update_state(self, instance, value):
        """状态更新处理"""
        # 颜色渐变动画
        Animation(
            rgba=self.pressed_color if value == 'down' else self.bg_color,
            duration=self.animation_duration
        ).start(self.bg_color_inst)

    def on_touch_down(self, touch):
        # 先执行父类的事件处理
        if super().on_touch_down(touch):
            return True  # 父类已处理事件

        if self.collide_point(*touch.pos):
            # 执行你的动画逻辑
            self.original_scale = self.scale
            Animation(
                scale=self.scale_factor,
                t='out_quad',
                duration=self.animation_duration
            ).start(self)

            if self.enable_ripple:
                self._create_ripple_effect(touch)
            return True  # 表示事件已处理

        return False  # 事件未处理



    def on_touch_up(self, touch):
        """处理释放事件"""
        Animation(
            scale=self.original_scale,
            t='out_elastic',
            duration=self.animation_duration * 2
        ).start(self)
        return super().on_touch_up(touch)

    def _create_ripple_effect(self, touch):
        with self.canvas.after:
            # 修改此行：self.pressed_color → self.ripple_color
            ripple_color = Color(*self.ripple_color)  # 关键修改
            ripple = RoundedRectangle(
                pos=(touch.x - 10, touch.y - 10),
                size=(20, 20),
                radius=self.radius
            )

            # 使用 self.ripple_duration 控制动画时间
            anim_shape = Animation(
                pos=(self.x - 50, self.y - 50),
                size=(self.width + 100, self.height + 100),
                duration=self.ripple_duration,  # 使用属性值
                t='out_quad'
            )

            anim_color = Animation(
                a=0,
                duration=self.ripple_duration * 1.2  # 同步调整
            )

            anim_shape.start(ripple)
            anim_color.start(ripple_color)

            # 自动清理画布
            def clean_canvas(*args):
                self.canvas.after.remove(ripple)
                self.canvas.after.remove(ripple_color)

            anim_shape.bind(on_complete=clean_canvas)


    def on_border_width(self, instance, value):
        """属性监听方法"""
        # 添加画布存在性检查
        if self.canvas and self.canvas.before:
            self.canvas.before.clear()
            self._init_canvas()

    def trigger_animation(self):
        """通用动画触发方法"""
        anim = (
                Animation(scale=self.scale_factor, duration=self.animation_duration / 2)
                + Animation(scale=1, duration=self.animation_duration / 2)
        )
        anim.start(self)