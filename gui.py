import pygame
import sys

class Button:
    def __init__(self, x, y, width, height, text, normal_color, hover_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.current_color = normal_color
        self.action = action
        self.clicked = False
        
    def draw(self, surface):
        font = pygame.font.SysFont('Arial', 30)
        BLACK = (0, 0, 0)
        # 绘制按钮
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)  # 边框
        
        # 渲染文本
        text_surf = font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        # 检查鼠标是否悬停在按钮上
        if self.rect.collidepoint(pos):
            self.current_color = self.hover_color
            return True
        else:
            self.current_color = self.normal_color
            return False
            
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
                if self.action:
                    return self.action()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.clicked and self.rect.collidepoint(event.pos):
                self.clicked = False
                # 这里可以添加点击后的效果
            else:
                self.clicked = False
        return None