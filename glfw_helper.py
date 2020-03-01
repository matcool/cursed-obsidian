# Mostly copy pasted from https://github.com/swistakm/pyimgui/blob/master/doc/examples/integrations_glfw3.py
import glfw
import OpenGL.GL as gl

import imgui
from imgui.integrations.glfw import GlfwRenderer

class Helper:
    def __init__(self, window_name: str, width: int, height: int, bg):
        self.bg = bg
        imgui.create_context()

        if not glfw.init():
            print("Could not initialize OpenGL context")
            exit(1)

        # OS X supports only forward-compatible core profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

        # Create a windowed mode window and its OpenGL context
        self.window = glfw.create_window(width, height, window_name, None, None)
        glfw.make_context_current(self.window)

        if not self.window:
            glfw.terminate()
            print("Could not initialize Window")
            exit(1)

        self.impl = GlfwRenderer(self.window)

    def stop(self):
        self.impl.shutdown()
        glfw.terminate()
    
    def loop(self):
        return not glfw.window_should_close(self.window)

    def __enter__(self):
        glfw.poll_events()
        self.impl.process_inputs()

        imgui.new_frame()

    def __exit__(self, *args):
        gl.glClearColor(*self.bg, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        self.impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self.window)
