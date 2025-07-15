import pygame
import sys
from gui import Button

if __name__=="__main__":
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (200, 200, 200)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)

    pygame.init()
    font = pygame.font.SysFont('华文行楷',30)
    screen = pygame.display.set_mode((800,600))
    pygame.display.set_caption("Trino")
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        screen.fill(WHITE)
        pygame.display.flip()
        button1 = Button(300, 200, 200, 50, "页面1", BLACK, BLUE)
        mouse_pos = pygame.mouse.get_pos()
        button1.check_hover(mouse_pos)
        button1.draw(screen)
        clock.tick(60)

    pygame.quit